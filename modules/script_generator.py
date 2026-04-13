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
    topic: str  # Agregado para que hooks.py funcione
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
                result = await self._generate_with_ai(idea, body_duration, tone)
                
                # Detectar si es un mock script completo (contiene 🎬 o es muy largo)
                if isinstance(result, str) and ("🎬" in result or "HOOK" in result or len(result) > 200):
                    # Es un mock completo - usarlo directamente
                    # Parsear el mock para obtener hook, body, cta
                    script_data = self._parse_mock_script(result, idea.hook)
                else:
                    script_data = result
            else:
                script_data = self._generate_basic(idea, body_duration, tone)
        except Exception as e:
            logger.warning(f"⚠️ Error con IA: {e}, usando básico")
            script_data = self._generate_basic(idea, body_duration, tone)
        
        # Limpiar el body si es muy corto o genérico -> usar mock
        body = script_data.get("body", "")
        
        # Si el body es muy corto (menos de 100 chars) o parece genérico, usar el mock
        if len(body.strip()) < 100 or "detalles sobre" in body or "información" in body.lower():
            logger.info("📝 Usando mock script completo...")
            try:
                from data.mock_script import get_mock_script
                mock = get_mock_script()
                script_data = self._parse_mock_script(mock, idea.hook)
                body = script_data.get("body", body)
            except Exception as e:
                logger.warning(f"No se pudo cargar mock: {e}")
        
        return Script(
            id=f"script_{idea.id}",
            idea_id=idea.id,
            topic=idea.topic,  # Agregado para hooks.py
            hook=idea.hook,  # Usar el hook de la idea
            body=body,
            cta=script_data["cta"],
            full_text=f"{idea.hook}. {body} {script_data['cta']}",
            duration=duration,
            word_count=int(duration * 2.5),  # ~150 palabras/min
            tone=tone,
            format=idea.format
        )
    
    async def _generate_with_ai(
        self,
        idea: Idea,
        body_duration: int,
        tone: str
    ) -> Dict[str, str]:
        """Genera guion usando IA o fallback con mock."""
        
        # Prompt para generar un guion completo (no solo el body)
        prompt = f"""Genera un guion completo para YouTube Shorts (~45 segundos) sobre este tema:

Tema: {idea.topic}
Hook: {idea.hook}
Formato: {idea.format}
Tono: {tone}

El guion debe tener:
- Hook inicial (3-5 segundos)
- Body con contenido desarrollado
- CTA final

Responde en JSON con formato: {{"hook": "...", "body": "...", "cta": "..."}}"""
        
        try:
            result = await self.ai_service.generate(
                prompt=prompt,
                temperature=0.8,
                max_tokens=1000
            )
            
            # Si el resultado es muy largo o tiene markers de mock, es el mock completo
            if isinstance(result, str) and ("🎬" in result or len(result) > 300):
                # Es el mock completo - parsearlo
                return self._parse_mock_script(result, idea.hook)
            
            # Intentar parsear como JSON
            try:
                import json
                data = json.loads(result)
                return {"body": data.get("body", result), "cta": data.get("cta", "Sígueme para más contenido 🔥")}
            except:
                # Si no es JSON, usar el resultado como body
                return {"body": result, "cta": "Sígueme para más contenido 🔥"}
                
        except Exception as e:
            logger.warning(f"Error con IA: {e}")
            # Cuando falla, importar el mock directamente
            try:
                from data.mock_script import get_mock_script
                mock = get_mock_script()
                return self._parse_mock_script(mock, idea.hook)
            except:
                return self._generate_basic(idea, body_duration, tone)
    
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
    
    def _parse_mock_script(self, mock_text: str, fallback_hook: str) -> Dict[str, str]:
        """Parsea un mock script completo para obtener hook, body, cta."""
        import re
        
        hook = fallback_hook
        body = ""
        cta = ""
        
        # Extraer el hook si está marcado
        hook_match = re.search(r'(?:HOOK|hook)[^\n]*(?:\n\s*)?(["\']?)([^"\']+)\1', mock_text, re.IGNORECASE)
        if not hook_match:
            # Buscar líneas que empiecen con "
            hook_match = re.search(r'^\s*["\']?([^"\']+)["\']?\s*$', mock_text, re.MULTILINE)
        
        # Extraer CTA si está marcada
        cta_match = re.search(r'CTA[:\s]+([^\n]+)', mock_text, re.IGNORECASE)
        if cta_match:
            cta = cta_match.group(1).strip()
        
        # El body es todo lo que no es hook o cta
        lines = mock_text.split('\n')
        body_lines = []
        for line in lines:
            line = line.strip()
            # Skip empty, hook lines, cta lines
            if not line:
                continue
            if line.startswith('🎬') or 'HOOK' in line.upper() or 'CTA' in line.upper():
                continue
            if '📝' in line or 'SCRIPT' in line.upper():
                continue
            body_lines.append(line)
        
        body = ' '.join(body_lines)
        
        if not cta:
            cta = "Sígueme para más contenido de tecnología 🔥"
        
        return {"body": body, "cta": cta}
    
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