"""
Hooks Generator - Generación de Hooks Virales
==============================================
Módulo para crear hooks que captan atención inmediatamente.
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.config import settings
from app.logger import logger
from modules.script_generator import Script
from services.ai_service import AIService  # Usar AIService unificado


@dataclass
class Hook:
    """Representa un hook viral."""
    id: str
    text: str
    type: str
    score: int
    variations: List[str] = None
    
    def __post_init__(self):
        if self.variations is None:
            self.variables = []


class HookGenerator:
    """
    Generador de hooks virales para shorts.
    
    Tipos de hooks:
    - question: Pregunta intrigante
    - statement: Afirmación fuerte
    - reveal: Revelación/secreto
    - list: Lista (5 cosas...)
    - trending: Referencia a trend
    - controversial: Afirmación controversial
    """
    
    def __init__(self):
        self.ai_service = AIService()  # Usar servicio unificado
        
        # Templates por tipo
        self.templates = {
            "question": [
                "¿Sabías esto sobre {}?",
                "¿Qué pasaría si {}?",
                "¿Por qué nadie habla de {}?",
                "¿Estás cometiendo este error con {}?",
                "¿Qué sería diferente si supieras sobre {}?"
            ],
            "statement": [
                "Esto va a cambiar {} para siempre",
                "{} es trending ahora y esto es lo que debes saber",
                "La verdad sobre {} que nadie te cuenta",
                "Por esto {} va a explotar en 2025",
                "El futuro de {} está aquí"
            ],
            "reveal": [
                "El secreto de {} que no quieres saber",
                "Lo que nobody te dice sobre {}",
                "La razón por la que {} funciona",
                "El verdadero motivo de {}",
                "Esto es lo que esconde {}"
            ],
            "list": [
                "5 cosas sobre {} que te sorprenderán",
                "3 secretos de {} que debes conocer",
                "7 datos sobre {} que changing todo",
                "10 facts de {} que te dejarán shockeado",
                "4 razones por las que {} es diferente"
            ],
            "trending": [
                "Por esto {} está en todas partes",
                "Qué está pasando con {}?",
                "Por qué {} es el topic del momento",
                "Todo sobre {} que está viral",
                "El fenómeno {} que no puedes ignorar"
            ],
            "controversial": [
                "La verdad incómoda sobre {}",
                "Por qué {} está sobrevalorado",
                "Esto es lo que realmente pasa con {}",
                "El lado oscuro de {}",
                "Por qué deberías dejar de {}"
            ]
        }
        
    async def generate_hooks(
        self,
        script: Script,
        variations: int = 3,
        preferred_type: Optional[str] = None
    ) -> List[Hook]:
        """
        Genera hooks para un guion.
        
        Args:
            script: Guion base
            variations: Número de variaciones
            preferred_type: Tipo de hook preferido
            
        Returns:
            Lista de hooks generados
        """
        logger.info(f"🎯 Generando {variations} hooks (type: {preferred_type or 'mixed'})")
        
        hooks = []
        
        # Usar IA si está disponible
        if settings.OPENAI_API_KEY:
            hooks = await self._generate_with_ai(script, variations)
        
        if not hooks:
            # Fallback a templates
            hooks = self._generate_from_templates(
                script.topic, preferred_type, variations
            )
        
        # Ordenar por score
        hooks.sort(key=lambda x: x.score, reverse=True)
        
        return hooks
    
    async def _generate_with_ai(
        self,
        script: Script,
        count: int
    ) -> List[Hook]:
        """Genera hooks usando OpenAI."""
        
        prompt = f"""Eres un experto en hooks virales para YouTube Shorts.
Genera {count} hooks diferentes basados en este guion:

Tema: {script.topic}
Formato: {script.format}

Cada hook debe:
- Ser corto (5-15 palabras)
- Captar atención inmediatamente
- Ser específico y no genérico
- Funcionar como opening

Tipos a usar: question, statement, reveal, list, trending, controversial

Responde en JSON:
[
  {{"text": "...", "type": "..."}}
 ]"""
        
        try:
            response = await self.ai_service.generate(
                prompt=prompt,
                temperature=0.9,
                max_tokens=500
            )
            
            hooks_data = self._parse_ai_response(response)
            return self._create_hooks(hooks_data)
            
        except Exception as e:
            logger.warning(f"Error con IA: {e}")
            return []
    
    def _generate_from_templates(
        self,
        topic: str,
        preferred_type: Optional[str],
        count: int
    ) -> List[Hook]:
        """Genera hooks desde templates."""
        
        hooks = []
        types = [preferred_type] if preferred_type else list(self.templates.keys())
        
        for i in range(count):
            hook_type = types[i % len(types)]
            templates = self.templates.get(hook_type, [])
            
            if templates:
                template = templates[i % len(templates)]
                text = template.format(topic)
                
                hooks.append(Hook(
                    id=f"hook_{i+1}",
                    text=text,
                    type=hook_type,
                    score=self._calculate_score(hook_type, text),
                    variations=[text]
                ))
        
        return hooks
    
    def _calculate_score(self, hook_type: str, text: str) -> int:
        """Calcula score de efectividad."""
        score = 50
        
        # Bonus por tipo
        type_scores = {
            "question": 90,    # Preguntas funcionan muy bien
            "reveal": 88,      # Secretos son efectivos
            "list": 85,        # Listas predecibles pero funcionan
            "statement": 75,   # Statements necesitan ser fuertes
            "trending": 80,    # Trendy funciona
            "controversial": 70  # Puede ser arriesgado
        }
        score = type_scores.get(hook_type, 50)
        
        # Bonus por palabras clave
        if any(kw in text.lower() for kw in ["secreto", " truth", "nadie", "nadie", "sorprendente", "cambiar"]):
            score += 5
        
        # Penalty por muy largo
        if len(text.split()) > 15:
            score -= 10
        
        return min(100, score)
    
    def _parse_ai_response(self, response: str) -> List[Dict]:
        """Parsea respuesta de IA."""
        import json
        
        try:
            start = response.find("[")
            end = response.rfind("]") + 1
            
            if start != -1 and end != 0:
                return json.loads(response[start:end])
        except:
            pass
        
        return []
    
    def _create_hooks(self, hooks_data: List[Dict]) -> List[Hook]:
        """Crea objetos Hook desde datos."""
        hooks = []
        
        for i, data in enumerate(hooks_data):
            hooks.append(Hook(
                id=f"hook_{i+1}",
                text=data.get("text", ""),
                type=data.get("type", "statement"),
                score=self._calculate_score(data.get("type", ""), data.get("text", "")),
                variations=[data.get("text", "")]
            ))
        
        return hooks
    
    def select_best_hook(
        self,
        hooks: List[Hook],
        performance_data: Optional[Dict] = None
    ) -> Hook:
        """
        Selecciona el mejor hook basado en datos.
        
        Args:
            hooks: Lista de hooks disponibles
            performance_data: Datos de rendimiento histórico
            
        Returns:
            El hook seleccionado
        """
        if not hooks:
            return Hook(
                id="default",
                text="Hook por defecto",
                type="statement",
                score=50
            )
        
        # Por ahora seleccionar el de mayor score
        # TODO: Usar performance_data cuando esté disponible
        return hooks[0]
    
    async def test_hook(self, hook: Hook) -> Dict[str, Any]:
        """Simula un test del hook."""
        return {
            "hook_id": hook.id,
            "predicted_score": hook.score,
            "recommendations": [
                "Más corto = mejor retención",
                "Evitar frases genéricas",
                "Ser específico en lugar de vago"
            ]
        }