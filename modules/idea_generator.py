"""
Idea Generator - Generación de Ideas
=====================================
Módulo para generar ideas de contenido basadas en trends.
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from app.config import settings
from app.logger import logger
from modules.trends import Trend
from services.ai_service import AIService


@dataclass
class Idea:
    """Representa una idea de contenido."""
    id: str
    trend_id: str
    topic: str
    hook: str
    format: str
    viral_potential: int
    description: str
    target_audience: str
    keywords: List[str]


class IdeaGenerator:
    """
    Generador de ideas de contenido viral.
    
    Usa trends + IA para generar ideas optimizadas.
    """
    
    def __init__(self):
        self.ai_service = AIService()
        self.formats = settings.CONTENT_FORMATS
        
    async def generate_ideas(
        self,
        trends: List[Trend],
        niche: Optional[str] = None,
        styles: List[str] = None,
        count: int = 5
    ) -> List[Idea]:
        """
        Genera ideas basadas en trends.
        
        Args:
            trends: Lista de trends disponibles
            niche: Nicho específico
            styles: Estilos de contenido a usar
            count: Número de ideas a generar
            
        Returns:
            Lista de ideas generadas
        """
        styles = styles or self.formats[:3]
        logger.info(f"🧠 Generando {count} ideas (styles: {styles})")
        
        ideas = []
        
        # Intentar con IA primero
        if trends:
            try:
                ideas = await self._generate_with_ai(trends, styles, count)
            except Exception as e:
                logger.warning(f"⚠️ Error con IA: {e}")
        
        # Si no se generaron ideas (o falló), usar fallback básico
        if not ideas:
            ideas = self._generate_basic(trends, styles, count)
        
        # Ordenar por potencial viral
        ideas.sort(key=lambda x: x.viral_potential, reverse=True)
        
        return ideas
    
    async def _generate_with_ai(
        self,
        trends: List[Trend],
        styles: List[str],
        count: int
    ) -> List[Idea]:
        """Genera ideas usando OpenAI."""
        
        # Construir prompt
        trends_text = "\n".join([f"- {t.topic}" for t in trends[:5]])
        
        prompt = f"""Eres un experto en contenido viral para YouTube Shorts.
Genera {count} ideas de contenido basadas en estas tendencias:

{trends_text}

Para cada idea, genera:
1. Un hook atractivo (máx 15 palabras)
2. El formato (story/list/reaction/tutorial/fact)
3. Descripción breve
4. Audiencia objetivo
5. Keywords relevantes

Responde en JSON:
[
  {{
    "hook": "...",
    "format": "...",
    "description": "...",
    "audience": "...",
    "keywords": ["...", "..."]
  }}
]"""
        
        try:
            response = await self.ai_service.generate(
                prompt=prompt,
                temperature=0.9,
                max_tokens=1000
            )
            
            # Parsear respuesta
            ideas_data = self._parse_ai_response(response)
            
            ideas = []
            for i, data in enumerate(ideas_data):
                ideas.append(Idea(
                    id=f"idea_{i+1}",
                    trend_id=trends[i % len(trends)].id,
                    topic=trends[i % len(trends)].topic,
                    hook=data.get("hook", "Hook automático"),
                    format=data.get("format", "story"),
                    viral_potential=self._estimate_potential(data),
                    description=data.get("description", ""),
                    target_audience=data.get("audience", "general"),
                    keywords=data.get("keywords", [])
                ))
            
            return ideas
            
        except Exception as e:
            logger.warning(f"Error generando con IA: {e}, usando básico")
            return self._generate_basic(trends, styles, count)
    
    def _generate_basic(
        self,
        trends: List[Trend],
        styles: List[str],
        count: int
    ) -> List[Idea]:
        """Genera ideas básicas (sin IA)."""
        
        ideas = []
        for i in range(count):
            trend = trends[i % len(trends)] if trends else None
            
            hook_templates = [
                "5 cosas sobre {topic} que debes saber",
                "¿Sabías esto sobre {topic}?",
                "El secreto de {topic} que nadie te cuenta",
                "Por esto {topic} es trending",
                "{topic} va a cambiar todo en 2025"
            ]
            
            topic = trend.topic if trend else "tema trending"
            hook = hook_templates[i % len(hook_templates)].format(topic=topic)
            
            ideas.append(Idea(
                id=f"idea_{i+1}",
                trend_id=trend.id if trend else "unknown",
                topic=topic,
                hook=hook,
                format=styles[i % len(styles)],
                viral_potential=80 - (i * 10),
                description=f"Idea basada en {topic}",
                target_audience="general",
                keywords=self._extract_keywords(topic)
            ))
        
        return ideas
    
    def _estimate_potential(self, idea_data: Dict) -> int:
        """Estima el potencial viral de una idea."""
        score = 50
        
        # Hook con pregunta tiene más engagement
        if "?" in idea_data.get("hook", ""):
            score += 15
        
        # Formatos probados
        format_score = {
            "list": 85,
            "tutorial": 80,
            "fact": 75,
            "reaction": 70,
            "story": 65
        }
        score += format_score.get(idea_data.get("format", ""), 0) - 50
        
        return min(100, score)
    
    def _parse_ai_response(self, response: str) -> List[Dict]:
        """Parsea la respuesta de la IA."""
        import json
        
        try:
            # Buscar JSON en la respuesta
            start = response.find("[")
            end = response.rfind("]") + 1
            
            if start != -1 and end != 0:
                return json.loads(response[start:end])
        except:
            pass
        
        return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extrae keywords de un texto."""
        words = text.lower().split()
        stopwords = {"the", "a", "an", "is", "are", "was", "of", "in", "on", "at", "que", "de", "el", "la"}
        return [w for w in words if len(w) > 3 and w not in stopwords][:5]
    
    async def validate_idea(self, idea: Idea) -> bool:
        """Valida que una idea sea viable."""
        # Checks básicos
        if len(idea.hook) < 5:
            return False
        if len(idea.hook) > 100:
            return False
        if idea.viral_potential < 30:
            return False
        return True