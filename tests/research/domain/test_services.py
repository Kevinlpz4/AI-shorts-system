"""
Tests para servicios de dominio: DuplicateDetector y ResearchScorer.
"""
import pytest
from datetime import datetime, timezone, timedelta

from research.domain.entities.research_topic import ResearchTopic
from research.domain.services.duplicate_detector import UrlNormalizerStrategy
from research.domain.value_objects.research_source import ResearchSource, SourceType
from research.domain.value_objects.research_score import ResearchScore


# ── DuplicateDetector ────────────────────────────────


class TestUrlNormalizerStrategy:

    @pytest.fixture
    def url_strategy(self):
        """Usar UrlNormalizerStrategy directamente (no Composite)."""
        return UrlNormalizerStrategy()

    def test_same_url_is_duplicate(self, duplicate_detector):
        """Dos topics con misma URL deben ser duplicados."""
        t1 = ResearchTopic(title="A", url="https://example.com/news/1")
        t2 = ResearchTopic(title="B", url="https://example.com/news/1")

        hashes = duplicate_detector.compute_hashes(t1)
        assert duplicate_detector.is_duplicate(t2, hashes) is True

    def test_url_with_protocol_variants(self, duplicate_detector):
        """URLs http y https deben ser iguales."""
        t1 = ResearchTopic(title="A", url="http://example.com/news/1")
        t2 = ResearchTopic(title="B", url="https://example.com/news/1")

        hashes = duplicate_detector.compute_hashes(t1)
        assert duplicate_detector.is_duplicate(t2, hashes) is True

    def test_url_with_tracking_params(self, duplicate_detector):
        """URLs con utm_source deben ser iguales."""
        t1 = ResearchTopic(title="A", url="https://example.com/news/1")
        t2 = ResearchTopic(title="B", url="https://example.com/news/1?utm_source=twitter&utm_medium=social")

        hashes = duplicate_detector.compute_hashes(t1)
        assert duplicate_detector.is_duplicate(t2, hashes) is True

    def test_url_trailing_slash(self, duplicate_detector):
        """URL con y sin trailing slash deben ser iguales."""
        t1 = ResearchTopic(title="A", url="https://example.com/news/1")
        t2 = ResearchTopic(title="B", url="https://example.com/news/1/")

        hashes = duplicate_detector.compute_hashes(t1)
        assert duplicate_detector.is_duplicate(t2, hashes) is True

    def test_different_urls_not_duplicate(self, duplicate_detector):
        """URLs diferentes NO deben ser duplicados."""
        t1 = ResearchTopic(title="A", url="https://example.com/news/1")
        t2 = ResearchTopic(title="B", url="https://example.com/news/2")

        hashes = duplicate_detector.compute_hashes(t1)
        assert duplicate_detector.is_duplicate(t2, hashes) is False

    def test_no_url_returns_none(self, url_strategy):
        """Topic sin URL debe retornar None (no hash posible)."""
        topic = ResearchTopic(title="Test")
        h = url_strategy.compute_hash(topic)
        assert h is None  # Sin URL no genera hash


class TestTitleNormalizerStrategy:

    def test_same_title_is_duplicate(self, duplicate_detector):
        """Dos topics con mismo título normalizado deben ser duplicados."""
        t1 = ResearchTopic(title="Nuevo modelo de IA sorprende al mundo")
        t2 = ResearchTopic(title="Nuevo modelo de IA sorprende al mundo")

        hashes = duplicate_detector.compute_hashes(t1)
        assert duplicate_detector.is_duplicate(t2, hashes) is True

    def test_title_case_insensitive(self, duplicate_detector):
        """Títulos con diferente capitalización deben ser iguales."""
        t1 = ResearchTopic(title="IA Supera a Humanos en Ajedrez")
        t2 = ResearchTopic(title="ia supera a humanos en ajedrez")

        hashes = duplicate_detector.compute_hashes(t1)
        assert duplicate_detector.is_duplicate(t2, hashes) is True

    def test_title_with_stop_words(self, duplicate_detector):
        """Stop words y puntuación no deben afectar la detección."""
        t1 = ResearchTopic(title="El nuevo modelo de IA: sorprende al mundo!")
        t2 = ResearchTopic(title="nuevo modelo IA sorprende mundo")

        hashes = duplicate_detector.compute_hashes(t1)
        assert duplicate_detector.is_duplicate(t2, hashes) is True

    def test_different_titles_not_duplicate(self, duplicate_detector):
        """Títulos diferentes NO deben ser duplicados."""
        t1 = ResearchTopic(title="Noticia sobre IA")
        t2 = ResearchTopic(title="Resultados de fútbol")

        hashes = duplicate_detector.compute_hashes(t1)
        assert duplicate_detector.is_duplicate(t2, hashes) is False

    def test_empty_title_returns_none(self, duplicate_detector):
        """Topic sin título no debe generar hash."""
        topic = ResearchTopic(title="")
        assert len(duplicate_detector.compute_hashes(topic)) == 0


