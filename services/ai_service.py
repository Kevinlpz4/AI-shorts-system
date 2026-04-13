"""
AI Service - Unified AI Provider
================================
Servicio unificado que soporta OpenAI, Anthropic y Gemini.
Permite cambiar de proveedor fácilmente.
"""

import asyncio
from typing import Optional, Dict, Any, List
from enum import Enum

# OpenAI
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None

# Anthropic
try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    AsyncAnthropic = None

# Gemini
try:
    from google.genai import client as google_client
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    google_client = None

from app.config import settings
from app.logger import logger


class AIProvider(Enum):
    """Proveedores de IA disponibles."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class AIService:
    """
    Servicio unificado de IA.
    
    Soporta múltiples proveedores:
    - OpenAI (gpt-4o-mini)
    - Anthropic (claude-haiku)
    - Gemini (gemini-2.0-flash-lite)
    
    Configurable via AI_PROVIDER en .env
    """
    
    # Singleton para evitar múltiples inicializaciones
    _instance = None
    _initialized = False
    
    # Contadores de uso (reseteables)
    _api_requests: int = 0
    _cache_hits: int = 0
    
    def __new__(cls, provider: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, provider: Optional[str] = None):
        """
        Inicializa el servicio.
        
        Args:
            provider: Proveedor a usar (openai, anthropic, gemini)
                     Si None, usa el de settings.AI_PROVIDER
        """
        if not AIService._initialized:
            self.provider_name = provider or settings.AI_PROVIDER
            self._init_clients()
            AIService._initialized = True
    
    def _init_clients(self):
        """Inicializa los clientes disponibles."""
        self.openai_client = None
        self.anthropic_client = None
        self.gemini_client = None
        
        # OpenAI
        if OPENAI_AVAILABLE and settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("✅ OpenAI client inicializado")
        
        # Anthropic
        if ANTHROPIC_AVAILABLE and settings.ANTHROPIC_API_KEY:
            self.anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            logger.info("✅ Anthropic client inicializado")
        
        # Gemini (google-genai nuevo API)
        if GEMINI_AVAILABLE and settings.GEMINI_API_KEY:
            try:
                self.gemini_client = google_client.Client(api_key=settings.GEMINI_API_KEY)
                logger.info("✅ Gemini client inicializado")
            except Exception as e:
                logger.warning(f"Error inicializando Gemini: {e}")
    
    async def generate(
        self,
        prompt: str,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        provider: Optional[str] = None
    ) -> str:
        """
        Genera texto usando el proveedor configurado.
        Si el proveedor falla, intenta automáticamente los otros disponibles.
        
        Args:
            prompt: Prompt para el modelo
            model: Modelo a usar (opcional, usa el default del proveedor)
            temperature: Temperatura de generación
            max_tokens: Máximo de tokens
            provider: Proveedor específico (override)
            
        Returns:
            Texto generado
        """
    async def generate(
        self,
        prompt: str,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        provider: Optional[str] = None
    ) -> str:
        """
        Genera texto usando el mejor proveedor disponible.
        
        Lógica:
        1. Si provider especificado → solo ese
        2. Si no → encontrar primer proveedor disponible
        3. Si falla por falta de credits → probar siguiente
        4. Si ninguno funciona → fallback
        
        Máx 1 llamada exitosa (no bucle infinito).
        """
        # Si se especifica provider, solo ese
        if provider:
            return await self._try_single_provider(
                provider, prompt, model, temperature, max_tokens
            )
        
        # Encontrar primer proveedor disponible (el mejor candidato)
        providers_order = self._get_available_providers_order()
        
        if not providers_order:
            logger.info("🔄 No hay proveedores disponibles, usando fallback...")
            return await self._generate_fallback(prompt)
        
        # Intentar el primer proveedor
        first_provider = providers_order[0]
        result = await self._try_single_provider(
            first_provider, prompt, model, temperature, max_tokens
        )
        
        # Si el resultado no es fallback (tuvo éxito), retornarlo
        if not self._is_fallback_result(result):
            return result
        
        # Si falló por falta de credits, intentar el siguiente proveedor
        if len(providers_order) > 1:
            logger.info(f"🔄 {first_provider.upper()} sin créditos, intentando siguiente...")
            second_provider = providers_order[1]
            result = await self._try_single_provider(
                second_provider, prompt, model, temperature, max_tokens
            )
            if not self._is_fallback_result(result):
                return result
            
            # Si el segundo también falló, probar el tercero si existe
            if len(providers_order) > 2:
                logger.info(f"🔄 {second_provider.upper()} sin créditos, intentando último...")
                third_provider = providers_order[2]
                result = await self._try_single_provider(
                    third_provider, prompt, model, temperature, max_tokens
                )
                return result
        
        # Ninguno funcionó → fallback
        logger.info("🔄 Ningún proveedor con créditos, usando fallback...")
        return await self._generate_fallback(prompt)
    
    def _get_available_providers_order(self) -> List[str]:
        """Retorna lista de proveedores disponibles.
        
        Usa el proveedor configurado primero, luego los demás.
        """
        # Proveedor configurado primero
        configured = self.provider_name
        
        available = []
        
        # Primero el proveedor configurado (si tiene cliente)
        if configured == "openai" and self.openai_client:
            available.append("openai")
        elif configured == "anthropic" and self.anthropic_client:
            available.append("anthropic")
        elif configured == "gemini" and self.gemini_client:
            available.append("gemini")
        
        # Luego los otros proveedores disponibles
        if self.openai_client and "openai" not in available:
            available.append("openai")
        if self.anthropic_client and "anthropic" not in available:
            available.append("anthropic")
        if self.gemini_client and "gemini" not in available:
            available.append("gemini")
        
        return available
    
    def _is_fallback_result(self, result: str) -> bool:
        """Detecta si el resultado es del fallback (contenido básico)."""
        fallback_markers = [
            "contenido básico",
            "Contenido generado con fallback",
            "5 cosas sobre este tema"
        ]
        return any(marker.lower() in result.lower() for marker in fallback_markers)
    
    async def _try_single_provider(
        self,
        provider: str,
        prompt: str,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> str:
        """Intenta generar con un solo proveedor."""
        
        # Verificar si este proveedor ya está marcado como sin créditos
        if hasattr(self, '_providers_without_credits') and provider in self._providers_without_credits:
            logger.info(f"⏭️ {provider.upper()} ya sin créditos (skip)")
            raise Exception(f"{provider} sin créditos previamente")
        
        try:
            if provider == "openai":
                return await self._generate_openai(prompt, model, temperature or 0.8, max_tokens or 2000)
            elif provider == "anthropic":
                return await self._generate_anthropic(prompt, model, temperature or 0.8, max_tokens or 2000)
            elif provider == "gemini":
                return await self._generate_gemini(prompt, model, temperature or 0.8, max_tokens or 2000)
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "rate" in error_msg.lower() or "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "insufficient_quota" in error_msg:
                logger.warning(f"⚠️ {provider.upper()} sin créditos, marcándolo para no reintentar...")
                # Marcar este proveedor como sin créditos
                if not hasattr(self, '_providers_without_credits'):
                    self._providers_without_credits = set()
                self._providers_without_credits.add(provider)
            else:
                logger.warning(f"⚠️ Error con {provider.upper()}: {error_msg[:50]}...")
        
        # Retornar string especial para indicar que falló
        return "FALLBACK_TRIGGER"
    
    async def _generate_openai(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.8,
        max_tokens: int = 2000
    ) -> str:
        """Genera usando OpenAI."""
        if not self.openai_client:
            raise Exception("OpenAI no disponible. Verificá OPENAI_API_KEY")
        
        model = model or settings.OPENAI_MODEL
        
        response = await self.openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Eres un experto en contenido viral para YouTube Shorts."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    async def _generate_anthropic(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.8,
        max_tokens: int = 2000
    ) -> str:
        """Genera usando Anthropic Claude."""
        if not self.anthropic_client:
            raise Exception("Anthropic no disponible. Verificá ANTHROPIC_API_KEY")
        
        model = model or settings.ANTHROPIC_MODEL
        
        response = await self.anthropic_client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system="Eres un experto en contenido viral para YouTube Shorts.",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def _generate_gemini(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.8,
        max_tokens: int = 2000
    ) -> str:
        """Genera usando Google Gemini."""
        if not self.gemini_client:
            raise Exception("Gemini no disponible. Verificá GEMINI_API_KEY")
        
        model = model or settings.GEMINI_MODEL
        
        # Configurar generación
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        
        # Agregar system prompt
        full_prompt = f"""Eres un experto en contenido viral para YouTube Shorts.

