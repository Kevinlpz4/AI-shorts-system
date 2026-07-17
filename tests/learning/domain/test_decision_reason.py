"""Tests for DecisionReason Value Object."""
from learning.domain.value_objects.decision_reason import DecisionReason


class TestDecisionReason:
    def test_all_values_exist(self):
        expected = {
            "LOW_QUALITY", "DUPLICATE", "CLICKBAIT",
            "NOT_RELEVANT", "OUTDATED", "LOCAL_ONLY", "OTHER",
        }
        assert {r.value for r in DecisionReason} == expected

    def test_str_enum_behavior(self):
        assert DecisionReason.LOW_QUALITY == "LOW_QUALITY"
        assert DecisionReason.CLICKBAIT.value == "CLICKBAIT"

    def test_all_reasons_are_strings(self):
        for reason in DecisionReason:
            assert isinstance(reason, str)
            assert isinstance(reason.value, str)

    def test_no_free_strings_allowed(self):
        """DecisionReason enforces normalized reasons — no free text."""
        for reason in DecisionReason:
            assert reason.value.isupper()
            assert "_" in reason.value or reason.value.isalpha()
