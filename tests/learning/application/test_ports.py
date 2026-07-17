"""Tests for Application Ports — Protocol definitions for dependency inversion."""

from __future__ import annotations

import inspect
import typing

import pytest

from learning.application.ports import (
    ClockPort,
    DatasetExporter,
    EventPublisher,
    LearningEventPublisher,
    UnitOfWork,
)


def _is_protocol(cls: type) -> bool:
    """Check if a class is a Protocol (compatible with Python < 3.12)."""
    return getattr(cls, "_is_protocol", False)


def _return_is_none(sig: inspect.Signature) -> bool:
    """Check if a method's return annotation is None (handles stringified annotations)."""
    ret = sig.return_annotation
    return ret is type(None) or ret is inspect.Parameter.empty or ret == "None"


class TestUnitOfWorkProtocol:
    """UnitOfWork — Context manager transaccional."""

    def test_is_protocol(self) -> None:
        assert _is_protocol(UnitOfWork)

    def test_has_enter_method(self) -> None:
        assert hasattr(UnitOfWork, "__enter__")

    def test_has_exit_method(self) -> None:
        assert hasattr(UnitOfWork, "__exit__")

    def test_has_commit_method(self) -> None:
        assert hasattr(UnitOfWork, "commit")

    def test_has_rollback_method(self) -> None:
        assert hasattr(UnitOfWork, "rollback")

    def test_enter_returns_uow(self) -> None:
        """__enter__ signature should return UnitOfWork."""
        sig = inspect.signature(UnitOfWork.__enter__)
        assert "UnitOfWork" in str(sig.return_annotation) or sig.return_annotation is inspect.Parameter.empty

    def test_commit_returns_none(self) -> None:
        sig = inspect.signature(UnitOfWork.commit)
        assert _return_is_none(sig)

    def test_rollback_returns_none(self) -> None:
        sig = inspect.signature(UnitOfWork.rollback)
        assert _return_is_none(sig)


class TestEventPublisherProtocol:
    """EventPublisher — Publicación de eventos de dominio."""

    def test_is_protocol(self) -> None:
        assert _is_protocol(EventPublisher)

    def test_has_publish_method(self) -> None:
        assert hasattr(EventPublisher, "publish")

    def test_has_publish_many_method(self) -> None:
        assert hasattr(EventPublisher, "publish_many")


class TestClockPortProtocol:
    """ClockPort — Obtención de la hora actual."""

    def test_is_protocol(self) -> None:
        assert _is_protocol(ClockPort)

    def test_has_now_method(self) -> None:
        assert hasattr(ClockPort, "now")

    def test_now_returns_datetime(self) -> None:
        sig = inspect.signature(ClockPort.now)
        ret = sig.return_annotation
        # Should return datetime
        assert "datetime" in str(ret) or ret is inspect.Parameter.empty


class TestDatasetExporterProtocol:
    """DatasetExporter — Exportación de datasets de entrenamiento."""

    def test_is_protocol(self) -> None:
        assert _is_protocol(DatasetExporter)

    def test_has_export_method(self) -> None:
        assert hasattr(DatasetExporter, "export")

    def test_export_returns_str(self) -> None:
        sig = inspect.signature(DatasetExporter.export)
        ret = sig.return_annotation
        assert "str" in str(ret) or ret is inspect.Parameter.empty


class TestLearningEventPublisherProtocol:
    """LearningEventPublisher — Publicación de eventos tipados del Learning BC."""

    def test_is_protocol(self) -> None:
        assert _is_protocol(LearningEventPublisher)

    def test_has_publish_feedback_captured(self) -> None:
        assert hasattr(LearningEventPublisher, "publish_feedback_captured")

    def test_has_publish_signal_aggregated(self) -> None:
        assert hasattr(LearningEventPublisher, "publish_signal_aggregated")

    def test_has_publish_score_adjusted(self) -> None:
        assert hasattr(LearningEventPublisher, "publish_score_adjusted")

    def test_has_publish_dataset_generated(self) -> None:
        assert hasattr(LearningEventPublisher, "publish_dataset_generated")

    def test_has_publish_learning_model_updated(self) -> None:
        assert hasattr(LearningEventPublisher, "publish_learning_model_updated")

    def test_all_methods_return_none(self) -> None:
        methods = [
            "publish_feedback_captured",
            "publish_signal_aggregated",
            "publish_score_adjusted",
            "publish_dataset_generated",
            "publish_learning_model_updated",
        ]
        for method_name in methods:
            method = getattr(LearningEventPublisher, method_name)
            sig = inspect.signature(method)
            assert _return_is_none(sig), (
                f"{method_name} should return None, got {sig.return_annotation}"
            )
