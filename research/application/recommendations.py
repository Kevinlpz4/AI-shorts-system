"""
Recommendations — Pure functions for script recommendations
============================================================
Recomendaciones determinísticas de tono, duración y nicho para un
ResearchTopic. No tienen dependencias externas ni estado — son
funciones puras, fáciles de testear unitariamente.

Todas las reglas están codificadas acá mismo, visibles y auditables.
Si en el futuro se necesitan reglas ML-driven, se agrega un
RecommendationEngine separado que use estas funciones como fallback.

Uso:
    from research.application.recommendations import get_recommendations
    recs = get_recommendations(topic)
    # recs.tone, recs.duration, recs.niche, recs.reasoning
"""

from dataclasses import dataclass, field
from research.domain.entities.research_topic import ResearchTopic


@dataclass
class ScriptRecommendations:
    """
    Recomendaciones del sistema para generar un script.

    Attributes:
        tone: Tono recomendado (educational, controversial, informative, etc.)
        duration: Duración recomendada en segundos
        niche: Nicho temático (tecnología, negocios, salud, etc.)
        reasoning: Explicación textual de cada recomendación
    """

    tone: str
    duration: int
    niche: str
    reasoning: dict = field(default_factory=dict)


# ── Mapping determinístico fuente → tono ─────────────────────────────

_SOURCE_TONE_MAP: dict[str, tuple[str, str]] = {
    "google-news": ("educational", "Fuente noticiosa → tono educativo y objetivo"),
    "rss": ("educational", "Contenido RSS → tono educativo y estructurado"),
    "google-news-rss": ("educational", "Feed de noticias → tono educativo"),
    "twitter": ("controversial", "Twitter → contenido opinativo y controversial"),
}


def recommend_tone(source_name: str) -> tuple[str, str]:
    """
    Recomienda un tono según el nombre de la fuente.

    Args:
        source_name: Nombre de la fuente (e.g. 'google-news', 'twitter').

    Returns:
        Tupla (tono, razonamiento).
    """
    if source_name.startswith("manual"):
        return ("informative", "Entrada manual → tono informativo general")
    return _SOURCE_TONE_MAP.get(
        source_name,
        ("educational", "Fuente estándar → tono educativo por defecto"),
    )


# ── Mapping score → duración ─────────────────────────────────────────


def recommend_duration(score_total: float) -> tuple[int, str]:
    """
    Recomienda una duración según el score total del topic.

    Reglas:
        >= 80 → 90s  (contenido de alto valor)
        60-79 → 60s  (contenido valioso)
        < 60  → 30s  (contenido simple)

    Args:
        score_total: Score total ponderado (0-100).

    Returns:
        Tupla (duración_segundos, razonamiento).
    """
    if score_total >= 80:
        return (90, "Score alto (≥80): contenido con alto valor → 90s")
    elif score_total >= 60:
        return (60, "Score medio (60-79): contenido valioso → 60s")
    else:
        return (30, "Score bajo (<60): contenido simple → 30s")


# ── Mapping keywords → nicho ─────────────────────────────────────────

_KEYWORDS_MAP: dict[str, list[str]] = {
    "tecnología": [
        "ia", "inteligencia artificial", "tecnología", "tecnologia",
        "software", "programación", "programacion", "digital",
        "robot", "algoritmo", "datos", "blockchain", "deepseek",
        "openai", "gpt",
    ],
    "negocios": [
        "negocio", "empresa", "startup", "mercado", "inversión",
        "inversion", "start-up", "corporativo", "ceo", "emprendedor",
    ],
    "salud": [
        "salud", "médico", "medico", "enfermedad", "tratamiento",
        "bienestar", "nutrición", "nutricion", "ejercicio",
        "mental", "covid",
    ],
    "educación": [
        "educación", "educacion", "aprendizaje", "curso",
        "formación", "formacion", "universidad", "estudiante",
        "clase", "enseñanza", "ensenanza",
    ],
    "finanzas": [
        "finanza", "economía", "economia", "cripto", "bitcoin",
        "bolsa", "inversión", "inversion", "ahorro", "pesos",
        "dólar", "dolar", "inflación", "inflacion",
    ],
}


def recommend_niche(title: str, description: str) -> tuple[str, str]:
    """
    Recomienda un nicho según keywords en título y descripción.

    Busca coincidencias en orden. La primera coincidencia gana.
    Si no hay ninguna, devuelve 'tecnología' por defecto.

    Args:
        title: Título del topic.
        description: Descripción del topic (puede ser vacía).

    Returns:
        Tupla (nicho, razonamiento).
    """
    text = (title + " " + (description or "")).lower()

    for niche, keywords in _KEYWORDS_MAP.items():
        if any(kw in text for kw in keywords):
            return (niche, f"Keywords detectadas → nicho: {niche}")

    return ("tecnología", "Nicho por defecto: tecnología (no se encontraron keywords específicas)")


# ── Orquestador ──────────────────────────────────────────────────────


def get_recommendations(topic: ResearchTopic) -> ScriptRecommendations:
    """
    Genera recomendaciones completas para un ResearchTopic.

    Orquesta las tres funciones de recomendación y devuelve un
    ScriptRecommendations con todos los campos poblados.

    Args:
        topic: ResearchTopic del cual obtener recomendaciones.

    Returns:
        ScriptRecommendations con tone, duration, niche y reasoning.
    """
    tone, tone_reason = recommend_tone(topic.source.name)
    duration, dur_reason = recommend_duration(topic.score.total)
    niche, niche_reason = recommend_niche(topic.title, topic.description)

    return ScriptRecommendations(
        tone=tone,
        duration=duration,
        niche=niche,
        reasoning={
            "tone": tone_reason,
            "duration": dur_reason,
            "niche": niche_reason,
        },
    )