{prompt}"""
        
        # Nueva API de google-genai
        response = self.gemini_client.models.generate_content(
            model=model,
            contents=full_prompt,
            config=generation_config
        )
        
        return response.text
    
    async def _generate_fallback(self, prompt: str) -> str:
        """Fallback cuando ningún proveedor está disponible - usa el mock script."""
        logger.warning("⚠️ Fallback activado - usando mock script")
        
        # Intentar importar el mock
        try:
            from data.mock_script import get_mock_script
            mock = get_mock_script()
        except ImportError:
            logger.warning("⚠️ No se pudo importar mock_script")
            mock = None
        
        prompt_lower = prompt.lower()
        
        # Si el prompt es para script/guion, retornar el mock completo
        if "guion" in prompt_lower or "script" in prompt.lower():
            if mock:
                return mock
            else:
                # Mock hardcoded de emergencia
                return """🎬 HOOK (0-3s):
"Esta inteligencia artificial ya está reemplazando trabajos… y probablemente ya la has usado."

📝 SCRIPT COMPLETO:
Esta inteligencia artificial ya está cambiando el mundo del trabajo, y lo más impactante es que probablemente ya la has usado.

Se llama ChatGPT, y puede hacer tareas que antes tomaban horas en solo minutos.
Desde escribir textos, responder clientes, hasta programar código básico.

