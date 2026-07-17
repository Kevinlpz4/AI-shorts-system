"""Tests for all Command dataclasses — 7 commands for the Learning BC."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from learning.application.commands import (
    AdjustScoreWeightsCommand,
    ArchiveFeedbackCommand,
    GenerateDatasetCommand,
    RecalculateSignalsCommand,
    RecordFeedbackCommand,
    RegisterSignalCommand,
    UpdateSourceProfileCommand,
)


class TestRecordFeedbackCommand:
    """RecordFeedbackCommand — Grabar una decisión humana sobre contenido."""

    def test_creates_with_all_required_fields(self) -> None:
        cmd = RecordFeedbackCommand(
            topic_id="topic-ai",
            decision="APPROVED",
            reason=None,
            source_name="TechBlog",
            title="Great Article",
        )
        assert cmd.topic_id == "topic-ai"
        assert cmd.decision == "APPROVED"
        assert cmd.reason is None
        assert cmd.source_name == "TechBlog"
        assert cmd.title == "Great Article"
        assert cmd.features is None

    def test_creates_with_optional_features(self) -> None:
        features = {"base_score": 0.75, "freshness_score": 0.80}
        cmd = RecordFeedbackCommand(
            topic_id="topic-ai",
            decision="REJECTED",
            reason="Off-topic",
            source_name="TechBlog",
            title="Spam Article",
            features=features,
        )
        assert cmd.features == features
        assert cmd.reason == "Off-topic"

    def test_is_frozen(self) -> None:
        cmd = RecordFeedbackCommand(
            topic_id="t", decision="APPROVED", reason=None,
            source_name="s", title="T",
        )
        with pytest.raises(FrozenInstanceError):
            cmd.topic_id = "mutated"  # type: ignore[misc]

    def test_equality(self) -> None:
        cmd1 = RecordFeedbackCommand(
            topic_id="t", decision="APPROVED", reason=None,
            source_name="s", title="T",
        )
        cmd2 = RecordFeedbackCommand(
            topic_id="t", decision="APPROVED", reason=None,
            source_name="s", title="T",
        )
        assert cmd1 == cmd2

    def test_repr_contains_class_name(self) -> None:
        cmd = RecordFeedbackCommand(
            topic_id="t", decision="APPROVED", reason=None,
            source_name="s", title="T",
        )
        assert "RecordFeedbackCommand" in repr(cmd)


class TestArchiveFeedbackCommand:
    """ArchiveFeedbackCommand — Archivar un FeedbackRecord existente."""

    def test_creates_with_single_field(self) -> None:
        cmd = ArchiveFeedbackCommand(feedback_id="fb-1")
        assert cmd.feedback_id == "fb-1"

    def test_is_frozen(self) -> None:
        cmd = ArchiveFeedbackCommand(feedback_id="fb-1")
        with pytest.raises(FrozenInstanceError):
            cmd.feedback_id = "mutated"  # type: ignore[misc]

    def test_equality(self) -> None:
        cmd1 = ArchiveFeedbackCommand(feedback_id="fb-1")
        cmd2 = ArchiveFeedbackCommand(feedback_id="fb-1")
        assert cmd1 == cmd2

    def test_repr_contains_class_name(self) -> None:
        cmd = ArchiveFeedbackCommand(feedback_id="fb-1")
        assert "ArchiveFeedbackCommand" in repr(cmd)


class TestAdjustScoreWeightsCommand:
    """AdjustScoreWeightsCommand — Ajustar pesos de scoring."""

    def test_creates_with_all_fields(self) -> None:
        weights = {"relevance": 0.4, "popularity": 0.3, "recency": 0.2, "source_reliability": 0.1}
        cmd = AdjustScoreWeightsCommand(
            source_id="model-1",
            weights=weights,
            reason="New weighting strategy",
        )
        assert cmd.source_id == "model-1"
        assert cmd.weights == weights
        assert cmd.reason == "New weighting strategy"

    def test_is_frozen(self) -> None:
        cmd = AdjustScoreWeightsCommand(
            source_id="m", weights={"r": 1.0}, reason="r",
        )
        with pytest.raises(FrozenInstanceError):
            cmd.source_id = "mutated"  # type: ignore[misc]

    def test_equality(self) -> None:
        w = {"relevance": 0.5}
        cmd1 = AdjustScoreWeightsCommand(source_id="m", weights=w, reason="r")
        cmd2 = AdjustScoreWeightsCommand(source_id="m", weights=w, reason="r")
        assert cmd1 == cmd2

    def test_repr_contains_class_name(self) -> None:
        cmd = AdjustScoreWeightsCommand(source_id="m", weights={}, reason="r")
        assert "AdjustScoreWeightsCommand" in repr(cmd)


class TestRecalculateSignalsCommand:
    """RecalculateSignalsCommand — Recalcular señales de aprendizaje."""

    def test_creates_with_no_args(self) -> None:
        cmd = RecalculateSignalsCommand()
        assert cmd.source_id is None
        assert cmd.signal_type is None

    def test_creates_with_source_id(self) -> None:
        cmd = RecalculateSignalsCommand(source_id="src-1")
        assert cmd.source_id == "src-1"
        assert cmd.signal_type is None

    def test_creates_with_all_fields(self) -> None:
        cmd = RecalculateSignalsCommand(source_id="src-1", signal_type="KEYWORD")
        assert cmd.source_id == "src-1"
        assert cmd.signal_type == "KEYWORD"

    def test_is_frozen(self) -> None:
        cmd = RecalculateSignalsCommand()
        with pytest.raises(FrozenInstanceError):
            cmd.source_id = "mutated"  # type: ignore[misc]

    def test_equality(self) -> None:
        cmd1 = RecalculateSignalsCommand(source_id="s", signal_type="KEYWORD")
        cmd2 = RecalculateSignalsCommand(source_id="s", signal_type="KEYWORD")
        assert cmd1 == cmd2

    def test_repr_contains_class_name(self) -> None:
        cmd = RecalculateSignalsCommand()
        assert "RecalculateSignalsCommand" in repr(cmd)


class TestRegisterSignalCommand:
    """RegisterSignalCommand — Registrar una nueva señal de aprendizaje."""

    def test_creates_with_all_fields(self) -> None:
        cmd = RegisterSignalCommand(
            dimension="KEYWORD",
            source="python",
            value=0.85,
        )
        assert cmd.dimension == "KEYWORD"
        assert cmd.source == "python"
        assert cmd.value == 0.85

    def test_is_frozen(self) -> None:
        cmd = RegisterSignalCommand(dimension="KEYWORD", source="python", value=0.5)
        with pytest.raises(FrozenInstanceError):
            cmd.dimension = "mutated"  # type: ignore[misc]

    def test_equality(self) -> None:
        cmd1 = RegisterSignalCommand(dimension="KEYWORD", source="python", value=0.85)
        cmd2 = RegisterSignalCommand(dimension="KEYWORD", source="python", value=0.85)
        assert cmd1 == cmd2

    def test_repr_contains_class_name(self) -> None:
        cmd = RegisterSignalCommand(dimension="KEYWORD", source="python", value=0.5)
        assert "RegisterSignalCommand" in repr(cmd)


class TestUpdateSourceProfileCommand:
    """UpdateSourceProfileCommand — Actualizar perfil de calidad de fuente."""

    def test_creates_with_all_fields(self) -> None:
        cmd = UpdateSourceProfileCommand(source_id="src-1", decision="approved")
        assert cmd.source_id == "src-1"
        assert cmd.decision == "approved"

    def test_is_frozen(self) -> None:
        cmd = UpdateSourceProfileCommand(source_id="src-1", decision="approved")
        with pytest.raises(FrozenInstanceError):
            cmd.source_id = "mutated"  # type: ignore[misc]

    def test_equality(self) -> None:
        cmd1 = UpdateSourceProfileCommand(source_id="src-1", decision="rejected")
        cmd2 = UpdateSourceProfileCommand(source_id="src-1", decision="rejected")
        assert cmd1 == cmd2

    def test_repr_contains_class_name(self) -> None:
        cmd = UpdateSourceProfileCommand(source_id="src-1", decision="approved")
        assert "UpdateSourceProfileCommand" in repr(cmd)


class TestGenerateDatasetCommand:
    """GenerateDatasetCommand — Generar un dataset de entrenamiento para ML."""

    def test_creates_with_required_only(self) -> None:
        cmd = GenerateDatasetCommand(
            name="Training Set v1",
            time_window_start="2026-01-01T00:00:00Z",
            time_window_end="2026-07-01T00:00:00Z",
        )
        assert cmd.name == "Training Set v1"
        assert cmd.time_window_start == "2026-01-01T00:00:00Z"
        assert cmd.time_window_end == "2026-07-01T00:00:00Z"
        assert cmd.max_samples is None

    def test_creates_with_max_samples(self) -> None:
        cmd = GenerateDatasetCommand(
            name="Small Set",
            time_window_start="2026-06-01T00:00:00Z",
            time_window_end="2026-07-01T00:00:00Z",
            max_samples=1000,
        )
        assert cmd.max_samples == 1000

    def test_is_frozen(self) -> None:
        cmd = GenerateDatasetCommand(
            name="x", time_window_start="s", time_window_end="e",
        )
        with pytest.raises(FrozenInstanceError):
            cmd.name = "mutated"  # type: ignore[misc]

    def test_equality(self) -> None:
        cmd1 = GenerateDatasetCommand(
            name="n", time_window_start="s", time_window_end="e", max_samples=100,
        )
        cmd2 = GenerateDatasetCommand(
            name="n", time_window_start="s", time_window_end="e", max_samples=100,
        )
        assert cmd1 == cmd2

    def test_repr_contains_class_name(self) -> None:
        cmd = GenerateDatasetCommand(
            name="n", time_window_start="s", time_window_end="e",
        )
        assert "GenerateDatasetCommand" in repr(cmd)


class TestAllCommandsImmutability:
    """All 7 commands must be frozen dataclasses."""

    @pytest.mark.parametrize(
        "cmd_factory",
        [
            lambda: RecordFeedbackCommand(
                topic_id="t", decision="APPROVED", reason=None,
                source_name="s", title="T",
            ),
            lambda: ArchiveFeedbackCommand(feedback_id="fb-1"),
            lambda: AdjustScoreWeightsCommand(
                source_id="m", weights={"r": 1.0}, reason="r",
            ),
            lambda: RecalculateSignalsCommand(),
            lambda: RegisterSignalCommand(dimension="KEYWORD", source="python", value=0.5),
            lambda: UpdateSourceProfileCommand(source_id="s", decision="approved"),
            lambda: GenerateDatasetCommand(
                name="n", time_window_start="s", time_window_end="e",
            ),
        ],
    )
    def test_all_commands_are_frozen(self, cmd_factory) -> None:
        cmd = cmd_factory()
        first_field = next(iter(cmd.__dataclass_fields__))
        with pytest.raises(FrozenInstanceError):
            setattr(cmd, first_field, "mutated")
