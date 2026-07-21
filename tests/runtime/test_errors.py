"""
Tests for RuntimeError — error codes, messages, construction.

Covers:
- RuntimeErrorCode enum values
- RuntimeError construction
- RuntimeError message formatting
"""
from __future__ import annotations

import pytest

from runtime.errors import RuntimeErrorCode, RuntimeError as RuntimeBaseError


class TestRuntimeErrorCode:
    """Tests for RuntimeErrorCode enum."""

    def test_all_codes_are_strings(self) -> None:
        """All RuntimeErrorCode members have string values."""
        for code in RuntimeErrorCode:
            assert isinstance(code.value, str)

    def test_expected_codes_exist(self) -> None:
        """Expected error codes are defined."""
        expected = {
            "SOURCE_FETCH_FAILED",
            "PROVIDER_NOT_FOUND",
            "STEP_EXECUTION_FAILED",
            "JOB_EXECUTION_FAILED",
            "CONFIGURATION_ERROR",
            "PIPELINE_FAILED",
            "ADAPTER_NOT_FOUND",
            "REGISTRY_ERROR",
        }
        actual = {code.value for code in RuntimeErrorCode}
        assert expected == actual


class TestRuntimeError:
    """Tests for RuntimeError."""

    def test_construction(self) -> None:
        """RuntimeError accepts code and message."""
        error = RuntimeBaseError(
            code=RuntimeErrorCode.SOURCE_FETCH_FAILED,
            message="Failed to fetch from RSS source",
        )

        assert error.code == RuntimeErrorCode.SOURCE_FETCH_FAILED
        assert error.message == "Failed to fetch from RSS source"
        assert error.detail is None

    def test_construction_with_detail(self) -> None:
        """RuntimeError accepts optional detail."""
        error = RuntimeBaseError(
            code=RuntimeErrorCode.STEP_EXECUTION_FAILED,
            message="Step 'fetch' failed",
            detail="Connection timeout after 30s",
        )

        assert error.detail == "Connection timeout after 30s"

    def test_str_without_detail(self) -> None:
        """str(error) formats as [CODE] message."""
        error = RuntimeBaseError(
            code=RuntimeErrorCode.CONFIGURATION_ERROR,
            message="Invalid database URL",
        )

        assert str(error) == "[CONFIGURATION_ERROR] Invalid database URL"

    def test_str_with_detail(self) -> None:
        """str(error) formats as [CODE] message: detail."""
        error = RuntimeBaseError(
            code=RuntimeErrorCode.CONFIGURATION_ERROR,
            message="Invalid database URL",
            detail="missing port",
        )

        assert str(error) == "[CONFIGURATION_ERROR] Invalid database URL: missing port"

    def test_is_exception(self) -> None:
        """RuntimeError is a subclass of Exception."""
        error = RuntimeBaseError(
            code=RuntimeErrorCode.JOB_EXECUTION_FAILED,
            message="job failed",
        )

        assert isinstance(error, Exception)

    def test_can_be_raised_and_caught(self) -> None:
        """RuntimeError can be raised and caught."""
        with pytest.raises(RuntimeBaseError) as exc_info:
            raise RuntimeBaseError(
                code=RuntimeErrorCode.PIPELINE_FAILED,
                message="Pipeline crashed",
            )

        assert exc_info.value.code == RuntimeErrorCode.PIPELINE_FAILED
