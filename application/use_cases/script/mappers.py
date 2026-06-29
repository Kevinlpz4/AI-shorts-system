"""
Mappers — Conversión entre entidades de dominio y DTOs
========================================================
Funciones PURAS que convierten de un formato a otro.
Sin lógica de negocio, sin efectos secundarios.

Propósito:
  - DRY: los mappers se comparten entre todos los use cases
  - SRP: los casos de uso orquestan, los mappers convierten
  - Testeable: se pueden testear independientemente
"""

from domain.entities.content_idea import ContentIdea
from domain.value_objects.viral_score import ViralScore
from research.domain.entities.research_topic import ResearchTopic


def research_topic_to_content_idea(
    topic: ResearchTopic,
    tone: str = "educational",
    format: str = "story",
) -> ContentIdea:
    """
    Convierte un ResearchTopic aprobado en una ContentIdea
    para que ScriptGeneratorPort pueda generar un guion.

    Es una función pura: mismo input → mismo output.
    No modifica la entidad ResearchTopic.

    Args:
        topic: ResearchTopic aprobado.
        tone: Tono deseado para el guion.
        format: Formato deseado para el guion.

    Returns:
        ContentIdea lista para generar guion.
    """
    return ContentIdea(
        hook=topic.title[:100] if topic.title else "",
        topic=topic.title,
        description=topic.description,
        format=format,
        target_audience="general",
        viral_score=ViralScore(int(topic.score.total)),
        keywords=[topic.title] if topic.title else [],
        trend_id=str(topic.id),
    )
