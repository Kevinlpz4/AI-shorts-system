"""Tests for Application Error hierarchy.

Verifies:
    - Inheritance chain (ApplicationError → FoundationError → Exception)
    - Code values
    - Raise/catch behavior
    - Message and detail propagation
"""

from __future__ import annotations

from foundation.errors import ApplicationError as FoundationApplicationError
from foundation.errors import FoundationError
from ingestion.application.exceptions import (
    CommandValidationError,
    ResourceNotFoundError,
)


class TestCommandValidationError:
    """Verifies CommandValidationError behavior."""

    def test_inherits_from_application_error(self) -> None:
        """Must inherit from foundation's ApplicationError."""
        assert issubclass(CommandValidationError, FoundationApplicationError)
        assert issubclass(CommandValidationError, FoundationError)
        assert issubclass(CommandValidationError, Exception)

    def test_code_value(self) -> None:
        """Code must be a non-empty string."""
        assert CommandValidationError.code == "COMMAND_VALIDATION_ERROR"
        assert isinstance(CommandValidationError.code, str)
        assert len(CommandValidationError.code) > 0

    def test_default_construction(self) -> None:
        """Default construction with no args should not fail."""
        error = CommandValidationError()
        assert error.message == ""
        assert error.detail == ""

    def test_message_propagation(self) -> None:
        """Message should be accessible via .message attribute."""
        error = CommandValidationError("Field 'source_id' is required")
        assert error.message == "Field 'source_id' is required"

    def test_detail_propagation(self) -> None:
        """Detail should be accessible via .detail attribute."""
        error = CommandValidationError(
            "Invalid command",
            detail="expected UUID, got 'abc'",
        )
        assert error.message == "Invalid command"
        assert error.detail == "expected UUID, got 'abc'"

    def test_can_be_raised_and_caught_as_application_error(self) -> None:
        """Must be catchable as FoundationApplicationError."""
        try:
            raise CommandValidationError("test error")
        except FoundationApplicationError as e:
            assert isinstance(e, CommandValidationError)
            assert e.message == "test error"
        else:
            pytest.fail("Expected CommandValidationError was not raised")

    def test_can_be_raised_and_caught_as_foundation_error(self) -> None:
        """Must be catchable as FoundationError (generic)."""
        try:
            raise CommandValidationError("test")
        except FoundationError as e:
            assert isinstance(e, CommandValidationError)
        else:
            pytest.fail("Expected CommandValidationError was not raised")


class TestResourceNotFoundError:
    """Verifies ResourceNotFoundError behavior."""

    def test_inherits_from_application_error(self) -> None:
        """Must inherit from foundation's ApplicationError."""
        assert issubclass(ResourceNotFoundError, FoundationApplicationError)
        assert issubclass(ResourceNotFoundError, FoundationError)
        assert issubclass(ResourceNotFoundError, Exception)

    def test_code_value(self) -> None:
        """Code must be the correct string value."""
        assert ResourceNotFoundError.code == "RESOURCE_NOT_FOUND_ERROR"
        assert isinstance(ResourceNotFoundError.code, str)

    def test_default_construction(self) -> None:
        error = ResourceNotFoundError()
        assert error.message == ""
        assert error.detail == ""

    def test_message_propagation(self) -> None:
        error = ResourceNotFoundError("Source not found")
        assert error.message == "Source not found"

    def test_detail_propagation(self) -> None:
        error = ResourceNotFoundError(
            "Feed not found",
            detail="feed_id=abc-123 does not exist",
        )
        assert error.message == "Feed not found"
        assert error.detail == "feed_id=abc-123 does not exist"

    def test_can_be_raised_and_caught_as_application_error(self) -> None:
        try:
            raise ResourceNotFoundError("not found")
        except FoundationApplicationError as e:
            assert isinstance(e, ResourceNotFoundError)
        else:
            pytest.fail("Expected ResourceNotFoundError was not raised")


class TestApplicationErrorSeparation:
    """Verifies application errors are separate from domain errors."""

    def test_not_domain_error(self) -> None:
        """Application errors must NOT be domain errors."""
        from foundation.errors import DomainError

        assert not issubclass(CommandValidationError, DomainError)
        assert not issubclass(ResourceNotFoundError, DomainError)

    def test_not_infrastructure_error(self) -> None:
        """Application errors must NOT be infrastructure errors."""
        from foundation.errors import InfrastructureError

        assert not issubclass(CommandValidationError, InfrastructureError)
        assert not issubclass(ResourceNotFoundError, InfrastructureError)

    def test_application_error_code_is_classvar(self) -> None:
        """code must be a ClassVar that doesn't appear in __dict__ of instances."""
        error = CommandValidationError()
        assert "code" not in error.__dict__

    def test_to_dict_includes_code(self) -> None:
        """to_dict() must include the error code."""
        error = CommandValidationError("validation failed")
        d = error.to_dict()
        assert d["error"] == "COMMAND_VALIDATION_ERROR"
        assert d["message"] == "validation failed"

    def test_to_error_preserves_code_in_message(self) -> None:
        """to_error() must prefix the exception code in brackets."""
        from foundation.result import ErrorCode

        error = ResourceNotFoundError("resource missing")
        result_error = error.to_error()
        assert result_error.code == ErrorCode.UNKNOWN  # type difference
        assert "[RESOURCE_NOT_FOUND_ERROR]" in result_error.message


import pytest  # noqa: E402 (needed for pytest.fail above)
