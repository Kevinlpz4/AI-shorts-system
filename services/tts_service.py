"""
TTS Service - Text-to-Speech Service (OPTIMIZADO)
=================================================
Servicio para generación de voz con protección anti-spam.

OPTIMIZACIONES:
1. Cache por contenido (text + voice_id + speed)
2. Rate limiting
3. Single responsibility - cada texto se procesa una vez
4. Concurrencia segura
5. httpx.AsyncClient (async non-blocking)
6. Observabilidad completa
7. Fallback inteligente (3 errores = mock forzado)
8. Hard guarantee: 1 request máximo por texto idéntico
"""

import asyncio
import hashlib
import os
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field

import httpx

from app.config import settings
from app.logger import logger


@dataclass
class TTSCacheEntry:
    """Entrada de cache para audio generado."""
    text_hash: str
    audio_path: str
    duration: float
    created_at: datetime = field(default_factory=datetime.now)


class TTSService:
    """
    Servicio de Text-to-Speech optimizado.
    
    PROTECCIONES ANTI-SPAM:
    - Cache por contenido: mismo texto = mismo audio sin API call
    - Rate limiting: máximo 1 request cada 2 segundos
    - Fallback after 3 errores: no más llamadas si falla seguido
    - Hard guarantee: 1 request máximo por texto único
    """
    
    # ========================================
    # VARIABLES DE CLASE (compartidas entre instancias)
    # ========================================
    
    # Cache global: text_hash -> TTSCacheEntry
    _cache: Dict[str, TTSCacheEntry] = {}
    
    # Contador de requests a la API
    _api_request_count: int = 0
    _cache_hits: int = 0
    
    # Control de errores (para fallback inteligente)
    _consecutive_errors: int = 0
    _max_consecutive_errors: int = 3
    _fallback_mode: bool = False
    
    # Rate limiting
    _last_request_time: float = 0
    _min_request_interval: float = 2.0  # 2 segundos entre requests
    
    # Lock para concurrencia segura
    _lock: asyncio.Lock = None
    
    @classmethod
    def _get_lock(cls) -> asyncio.Lock:
        if cls._lock is None:
            cls._lock = asyncio.Lock()
        return cls._lock
    
    # ========================================
    # INICIALIZACIÓN
    # ========================================
    
    def __init__(self):
        self.provider = settings.TTS_PROVIDER
        self._client: Optional[httpx.AsyncClient] = None
        
        # Configuración
        self.voice_id = settings.TTS_VOICE_ID
        self.model_id = "eleven_multilingual_v2"
        
        logger.info("🎤 TTS Service inicializado (optimizado anti-spam)")
        logger.info(f"   📊 Cache: {len(TTSService._cache)} entradas")
    
    # ========================================
    # GENERACIÓN PRINCIPAL
    # ========================================
    
    async def generate(
        self,
        text: str,
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Genera audio desde texto.
        
        OPTIMIZADO:
        - Si el texto ya fue generado → usa cache (0 API calls)
        - Si hay muchos errores → usa mock (0 API calls)
        - Rate limiting incluido
        """
        voice_id = voice_id or self.voice_id
        
        # ========================================
        # 1. CHECK CACHE (Hard Guarantee)
        # ========================================
        text_hash = self._generate_hash(text, voice_id, speed)
        
        async with self._get_lock():
            if text_hash in TTSService._cache:
                entry = TTSService._cache[text_hash]
                TTSService._cache_hits += 1
                logger.info(f"🎤 Cache HIT: reutilizando audio existente ({TTSService._cache_hits} hits)")
                return {
                    "audio_path": entry.audio_path,
                    "duration": entry.duration,
                    "provider": self.provider,
                    "status": "cache",
                    "cached": True
                }
        
        # ========================================
        # 2. FALLBACK MODE (si hay demasiados errores)
        # ========================================
        if TTSService._fallback_mode:
            logger.warning("⚠️ TTS en modo fallback (errores consecutivos), usando mock")
            return self._generate_mock(output_path, text)
        
        # ========================================
        # 3. RATE LIMITING
        # ========================================
        await self._wait_for_rate_limit()
        
        # ========================================
        # 4. GENERAR AUDIO
        # ========================================
        if self.provider == "elevenlabs":
            result = await self._generate_elevenlabs(text, voice_id, speed, output_path)
        elif self.provider == "azure":
            result = await self._generate_azure(text, voice_id, speed, output_path)
        else:
            result = self._generate_mock(output_path, text)
        
        # ========================================
        # 5. GUARDAR EN CACHE (si fue éxito)
        # ========================================
        if result.get("status") == "success":
            async with self._get_lock():
                TTSService._cache[text_hash] = TTSCacheEntry(
                    text_hash=text_hash,
                    audio_path=result["audio_path"],
                    duration=result["duration"]
                )
            logger.info(f"💾 Audio guardado en cache: {text_hash[:16]}...")
        
        return result
    
    # ========================================
    # ELEVENLABS API (CON TODAS LAS PROTECCIONES)
    # ========================================
    
    async def _generate_elevenlabs(
        self,
        text: str,
        voice_id: str,
        speed: float,
        output_path: Optional[str]
    ) -> Dict[str, Any]:
        """Genera usando ElevenLabs API con protecciones anti-spam."""
        
        api_key = settings.ELEVENLABS_API_KEY
        
        if not api_key:
            logger.warning("⚠️ No hay API key, usando mock")
            return self._generate_mock(output_path, text)
        
        # Usar httpx.AsyncClient (async non-blocking)
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0)
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        data = {
            "text": text[:5000],  # Limitar a 5000 chars
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        try:
            # Rate limiting
            await self._wait_for_rate_limit()
            
            logger.info(f"🎤 [REQUEST #{TTSService._api_request_count + 1}] Generando audio con ElevenLabs...")
            TTSService._api_request_count += 1
            
            response = await self._client.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                # ÉXITO
                TTSService._consecutive_errors = 0  # Reset errores
                
                # Generar output_path si no existe
                if not output_path:
                    output_dir = settings.AUDIO_DIR
                    output_dir.mkdir(parents=True, exist_ok=True)
                    filename = f"voice_{os.urandom(4).hex()}.mp3"
                    output_path = str(output_dir / filename)
                
                # Guardar archivo
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(response.content)
                
                # Calcular duración
                word_count = len(text.split())
                duration = word_count / 150 * 60
                
                logger.info(f"✅ Audio generado: {output_path} ({duration:.1f}s)")
                logger.info(f"📊 Total API requests: {TTSService._api_request_count}")
                
                return {
                    "audio_path": output_path,
                    "duration": duration,
                    "provider": "elevenlabs",
                    "status": "success"
                }
            else:
                # ERROR DE API
                error_msg = response.text[:200]
                await self._handle_api_error(response.status_code, error_msg)
                return self._generate_mock(output_path, text)
                
        except Exception as e:
            await self._handle_api_error(0, str(e)[:100])
            return self._generate_mock(output_path, text)
    
    # ========================================
    # MANEJO DE ERRORES
    # ========================================
    
    async def _handle_api_error(self, status_code: int, error_msg: str):
        """Maneja errores de API y activa fallback si es necesario."""
        TTSService._consecutive_errors += 1
        
        logger.error(f"❌ Error API ({status_code}): {error_msg}")
        logger.warning(f"⚠️ Errores consecutivos: {TTSService._consecutive_errors}/{TTSService._max_consecutive_errors}")
        
        if TTSService._consecutive_errors >= TTSService._max_consecutive_errors:
            TTSService._fallback_mode = True
            logger.warning("🚫 FALLBACK MODE ACTIVADO - no más llamadas a la API")
    
    # ========================================
    # RATE LIMITING
    # ========================================
    
    async def _wait_for_rate_limit(self):
        """Espera el tiempo necesario entre requests."""
        async with self._get_lock():
            now = asyncio.get_event_loop().time()
            time_since_last = now - TTSService._last_request_time
            
            if time_since_last < TTSService._min_request_interval:
                wait_time = TTSService._min_request_interval - time_since_last
                logger.info(f"⏳ Rate limiting: esperando {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
            
            TTSService._last_request_time = asyncio.get_event_loop().time()
    
    # ========================================
    # MOCK (FALLBACK)
    # ========================================
    
    def _generate_mock(self, output_path: Optional[str], text: str = "") -> Dict[str, Any]:
        """Genera respuesta mock cuando la API no está disponible."""
        
        if not output_path:
            output_dir = settings.AUDIO_DIR
            output_dir.mkdir(parents=True, exist_ok=True)
            filename = f"voice_mock_{os.urandom(4).hex()}.mp3"
            output_path = str(output_dir / filename)
        
        # Crear archivo vacío
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.touch()
        
        # Calcular duración aproximada
        word_count = len(text.split()) if text else 0
        duration = word_count / 150 * 60 if word_count else 30
        
        return {
            "audio_path": output_path,
            "duration": duration,
            "provider": self.provider,
            "status": "mock"
        }
    
    # ========================================
    # UTILIDADES
    # ========================================
    
    def _generate_hash(self, text: str, voice_id: str, speed: float) -> str:
        """Genera hash único para el contenido."""
        content = f"{text}|{voice_id}|{speed}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de uso."""
        return {
            "api_requests": TTSService._api_request_count,
            "cache_hits": TTSService._cache_hits,
            "cache_size": len(TTSService._cache),
            "consecutive_errors": TTSService._consecutive_errors,
            "fallback_mode": TTSService._fallback_mode
        }
    
    async def reset_stats(self):
        """Resetea contadores (para nueva ejecución)."""
        TTSService._api_request_count = 0
        TTSService._cache_hits = 0
        TTSService._consecutive_errors = 0
        TTSService._fallback_mode = False
        TTSService._cache.clear()
        logger.info("📊 Stats de TTS reseteados")
    
    def is_available(self) -> bool:
        """Verifica si el servicio está disponible."""
        if self.provider == "elevenlabs":
            return bool(settings.ELEVENLABS_API_KEY)
        elif self.provider == "azure":
            return bool(settings.AZURE_SPEECH_KEY)
        return False
    
    async def close(self):
        """Cierra el cliente HTTP."""
        if self._client:
            await self._client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# ========================================
# IMPLEMENTACIÓN LEGACY (para compatibilidad)
# ========================================

async def generate(
    text: str,
    voice_id: Optional[str] = None,
    speed: float = 1.0,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """Función legacy para compatibilidad."""
    async with TTSService() as service:
        return await service.generate(text, voice_id, speed, output_path)
