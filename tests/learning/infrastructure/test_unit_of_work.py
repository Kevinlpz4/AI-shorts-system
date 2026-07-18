"""
Tests for InMemoryLearningUnitOfWork.

Covers context manager lifecycle, commit, rollback, and property checks.
"""
from __future__ import annotations

import pytest

from learning.infrastructure.inmemory.unit_of_work import (
    InMemoryLearningUnitOfWork,
)


class TestInMemoryLearningUnitOfWork:
    """Tests for InMemoryLearningUnitOfWork lifecycle."""

    def test_context_manager_enter_exit(self) -> None:
        uow = InMemoryLearningUnitOfWork()

        with uow:
            assert uow.is_committed is False
            assert uow.is_rolled_back is False

        # After clean exit, still no commit/rollback
        assert uow.is_committed is False
        assert uow.is_rolled_back is False

    def test_commit(self) -> None:
        uow = InMemoryLearningUnitOfWork()

        with uow:
            uow.commit()

        assert uow.is_committed is True
        assert uow.is_rolled_back is False

    def test_rollback_on_exception(self) -> None:
        uow = InMemoryLearningUnitOfWork()

        with pytest.raises(RuntimeError):
            with uow:
                raise RuntimeError("simulated failure")

        assert uow.is_committed is False
        assert uow.is_rolled_back is True

    def test_rollback_manual(self) -> None:
        uow = InMemoryLearningUnitOfWork()

        with uow:
            uow.rollback()

        assert uow.is_committed is False
        assert uow.is_rolled_back is True

    def test_is_committed_property(self) -> None:
        uow = InMemoryLearningUnitOfWork()
        assert uow.is_committed is False

        with uow:
            uow.commit()
            assert uow.is_committed is True

        assert uow.is_committed is True

    def test_is_rolled_back_property(self) -> None:
        uow = InMemoryLearningUnitOfWork()
        assert uow.is_rolled_back is False

        with uow:
            assert uow.is_rolled_back is False

        assert uow.is_rolled_back is False

    def test_enter_resets_flags(self) -> None:
        """Re-entering the context manager resets previous state."""
        uow = InMemoryLearningUnitOfWork()

        with uow:
            uow.commit()

        assert uow.is_committed is True

        # Second transaction resets flags
        with uow:
            assert uow.is_committed is False
            assert uow.is_rolled_back is False
            uow.commit()

        assert uow.is_committed is True
