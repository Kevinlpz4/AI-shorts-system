"""
Tests for rejection reasons catalog.
"""
from __future__ import annotations

import pytest

from runtime.feedback.reasons import FeedbackReasons, RejectionReason


class TestRejectionReason:
    """Tests for RejectionReason dataclass."""

    def test_creation(self):
        reason = RejectionReason(
            code="test",
            label="Test Reason",
            description="A test reason",
        )
        assert reason.code == "test"
        assert reason.label == "Test Reason"
        assert reason.description == "A test reason"
        assert reason.is_default is False

    def test_immutability(self):
        reason = RejectionReason(
            code="test",
            label="Test",
            description="Desc",
        )
        with pytest.raises(AttributeError):
            reason.code = "changed"


class TestFeedbackReasons:
    """Tests for FeedbackReasons catalog."""

    def test_default_reasons_loaded(self):
        reasons = FeedbackReasons()
        all_reasons = reasons.list_all()
        assert len(all_reasons) == 10  # 10 default reasons

    def test_get_existing_reason(self):
        reasons = FeedbackReasons()
        result = reasons.get("low_relevance")
        assert result.is_success
        assert result.value.code == "low_relevance"
        assert result.value.label == "Poco relevante"

    def test_get_nonexistent_reason(self):
        reasons = FeedbackReasons()
        result = reasons.get("nonexistent")
        assert result.is_failure
        assert "Unknown" in result.error.message

    def test_add_custom_reason(self):
        reasons = FeedbackReasons()
        custom = RejectionReason(
            code="custom",
            label="Custom Reason",
            description="A custom reason",
        )
        result = reasons.add(custom)
        assert result.is_success
        # Verify it was added
        get_result = reasons.get("custom")
        assert get_result.is_success
        assert get_result.value.label == "Custom Reason"

    def test_add_overrides_default(self):
        reasons = FeedbackReasons()
        custom = RejectionReason(
            code="clickbait",
            label="Engañoso",
            description="El título es engañoso (custom)",
        )
        reasons.add(custom)
        result = reasons.get("clickbait")
        assert result.is_success
        assert result.value.label == "Engañoso"

    def test_custom_reasons_in_constructor(self):
        custom = {
            "my_reason": RejectionReason(
                code="my_reason",
                label="My Reason",
                description="Custom in constructor",
            )
        }
        reasons = FeedbackReasons(custom_reasons=custom)
        result = reasons.get("my_reason")
        assert result.is_success
        assert len(reasons.list_all()) == 11  # 10 defaults + 1 custom

    def test_validate_valid_reason(self):
        reasons = FeedbackReasons()
        result = reasons.validate("low_relevance")
        assert result.is_success

    def test_validate_invalid_reason(self):
        reasons = FeedbackReasons()
        result = reasons.validate("nonexistent")
        assert result.is_failure

    def test_validate_other_requires_comment(self):
        reasons = FeedbackReasons()
        result = reasons.validate("other", comment=None)
        assert result.is_failure
        assert "comment" in result.error.message.lower()

    def test_validate_other_with_comment(self):
        reasons = FeedbackReasons()
        result = reasons.validate("other", comment="Some reason")
        assert result.is_success

    def test_default_reason_has_is_default(self):
        reasons = FeedbackReasons()
        very_relevant = reasons.get("very_relevant")
        assert very_relevant.value.is_default is True

    def test_list_all_contains_all_codes(self):
        reasons = FeedbackReasons()
        all_reasons = reasons.list_all()
        codes = {r.code for r in all_reasons}
        expected = {
            "very_relevant", "low_relevance", "duplicate",
            "unreliable_source", "clickbait", "low_quality",
            "too_local", "not_channel_fit", "incomplete", "other",
        }
        assert codes == expected
