"""Tests for all DTOs — 13 DTOs (12 domain-specific + 3 common), all frozen."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from learning.application.dto import (
    AnalyticsDTO,
    DatasetDTO,
    ErrorDTO,
    ExplanationDTO,
    FeedbackDetailDTO,
    FeedbackSummaryDTO,
    KeywordStatDTO,
    LearningModelDTO,
    LearningSignalDTO,
    PaginatedDTO,
    PredictionDTO,
    ResultDTO,
    SourceQualityDTO,
)


class TestFeedbackSummaryDTO:
    """FeedbackSummaryDTO — Resumen de FeedbackRecord."""

    def test_creates(self) -> None:
        dto = FeedbackSummaryDTO(
            id="fb-1",
            topic_id="topic-ai",
            decision="APPROVED",
            source_name="TechBlog",
            created_at="2026-07-15T00:00:00+00:00",
        )
        assert dto.id == "fb-1"
        assert dto.topic_id == "topic-ai"
        assert dto.decision == "APPROVED"
        assert dto.source_name == "TechBlog"
        assert dto.created_at == "2026-07-15T00:00:00+00:00"

    def test_is_frozen(self) -> None:
        dto = FeedbackSummaryDTO(
            id="fb-1", topic_id="t", decision="APPROVED",
            source_name="s", created_at="ts",
        )
        with pytest.raises(FrozenInstanceError):
            dto.id = "mutated"  # type: ignore[misc]

    def test_equality(self) -> None:
        dto1 = FeedbackSummaryDTO(
            id="fb-1", topic_id="t", decision="APPROVED",
            source_name="s", created_at="ts",
        )
        dto2 = FeedbackSummaryDTO(
            id="fb-1", topic_id="t", decision="APPROVED",
            source_name="s", created_at="ts",
        )
        assert dto1 == dto2

    def test_repr_contains_class_name(self) -> None:
        dto = FeedbackSummaryDTO(
            id="fb-1", topic_id="t", decision="APPROVED",
            source_name="s", created_at="ts",
        )
        assert "FeedbackSummaryDTO" in repr(dto)


class TestFeedbackDetailDTO:
    """FeedbackDetailDTO — Detalle completo de FeedbackRecord."""

    def test_creates_with_required_only(self) -> None:
        dto = FeedbackDetailDTO(
            id="fb-1", topic_id="t", decision="APPROVED",
            reason=None, source_name="s", title="T",
            features=None, created_at="ts",
        )
        assert dto.reason is None
        assert dto.features is None

    def test_creates_with_all_fields(self) -> None:
        features = {"base_score": 0.75, "freshness_score": 0.80}
        dto = FeedbackDetailDTO(
            id="fb-1", topic_id="t", decision="REJECTED",
            reason="Off-topic", source_name="s", title="T",
            features=features, created_at="ts",
        )
        assert dto.reason == "Off-topic"
        assert dto.features == features

    def test_is_frozen(self) -> None:
        dto = FeedbackDetailDTO(
            id="fb-1", topic_id="t", decision="APPROVED",
            reason=None, source_name="s", title="T",
            features=None, created_at="ts",
        )
        with pytest.raises(FrozenInstanceError):
            dto.id = "mutated"  # type: ignore[misc]

    def test_equality(self) -> None:
        dto1 = FeedbackDetailDTO(
            id="fb-1", topic_id="t", decision="APPROVED",
            reason=None, source_name="s", title="T",
            features=None, created_at="ts",
        )
        dto2 = FeedbackDetailDTO(
            id="fb-1", topic_id="t", decision="APPROVED",
            reason=None, source_name="s", title="T",
            features=None, created_at="ts",
        )
        assert dto1 == dto2


class TestLearningSignalDTO:
    """LearningSignalDTO — Representación de una señal de aprendizaje."""

    def test_creates(self) -> None:
        dto = LearningSignalDTO(
            id="sig-1", dimension="KEYWORD", source="python",
            sample_size=42, approval_rate=0.78,
            strength=0.85, decay_factor=0.1,
            updated_at="2026-07-15T00:00:00+00:00",
        )
        assert dto.id == "sig-1"
        assert dto.dimension == "KEYWORD"
        assert dto.source == "python"
        assert dto.sample_size == 42
        assert dto.approval_rate == 0.78
        assert dto.strength == 0.85
        assert dto.decay_factor == 0.1

    def test_is_frozen(self) -> None:
        dto = LearningSignalDTO(
            id="sig-1", dimension="KEYWORD", source="python",
            sample_size=42, approval_rate=0.78,
            strength=0.85, decay_factor=0.1, updated_at="ts",
        )
        with pytest.raises(FrozenInstanceError):
            dto.id = "mutated"  # type: ignore[misc]

    def test_equality(self) -> None:
        dto1 = LearningSignalDTO(
            id="sig-1", dimension="KEYWORD", source="python",
            sample_size=42, approval_rate=0.78,
            strength=0.85, decay_factor=0.1, updated_at="ts",
        )
        dto2 = LearningSignalDTO(
            id="sig-1", dimension="KEYWORD", source="python",
            sample_size=42, approval_rate=0.78,
            strength=0.85, decay_factor=0.1, updated_at="ts",
        )
        assert dto1 == dto2


class TestKeywordStatDTO:
    """KeywordStatDTO — Estadísticas de un keyword específico."""

    def test_creates(self) -> None:
        dto = KeywordStatDTO(
            keyword="python", count=10, approved_count=8,
            approval_rate=0.8,
        )
        assert dto.keyword == "python"
        assert dto.count == 10
        assert dto.approved_count == 8
        assert dto.approval_rate == 0.8

    def test_is_frozen(self) -> None:
        dto = KeywordStatDTO(keyword="python", count=10, approved_count=8, approval_rate=0.8)
        with pytest.raises(FrozenInstanceError):
            dto.keyword = "mutated"  # type: ignore[misc]

    def test_equality(self) -> None:
        dto1 = KeywordStatDTO(keyword="python", count=10, approved_count=8, approval_rate=0.8)
        dto2 = KeywordStatDTO(keyword="python", count=10, approved_count=8, approval_rate=0.8)
        assert dto1 == dto2


class TestSourceQualityDTO:
    """SourceQualityDTO — Perfil de calidad de una fuente."""

    def test_creates_with_empty_keyword_stats(self) -> None:
        dto = SourceQualityDTO(
            source_name="TechBlog",
            total_decisions=20,
            approved=15,
            rejected=3,
            overridden=1,
            approval_rate=0.75,
        )
        assert dto.keyword_stats == ()

    def test_creates_with_keyword_stats(self) -> None:
        kw = KeywordStatDTO(keyword="python", count=10, approved_count=8, approval_rate=0.8)
        dto = SourceQualityDTO(
            source_name="TechBlog",
            total_decisions=20,
            approved=15,
            rejected=3,
            overridden=1,
            approval_rate=0.75,
            keyword_stats=(kw,),
        )
        assert len(dto.keyword_stats) == 1
        assert dto.keyword_stats[0].keyword == "python"

    def test_is_frozen(self) -> None:
        dto = SourceQualityDTO(
            source_name="s", total_decisions=0, approved=0,
            rejected=0, overridden=0, approval_rate=0.0,
        )
        with pytest.raises(FrozenInstanceError):
            dto.source_name = "mutated"  # type: ignore[misc]

    def test_equality(self) -> None:
        dto1 = SourceQualityDTO(
            source_name="s", total_decisions=0, approved=0,
            rejected=0, overridden=0, approval_rate=0.0,
        )
        dto2 = SourceQualityDTO(
            source_name="s", total_decisions=0, approved=0,
            rejected=0, overridden=0, approval_rate=0.0,
        )
        assert dto1 == dto2


class TestLearningModelDTO:
    """LearningModelDTO — Representación del modelo de aprendizaje."""

    def test_creates(self) -> None:
        weights = {"relevance": 0.3, "popularity": 0.25, "recency": 0.2, "source_reliability": 0.25}
        dto = LearningModelDTO(
            id="model-1",
            algorithm_version="1.2.3",
            weights=weights,
            minimum_confidence=0.5,
            minimum_sample_size=10,
            rules_count=2,
        )
        assert dto.id == "model-1"
        assert dto.algorithm_version == "1.2.3"
        assert dto.weights == weights
        assert dto.minimum_confidence == 0.5
        assert dto.minimum_sample_size == 10
        assert dto.rules_count == 2

    def test_is_frozen(self) -> None:
        dto = LearningModelDTO(
            id="m", algorithm_version="1.0.0", weights={},
            minimum_confidence=0.5, minimum_sample_size=1, rules_count=0,
        )
        with pytest.raises(FrozenInstanceError):
            dto.id = "mutated"  # type: ignore[misc]

    def test_equality(self) -> None:
        dto1 = LearningModelDTO(
            id="m", algorithm_version="1.0.0", weights={},
            minimum_confidence=0.5, minimum_sample_size=1, rules_count=0,
        )
        dto2 = LearningModelDTO(
            id="m", algorithm_version="1.0.0", weights={},
            minimum_confidence=0.5, minimum_sample_size=1, rules_count=0,
        )
        assert dto1 == dto2


class TestPredictionDTO:
    """PredictionDTO — Resultado de una predicción de aprobación."""

    def test_creates(self) -> None:
        dto = PredictionDTO(
            probability=0.85,
            confidence=0.90,
            reasoning_summary="High source reliability",
        )
        assert dto.probability == 0.85
        assert dto.confidence == 0.90
        assert dto.reasoning_summary == "High source reliability"

    def test_is_frozen(self) -> None:
        dto = PredictionDTO(probability=0.5, confidence=0.5, reasoning_summary="x")
        with pytest.raises(FrozenInstanceError):
            dto.probability = 0.9  # type: ignore[misc]

    def test_equality(self) -> None:
        dto1 = PredictionDTO(probability=0.5, confidence=0.5, reasoning_summary="x")
        dto2 = PredictionDTO(probability=0.5, confidence=0.5, reasoning_summary="x")
        assert dto1 == dto2


class TestAnalyticsDTO:
    """AnalyticsDTO — Analíticas generales del sistema de aprendizaje."""

    def test_creates(self) -> None:
        top = SourceQualityDTO(
            source_name="Blog", total_decisions=10, approved=8,
            rejected=2, overridden=0, approval_rate=0.8,
        )
        dto = AnalyticsDTO(
            total_feedback=100,
            total_signals=50,
            average_approval_rate=0.72,
            signals_by_dimension={"KEYWORD": 30, "SOURCE": 20},
            top_sources=(top,),
        )
        assert dto.total_feedback == 100
        assert dto.total_signals == 50
        assert dto.average_approval_rate == 0.72
        assert dto.signals_by_dimension == {"KEYWORD": 30, "SOURCE": 20}
        assert len(dto.top_sources) == 1

    def test_is_frozen(self) -> None:
        dto = AnalyticsDTO(
            total_feedback=0, total_signals=0, average_approval_rate=0.0,
            signals_by_dimension={}, top_sources=(),
        )
        with pytest.raises(FrozenInstanceError):
            dto.total_feedback = 1  # type: ignore[misc]

    def test_equality(self) -> None:
        dto1 = AnalyticsDTO(
            total_feedback=0, total_signals=0, average_approval_rate=0.0,
            signals_by_dimension={}, top_sources=(),
        )
        dto2 = AnalyticsDTO(
            total_feedback=0, total_signals=0, average_approval_rate=0.0,
            signals_by_dimension={}, top_sources=(),
        )
        assert dto1 == dto2


class TestDatasetDTO:
    """DatasetDTO — Representación de un dataset de entrenamiento."""

    def test_creates(self) -> None:
        dto = DatasetDTO(
            id="ds-1",
            name="Training Set v1",
            time_window_start="2026-01-01T00:00:00Z",
            time_window_end="2026-07-01T00:00:00Z",
            sample_count=500,
            created_at="2026-07-15T00:00:00Z",
        )
        assert dto.id == "ds-1"
        assert dto.name == "Training Set v1"
        assert dto.time_window_start == "2026-01-01T00:00:00Z"
        assert dto.time_window_end == "2026-07-01T00:00:00Z"
        assert dto.sample_count == 500

    def test_is_frozen(self) -> None:
        dto = DatasetDTO(
            id="ds-1", name="n", time_window_start="s",
            time_window_end="e", sample_count=0, created_at="ts",
        )
        with pytest.raises(FrozenInstanceError):
            dto.id = "mutated"  # type: ignore[misc]

    def test_equality(self) -> None:
        dto1 = DatasetDTO(
            id="ds-1", name="n", time_window_start="s",
            time_window_end="e", sample_count=0, created_at="ts",
        )
        dto2 = DatasetDTO(
            id="ds-1", name="n", time_window_start="s",
            time_window_end="e", sample_count=0, created_at="ts",
        )
        assert dto1 == dto2


class TestExplanationDTO:
    """ExplanationDTO — Explicación detallada del score de una fuente."""

    def test_creates(self) -> None:
        dto = ExplanationDTO(
            source_name="TechBlog",
            base_score=0.75,
            freshness_score=0.80,
            keyword_bonus=0.60,
            source_bonus=0.55,
            topic_penalty=0.10,
            confidence=0.90,
            final_score=0.82,
            timestamp="2026-07-15T00:00:00Z",
            model_version="1.2.3",
            active_signals=("KEYWORD:python", "SOURCE:TechBlog"),
        )
        assert dto.source_name == "TechBlog"
        assert dto.base_score == 0.75
        assert dto.final_score == 0.82
        assert dto.model_version == "1.2.3"
        assert dto.active_signals == ("KEYWORD:python", "SOURCE:TechBlog")

    def test_is_frozen(self) -> None:
        dto = ExplanationDTO(
            source_name="s", base_score=0.0, freshness_score=0.0,
            keyword_bonus=0.0, source_bonus=0.0, topic_penalty=0.0,
            confidence=0.0, final_score=0.0, timestamp="ts",
            model_version="1.0.0", active_signals=(),
        )
        with pytest.raises(FrozenInstanceError):
            dto.source_name = "mutated"  # type: ignore[misc]


class TestErrorDTO:
    """ErrorDTO — Representación de un error de aplicación."""

    def test_creates_without_detail(self) -> None:
        dto = ErrorDTO(code="RESOURCE_NOT_FOUND", message="Not found")
        assert dto.code == "RESOURCE_NOT_FOUND"
        assert dto.message == "Not found"
        assert dto.detail is None

    def test_creates_with_detail(self) -> None:
        dto = ErrorDTO(
            code="COMMAND_INVALID", message="Bad data",
            detail="Field 'source_name' is required",
        )
        assert dto.detail == "Field 'source_name' is required"

    def test_is_frozen(self) -> None:
        dto = ErrorDTO(code="c", message="m")
        with pytest.raises(FrozenInstanceError):
            dto.code = "mutated"  # type: ignore[misc]

    def test_equality(self) -> None:
        dto1 = ErrorDTO(code="c", message="m")
        dto2 = ErrorDTO(code="c", message="m")
        assert dto1 == dto2


class TestResultDTO:
    """ResultDTO — Envoltorio genérico para resultados operacionales."""

    def test_success_with_data(self) -> None:
        dto = ResultDTO(success=True, data="some value")
        assert dto.success is True
        assert dto.data == "some value"
        assert dto.error is None

    def test_failure_with_error(self) -> None:
        error = ErrorDTO(code="c", message="m")
        dto = ResultDTO(success=False, error=error)
        assert dto.success is False
        assert dto.data is None
        assert dto.error == error

    def test_is_frozen(self) -> None:
        dto = ResultDTO(success=True)
        with pytest.raises(FrozenInstanceError):
            dto.success = False  # type: ignore[misc]


class TestPaginatedDTO:
    """PaginatedDTO — Envoltorio genérico para respuestas paginadas (from dto.common_dto)."""

    def test_creates(self) -> None:
        dto = PaginatedDTO(
            items=("a", "b"),
            total=10,
            page=1,
            size=5,
            pages=2,
        )
        assert dto.items == ("a", "b")
        assert dto.total == 10
        assert dto.page == 1
        assert dto.size == 5
        assert dto.pages == 2

    def test_empty_items(self) -> None:
        dto = PaginatedDTO(items=(), total=0, page=1, size=50, pages=0)
        assert len(dto.items) == 0
        assert dto.pages == 0

    def test_is_frozen(self) -> None:
        dto = PaginatedDTO(items=(), total=0, page=1, size=50, pages=0)
        with pytest.raises(FrozenInstanceError):
            dto.total = 1  # type: ignore[misc]

    def test_equality(self) -> None:
        dto1 = PaginatedDTO(items=("a",), total=1, page=1, size=10, pages=1)
        dto2 = PaginatedDTO(items=("a",), total=1, page=1, size=10, pages=1)
        assert dto1 == dto2


class TestAllDTOsImmutability:
    """All DTOs must be frozen dataclasses."""

    @pytest.mark.parametrize(
        "dto_factory",
        [
            lambda: FeedbackSummaryDTO(
                id="a", topic_id="t", decision="APPROVED",
                source_name="s", created_at="ts",
            ),
            lambda: FeedbackDetailDTO(
                id="a", topic_id="t", decision="APPROVED",
                reason=None, source_name="s", title="T",
                features=None, created_at="ts",
            ),
            lambda: LearningSignalDTO(
                id="a", dimension="KEYWORD", source="s",
                sample_size=0, approval_rate=0.0,
                strength=0.0, decay_factor=0.0, updated_at="ts",
            ),
            lambda: KeywordStatDTO(keyword="k", count=0, approved_count=0, approval_rate=0.0),
            lambda: SourceQualityDTO(
                source_name="s", total_decisions=0, approved=0,
                rejected=0, overridden=0, approval_rate=0.0,
            ),
            lambda: LearningModelDTO(
                id="a", algorithm_version="1.0.0", weights={},
                minimum_confidence=0.0, minimum_sample_size=1, rules_count=0,
            ),
            lambda: PredictionDTO(probability=0.0, confidence=0.0, reasoning_summary="x"),
            lambda: AnalyticsDTO(
                total_feedback=0, total_signals=0, average_approval_rate=0.0,
                signals_by_dimension={}, top_sources=(),
            ),
            lambda: DatasetDTO(
                id="a", name="n", time_window_start="s",
                time_window_end="e", sample_count=0, created_at="ts",
            ),
            lambda: ExplanationDTO(
                source_name="s", base_score=0.0, freshness_score=0.0,
                keyword_bonus=0.0, source_bonus=0.0, topic_penalty=0.0,
                confidence=0.0, final_score=0.0, timestamp="ts",
                model_version="1.0.0", active_signals=(),
            ),
            lambda: ErrorDTO(code="c", message="m"),
            lambda: ResultDTO(success=True),
            lambda: PaginatedDTO(items=(), total=0, page=1, size=50, pages=0),
        ],
    )
    def test_all_dtos_are_frozen(self, dto_factory) -> None:
        dto = dto_factory()
        first_field = next(iter(dto.__dataclass_fields__))
        with pytest.raises(FrozenInstanceError):
            setattr(dto, first_field, "mutated")
