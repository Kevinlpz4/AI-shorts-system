"""Tests for ErrorMapper — domain → application error conversion."""

from __future__ import annotations

from enum import Enum

from foundation.errors.base import DomainError
from foundation.result.result import Error, ErrorCode

from learning.application.errors import ErrorMapper
from learning.application.exceptions.error_code import ApplicationErrorCode
from learning.domain.exceptions.errors import LearningErrorCode


# ── Helpers ──


class _DomainErrorWithCode(DomainError):
    """Dynamic domain error stub — code is set via __init_subclass__."""

    code = "DEFAULT"


def _make_domain_error(code: str, message: str = "test error", detail: str = "") -> DomainError:
    """Create a DomainError with a specific code for testing."""
    # Create a new class with the specific code
    klass = type(
        f"DomainError_{code}",
        (_DomainErrorWithCode,),
        {"code": code},
    )
    return klass(message=message, detail=detail)


class TestErrorMapperMapDomainError:
    """Tests for ErrorMapper.map_domain_error() with all LearningErrorCode values."""

    def test_maps_feedback_not_found(self) -> None:
        error = _make_domain_error(LearningErrorCode.FEEDBACK_NOT_FOUND.value)
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.RESOURCE_NOT_FOUND
        assert result.message == "test error"

    def test_maps_duplicate_feedback(self) -> None:
        error = _make_domain_error(LearningErrorCode.DUPLICATE_FEEDBACK.value)
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID

    def test_maps_signal_not_found(self) -> None:
        error = _make_domain_error(LearningErrorCode.SIGNAL_NOT_FOUND.value)
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.RESOURCE_NOT_FOUND

    def test_maps_signal_already_finalized(self) -> None:
        error = _make_domain_error(LearningErrorCode.SIGNAL_ALREADY_FINALIZED.value)
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID

    def test_maps_source_quality_not_found(self) -> None:
        error = _make_domain_error(LearningErrorCode.SOURCE_QUALITY_NOT_FOUND.value)
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.RESOURCE_NOT_FOUND

    def test_maps_model_not_found(self) -> None:
        error = _make_domain_error(LearningErrorCode.MODEL_NOT_FOUND.value)
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.RESOURCE_NOT_FOUND

    def test_maps_invalid_decision_type(self) -> None:
        error = _make_domain_error(LearningErrorCode.INVALID_DECISION_TYPE.value)
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID

    def test_maps_invalid_confidence(self) -> None:
        error = _make_domain_error(LearningErrorCode.INVALID_CONFIDENCE.value)
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID

    def test_maps_invalid_weights(self) -> None:
        error = _make_domain_error(LearningErrorCode.INVALID_WEIGHTS.value)
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID

    def test_maps_window_invalid(self) -> None:
        error = _make_domain_error(LearningErrorCode.WINDOW_INVALID.value)
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID

    def test_maps_insufficient_data(self) -> None:
        error = _make_domain_error(LearningErrorCode.INSUFFICIENT_DATA.value)
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.OPERATION_FAILED

    def test_maps_unknown_code_to_operation_failed(self) -> None:
        """Unknown error codes fall back to OPERATION_FAILED."""
        error = _make_domain_error("COMPLETELY_UNKNOWN_CODE")
        result = ErrorMapper.map_domain_error(error)
        assert result.code == ApplicationErrorCode.OPERATION_FAILED
        assert result.message == "test error"

    def test_preserves_message_and_detail(self) -> None:
        error = _make_domain_error(
            LearningErrorCode.FEEDBACK_NOT_FOUND.value,
            message="Feedback not found",
            detail="No feedback with id=fb-1",
        )
        result = ErrorMapper.map_domain_error(error)
        assert result.message == "Feedback not found"
        assert result.detail == "No feedback with id=fb-1"


