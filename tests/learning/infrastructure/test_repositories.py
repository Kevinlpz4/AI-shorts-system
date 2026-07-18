"""
Tests for InMemory repositories in the Learning Infrastructure layer.

Covers all 4 repositories:
- InMemoryFeedbackRepository
- InMemoryLearningSignalRepository
- InMemorySourceQualityRepository
- InMemoryLearningModelRepository
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from learning.domain.entities.ids import (
    FeedbackId,
    LearningModelId,
    LearningSignalId,
    SourceQualityId,
)
from learning.domain.exceptions.errors import LearningErrorCode
from learning.domain.value_objects.algorithm_version import AlgorithmVersion
from learning.domain.value_objects.decision_type import DecisionType
from learning.domain.value_objects.signal_type import SignalType
from learning.infrastructure.inmemory.repositories import (
    InMemoryFeedbackRepository,
    InMemoryLearningModelRepository,
    InMemoryLearningSignalRepository,
    InMemorySourceQualityRepository,
)

from .conftest import (
    FIXED_TS,
    make_feedback,
    make_model,
    make_signal,
    make_source_quality,
)


# ===========================================================================
# InMemoryFeedbackRepository
# ===========================================================================


class TestInMemoryFeedbackRepository:
    """Tests for InMemoryFeedbackRepository."""

    def test_save_and_find_by_id(self) -> None:
        repo = InMemoryFeedbackRepository()
        fb = make_feedback()

        repo.save(fb)

        result = repo.find_by_id(fb.id)
        assert result.is_success
        assert result.unwrap() is fb

    def test_save_duplicate_raises(self) -> None:
        repo = InMemoryFeedbackRepository()
        fb = make_feedback()

        repo.save(fb)

        with pytest.raises(ValueError, match="Duplicate feedback"):
            repo.save(fb)

    def test_find_by_topic_id(self) -> None:
        repo = InMemoryFeedbackRepository()
        fb1 = make_feedback(topic_id="topic-A")
        fb2 = make_feedback(topic_id="topic-B")
        fb3 = make_feedback(topic_id="topic-A")

        repo.save(fb1)
        repo.save(fb2)
        repo.save(fb3)

        results = repo.find_by_topic_id("topic-A")
        assert len(results) == 2
        assert fb1 in results
        assert fb3 in results

    def test_find_by_source(self) -> None:
        repo = InMemoryFeedbackRepository()
        fb1 = make_feedback(source_name="source-x")
        fb2 = make_feedback(source_name="source-y")
        fb3 = make_feedback(source_name="source-x")

        repo.save(fb1)
        repo.save(fb2)
        repo.save(fb3)

        results = repo.find_by_source("source-x")
        assert len(results) == 2
        assert fb1 in results
        assert fb3 in results

    def test_find_all_in_window(self) -> None:
        repo = InMemoryFeedbackRepository()

        ts1 = datetime(2026, 7, 10, tzinfo=timezone.utc)
        ts2 = datetime(2026, 7, 15, tzinfo=timezone.utc)
        ts3 = datetime(2026, 7, 20, tzinfo=timezone.utc)

        fb1 = make_feedback(captured_at=ts1)  # before window
        fb2 = make_feedback(captured_at=ts2)  # inside window
        fb3 = make_feedback(captured_at=ts3)  # after window

        repo.save(fb1)
        repo.save(fb2)
        repo.save(fb3)

        start = datetime(2026, 7, 12, tzinfo=timezone.utc)
        end = datetime(2026, 7, 18, tzinfo=timezone.utc)

        results = repo.find_all_in_window(start, end)
        assert len(results) == 1
        assert results[0] is fb2

    def test_count_by_decision(self) -> None:
        repo = InMemoryFeedbackRepository()
        repo.save(make_feedback(decision=DecisionType.APPROVED))
        repo.save(make_feedback(decision=DecisionType.APPROVED))
        repo.save(
            make_feedback(
                decision=DecisionType.REJECTED, reason="low_quality"
            )
        )

        assert repo.count_by_decision(DecisionType.APPROVED) == 2
        assert repo.count_by_decision(DecisionType.REJECTED) == 1
        assert repo.count_by_decision(DecisionType.AUTO_APPROVED) == 0

    def test_find_by_id_not_found(self) -> None:
        repo = InMemoryFeedbackRepository()
        result = repo.find_by_id(FeedbackId.generate())

        assert result.is_failure
        assert result.error.code == LearningErrorCode.FEEDBACK_NOT_FOUND


# ===========================================================================
# InMemoryLearningSignalRepository
# ===========================================================================


class TestInMemoryLearningSignalRepository:
    """Tests for InMemoryLearningSignalRepository."""

    def test_save_and_find_by_id(self) -> None:
        repo = InMemoryLearningSignalRepository()
        sig = make_signal()

        repo.save(sig)

        result = repo.find_by_id(sig.id)
        assert result.is_success
        assert result.unwrap() is sig

    def test_save_upsert(self) -> None:
        """Same ID replaces the old signal (upsert)."""
        repo = InMemoryLearningSignalRepository()
        sig_id = LearningSignalId.generate()

        sig1 = make_signal(id=sig_id, dimension="python")
        sig2 = make_signal(id=sig_id, dimension="rust")

        repo.save(sig1)
        repo.save(sig2)

        result = repo.find_by_id(sig_id)
        assert result.is_success
        assert result.unwrap().dimension == "rust"

    def test_save_batch(self) -> None:
        repo = InMemoryLearningSignalRepository()
        signals = [make_signal() for _ in range(5)]

        repo.save_batch(signals)

        for sig in signals:
            assert repo.find_by_id(sig.id).is_success

    def test_find_by_type_and_dimension(self) -> None:
        repo = InMemoryLearningSignalRepository()
        sig = make_signal(
            signal_type=SignalType.KEYWORD, dimension="python"
        )
        repo.save(sig)

        result = repo.find_by_type_and_dimension(
            SignalType.KEYWORD, "python"
        )
        assert result.is_success
        assert result.unwrap() is sig

    def test_find_by_type_and_dimension_not_found(self) -> None:
        repo = InMemoryLearningSignalRepository()

        result = repo.find_by_type_and_dimension(
            SignalType.KEYWORD, "nonexistent"
        )
        assert result.is_failure
        assert result.error.code == LearningErrorCode.SIGNAL_NOT_FOUND

    def test_find_by_window(self) -> None:
        repo = InMemoryLearningSignalRepository()

        # Signal covers Jul 5-11 — overlaps query [Jul 10, Jul 12)
        # (signal.end=Jul 11 > query.start=Jul 10 → overlap)
        sig_inside = make_signal(
            window_start=datetime(2026, 7, 5, tzinfo=timezone.utc),
            window_end=datetime(2026, 7, 11, tzinfo=timezone.utc),
        )
        # Signal covers Jul 20-31 (no overlap with query)
        sig_outside = make_signal(
            window_start=datetime(2026, 7, 20, tzinfo=timezone.utc),
            window_end=datetime(2026, 7, 31, tzinfo=timezone.utc),
        )
        # Signal covers Jul 8-18 (overlaps with query Jul 10-12)
        sig_overlap = make_signal(
            window_start=datetime(2026, 7, 8, tzinfo=timezone.utc),
            window_end=datetime(2026, 7, 18, tzinfo=timezone.utc),
        )

        repo.save(sig_inside)
        repo.save(sig_outside)
        repo.save(sig_overlap)

        results = repo.find_by_window(
            datetime(2026, 7, 10, tzinfo=timezone.utc),
            datetime(2026, 7, 12, tzinfo=timezone.utc),
        )
        assert len(results) == 2
        assert sig_inside in results
        assert sig_overlap in results
        assert sig_outside not in results

    def test_find_all_active(self) -> None:
        repo = InMemoryLearningSignalRepository()
        active = make_signal(sample_size=10)
        inactive = make_signal(sample_size=0)

        repo.save(active)
        repo.save(inactive)

        results = repo.find_all_active()
        assert len(results) == 1
        assert results[0] is active

    def test_find_by_id_not_found(self) -> None:
        repo = InMemoryLearningSignalRepository()
        result = repo.find_by_id(LearningSignalId.generate())

        assert result.is_failure
        assert result.error.code == LearningErrorCode.SIGNAL_NOT_FOUND


# ===========================================================================
# InMemorySourceQualityRepository
# ===========================================================================


class TestInMemorySourceQualityRepository:
    """Tests for InMemorySourceQualityRepository."""

    def test_save_and_find_by_id(self) -> None:
        repo = InMemorySourceQualityRepository()
        profile = make_source_quality()

        repo.save(profile)

        result = repo.find_by_id(profile.id)
        assert result.is_success
        assert result.unwrap() is profile

    def test_find_by_source_name(self) -> None:
        repo = InMemorySourceQualityRepository()
        profile = make_source_quality(source_name="my-source")

        repo.save(profile)

        result = repo.find_by_source_name("my-source")
        assert result.is_success
        assert result.unwrap().source_name == "my-source"

    def test_find_by_source_name_not_found(self) -> None:
        repo = InMemorySourceQualityRepository()
        result = repo.find_by_source_name("nonexistent")

        assert result.is_failure
        assert result.error.code == LearningErrorCode.SOURCE_QUALITY_NOT_FOUND

    def test_find_all_active(self) -> None:
        repo = InMemorySourceQualityRepository()
        active = make_source_quality(
            total_decisions=10,
            approved_count=5,
            rejected_count=3,
            auto_approved_count=1,
            auto_rejected_count=1,
            overridden_count=0,
        )
        inactive = make_source_quality(
            source_name="empty-source",
            total_decisions=0,
            approved_count=0,
            rejected_count=0,
            auto_approved_count=0,
            auto_rejected_count=0,
            overridden_count=0,
        )

        repo.save(active)
        repo.save(inactive)

        results = repo.find_all_active()
        assert len(results) == 1
        assert results[0] is active

    def test_exists_by_source_name(self) -> None:
        repo = InMemorySourceQualityRepository()
        repo.save(make_source_quality(source_name="exists"))

        assert repo.exists_by_source_name("exists") is True

    def test_exists_by_source_name_false(self) -> None:
        repo = InMemorySourceQualityRepository()

        assert repo.exists_by_source_name("nope") is False


# ===========================================================================
# InMemoryLearningModelRepository
# ===========================================================================


class TestInMemoryLearningModelRepository:
    """Tests for InMemoryLearningModelRepository."""

    def test_save_and_find_by_id(self) -> None:
        repo = InMemoryLearningModelRepository()
        model = make_model()

        repo.save(model)

        result = repo.find_by_id(model.id)
        assert result.is_success
        assert result.unwrap() is model

    def test_find_current_returns_latest_version(self) -> None:
        repo = InMemoryLearningModelRepository()
        model_v1 = make_model(version="1.0.0")
        model_v2 = make_model(version="2.0.0")
        model_v1_1 = make_model(version="1.1.0")

        repo.save(model_v1)
        repo.save(model_v2)
        repo.save(model_v1_1)

        result = repo.find_current()
        assert result.is_success
        assert result.unwrap() is model_v2

    def test_find_current_empty(self) -> None:
        repo = InMemoryLearningModelRepository()

        result = repo.find_current()
        assert result.is_failure
        assert result.error.code == LearningErrorCode.MODEL_NOT_FOUND

    def test_find_by_version(self) -> None:
        repo = InMemoryLearningModelRepository()
        model = make_model(version="1.2.3")

        repo.save(model)

        result = repo.find_by_version("1.2.3")
        assert result.is_success
        assert result.unwrap() is model

    def test_find_by_version_not_found(self) -> None:
        repo = InMemoryLearningModelRepository()
        repo.save(make_model(version="1.0.0"))

        result = repo.find_by_version("9.9.9")
        assert result.is_failure
        assert result.error.code == LearningErrorCode.MODEL_NOT_FOUND
