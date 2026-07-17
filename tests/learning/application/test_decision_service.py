"""Tests for DecisionService — 16 test cases covering all methods and AL rules."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, call

import pytest

from foundation.result.result import Error, Result
from learning.application.commands.feedback_commands import (
    ArchiveFeedbackCommand,
    RecordFeedbackCommand,
)
from learning.application.dto.feedback_dto import FeedbackDetailDTO, FeedbackSummaryDTO
from learning.application.exceptions.error_code import ApplicationErrorCode
from learning.application.queries.feedback_queries import (
    GetFeedbackQuery,
    ListFeedbackQuery,
)
from learning.application.services.decision_service import DecisionService
from learning.application.common.query_result import QueryResult
from learning.domain.entities.ids import FeedbackId
from learning.domain.exceptions import LearningDomainError

FIXED_TS = datetime(2026, 7, 15, tzinfo=timezone.utc)


class TestDecisionServiceRecordFeedback:
    """Tests for DecisionService.execute_record_feedback — command."""

    def _make_service(self):
        feedback_repo = MagicMock()
        source_quality_repo = MagicMock()
        uow = MagicMock()
        event_publisher = MagicMock()
        clock = MagicMock()
        clock.now.return_value = FIXED_TS

        service = DecisionService(
            feedback_repo=feedback_repo,
            source_quality_repo=source_quality_repo,
            uow=uow,
            event_publisher=event_publisher,
            clock=clock,
        )
        return service, feedback_repo, source_quality_repo, uow, event_publisher, clock

    def test_record_feedback_success(self, feature_snapshot) -> None:
        """APPROVED feedback without source profile → success + DTO returned."""
        service, feedback_repo, source_quality_repo, uow, event_publisher, clock = (
            self._make_service()
        )
        source_quality_repo.find_by_source_name.return_value = Result.failure(
            Error(code="SOURCE_QUALITY_NOT_FOUND", message="Not found")
        )

        cmd = RecordFeedbackCommand(
            topic_id="topic-1",
            decision="APPROVED",
            reason=None,
            source_name="TechBlog",
            title="Test Article",
            features={
                "base_score": 0.8,
                "freshness_score": 0.7,
                "keyword_bonus": 0.1,
                "source_bonus": 0.2,
                "topic_penalty": 0.0,
                "confidence": 0.9,
                "final_score": 0.85,
            },
        )

        result = service.execute_record_feedback(cmd)

        assert result.is_success
        dto = result.value
        assert isinstance(dto, FeedbackDetailDTO)
        assert dto.topic_id == "topic-1"
        assert dto.decision == "APPROVED"
        assert dto.source_name == "TechBlog"
        assert dto.title == "Test Article"
        assert dto.reason is None

    def test_record_feedback_with_source_profile_updates_quality(self) -> None:
        """When source profile exists, record_decision is called on it."""
        service, feedback_repo, source_quality_repo, uow, event_publisher, clock = (
            self._make_service()
        )
        mock_profile = MagicMock()
        mock_profile.record_decision = MagicMock()
        source_quality_repo.find_by_source_name.return_value = Result.success(
            mock_profile
        )

        cmd = RecordFeedbackCommand(
            topic_id="topic-1",
            decision="APPROVED",
            reason=None,
            source_name="TechBlog",
            title="Test Article",
            features=None,
        )

        result = service.execute_record_feedback(cmd)

        assert result.is_success
        mock_profile.record_decision.assert_called_once_with(decision_type="approved")
        source_quality_repo.save.assert_called_once_with(mock_profile)

    def test_record_feedback_rejected_with_reason(self) -> None:
        """REJECTED with reason → success."""
        service, feedback_repo, source_quality_repo, uow, event_publisher, clock = (
            self._make_service()
        )
        source_quality_repo.find_by_source_name.return_value = Result.failure(
            Error(code="SOURCE_QUALITY_NOT_FOUND", message="Not found")
        )

        cmd = RecordFeedbackCommand(
            topic_id="topic-1",
            decision="REJECTED",
            reason="Off-topic content",
            source_name="TechBlog",
            title="Spam Article",
            features=None,
        )

        result = service.execute_record_feedback(cmd)

        assert result.is_success
        assert result.value.decision == "REJECTED"
        assert result.value.reason == "Off-topic content"

    def test_record_feedback_rejected_without_reason(self) -> None:
        """REJECTED without reason → LearningDomainError → failure."""
        service, feedback_repo, source_quality_repo, uow, event_publisher, clock = (
            self._make_service()
        )

        cmd = RecordFeedbackCommand(
            topic_id="topic-1",
            decision="REJECTED",
            reason=None,
            source_name="TechBlog",
            title="Spam Article",
            features=None,
        )

        result = service.execute_record_feedback(cmd)

        assert result.is_failure
        assert result.error.code == ApplicationErrorCode.OPERATION_FAILED

    def test_record_feedback_invalid_decision(self) -> None:
        """Invalid decision type string → ValueError → failure."""
        service, feedback_repo, source_quality_repo, uow, event_publisher, clock = (
            self._make_service()
        )

        cmd = RecordFeedbackCommand(
            topic_id="topic-1",
            decision="INVALID_DECISION",
            reason=None,
            source_name="TechBlog",
            title="Test",
            features=None,
        )

        result = service.execute_record_feedback(cmd)

        assert result.is_failure

    def test_record_feedback_empty_topic_id(self) -> None:
        """Empty topic_id → LearningDomainError → failure."""
        service, feedback_repo, source_quality_repo, uow, event_publisher, clock = (
            self._make_service()
        )

        cmd = RecordFeedbackCommand(
            topic_id="",
            decision="APPROVED",
            reason=None,
            source_name="TechBlog",
            title="Test",
            features=None,
        )

        result = service.execute_record_feedback(cmd)

        assert result.is_failure

    def test_record_feedback_uow_commit_called(self) -> None:
        """UoW.commit() must be called for write operations."""
        service, feedback_repo, source_quality_repo, uow, event_publisher, clock = (
            self._make_service()
        )
        source_quality_repo.find_by_source_name.return_value = Result.failure(
            Error(code="SOURCE_QUALITY_NOT_FOUND", message="Not found")
        )

        cmd = RecordFeedbackCommand(
            topic_id="topic-1",
            decision="APPROVED",
            reason=None,
            source_name="TechBlog",
            title="Test",
            features=None,
        )

        service.execute_record_feedback(cmd)

        uow.commit.assert_called_once()

    def test_record_feedback_events_published_after_commit(self) -> None:
        """Events must be published AFTER commit, not before."""
        service, feedback_repo, source_quality_repo, uow, event_publisher, clock = (
            self._make_service()
        )
        source_quality_repo.find_by_source_name.return_value = Result.failure(
            Error(code="SOURCE_QUALITY_NOT_FOUND", message="Not found")
        )

        call_order: list[str] = []
        uow.commit.side_effect = lambda: call_order.append("commit")
        event_publisher.publish_many.side_effect = lambda e: call_order.append(
            "publish_many"
        )

        cmd = RecordFeedbackCommand(
            topic_id="topic-1",
            decision="APPROVED",
            reason=None,
            source_name="TechBlog",
            title="Test",
            features=None,
        )

        service.execute_record_feedback(cmd)

        assert "commit" in call_order
        assert "publish_many" in call_order
        assert call_order.index("commit") < call_order.index("publish_many")

    def test_record_feedback_publishes_domain_events(self) -> None:
        """FeedbackCaptured event must be published after commit."""
        service, feedback_repo, source_quality_repo, uow, event_publisher, clock = (
            self._make_service()
        )
        source_quality_repo.find_by_source_name.return_value = Result.failure(
            Error(code="SOURCE_QUALITY_NOT_FOUND", message="Not found")
        )

        cmd = RecordFeedbackCommand(
            topic_id="topic-1",
            decision="APPROVED",
            reason=None,
            source_name="TechBlog",
            title="Test",
            features=None,
        )

        service.execute_record_feedback(cmd)

        event_publisher.publish_many.assert_called_once()
        published_events = event_publisher.publish_many.call_args[0][0]
        assert len(published_events) >= 1


class TestDecisionServiceArchiveFeedback:
    """Tests for DecisionService.execute_archive_feedback — command."""

    def _make_service(self):
        feedback_repo = MagicMock()
        source_quality_repo = MagicMock()
        uow = MagicMock()
        event_publisher = MagicMock()
        clock = MagicMock()

        service = DecisionService(
            feedback_repo=feedback_repo,
            source_quality_repo=source_quality_repo,
            uow=uow,
            event_publisher=event_publisher,
            clock=clock,
        )
        return service, feedback_repo

    def test_archive_feedback_success(self, feedback_record) -> None:
        """Archive existing feedback → returns FeedbackSummaryDTO."""
        service, feedback_repo = self._make_service()
        feedback_repo.find_by_id.return_value = Result.success(feedback_record)

        cmd = ArchiveFeedbackCommand(feedback_id=str(feedback_record.id))
        result = service.execute_archive_feedback(cmd)

        assert result.is_success
        dto = result.value
        assert isinstance(dto, FeedbackSummaryDTO)
        assert dto.topic_id == "topic-ai"
        assert dto.decision == "APPROVED"

    def test_archive_feedback_not_found(self) -> None:
        """Archive nonexistent feedback → failure."""
        service, feedback_repo = self._make_service()
        feedback_repo.find_by_id.return_value = Result.failure(
            Error(code="FEEDBACK_NOT_FOUND", message="Not found")
        )

        cmd = ArchiveFeedbackCommand(feedback_id="00000000-0000-0000-0000-000000000099")
        result = service.execute_archive_feedback(cmd)

        assert result.is_failure
        assert result.error.code == ApplicationErrorCode.RESOURCE_NOT_FOUND


class TestDecisionServiceGetFeedback:
    """Tests for DecisionService.execute_get_feedback — query (no UoW)."""

    def _make_service(self):
        feedback_repo = MagicMock()
        source_quality_repo = MagicMock()
        uow = MagicMock()
        event_publisher = MagicMock()
        clock = MagicMock()

        service = DecisionService(
            feedback_repo=feedback_repo,
            source_quality_repo=source_quality_repo,
            uow=uow,
            event_publisher=event_publisher,
            clock=clock,
        )
        return service, feedback_repo, uow

    def test_get_feedback_success(self, feedback_record) -> None:
        """Get existing feedback → returns FeedbackDetailDTO."""
        service, feedback_repo, uow = self._make_service()
        feedback_repo.find_by_id.return_value = Result.success(feedback_record)

        query = GetFeedbackQuery(feedback_id=str(feedback_record.id))
        result = service.execute_get_feedback(query)

        assert result.is_success
        dto = result.value
        assert isinstance(dto, FeedbackDetailDTO)
        assert dto.topic_id == "topic-ai"
        assert dto.source_name == "TechBlog"

    def test_get_feedback_not_found(self) -> None:
        """Get nonexistent feedback → failure."""
        service, feedback_repo, uow = self._make_service()
        feedback_repo.find_by_id.return_value = Result.failure(
            Error(code="FEEDBACK_NOT_FOUND", message="Not found")
        )

        query = GetFeedbackQuery(feedback_id="00000000-0000-0000-0000-000000000099")
        result = service.execute_get_feedback(query)

        assert result.is_failure

    def test_get_feedback_no_uow_commit(self, feedback_record) -> None:
        """Queries must NOT call UoW.commit()."""
        service, feedback_repo, uow = self._make_service()
        feedback_repo.find_by_id.return_value = Result.success(feedback_record)

        query = GetFeedbackQuery(feedback_id=str(feedback_record.id))
        service.execute_get_feedback(query)

        uow.commit.assert_not_called()


class TestDecisionServiceListFeedback:
    """Tests for DecisionService.execute_list_feedback — query (no UoW)."""

    def _make_service(self):
        feedback_repo = MagicMock()
        source_quality_repo = MagicMock()
        uow = MagicMock()
        event_publisher = MagicMock()
        clock = MagicMock()

        service = DecisionService(
            feedback_repo=feedback_repo,
            source_quality_repo=source_quality_repo,
            uow=uow,
            event_publisher=event_publisher,
            clock=clock,
        )
        return service, feedback_repo, uow

    def test_list_feedback_success_by_topic(
        self, feedback_record, feature_snapshot
    ) -> None:
        """List feedback filtered by topic → returns QueryResult with data."""
        service, feedback_repo, uow = self._make_service()
        feedback_repo.find_by_topic_id.return_value = [feedback_record]

        query = ListFeedbackQuery(topic_id="topic-ai")
        result = service.execute_list_feedback(query)

        assert result.is_success
        qr = result.value
        assert isinstance(qr, QueryResult)
        assert qr.total == 1
        assert len(qr.data) == 1
        assert isinstance(qr.data[0], FeedbackSummaryDTO)

    def test_list_feedback_success_by_source(self, feedback_record) -> None:
        """List feedback filtered by source → returns QueryResult with data."""
        service, feedback_repo, uow = self._make_service()
        feedback_repo.find_by_source.return_value = [feedback_record]

        query = ListFeedbackQuery(source_name="TechBlog")
        result = service.execute_list_feedback(query)

        assert result.is_success
        qr = result.value
        assert qr.total == 1
        assert qr.data[0].source_name == "TechBlog"

    def test_list_feedback_empty(self) -> None:
        """List feedback with no filter → returns empty QueryResult."""
        service, feedback_repo, uow = self._make_service()

        query = ListFeedbackQuery()
        result = service.execute_list_feedback(query)

        assert result.is_success
        qr = result.value
        assert isinstance(qr, QueryResult)
        assert qr.total == 0
        assert len(qr.data) == 0

    def test_list_feedback_no_uow_commit(self, feedback_record) -> None:
        """Queries must NOT call UoW.commit()."""
        service, feedback_repo, uow = self._make_service()
        feedback_repo.find_by_topic_id.return_value = [feedback_record]

        query = ListFeedbackQuery(topic_id="topic-ai")
        service.execute_list_feedback(query)

        uow.commit.assert_not_called()
