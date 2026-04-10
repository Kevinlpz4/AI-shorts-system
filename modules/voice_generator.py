"""
Voice Generator - Text-to-Speech
=================================
Módulo para convertir texto a voz usando TTS.
"""

import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

from app.config import settings
from app.logger import logger
from services.tts_service import TTSService


@dataclass
class VoiceAudio:
    """Representa audio generado por TTS."""
    id: str
    text: str
    audio_path: str
    duration: float
    voice_id: str
    speed: float
    provider: str


class VoiceGenerator:
    """
    Generador de voz para shorts.
    
    Usa servicios TTS como ElevenLabs o Azure.
    """
    
    def __init__(self):
        self.tts_service = TTSService()
        
    async def generate_voice(
        self,
        text: str,
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        output_path: Optional[str] = None
    ) -> VoiceAudio:
        """
        Convierte texto a audio.
        
        Args:
            text: Texto a convertir
            voice_id: ID de voz a usar
            speed: Velocidad de reproducción (0.8 - 1.2)
            output_path: Ruta de salida (opcional)
            
        Returns:
            Audio generado
        """
        voice_id = voice_id or settings.TTS_VOICE_ID
        output_path = output_path or self._default_output_path()
        
        logger.info(f"🔊 Generando voz (voice: {voice_id}, speed: {speed})")
        
        # Generar audio
        audio_data = await self.tts_service.generate(
            text=text,
            voice_id=voice_id,
            speed=speed,
            output_path=output_path
        )
        
        return VoiceAudio(
            id=f"voice_{Path(output_path).stem}",
            text=text,
            audio_path=audio_data.get("audio_path", output_path),
            duration=audio_data.get("duration", self._estimate_duration(text, speed)),
            voice_id=voice_id,
            speed=speed,
            provider=settings.TTS_PROVIDER
        )
    
    def _default_output_path(self) -> str:
        """Genera ruta de salida por defecto."""
        from datetime import datetime
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return str(settings.AUDIO_DIR / f"voice_{timestamp}.mp3")
    
    def _estimate_duration(self, text: str, speed: float) -> float:
        """Estima duración del audio."""
        word_count = len(text.split())
        # ~150 palabras por minuto a velocidad 1.0
        base_duration = word_count / 150 * 60
        return base_duration / speed
    
    async def generate_multiple_voices(
        self,
        text: str,
        voice_ids: list,
        speed: float = 1.0
    ) -> Dict[str, VoiceAudio]:
        """Genera el mismo texto con diferentes voces."""
        
        results = {}
        for voice_id in voice_ids:
            try:
                audio = await self.generate_voice(text, voice_id, speed)
                results[voice_id] = audio
            except Exception as e:
                logger.warning(f"Error con voz {voice_id}: {e}")
        
        return results
    
    async def preview_voice(
        self,
        voice_id: str,
        text: str = "Hola, soy la voz de tu video."
    ) -> str:
        """Genera preview de una voz."""
        
        logger.info(f"🎤 Preview de voz: {voice_id}")
        
        preview = await self.generate_voice(
            text=text,
            voice_id=voice_id,
            speed=1.0
        )
        
        return preview.audio_path
    
    def get_available_voices(self) -> list:
        """Retorna lista de voces disponibles."""
        # Voces de ElevenLabs (ejemplo)
        return [
            {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "language": "es"},
            {"id": "AZnzlk1qwdmhhLCTg", "name": "Arnold", "language": "es"},
            {"id": "VR6A", "name": "Adam", "language": "es"},
            {"id": "pNInz6obpgDQGcFmaJ", "name": "Bella", "language": "es"},
        ]
    
    async def clone_voice(
        self,
        audio_sample_path: str,
        name: str
    ) -> str:
        """Clona una voz desde un sample de audio."""
        
        logger.info(f"🎭 Clonando voz: {name}")
        
        # TODO: Implementar con ElevenLabs Voice Clone API
        return "voice_clone_id"
    
    async def adjust_pitch(
        self,
        audio_path: str,
        pitch: float = 1.0
    ) -> str:
        """Ajusta el pitch del audio."""
        
        # TODO: Implementar con procesamiento de audio
        logger.info(f"🎚️ Ajustando pitch a {pitch}")
        return audio_path
    
    async def add_background_music(
        self,
        voice_path: str,
        music_path: str,
        music_volume: float = 0.2
    ) -> str:
        """Mezcla voz con música de fondo."""
        
        # TODO: Implementar con ffmpeg
        logger.info(f"🎵 Mezclando voz con música (vol: {music_volume})")
        return voice_path