class TestCompositeDuplicateDetector:

    def test_detects_url_duplicate(self, duplicate_detector):
        """Detecta duplicado por URL aunque el título sea diferente."""
        t1 = ResearchTopic(title="Noticia A", url="https://example.com/news/1")
        t2 = ResearchTopic(title="Noticia B (copy)", url="https://example.com/news/1")

        hashes = duplicate_detector.compute_hashes(t1)
        assert duplicate_detector.is_duplicate(t2, hashes) is True

    def test_detects_title_duplicate(self, duplicate_detector):
        """Detecta duplicado por título aunque la URL sea diferente."""
        t1 = ResearchTopic(title="Noticia importante sobre IA", url="https://example.com/a")
        t2 = ResearchTopic(title="Noticia importante sobre IA", url="https://example.com/b")

        hashes = duplicate_detector.compute_hashes(t1)
        assert duplicate_detector.is_duplicate(t2, hashes) is True

    def test_filter_duplicates(self, duplicate_detector):
        """filter_duplicates separa correctamente únicos y duplicados."""
        existing = ResearchTopic(title="Noticia existente", url="https://ex.com/1")
        new_unique = ResearchTopic(title="Noticia nueva", url="https://ex.com/2")
        new_dup = ResearchTopic(title="Noticia existente", url="https://ex.com/3")

        existing_hashes = duplicate_detector.compute_hashes(existing)
        unique, dups = duplicate_detector.filter_duplicates(
            [new_unique, new_dup],
            existing_hashes,
        )

        assert len(unique) == 1
        assert unique[0].title == "Noticia nueva"
        assert len(dups) == 1
        assert dups[0].title == "Noticia existente"

    def test_empty_strategies_raises(self):
        """No se puede crear detector sin estrategias."""
        from research.domain.services.duplicate_detector import CompositeDuplicateDetector
        with pytest.raises(ValueError, match="al menos una"):
            CompositeDuplicateDetector([])


# ── ResearchScorer ───────────────────────────────────


class TestResearchScorer:

    def test_score_basic_topic(self, scorer, sample_topic):
        """Un topic completo debe tener score > 50."""
        score = scorer.calculate(sample_topic)
        assert score.total > 50
        assert 0 <= score.relevance <= 100
        assert 0 <= score.popularity <= 100
        assert 0 <= score.recency <= 100
        assert 0 <= score.source_reliability <= 100

    def test_score_minimal_topic_less_than_rich(self, scorer):
        """Un topic mínimo debe tener score MENOR que uno completo."""
        minimal = ResearchTopic(
            title="",
            content="",
            source=ResearchSource(name="empty", type=SourceType.AUTOMATIC, reliability=0),
        )
        rich = ResearchTopic(
            title="Nuevo descubrimiento revolucionario de inteligencia artificial",
            content="Contenido extenso con IA y ChatGPT. " * 20,
            source=ResearchSource.google_news(),
            url="https://example.com/rich",
        )

        score_min = scorer.calculate(minimal)
        score_rich = scorer.calculate(rich)
        assert score_min.total < score_rich.total

    def test_score_relevance_keywords_boost(self, scorer):
        """Keywords de alto valor deben aumentar relevance."""
        topic_with_kw = ResearchTopic(
            title="Nuevo descubrimiento revolucionario de inteligencia artificial",
            content="Contenido con IA y ChatGPT. " * 20,
        )
        topic_without_kw = ResearchTopic(
            title="El clima en Buenos Aires hoy",
            content="Soleado. " * 5,
        )

        score_with = scorer.calculate(topic_with_kw)
        score_without = scorer.calculate(topic_without_kw)
        assert score_with.relevance > score_without.relevance

    def test_score_popularity_by_source(self, scorer):
        """Fuente manual debe tener más popularidad que automática."""
        manual = ResearchTopic(
            title="Test",
            source=ResearchSource.manual(),
        )
        automatic = ResearchTopic(
            title="Test",
            source=ResearchSource.twitter(),
        )

        score_manual = scorer.calculate(manual)
        score_auto = scorer.calculate(automatic)
        assert score_manual.popularity > score_auto.popularity

    def test_score_recency_recent_is_higher(self, scorer):
        """Noticias recientes deben tener más recency."""
        recent = ResearchTopic(
            title="Test",
            published_at=datetime.now(timezone.utc) - timedelta(minutes=30),
        )
        old = ResearchTopic(
            title="Test",
            published_at=datetime.now(timezone.utc) - timedelta(days=30),
        )

        score_recent = scorer.calculate(recent)
        score_old = scorer.calculate(old)
        assert score_recent.recency > score_old.recency

    def test_score_many(self, scorer, topics_batch):
        """calculate_many debe calcular scores para todos."""
        results = scorer.calculate_many(topics_batch)
        assert len(results) == 5
        for topic in results:
            assert topic.score.total > 0

    def test_score_without_date_uses_created_at(self, scorer):
        """Si no hay published_at, usa created_at como aproximación."""
        topic = ResearchTopic(title="Test")
        score = scorer.calculate(topic)
        # created_at es ahora mismo, así que recency debe ser alto
        assert score.recency >= 50
