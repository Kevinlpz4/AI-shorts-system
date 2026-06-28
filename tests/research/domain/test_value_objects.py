"""
Tests para Value Objects del módulo Research.
"""
import pytest

from research.domain.value_objects.research_status import ResearchStatus
from research.domain.value_objects.research_source import ResearchSource, SourceType
from research.domain.value_objects.research_score import ResearchScore


# ── ResearchStatus ───────────────────────────────────


class TestResearchStatus:

    def test_default_is_pending_review(self):
        """El estado por defecto debe ser PENDING_REVIEW (control editorial)."""
        assert ResearchStatus.default() == ResearchStatus.PENDING_REVIEW

    def test_terminal_states(self):
        """APPROVED y REJECTED son terminales."""
        assert ResearchStatus.APPROVED.is_terminal is True
        assert ResearchStatus.REJECTED.is_terminal is True
        assert ResearchStatus.PENDING_REVIEW.is_terminal is False
        assert ResearchStatus.FOUND.is_terminal is False

    def test_is_reviewable(self):
        """Solo PENDING_REVIEW es reviewable."""
        assert ResearchStatus.PENDING_REVIEW.is_reviewable is True
        assert ResearchStatus.FOUND.is_reviewable is False
        assert ResearchStatus.APPROVED.is_reviewable is False
        assert ResearchStatus.REJECTED.is_reviewable is False

    def test_enum_values(self):
        assert ResearchStatus.FOUND.value == "found"
        assert ResearchStatus.PENDING_REVIEW.value == "pending_review"
        assert ResearchStatus.APPROVED.value == "approved"
        assert ResearchStatus.REJECTED.value == "rejected"


# ── ResearchSource ───────────────────────────────────


class TestResearchSource:

    def test_create_valid_source(self):
        source = ResearchSource(name="test", type=SourceType.MANUAL, reliability=80)
        assert source.name == "test"
        assert source.type == SourceType.MANUAL
        assert source.reliability == 80

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="vacío"):
            ResearchSource(name="", type=SourceType.MANUAL)

    def test_reliability_below_zero_raises(self):
        with pytest.raises(ValueError, match="0-100"):
            ResearchSource(name="test", type=SourceType.MANUAL, reliability=-1)

    def test_reliability_above_100_raises(self):
        with pytest.raises(ValueError, match="0-100"):
            ResearchSource(name="test", type=SourceType.MANUAL, reliability=150)

    def test_manual_factory(self):
        source = ResearchSource.manual()
        assert source.name == "manual"
        assert source.type == SourceType.MANUAL
        assert source.reliability == 100

    def test_google_news_factory(self):
        source = ResearchSource.google_news()
        assert source.name == "google-news"
        assert source.type == SourceType.AUTOMATIC
        assert source.reliability == 80

    def test_twitter_factory(self):
        source = ResearchSource.twitter()
        assert source.name == "twitter"
        assert source.type == SourceType.AUTOMATIC
        assert source.reliability == 50

    def test_immutable(self):
        source = ResearchSource.manual()
        with pytest.raises(AttributeError):
            source.name = "otro"

    def test_equality(self):
        a = ResearchSource.manual()
        b = ResearchSource.manual()
        assert a == b

    def test_custom_manual_name(self):
        source = ResearchSource.manual(name="web-scraping")
        assert source.name == "web-scraping"


# ── ResearchScore ────────────────────────────────────


class TestResearchScore:

    def test_default_score_is_zero(self):
        """Score por defecto debe ser 0 en todos los componentes."""
        score = ResearchScore()
        assert score.relevance == 0
        assert score.popularity == 0
        assert score.recency == 0
        assert score.source_reliability == 0
        assert score.total == 0.0

    def test_total_calculation(self):
        """total = relevance*0.35 + popularity*0.25 + recency*0.25 + reliability*0.15"""
        score = ResearchScore(
            relevance=100,
            popularity=100,
            recency=100,
            source_reliability=100,
        )
        assert score.total == 100.0

    def test_weighted_average(self):
        score = ResearchScore(
            relevance=100,   # 100 * 0.35 = 35
            popularity=0,    # 0 * 0.25 = 0
            recency=0,       # 0 * 0.25 = 0
            source_reliability=0,  # 0 * 0.15 = 0
        )
        assert score.total == 35.0

    def test_total_rounds_to_one_decimal(self):
        score = ResearchScore(relevance=33, popularity=33, recency=33, source_reliability=33)
        # 33*0.35 + 33*0.25 + 33*0.25 + 33*0.15 = 33*1.0 = 33.0
        assert score.total == 33.0

    def test_notable_threshold(self):
        assert ResearchScore(relevance=100, popularity=100, recency=100, source_reliability=100).is_notable is True
        assert ResearchScore(relevance=50, popularity=50, recency=50, source_reliability=50).is_notable is False

    def test_negative_relevance_raises(self):
        with pytest.raises(ValueError):
            ResearchScore(relevance=-1)

    def test_relevance_over_100_raises(self):
        with pytest.raises(ValueError):
            ResearchScore(relevance=101)

    def test_non_int_relevance_raises(self):
        with pytest.raises(TypeError):
            ResearchScore(relevance=50.5)  # type: ignore

    def test_sorting_higher_first(self):
        """__lt__ está invertido: mejor score primero."""
        high = ResearchScore(relevance=100, popularity=100, recency=100, source_reliability=100)
        low = ResearchScore(relevance=0, popularity=0, recency=0, source_reliability=0)
        scores = [low, high]
        scores.sort()
        assert scores == [high, low]  # high first

    def test_immutable(self):
        score = ResearchScore(relevance=50)
        with pytest.raises(AttributeError):
            score.relevance = 60

    def test_str_representation(self):
        score = ResearchScore(relevance=80, popularity=70, recency=60, source_reliability=90)
        assert "ResearchScore" in str(score)
        assert "80" in str(score)
        assert "70" in str(score)
