"""
AI Service - Unified AI Provider
================================
Servicio unificado que soporta OpenAI, Anthropic y Gemini.
Permite cambiar de proveedor fácilmente.
"""

import asyncio
from typing import Optional, Dict, Any
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
    
    def __init__(self, provider: Optional[str] = None):
        """
        Inicializa el servicio.
        
        Args:
            provider: Proveedor a usar (openai, anthropic, gemini)
                     Si None, usa el de settings.AI_PROVIDER
        """
        self.provider_name = provider or settings.AI_PROVIDER
        self._init_clients()
    
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
        # Proveedores en orden de prioridad
        providers_order = ["openai", "anthropic", "gemini"]
        
        # Si se especifica un provider, solo ese
        if provider:
            providers_order = [provider]
        
        # Probar cada proveedor en orden
        last_error = None
        for prov in providers_order:
            if not self.is_available(prov):
                continue
            
            try:
                if prov == "openai":
                    return await self._generate_openai(prompt, model, temperature or 0.8, max_tokens or 2000)
                elif prov == "anthropic":
                    return await self._generate_anthropic(prompt, model, temperature or 0.8, max_tokens or 2000)
                elif prov == "gemini":
                    return await self._generate_gemini(prompt, model, temperature or 0.8, max_tokens or 2000)
            except Exception as e:
                error_msg = str(e)
                # Verificar si es error de cuota/rate limit
                if "quota" in error_msg.lower() or "rate" in error_msg.lower() or "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    logger.warning(f"⚠️ {prov.upper()} sin créditos/rate limit: {error_msg[:50]}...")
                else:
                    logger.warning(f"⚠️ Error con {prov.upper()}: {error_msg[:50]}...")
                
                last_error = e
                # Continuar al siguiente proveedor
                continue
        
        # Si ningún proveedor funcionó, intentar fallback
        logger.info("🔄 Ningún proveedor disponible, usando fallback...")
        return await self._generate_fallback(prompt)
    
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
        """Fallback cuando ningún proveedor está disponible."""
        logger.warning("⚠️ Fallback activado - retornando contenido básico")
        
        # Generar contenido básico basado en el prompt
        if "idea" in prompt.lower():
            return '''[
  {
    "hook": "5 cosas sobre este tema que debes saber",
    "format": "list",
    "description": "Lista con información clave",
    "audience": "general"
  }
]'''
        elif "guion" in prompt.lower() or "script" in prompt.lower():
            return '''{
  "hook": "Descubre esto ahora",
  "body": "Información importante que necesitas saber. Este tema está revolucionando todo. Presta atención porque esto puede cambiar tu perspectiva.",
  "cta": "Sígueme para más contenido like este!"
}'''
        else:
            return "Contenido generado con fallback básico."
    
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
        """Verifica si un proveedor está disponible."""
        provider = provider or self.provider_name
        
        if provider == "openai":
            return self.openai_client is not None
        elif provider == "anthropic":
            return self.anthropic_client is not None
        elif provider == "gemini":
            return self.gemini_client is not None
        
        return False
    
    def get_available_providers(self) -> Dict[str, bool]:
        """Retorna qué proveedores están disponibles."""
        return {
            "openai": self.openai_client is not None,
            "anthropic": self.anthropic_client is not None,
            "gemini": self.gemini_client is not None
        }
    
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
