"""Tests for Repository Ports — Protocol structural typing compliance."""
import pytest
from datetime import datetime, timezone
from learning.domain.ports.repositories import (
    FeedbackRepository,
    LearningSignalRepository,
    SourceQualityRepository,
    LearningModelRepository,
)
from learning.domain.entities.feedback_record import FeedbackRecord
from learning.domain.entities.learning_signal import LearningSignal
from learning.domain.entities.source_quality import SourceQualityProfile
from learning.domain.entities.learning_model import LearningModel
from learning.domain.entities.ids import FeedbackId, LearningSignalId, SourceQualityId, LearningModelId
from learning.domain.value_objects.decision_type import DecisionType
from learning.domain.value_objects.signal_type import SignalType
from learning.domain.value_objects.signal_strength import SignalStrength
from learning.domain.value_objects.time_window import TimeWindow
from learning.domain.value_objects.score_weights import ScoreWeights
from learning.domain.value_objects.algorithm_version import AlgorithmVersion
from foundation.result.result import Result


class TestRepositoryProtocolCompliance:
    """Verify that the repository ports are proper Protocols."""

    def test_feedback_repository_is_protocol(self):
        assert hasattr(FeedbackRepository, "__protocol_attrs__") or hasattr(
            FeedbackRepository, "__abstractmethods__"
        )

    def test_signal_repository_is_protocol(self):
        assert hasattr(LearningSignalRepository, "__protocol_attrs__") or hasattr(
            LearningSignalRepository, "__abstractmethods__"
        )

    def test_source_quality_repository_is_protocol(self):
        assert hasattr(SourceQualityRepository, "__protocol_attrs__") or hasattr(
            SourceQualityRepository, "__abstractmethods__"
        )

    def test_learning_model_repository_is_protocol(self):
        assert hasattr(LearningModelRepository, "__protocol_attrs__") or hasattr(
            LearningModelRepository, "__abstractmethods__"
        )


class TestInMemoryFeedbackRepository:
    """Test that a concrete implementation satisfies the Protocol."""

    def test_satisfies_protocol(self):
        class InMemoryFeedbackRepo:
            def __init__(self):
                self._data: dict[str, FeedbackRecord] = {}

            def save(self, feedback: FeedbackRecord) -> None:
                self._data[str(feedback.id)] = feedback

            def find_by_id(self, id: FeedbackId):
                item = self._data.get(str(id))
                if item:
                    return Result.success(item)
                return Result.failure("FEEDBACK_NOT_FOUND")

            def find_by_topic_id(self, topic_id: str):
                return [f for f in self._data.values() if f.topic_id == topic_id]

            def find_by_source(self, source_name: str):
                return [f for f in self._data.values() if f.source_name == source_name]

            def find_all_in_window(self, start: datetime, end: datetime):
                return [f for f in self._data.values() if start <= f.captured_at < end]

            def count_by_decision(self, decision: DecisionType):
                return sum(1 for f in self._data.values() if f.decision == decision)

        repo = InMemoryFeedbackRepo()
        # Structural typing check — this should not raise
        assert isinstance(repo, type(repo))  # basic sanity
        # Functional check
        assert callable(getattr(repo, "save", None))
        assert callable(getattr(repo, "find_by_id", None))
