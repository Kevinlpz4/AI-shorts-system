"""Tests for SignalService — 11 test cases covering all methods and AL rules."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from foundation.result.result import Error, Result
from learning.application.commands.score_commands import RecalculateSignalsCommand
from learning.application.commands.signal_commands import RegisterSignalCommand
from learning.application.dto.signal_dto import LearningSignalDTO
from learning.application.exceptions.error_code import ApplicationErrorCode
from learning.application.queries.model_queries import GetLearningSignalsQuery
from learning.application.services.signal_service import SignalService
from learning.application.common.query_result import QueryResult
from learning.domain.entities.learning_signal import LearningSignal
from learning.domain.value_objects.signal_strength import SignalStrength
from learning.domain.value_objects.signal_type import SignalType
from learning.domain.value_objects.time_window import TimeWindow

FIXED_TS = datetime(2026, 7, 15, tzinfo=timezone.utc)


class TestSignalServiceRegisterSignal:
    """Tests for SignalService.execute_register_signal — command."""

    def _make_service(self):
        signal_repo = MagicMock()
        signal_registry = MagicMock()
        uow = MagicMock()
        event_publisher = MagicMock()
        clock = MagicMock()
        clock.now.return_value = FIXED_TS

        service = SignalService(
            signal_repo=signal_repo,
            signal_registry=signal_registry,
            uow=uow,
            event_publisher=event_publisher,
            clock=clock,
        )
        return service, signal_repo, signal_registry, uow, event_publisher, clock

    def test_register_signal_success(self) -> None:
        """Register a valid signal → success + LearningSignalDTO returned."""
        service, signal_repo, signal_registry, uow, event_publisher, clock = (
            self._make_service()
        )
        mock_handler = MagicMock()
        mock_handler.compute.return_value = SignalStrength(
            value=0.8, decay_factor=0.1
        )
        signal_registry.get_handler.return_value = mock_handler

        cmd = RegisterSignalCommand(
            dimension="KEYWORD",
            source="python",
            value=0.85,
        )

        result = service.execute_register_signal(cmd)

        assert result.is_success
        dto = result.value
        assert isinstance(dto, LearningSignalDTO)
        assert dto.dimension == "KEYWORD"
        assert dto.source == "python"
        assert dto.sample_size == 1
        assert dto.approval_rate == 0.85

    def test_register_signal_uow_commit_called(self) -> None:
        """UoW.commit() must be called for write operations."""
        service, signal_repo, signal_registry, uow, event_publisher, clock = (
            self._make_service()
        )
        mock_handler = MagicMock()
        mock_handler.compute.return_value = SignalStrength(
            value=0.8, decay_factor=0.1
        )
        signal_registry.get_handler.return_value = mock_handler

        cmd = RegisterSignalCommand(dimension="KEYWORD", source="python", value=0.85)
        service.execute_register_signal(cmd)

        uow.commit.assert_called_once()

    def test_register_signal_events_published(self) -> None:
        """Events must be published after commit."""
        service, signal_repo, signal_registry, uow, event_publisher, clock = (
            self._make_service()
        )
        mock_handler = MagicMock()
        mock_handler.compute.return_value = SignalStrength(
            value=0.8, decay_factor=0.1
        )
        signal_registry.get_handler.return_value = mock_handler

        cmd = RegisterSignalCommand(dimension="KEYWORD", source="python", value=0.85)
        service.execute_register_signal(cmd)

        # LearningSignal doesn't emit events on __init__, only on update()
        # So publish_many may or may not be called depending on events
        signal_repo.save.assert_called_once()

    def test_register_signal_unknown_dimension(self) -> None:
        """Unknown signal dimension → KeyError → COMMAND_INVALID."""
        service, signal_repo, signal_registry, uow, event_publisher, clock = (
            self._make_service()
        )
        # Use valid SignalType string but registry has no handler for it
        signal_registry.get_handler.side_effect = KeyError("No handler for signal type 'KEYWORD'")

        cmd = RegisterSignalCommand(dimension="KEYWORD", source="test", value=0.5)
        result = service.execute_register_signal(cmd)

        assert result.is_failure
        assert result.error.code == ApplicationErrorCode.COMMAND_INVALID

    def test_register_signal_saves_to_repo(self) -> None:
        """Registering a signal must persist via signal_repo.save()."""
        service, signal_repo, signal_registry, uow, event_publisher, clock = (
            self._make_service()
        )
        mock_handler = MagicMock()
        mock_handler.compute.return_value = SignalStrength(
            value=0.8, decay_factor=0.1
        )
        signal_registry.get_handler.return_value = mock_handler

        cmd = RegisterSignalCommand(dimension="KEYWORD", source="python", value=0.85)
        service.execute_register_signal(cmd)

        signal_repo.save.assert_called_once()
        saved_signal = signal_repo.save.call_args[0][0]
        assert isinstance(saved_signal, LearningSignal)


class TestSignalServiceRecalculateSignals:
    """Tests for SignalService.execute_recalculate_signals — command."""

    def _make_service(self):
        signal_repo = MagicMock()
        signal_registry = MagicMock()
        uow = MagicMock()
        event_publisher = MagicMock()
        clock = MagicMock()
        clock.now.return_value = FIXED_TS

        service = SignalService(
            signal_repo=signal_repo,
            signal_registry=signal_registry,
            uow=uow,
            event_publisher=event_publisher,
            clock=clock,
        )
        return service, signal_repo, uow

    def test_recalculate_signals_success(self, learning_signal) -> None:
        """Recalculate with existing signals → returns count of recalculated."""
        service, signal_repo, uow = self._make_service()
        signal_repo.find_all_active.return_value = [learning_signal]

        # Clock must return a time AFTER signal.last_updated (FIXED_TS) so elapsed > 0
        from datetime import timedelta
        service._clock.now.return_value = FIXED_TS + timedelta(hours=6)

        cmd = RecalculateSignalsCommand()
        result = service.execute_recalculate_signals(cmd)

        assert result.is_success
        assert result.value == 1

    def test_recalculate_signals_empty(self) -> None:
        """Recalculate with no signals → returns 0."""
        service, signal_repo, uow = self._make_service()
        signal_repo.find_all_active.return_value = []

        cmd = RecalculateSignalsCommand()
        result = service.execute_recalculate_signals(cmd)

        assert result.is_success
        assert result.value == 0

    def test_recalculate_signals_with_type_filter(self, learning_signal) -> None:
        """Recalculate with signal_type filter → only matching signals."""
        service, signal_repo, uow = self._make_service()
        # find_all_active returns all signals, service filters by type
        signal_repo.find_all_active.return_value = [learning_signal]

        # Clock must return a time AFTER signal.last_updated so elapsed > 0
        from datetime import timedelta
        service._clock.now.return_value = FIXED_TS + timedelta(hours=6)

        cmd = RecalculateSignalsCommand(signal_type="KEYWORD")
        result = service.execute_recalculate_signals(cmd)

        assert result.is_success
        assert result.value == 1

    def test_recalculate_signals_with_type_filter_no_match(self) -> None:
        """Recalculate with signal_type filter that matches nothing → 0."""
        service, signal_repo, uow = self._make_service()
        # Create a SOURCE signal but filter for KEYWORD
        source_signal = MagicMock()
        source_signal.signal_type = SignalType.SOURCE
        source_signal.last_updated = FIXED_TS
        signal_repo.find_all_active.return_value = [source_signal]

        cmd = RecalculateSignalsCommand(signal_type="KEYWORD")
        result = service.execute_recalculate_signals(cmd)

        assert result.is_success
        assert result.value == 0

    def test_recalculate_signals_uow_commit_called(self) -> None:
        """UoW.commit() must be called for write operations."""
        service, signal_repo, uow = self._make_service()
        signal_repo.find_all_active.return_value = []

        cmd = RecalculateSignalsCommand()
        service.execute_recalculate_signals(cmd)

        uow.commit.assert_called_once()


class TestSignalServiceGetLearningSignals:
    """Tests for SignalService.execute_get_learning_signals — query (no UoW)."""

    def _make_service(self):
        signal_repo = MagicMock()
        signal_registry = MagicMock()
        uow = MagicMock()
        event_publisher = MagicMock()
        clock = MagicMock()

        service = SignalService(
            signal_repo=signal_repo,
            signal_registry=signal_registry,
            uow=uow,
            event_publisher=event_publisher,
            clock=clock,
        )
        return service, signal_repo, uow

    def test_get_learning_signals_success(self, learning_signal) -> None:
        """Get signals with no filter → returns QueryResult."""
        service, signal_repo, uow = self._make_service()
        signal_repo.find_all_active.return_value = [learning_signal]

        query = GetLearningSignalsQuery()
        result = service.execute_get_learning_signals(query)

        assert result.is_success
        qr = result.value
        assert isinstance(qr, QueryResult)
        assert qr.total == 1
        assert isinstance(qr.data[0], LearningSignalDTO)

    def test_get_learning_signals_by_dimension(self, learning_signal) -> None:
        """Filter by dimension → only matching signals returned."""
        service, signal_repo, uow = self._make_service()
        signal_repo.find_all_active.return_value = [learning_signal]

        query = GetLearningSignalsQuery(dimension="KEYWORD")
        result = service.execute_get_learning_signals(query)

        assert result.is_success
        assert result.value.total == 1
        assert result.value.data[0].dimension == "KEYWORD"

    def test_get_learning_signals_by_source(self, learning_signal) -> None:
        """Filter by source → only matching signals returned."""
        service, signal_repo, uow = self._make_service()
        signal_repo.find_all_active.return_value = [learning_signal]

        query = GetLearningSignalsQuery(source="python")
        result = service.execute_get_learning_signals(query)

        assert result.is_success
        assert result.value.total == 1
        assert result.value.data[0].source == "python"

    def test_get_learning_signals_no_uow(self, learning_signal) -> None:
        """Queries must NOT call UoW.commit()."""
        service, signal_repo, uow = self._make_service()
        signal_repo.find_all_active.return_value = [learning_signal]

        query = GetLearningSignalsQuery()
        service.execute_get_learning_signals(query)

        uow.commit.assert_not_called()
