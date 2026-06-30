"""
Tests unitarios para research/application/recommendations.py
============================================================
Funciones puras — sin dependencias externas, sin mocks necesarios.
"""
import pytest

from research.application.recommendations import (
    recommend_tone,
    recommend_duration,
    recommend_niche,
    get_recommendations,
    ScriptRecommendations,
)
from research.domain.entities.research_topic import ResearchTopic
from research.domain.value_objects.research_source import ResearchSource
from research.domain.value_objects.research_score import ResearchScore


# ── recommend_tone ─────────────────────────────────────


class TestRecommendTone:

    @pytest.mark.parametrize("source_name,expected_tone,expected_reason_substr", [
        ("google-news", "educational", "educativo"),
        ("rss", "educational", "educativo"),
        ("google-news-rss", "educational", "educativo"),
        ("twitter", "controversial", "controversial"),
    ])
    def test_known_sources(self, source_name, expected_tone, expected_reason_substr):
        """Fuentes conocidas deben retornar tono esperado."""
        tone, reason = recommend_tone(source_name)
        assert tone == expected_tone
        assert expected_reason_substr in reason.lower()

    def test_manual_input(self):
        """Fuente manual → informative."""
        tone, reason = recommend_tone("manual-input")
        assert tone == "informative"
        assert "manual" in reason.lower()

    def test_unknown_source_defaults_to_educational(self):
        """Fuente desconocida → educational por defecto."""
        tone, reason = recommend_tone("some-unknown-source")
        assert tone == "educational"
        assert "defecto" in reason.lower() or "estándar" in reason.lower()

    def test_empty_string_source(self):
        """Fuente vacía → educational por defecto."""
        tone, reason = recommend_tone("")
        assert tone == "educational"

    def test_source_starting_with_manual(self):
        """Cualquier source que empiece con 'manual' debe ser informative."""
        tone, reason = recommend_tone("manual-custom")
        assert tone == "informative"


# ── recommend_duration ─────────────────────────────────


class TestRecommendDuration:

    @pytest.mark.parametrize("score,expected_duration,expected_reason_substr", [
        (100, 90, "alto"),
        (95, 90, "alto"),
        (80, 90, "alto"),
        (79, 60, "medio"),
        (70, 60, "medio"),
        (60, 60, "medio"),
        (59, 30, "bajo"),
        (30, 30, "bajo"),
        (0, 30, "bajo"),
    ])
    def test_various_scores(self, score, expected_duration, expected_reason_substr):
        """Score alto → 90s, medio → 60s, bajo → 30s."""
        duration, reason = recommend_duration(score)
        assert duration == expected_duration
        assert expected_reason_substr in reason.lower()

    def test_exactly_80_returns_90s(self):
        """Boundary: exactamente 80 debe dar 90s."""
        duration, reason = recommend_duration(80)
        assert duration == 90
        assert "≥80" in reason or "alto" in reason

    def test_exactly_60_returns_60s(self):
        """Boundary: exactamente 60 debe dar 60s."""
        duration, reason = recommend_duration(60)
        assert duration == 60
        assert "60-79" in reason or "medio" in reason

    def test_high_decimal_score(self):
        """Score con decimales debe funcionar."""
        duration, reason = recommend_duration(84.7)
        assert duration == 90

    def test_negative_score_treated_as_low(self):
        """Score negativo debe tratarse como bajo."""
        duration, reason = recommend_duration(-10)
        assert duration == 30


# ── recommend_niche ────────────────────────────────────


