"""Tests for all Query dataclasses — 9 queries for the Learning BC."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from learning.application.queries import (
    ExplainScoreQuery,
    GetAnalyticsQuery,
    GetFeedbackQuery,
    GetLearningModelQuery,
    GetLearningSignalsQuery,
    GetSourceQualityQuery,
    ListDatasetsQuery,
    ListFeedbackQuery,
    PredictApprovalQuery,
)


class TestGetFeedbackQuery:
    """GetFeedbackQuery — Obtener un FeedbackRecord por ID."""

    def test_creates(self) -> None:
        q = GetFeedbackQuery(feedback_id="fb-1")
        assert q.feedback_id == "fb-1"

    def test_is_frozen(self) -> None:
        q = GetFeedbackQuery(feedback_id="fb-1")
        with pytest.raises(FrozenInstanceError):
            q.feedback_id = "mutated"  # type: ignore[misc]

    def test_equality(self) -> None:
        q1 = GetFeedbackQuery(feedback_id="fb-1")
        q2 = GetFeedbackQuery(feedback_id="fb-1")
        assert q1 == q2

    def test_repr_contains_class_name(self) -> None:
        q = GetFeedbackQuery(feedback_id="fb-1")
        assert "GetFeedbackQuery" in repr(q)


class TestListFeedbackQuery:
    """ListFeedbackQuery — Listar FeedbackRecords con filtros y paginación."""

    def test_creates_with_defaults(self) -> None:
        q = ListFeedbackQuery()
        assert q.topic_id is None
        assert q.source_name is None
        assert q.page == 1
        assert q.size == 50

    def test_creates_with_all_filters(self) -> None:
        q = ListFeedbackQuery(
            topic_id="topic-ai",
            source_name="TechBlog",
            page=3,
            size=25,
        )
        assert q.topic_id == "topic-ai"
        assert q.source_name == "TechBlog"
        assert q.page == 3
        assert q.size == 25

    def test_is_frozen(self) -> None:
        q = ListFeedbackQuery()
        with pytest.raises(FrozenInstanceError):
            q.page = 2  # type: ignore[misc]

    def test_equality(self) -> None:
        q1 = ListFeedbackQuery(topic_id="t", page=1, size=50)
        q2 = ListFeedbackQuery(topic_id="t", page=1, size=50)
        assert q1 == q2

    def test_repr_contains_class_name(self) -> None:
        q = ListFeedbackQuery()
        assert "ListFeedbackQuery" in repr(q)


class TestGetLearningModelQuery:
    """GetLearningModelQuery — Obtener el modelo de aprendizaje actual (singleton)."""

    def test_creates(self) -> None:
        q = GetLearningModelQuery()
        assert isinstance(q, GetLearningModelQuery)

    def test_is_frozen(self) -> None:
        q = GetLearningModelQuery()
        # No fields to mutate, verify it's hashable (frozen dataclass with eq=True)
        assert hash(q) is not None

    def test_equality(self) -> None:
        q1 = GetLearningModelQuery()
        q2 = GetLearningModelQuery()
        assert q1 == q2

    def test_repr_contains_class_name(self) -> None:
        q = GetLearningModelQuery()
        assert "GetLearningModelQuery" in repr(q)


class TestGetSourceQualityQuery:
    """GetSourceQualityQuery — Obtener el perfil de calidad de una fuente."""

    def test_creates(self) -> None:
        q = GetSourceQualityQuery(source_name="TechBlog")
        assert q.source_name == "TechBlog"

    def test_is_frozen(self) -> None:
        q = GetSourceQualityQuery(source_name="TechBlog")
        with pytest.raises(FrozenInstanceError):
            q.source_name = "mutated"  # type: ignore[misc]

    def test_equality(self) -> None:
        q1 = GetSourceQualityQuery(source_name="TechBlog")
        q2 = GetSourceQualityQuery(source_name="TechBlog")
        assert q1 == q2

    def test_repr_contains_class_name(self) -> None:
        q = GetSourceQualityQuery(source_name="TechBlog")
        assert "GetSourceQualityQuery" in repr(q)


class TestGetLearningSignalsQuery:
    """GetLearningSignalsQuery — Obtener señales de aprendizaje con filtros."""

    def test_creates_with_defaults(self) -> None:
        q = GetLearningSignalsQuery()
        assert q.dimension is None
        assert q.source is None

    def test_creates_with_all_filters(self) -> None:
        q = GetLearningSignalsQuery(dimension="KEYWORD", source="python")
        assert q.dimension == "KEYWORD"
        assert q.source == "python"

    def test_is_frozen(self) -> None:
        q = GetLearningSignalsQuery()
        with pytest.raises(FrozenInstanceError):
            q.dimension = "mutated"  # type: ignore[misc]

    def test_equality(self) -> None:
        q1 = GetLearningSignalsQuery(dimension="KEYWORD", source="python")
        q2 = GetLearningSignalsQuery(dimension="KEYWORD", source="python")
        assert q1 == q2

    def test_repr_contains_class_name(self) -> None:
        q = GetLearningSignalsQuery()
        assert "GetLearningSignalsQuery" in repr(q)


class TestGetAnalyticsQuery:
    """GetAnalyticsQuery — Obtener analíticas generales."""

    def test_creates_with_defaults(self) -> None:
        q = GetAnalyticsQuery()
        assert q.time_window_start is None
        assert q.time_window_end is None

    def test_creates_with_time_window(self) -> None:
        q = GetAnalyticsQuery(
            time_window_start="2026-01-01T00:00:00Z",
            time_window_end="2026-07-01T00:00:00Z",
        )
        assert q.time_window_start == "2026-01-01T00:00:00Z"
        assert q.time_window_end == "2026-07-01T00:00:00Z"

    def test_is_frozen(self) -> None:
        q = GetAnalyticsQuery()
        with pytest.raises(FrozenInstanceError):
            q.time_window_start = "mutated"  # type: ignore[misc]

    def test_equality(self) -> None:
        q1 = GetAnalyticsQuery(time_window_start="s", time_window_end="e")
        q2 = GetAnalyticsQuery(time_window_start="s", time_window_end="e")
        assert q1 == q2

    def test_repr_contains_class_name(self) -> None:
        q = GetAnalyticsQuery()
        assert "GetAnalyticsQuery" in repr(q)


class TestPredictApprovalQuery:
    """PredictApprovalQuery — Predecir probabilidad de aprobación."""

    def test_creates_with_required_only(self) -> None:
        q = PredictApprovalQuery(source_name="TechBlog")
        assert q.source_name == "TechBlog"
        assert q.features is None

    def test_creates_with_features(self) -> None:
        features = {"relevance": 0.8, "popularity": 0.6}
        q = PredictApprovalQuery(source_name="TechBlog", features=features)
        assert q.features == features

    def test_is_frozen(self) -> None:
        q = PredictApprovalQuery(source_name="TechBlog")
        with pytest.raises(FrozenInstanceError):
            q.source_name = "mutated"  # type: ignore[misc]

    def test_equality(self) -> None:
        q1 = PredictApprovalQuery(source_name="TechBlog")
        q2 = PredictApprovalQuery(source_name="TechBlog")
        assert q1 == q2

    def test_repr_contains_class_name(self) -> None:
        q = PredictApprovalQuery(source_name="TechBlog")
        assert "PredictApprovalQuery" in repr(q)


class TestExplainScoreQuery:
    """ExplainScoreQuery — Explicar el score de una fuente."""

    def test_creates_with_required_only(self) -> None:
        q = ExplainScoreQuery(source_name="TechBlog")
        assert q.source_name == "TechBlog"
        assert q.features is None

    def test_creates_with_features(self) -> None:
        features = {"base_score": 0.75}
        q = ExplainScoreQuery(source_name="TechBlog", features=features)
        assert q.features == features

    def test_is_frozen(self) -> None:
        q = ExplainScoreQuery(source_name="TechBlog")
        with pytest.raises(FrozenInstanceError):
            q.source_name = "mutated"  # type: ignore[misc]

    def test_equality(self) -> None:
        q1 = ExplainScoreQuery(source_name="TechBlog")
        q2 = ExplainScoreQuery(source_name="TechBlog")
        assert q1 == q2

    def test_repr_contains_class_name(self) -> None:
        q = ExplainScoreQuery(source_name="TechBlog")
        assert "ExplainScoreQuery" in repr(q)


class TestListDatasetsQuery:
    """ListDatasetsQuery — Listar datasets de entrenamiento con paginación."""

    def test_creates_with_defaults(self) -> None:
        q = ListDatasetsQuery()
        assert q.page == 1
        assert q.size == 50

    def test_creates_with_custom_pagination(self) -> None:
        q = ListDatasetsQuery(page=5, size=20)
        assert q.page == 5
        assert q.size == 20

    def test_is_frozen(self) -> None:
        q = ListDatasetsQuery()
        with pytest.raises(FrozenInstanceError):
            q.page = 2  # type: ignore[misc]

    def test_equality(self) -> None:
        q1 = ListDatasetsQuery(page=1, size=50)
        q2 = ListDatasetsQuery(page=1, size=50)
        assert q1 == q2

    def test_repr_contains_class_name(self) -> None:
        q = ListDatasetsQuery()
        assert "ListDatasetsQuery" in repr(q)


class TestAllQueriesImmutability:
    """All 9 queries must be frozen dataclasses."""

    @pytest.mark.parametrize(
        "q_factory",
        [
            lambda: GetFeedbackQuery(feedback_id="x"),
            lambda: ListFeedbackQuery(),
            lambda: GetLearningModelQuery(),
            lambda: GetSourceQualityQuery(source_name="x"),
            lambda: GetLearningSignalsQuery(),
            lambda: GetAnalyticsQuery(),
            lambda: PredictApprovalQuery(source_name="x"),
            lambda: ExplainScoreQuery(source_name="x"),
            lambda: ListDatasetsQuery(),
        ],
    )
    def test_all_queries_are_frozen(self, q_factory) -> None:
        q = q_factory()
        fields = list(q.__dataclass_fields__)
        if fields:
            with pytest.raises(FrozenInstanceError):
                setattr(q, fields[0], "mutated")
        else:
            # No fields (GetLearningModelQuery) — verify hashable
            assert hash(q) is not None
