"""
Idea Tool - Wrapper para generar ideas
=======================================
Conecta el agente con el generador de ideas.
"""

from typing import Dict, Any, List, Optional


class IdeaTool:
    """
    Tool para generar ideas de contenido.
    
    Uso:
        idea_tool = IdeaTool()
        result = await idea_tool.execute(
            trends=[...],
            niche="tecnología",
            style=["story", "list"]
        )
    """
    
    def __init__(self):
        self.name = "generate_idea"
        self.description = "Genera ideas basadas en tendencias actuales"
    
    async def execute(
        self,
        trends: List[Dict],
        niche: Optional[str] = None,
        style: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta la skill de generación de ideas.
        
        Args:
            trends: Lista de trends disponibles
            niche: Nicho específico (opcional)
            style: Estilos a usar (story, list, reaction, tutorial, fact)
            
        Returns:
            Dict con ideas generadas
        """
        # TODO: Conectar con modules/idea_generator.py
        styles = style or ["story", "list", "reaction", "tutorial", "fact"]
        
        ideas = []
        for i, trend in enumerate(trends[:5]):
            ideas.append({
                "id": f"idea_{i+1}",
                "trend_id": trend.get("id", "unknown"),
                "hook": self._generate_hook(trend, niche),
                "format": styles[i % len(styles)],
                "viral_potential": trend.get("viral_score", 70) - (i * 5),
                "topic": trend.get("topic"),
                "description": f"Idea basada en trend {trend.get('topic')}"
            })
        
        return {
            "ideas": ideas,
            "count": len(ideas),
            "styles_used": styles
        }
    
    def _generate_hook(self, trend: Dict, niche: Optional[str]) -> str:
        """Genera un hook basado en el trend."""
        topic = trend.get("topic", "tema")
        return f"5 cosas sobre {topic} que debes saber"
    
    def validate_params(self, params: Dict) -> bool:
        """Valida los parámetros de entrada."""
        if not params.get("trends"):
            return False
        return True