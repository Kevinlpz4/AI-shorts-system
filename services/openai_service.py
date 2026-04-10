"""
OpenAI Service - Integración con OpenAI
=======================================
Servicio para usar modelos de OpenAI (GPT-4, etc).
"""

import asyncio
from typing import Optional, Dict, Any
from openai import AsyncOpenAI

from app.config import settings
from app.logger import logger


class OpenAIService:
    """
    Servicio de OpenAI para generación de texto.
    
    Usa la API de OpenAI para:
    - Generación de ideas
    - Escritura de guiones
    - Generación de hooks
    """
    
    def __init__(self):
        self.client = None
        if settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate(
        self,
        prompt: str,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> str:
        """
        Genera texto usando OpenAI.
        
        Args:
            prompt: Prompt para el modelo
            model: Modelo a usar (default: config)
            temperature: Temperatura de generación
            max_tokens: Máximo de tokens
            
        Returns:
            Texto generado
        """
        if not self.client:
            logger.warning("OpenAI API key no configurada")
            return ""
        
        model = model or settings.OPENAI_MODEL
        temperature = temperature or settings.OPENAI_TEMPERATURE
        max_tokens = max_tokens or settings.OPENAI_MAX_TOKENS
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Eres un experto en contenido viral para YouTube Shorts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error en OpenAI: {e}")
            raise
    
    async def generate_with_context(
        self,
        prompt: str,
        context: str,
        **kwargs
    ) -> str:
        """Genera texto con contexto adicional."""
        
        full_prompt = f"""Contexto:
{context}

---
Pregunta:
{prompt}"""
        
        return await self.generate(full_prompt, **kwargs)
    
    async def generate_json(
        self,
        prompt: str,
        schema: Dict = None,
        **kwargs
    ) -> Dict:
        """Genera respuesta en formato JSON."""
        
        # Agregar instrucción de formato JSON
        json_prompt = prompt + "\n\nResponde en formato JSON válido."
        
        if schema:
            json_prompt += f"\n\nSchema requerido: {schema}"
        
        response = await self.generate(json_prompt, **kwargs)
        
        # Parsear JSON
        import json
        try:
            return json.loads(response)
        except:
            logger.warning("No se pudo parsear JSON")
            return {}
    
    async def analyze_text(
        self,
        text: str,
        analysis_type: str = "sentiment"
    ) -> Dict:
        """
        Analiza un texto.
        
        Tipos de análisis:
        - sentiment: Sentimiento del texto
        - keywords: Keywords principales
        - summary: Resumen
        """
        
        prompts = {
            "sentiment": f"Analiza el sentimiento de este texto:\n{text}\n\nResponde con: positivo, negativo o neutro",
            "keywords": f"Extrae las keywords principales de:\n{text}\n\nResponde como lista de palabras",
            "summary": f"Resume brevemente:\n{text}"
        }
        
        prompt = prompts.get(analysis_type, prompts["summary"])
        
        result = await self.generate(prompt, temperature=0.3)
        
        return {
            "analysis_type": analysis_type,
            "result": result,
            "text": text
        }
    
    def is_available(self) -> bool:
        """Verifica si el servicio está disponible."""
        return self.client is not None