class TestErrorMapperMapResultError:
    """Tests for ErrorMapper.map_result_error() mapping Result errors."""

    def test_preserves_already_mapped_application_error_code(self) -> None:
        """If the Error already has an ApplicationErrorCode, return as-is."""
        error = Error(code=ApplicationErrorCode.COMMAND_INVALID, message="test")
        result = ErrorMapper.map_result_error(error)
        assert result is error  # same object identity

    def test_maps_learning_error_code_feedback_not_found(self) -> None:
        """LearningErrorCode.FEEDBACK_NOT_FOUND → RESOURCE_NOT_FOUND."""
        error = Error(
            code=LearningErrorCode.FEEDBACK_NOT_FOUND,
            message="Feedback missing",
        )
        result = ErrorMapper.map_result_error(error)
        assert result.code == ApplicationErrorCode.RESOURCE_NOT_FOUND
        assert result.message == "Feedback missing"

    def test_maps_learning_error_code_duplicate_feedback(self) -> None:
        error = Error(
            code=LearningErrorCode.DUPLICATE_FEEDBACK,
            message="Duplicate",
        )
        result = ErrorMapper.map_result_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID

    def test_maps_learning_error_code_signal_not_found(self) -> None:
        error = Error(
            code=LearningErrorCode.SIGNAL_NOT_FOUND,
            message="Signal missing",
        )
        result = ErrorMapper.map_result_error(error)
        assert result.code == ApplicationErrorCode.RESOURCE_NOT_FOUND

    def test_maps_learning_error_code_signal_already_finalized(self) -> None:
        error = Error(
            code=LearningErrorCode.SIGNAL_ALREADY_FINALIZED,
            message="Already finalized",
        )
        result = ErrorMapper.map_result_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID

    def test_maps_learning_error_code_source_quality_not_found(self) -> None:
        error = Error(
            code=LearningErrorCode.SOURCE_QUALITY_NOT_FOUND,
            message="Source quality missing",
        )
        result = ErrorMapper.map_result_error(error)
        assert result.code == ApplicationErrorCode.RESOURCE_NOT_FOUND

    def test_maps_learning_error_code_model_not_found(self) -> None:
        error = Error(
            code=LearningErrorCode.MODEL_NOT_FOUND,
            message="Model missing",
        )
        result = ErrorMapper.map_result_error(error)
        assert result.code == ApplicationErrorCode.RESOURCE_NOT_FOUND

    def test_maps_learning_error_code_invalid_decision_type(self) -> None:
        error = Error(
            code=LearningErrorCode.INVALID_DECISION_TYPE,
            message="Bad decision",
        )
        result = ErrorMapper.map_result_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID

    def test_maps_learning_error_code_invalid_confidence(self) -> None:
        error = Error(
            code=LearningErrorCode.INVALID_CONFIDENCE,
            message="Bad confidence",
        )
        result = ErrorMapper.map_result_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID

    def test_maps_learning_error_code_invalid_weights(self) -> None:
        error = Error(
            code=LearningErrorCode.INVALID_WEIGHTS,
            message="Bad weights",
        )
        result = ErrorMapper.map_domain_error(error)  # using map_domain_error for domain codes
        assert result.code == ApplicationErrorCode.COMMAND_INVALID

    def test_maps_learning_error_code_window_invalid(self) -> None:
        error = Error(
            code=LearningErrorCode.WINDOW_INVALID,
            message="Bad window",
        )
        result = ErrorMapper.map_result_error(error)
        assert result.code == ApplicationErrorCode.COMMAND_INVALID

    def test_maps_learning_error_code_insufficient_data(self) -> None:
        error = Error(
            code=LearningErrorCode.INSUFFICIENT_DATA,
            message="Not enough data",
        )
        result = ErrorMapper.map_result_error(error)
        assert result.code == ApplicationErrorCode.OPERATION_FAILED

    def test_maps_foundation_unknown_to_operation_failed(self) -> None:
        """Foundation ErrorCode.UNKNOWN maps to OPERATION_FAILED."""
        error = Error(code=ErrorCode.UNKNOWN, message="Unknown error")
        result = ErrorMapper.map_result_error(error)
        assert result.code == ApplicationErrorCode.OPERATION_FAILED

    def test_maps_unknown_string_code_to_operation_failed(self) -> None:
        """Unknown string code falls back to OPERATION_FAILED."""

        class _CustomCode(str, Enum):
            CUSTOM = "CUSTOM_THING"

        error = Error(code=_CustomCode.CUSTOM, message="Custom error")
        result = ErrorMapper.map_result_error(error)
        assert result.code == ApplicationErrorCode.OPERATION_FAILED

    def test_preserves_message_and_detail(self) -> None:
        error = Error(
            code=LearningErrorCode.FEEDBACK_NOT_FOUND,
            message="Feedback missing",
            detail="No feedback with id=fb-1",
        )
        result = ErrorMapper.map_result_error(error)
        assert result.message == "Feedback missing"
        assert result.detail == "No feedback with id=fb-1"