Empresas de todo el mundo ya la están usando para automatizar procesos y reducir costos.

Pero aquí viene lo fuerte,
no necesitas ser experto para usarla.

Hoy, cualquier persona puede hacer el trabajo de varios con solo saber cómo usar esta herramienta.

Y esto no es el futuro,
ya está pasando ahora.

La verdadera pregunta es,
vas a aprender a usarla a tu favor,
o vas a ser reemplazado por alguien que sí lo haga.

🎯 CTA: Sígueme para más contenido de tecnología que va a cambiar tu vida 🔥"""
        
        # Si es para idea, retornar idea simple
        if "idea" in prompt.lower():
            import json
            import random
            idea = {
                "hook": "Esta IA ya está reemplazando trabajos",
                "format": "story",
                "description": "Contenido sobre inteligencia artificial y el futuro del trabajo",
                "audience": "general",
                "topic": "Inteligencia Artificial",
                "potential_views": random.randint(100000, 500000)
            }
            return json.dumps([idea], ensure_ascii=False)
        
        # Default
        return mock or "Contenido de fallback"
    
    async def generate_json(
        self,
        prompt: str,
        schema: Dict = None,
        **kwargs
    ) -> Dict:
        """Genera respuesta en formato JSON."""
        json_prompt = prompt + "\n\nResponde en formato JSON válido."
        
        if schema:
            json_prompt += f"\n\nSchema requerido: {schema}"
        
        response = await self.generate(json_prompt, **kwargs)
        
        import json
        try:
            return json.loads(response)
        except:
            logger.warning("No se pudo parsear JSON")
            return {}
    
    def is_available(self, provider: Optional[str] = None) -> bool:
        """Verifica si un proveedor está disponible y tiene créditos."""
        provider = provider or self.provider_name
        
        if provider == "openai":
            return self.openai_client is not None
        elif provider == "anthropic":
            return self.anthropic_client is not None
        elif provider == "gemini":
            return self.gemini_client is not None
        
        return False
    
    def has_any_provider_with_credits(self) -> bool:
        """Verifica si AL MENOS un proveedor tiene créditos reales."""
        # Por ahora siempre retorna True para intentar
        # En el futuro se podría hacer un test calllightweight
        return True
    
    def get_available_providers(self) -> Dict[str, bool]:
        """Retorna qué proveedores están disponibles."""
        return {
            "openai": self.openai_client is not None,
            "anthropic": self.anthropic_client is not None,
            "gemini": self.gemini_client is not None
        }
    
    def get_best_provider(self) -> Optional[str]:
        """Retorna el mejor proveedor disponible (el primero que funcione)."""
        providers = self.get_available_providers()
        for prov, available in providers.items():
            if available:
                return prov
        return None
    
    async def generate_idea(self, trends: list) -> str:
        """Genera una idea viral basada en trends."""
        trends_text = "\n".join([f"- {t}" for t in trends])
        
        prompt = f"""Eres un experto en contenido viral para YouTube Shorts.

Basado en estas tendencias:
{trends_text}

Genera UNA idea viral con:
- Hook atractivo (máx 15 palabras)
- Formato (story/list/reaction/tutorial/fact)
- Descripción breve
- Audiencia objetivo

Responde en JSON:
{{
  "hook": "...",
  "format": "...",
  "description": "...",
  "audience": "..."
}}"""
        
        return await self.generate_json(prompt)
    
    async def generate_script(self, idea: str, duration: int = 45) -> str:
        """Genera un guion basado en una idea."""
        prompt = f"""Convierte esta idea en un guion para YouTube Shorts (máx {duration} segundos):

IDEA:
{idea}

Estructura requerida:
- Hook inicial fuerte (3-5 segundos)
- Desarrollo rápido con valor
- Final con CTA (call to action)

El guion debe:
- Ser conversacional y energético
- Aportar valor real
- Usar oraciones cortas
- Estar en español

Responde en JSON:
{{
  "hook": "...",
  "body": "...",
  "cta": "..."
 }}"""
        
        return await self.generate_json(prompt)
    
    # =========================================
    # OBSERVABILIDAD
    # =========================================
    
    @classmethod
    def reset_counters(cls):
        """Resetea contadores entre ejecuciones."""
        cls._api_requests = 0
        cls._cache_hits = 0
        if hasattr(cls, '_providers_without_credits'):
            cls._providers_without_credits.clear()
        logger.info("📊 Contadores de AI Service reseteados")
    
    @classmethod
    def get_stats(cls) -> dict:
        """Retorna estadísticas de uso."""
        return {
            "api_requests": cls._api_requests,
            "cache_hits": cls._cache_hits,
            "total_requests": cls._api_requests + cls._cache_hits
        }
