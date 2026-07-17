"""Tests for SignalType Value Object."""
from learning.domain.value_objects.signal_type import SignalType


class TestSignalType:
    def test_all_values_exist(self):
        expected = {"KEYWORD", "SOURCE", "CATEGORY", "TOPIC", "TIME"}
        assert {s.value for s in SignalType} == expected

    def test_str_enum_behavior(self):
        assert SignalType.KEYWORD == "KEYWORD"
        assert SignalType.SOURCE.value == "SOURCE"

    def test_five_signal_types(self):
        assert len(SignalType) == 5
