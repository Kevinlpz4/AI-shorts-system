"""
Script Generator - Generación de Guiones
========================================
Módulo para escribir guiones optimizados para shorts.
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.config import settings
from app.logger import logger
from modules.idea_generator import Idea
from services.ai_service import AIService


@dataclass
class Script:
    """Representa un guion para short."""
    id: str
    idea_id: str
    hook: str
    body: str
    cta: str
    full_text: str
    duration: int
    word_count: int
    tone: str
    format: str


class ScriptGenerator:
    """
    Generador de guiones para videos cortos.
    
    Genera guiones optimizados con estructura:
    - Hook (3-5 segundos): Captar atención
    - Body (35-50 segundos): Valor principal
    - CTA (5 segundos): Llamada a la acción
    """
    
    def __init__(self):
        self.ai_service = AIService()
        self.default_duration = 45  # segundos
        
    async def generate_script(
        self,
        idea: Idea,
        duration: int = None,
        tone: str = "educational"
    ) -> Script:
        """
        Genera un guion basado en una idea.
        
        Args:
            idea: Idea a desarrollar
            duration: Duración objetivo en segundos
            tone: Tono del contenido
            
        Returns:
            Guion generado
        """
        duration = duration or self.default_duration
        logger.info(f"✍️ Generando guion ({duration}s, tone: {tone})")
        
        # Calcular distribución
        hook_duration = min(5, int(duration * 0.1))  # 10% para hook
        cta_duration = min(5, int(duration * 0.1))   # 10% para CTA
        body_duration = duration - hook_duration - cta_duration  # 80% para body
        
        # Intentar con IA primero
        try:
            if self.ai_service.is_available():
                script_data = await self._generate_with_ai(idea, body_duration, tone)
            else:
                script_data = self._generate_basic(idea, body_duration, tone)
        except Exception as e:
            logger.warning(f"⚠️ Error con IA: {e}, usando básico")
            script_data = self._generate_basic(idea, body_duration, tone)
        
        return Script(
            id=f"script_{idea.id}",
            idea_id=idea.id,
            hook=idea.hook,  # Usar el hook de la idea
            body=script_data["body"],
            cta=script_data["cta"],
            full_text=f"{idea.hook}. {script_data['body']} {script_data['cta']}",
            duration=duration,
            word_count=int(duration * 2.5),  # ~150 words/min
            tone=tone,
            format=idea.format
        )
    
    async def _generate_with_ai(
        self,
        idea: Idea,
        body_duration: int,
        tone: str
    ) -> Dict[str, str]:
        """Genera guion usando OpenAI."""
        
        prompt = f"""Eres un experto en guiones para YouTube Shorts.
Genera el cuerpo de un guion basado en esta idea:

Hook: {idea.hook}
Formato: {idea.format}
Tono: {tone}
Duración del cuerpo: ~{body_duration} segundos

El guion debe:
- Ser conversacional y energético
- Aportar valor real al espectador
- Usar oraciones cortas y directas
- Evitar relleno innecesario
- Estar en español

Responde solo con el cuerpo del guion (sin hook ni CTA)."""
        
        try:
            body = await self.ai_service.generate(
                prompt=prompt,
                temperature=0.8,
                max_tokens=500
            )
        except Exception as e:
            logger.warning(f"Error con IA: {e}")
            body = self._get_default_body(idea.topic, tone)
        
        return {
            "body": body.strip(),
            "cta": self._get_cta(tone)
        }
    
    def _generate_basic(
        self,
        idea: Idea,
        body_duration: int,
        tone: str
    ) -> Dict[str, str]:
        """Genera guion básico sin IA."""
        
        topic = idea.topic
        
        bodies = {
            "educational": f"Aquí te cuento los detalles sobre {topic}. "
                           f"Esto es lo que nadie te dice y necesitas saber. "
                           f"Presta atención porque esto puede cambiar tu perspectiva.",
            
            "entertaining": f"¿Sabías esto sobre {topic}? Es incrível lo que vas a escuchar. "
                           f"Nadie habla de esto pero es trending ahora. "
                           f"Prepárate para lo que viene porque te va a sorprender.",
            
            "controversial": f"La verdad sobre {topic} que nadie quiere admitir. "
                           f"Esto va a cambiar cómo lo ves. "
                           f"Después de ver esto no vas a ser el mismo.",
            
            "inspirational": f"{topic} nos demuestra que todo es posible. "
                           f"Si ellos pudieron, vos también podés. "
                           f"Aprovecha esta oportunidad y aprendé de su experiencia."
        }
        
        return {
            "body": bodies.get(tone, bodies["educational"]),
            "cta": self._get_cta(tone)
        }
    
    def _get_default_body(self, topic: str, tone: str) -> str:
        """Cuerpo por defecto."""
        return f"Hablemos de {topic}. Esto es lo que tenés que saber. " \
               f"Información clave que vas a usar. No te lo pierdas."
    
    def _get_cta(self, tone: str) -> str:
        """Genera CTA según tono."""
        ctas = {
            "educational": "Sígueme para más contenido educativo like this! 🧠",
            "entertaining": "Sígueme para más contenido interesante! 🔥",
            "controversial": "Déjame tu opinión en comentarios 👇",
            "inspirational": "Dale like si te motivó y compartilo! 💪",
            "humor": "No te olvides de seguirme para más videos así! 😄"
        }
        return ctas.get(tone, "Sígueme para más contenido!")
    
    async def generate_variations(
        self,
        script: Script,
        count: int = 3
    ) -> List[str]:
        """Genera variaciones del guion."""
        
        prompt = f"""Genera {count} variaciones del siguiente guion.
Cada variación debe ser diferente pero mantener el mismo mensaje:

{script.full_text}

Responde solo con las variaciones, una por línea."""
        
        # Por ahora retornar solo la versión original
        return [script.full_text]
    
    def estimate_duration(self, text: str) -> int:
        """Estima la duración del texto en segundos."""
        # Promedio: 150 palabras por minuto = 2.5 palabras por segundo
        word_count = len(text.split())
        return int(word_count / 2.5)
    
    async def optimize_for_retention(self, script: Script) -> Script:
        """Optimiza el guion para máxima retención."""
        # Mejoras recomendadas:
        # 1. Hook más corto
        # 2. Más variedad en el texto
        # 3. Pausas naturales
        # 4. Fin fuerte antes del CTA
        
        # Por ahora retornar igual
        return script