class TestRecommendNiche:

    @pytest.mark.parametrize("title,description,expected_niche", [
        ("Nuevo modelo de IA", "", "tecnología"),
        ("", "Avances en inteligencia artificial", "tecnología"),
        ("Mi empresa creció", "", "negocios"),
        ("", "Startup recauda inversión", "negocios"),
        ("Nueva cura para la salud", "", "salud"),
        ("", "Tratamiento médico innovador", "salud"),
        ("Aprendizaje universidad", "", "educación"),      # "aprendizaje" → solo en educación
        ("", "Clase de enseñanza online", "educación"),    # "clase" → solo en educación
        ("Bitcoin alcanza nuevo máximo", "", "finanzas"),
        ("", "La economía y la inflación", "finanzas"),
    ])
    def test_keywords_detect_niche(self, title, description, expected_niche):
        """Keywords en title/description deben detectar el nicho correcto."""
        niche, reason = recommend_niche(title, description)
        assert niche == expected_niche
        assert "keywords" in reason.lower() or "detectadas" in reason.lower()

    def test_no_keywords_defaults_to_tecnologia(self):
        """Sin keywords que coincidan → tecnología por defecto."""
        niche, reason = recommend_niche("Cosas random", "Sin palabras clave")
        assert niche == "tecnología"
        assert "defecto" in reason

    def test_title_priority_over_description(self):
        """El título se busca primero (orden del map)."""
        niche, reason = recommend_niche("IA y salud", "Tratamiento médico")
        # "ia" en KEYWORDS_MAP aparece antes que "salud" → tecnología
        assert niche == "tecnología"

    def test_case_insensitive_keywords(self):
        """Keywords deben ser case-insensitive."""
        niche, reason = recommend_niche("INTELIGENCIA ARTIFICIAL", "")
        assert niche == "tecnología"

    def test_keyword_as_substring(self):
        """Keywords deben detectarse como substrings."""
        niche, reason = recommend_niche("blockchain", "empresa startup")
        # blockchain → tecnología, empresa → negocios
        # La primera coincidencia en el map es tecnología (ia está antes que empresa)
        # Pero "ia" no está en "blockchain"... entonces "negocio" keyword search...
        # empresa aparece después, y el map itera en orden: tecnología, negocios...
        # wait: blockchain is keyword for tecnología. So first match is tecnología.
        assert niche == "tecnología"


# ── get_recommendations (orquestador) ──────────────────


class TestGetRecommendations:

    def test_returns_all_recommendations(self):
        """get_recommendations debe retornar tone, duration, niche y reasoning."""
        topic = ResearchTopic(
            title="Clases de biología molecular",
            description="Nuevo método de enseñanza",
            content="Contenido educativo de prueba",
            source=ResearchSource.google_news(),
            score=ResearchScore(relevance=85, popularity=80, recency=90, source_reliability=80),
        )
        recs = get_recommendations(topic)

        assert isinstance(recs, ScriptRecommendations)
        assert recs.tone == "educational"  # google-news → educational
        assert recs.duration == 90  # score total ~83.5 → 90s
        assert recs.niche == "educación"  # "clase" y "enseñanza" → educación

    def test_reasoning_has_all_keys(self):
        """El dict reasoning debe contener tone, duration y niche."""
        topic = ResearchTopic(
            title="Noticia de tecnología",
            source=ResearchSource(name="twitter", type="automatic", reliability=50),
            score=ResearchScore(relevance=50, popularity=50, recency=50, source_reliability=50),
        )
        recs = get_recommendations(topic)

        assert "tone" in recs.reasoning
        assert "duration" in recs.reasoning
        assert "niche" in recs.reasoning
        assert isinstance(recs.reasoning["tone"], str)
        assert isinstance(recs.reasoning["duration"], str)
        assert isinstance(recs.reasoning["niche"], str)

    def test_uses_topic_score_for_duration(self):
        """La duración se calcula según el score total del topic."""
        low_score_topic = ResearchTopic(
            title="Nota breve",
            source=ResearchSource.google_news(),
            score=ResearchScore(relevance=10, popularity=10, recency=10, source_reliability=10),
        )
        recs = get_recommendations(low_score_topic)
        # score total = 10*0.35 + 10*0.25 + 10*0.25 + 10*0.15 = 10.0
        assert recs.duration == 30

    def test_uses_source_for_tone(self):
        """El tono se determina por la fuente."""
        twitter_topic = ResearchTopic(
            title="Polémica en redes",
            source=ResearchSource.twitter(),
            score=ResearchScore(relevance=60, popularity=60, recency=60, source_reliability=60),
        )
        recs = get_recommendations(twitter_topic)
        assert recs.tone == "controversial"

    def test_uses_title_and_description_for_niche(self):
        """El nicho se determina por keywords en title/description."""
        salud_topic = ResearchTopic(
            title="Nuevo tratamiento médico",
            description="Avances en salud pública",
            source=ResearchSource.google_news(),
            score=ResearchScore(relevance=80, popularity=80, recency=80, source_reliability=80),
        )
        recs = get_recommendations(salud_topic)
        assert recs.niche == "salud"
