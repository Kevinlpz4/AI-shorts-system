"""Tests for ApplicationErrorCode enum."""

from __future__ import annotations

from enum import Enum

from ingestion.application.exceptions import ApplicationErrorCode


class TestApplicationErrorCode:
    """Verifies all error codes are defined and correct."""

    def test_all_codes_defined(self) -> None:
        expected_codes = {
            "COMMAND_INVALID",
            "COMMAND_MISSING_FIELD",
            "RESOURCE_NOT_FOUND",
            "OPERATION_FAILED",
            "TRANSACTION_FAILED",
            "CONCURRENCY_CONFLICT",
        }
        actual_codes = {code.value for code in ApplicationErrorCode}
        assert actual_codes == expected_codes

    def test_str_enum_values(self) -> None:
        """Each code must equal its own value (str, Enum pattern)."""
        assert ApplicationErrorCode.COMMAND_INVALID == "COMMAND_INVALID"
        assert ApplicationErrorCode.COMMAND_MISSING_FIELD == "COMMAND_MISSING_FIELD"
        assert ApplicationErrorCode.RESOURCE_NOT_FOUND == "RESOURCE_NOT_FOUND"
        assert ApplicationErrorCode.OPERATION_FAILED == "OPERATION_FAILED"
        assert ApplicationErrorCode.TRANSACTION_FAILED == "TRANSACTION_FAILED"
        assert ApplicationErrorCode.CONCURRENCY_CONFLICT == "CONCURRENCY_CONFLICT"

    def test_members_count(self) -> None:
        """Prevent accidental addition/removal without updating tests."""
        assert len(ApplicationErrorCode) == 6

    def test_is_str_enum(self) -> None:
        """Must inherit from str for serialization compatibility."""
        assert issubclass(ApplicationErrorCode, str)
        assert issubclass(ApplicationErrorCode, Enum)

    def test_all_codes_are_unique(self) -> None:
        """No duplicate values allowed in Enum."""
        values = [code.value for code in ApplicationErrorCode]
        assert len(values) == len(set(values))
