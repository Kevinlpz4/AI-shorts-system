"""Tests for DecisionType Value Object."""
from learning.domain.value_objects.decision_type import DecisionType


class TestDecisionType:
    def test_all_values_exist(self):
        expected = {"APPROVED", "REJECTED", "AUTO_APPROVED", "AUTO_REJECTED", "OVERRIDDEN"}
        assert {d.value for d in DecisionType} == expected

    def test_is_rejection(self):
        assert DecisionType.REJECTED.is_rejection
        assert DecisionType.AUTO_REJECTED.is_rejection
        assert not DecisionType.APPROVED.is_rejection
        assert not DecisionType.AUTO_APPROVED.is_rejection
        assert not DecisionType.OVERRIDDEN.is_rejection

    def test_is_approval(self):
        assert DecisionType.APPROVED.is_approval
        assert DecisionType.AUTO_APPROVED.is_approval
        assert not DecisionType.REJECTED.is_approval
        assert not DecisionType.AUTO_REJECTED.is_approval

    def test_is_auto(self):
        assert DecisionType.AUTO_APPROVED.is_auto
        assert DecisionType.AUTO_REJECTED.is_auto
        assert not DecisionType.APPROVED.is_auto
        assert not DecisionType.REJECTED.is_auto
        assert not DecisionType.OVERRIDDEN.is_auto

    def test_str_enum_behavior(self):
        assert DecisionType.APPROVED == "APPROVED"
        assert DecisionType.REJECTED.value == "REJECTED"

    def test_immutability(self):
        import pytest
        with pytest.raises(AttributeError):
            DecisionType.APPROVED.value = "X"  # type: ignore[misc]
