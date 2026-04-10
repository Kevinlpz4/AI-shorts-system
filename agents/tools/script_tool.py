"""
Script Tool - Wrapper para escribir guiones
==========================================
Conecta el agente con el generador de guiones.
"""

from typing import Dict, Any, Optional


class ScriptTool:
    """
    Tool para escribir guiones optimizados para shorts.
    
    Uso:
        script_tool = ScriptTool()
        result = await script_tool.execute(
            idea={...},
            duration=45,
            tone="educational"
        )
    """
    
    def __init__(self):
        self.name = "write_script"
        self.description = "Escribe guion optimizado para short (30-60s)"
    
    async def execute(
        self,
        idea: Dict,
        duration: int = 45,
        tone: str = "educational"
    ) -> Dict[str, Any]:
        """
        Ejecuta la skill de escritura de guion.
        
        Args:
            idea: Idea seleccionada
            duration: Duración objetivo en segundos
            tone: Tono del contenido (educational, entertaining, etc.)
            
        Returns:
            Dict con el guion generado
        """
        # TODO: Conectar con modules/script_generator.py
        
        hook_text = idea.get("hook", "Hook automático")
        topic = idea.get("topic", "tema relevante")
        
        # Estructura: Hook (3s) + Valor (45s) + CTA (5s)
        body = self._generate_body(topic, tone)
        
        return {
            "script": {
                "hook": hook_text,
                "body": body,
                "cta": self._generate_cta(tone),
                "full_text": f"{hook_text}. {body}",
                "total_duration": duration,
                "words": int(duration * 2.5),
                "tone": tone,
                "format": idea.get("format", "story")
            },
            "idea_id": idea.get("id"),
            "duration": duration
        }
    
    def _generate_body(self, topic: str, tone: str) -> str:
        """Genera el cuerpo del guion."""
        if tone == "educational":
            return f"Contenido educativo sobre {topic}. " \
                   f"Información clave que el espectador debe saber."
        elif tone == "entertaining":
            return f"Algo increíble sobre {topic} que te va a surprise. " \
                   f"Esto es lo que nadie te cuenta."
        elif tone == "controversial":
            return f"La verdad sobre {topic} que nadie quiere admitir. " \
                   f"Prepárate para lo que viene."
        else:
            return f"Datos importantes sobre {topic} que debes conocer."
    
    def _generate_cta(self, tone: str) -> str:
        """Genera el call-to-action."""
        ctas = {
            "educational": "Sígueme para más contenido educativo like this! #learn",
            "entertaining": "Sígueme para más contenido interesante! 🔥",
            "controversial": "Déjame tu opinión en comentarios! 👇",
            "inspirational": "Dale like y comparte si te motivó!"
        }
        return ctas.get(tone, "Sígueme para más contenido!")
    
    def validate_params(self, params: Dict) -> bool:
        """Valida los parámetros de entrada."""
        if not params.get("idea"):
            return False
        duration = params.get("duration", 45)
        if duration < 15 or duration > 90:
            return False
        return True