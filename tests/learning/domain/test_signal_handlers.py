"""Tests for Signal Handlers — Open/Closed hierarchy."""
import pytest
from learning.domain.signals.handlers import (
    SignalHandler,
    KeywordSignalHandler,
    SourceSignalHandler,
    CategorySignalHandler,
    TopicSignalHandler,
    TimeSignalHandler,
)
from learning.domain.signals.registry import SignalRegistry
from learning.domain.value_objects.signal_type import SignalType
from learning.domain.value_objects.signal_strength import SignalStrength


class TestSignalHandlers:
    def test_all_implement_protocol(self):
        handlers = [
            KeywordSignalHandler(), SourceSignalHandler(),
            CategorySignalHandler(), TopicSignalHandler(), TimeSignalHandler(),
        ]
        for h in handlers:
            assert hasattr(h, "signal_type")
            assert hasattr(h, "compute")
            assert callable(h.compute)

    def test_keyword_handler(self):
        h = KeywordSignalHandler()
        assert h.signal_type == SignalType.KEYWORD
        s = h.compute({"approval_rate": 0.8, "sample_size": 20})
        assert isinstance(s, SignalStrength)
        assert 0.0 <= s.value <= 1.0

    def test_source_handler(self):
        h = SourceSignalHandler()
        assert h.signal_type == SignalType.SOURCE
        s = h.compute({"approval_rate": 0.9, "sample_size": 30})
        assert s.value > 0

    def test_category_handler(self):
        h = CategorySignalHandler()
        assert h.signal_type == SignalType.CATEGORY
        s = h.compute({"approval_rate": 0.7, "sample_size": 15})
        assert s.value > 0

    def test_topic_handler(self):
        h = TopicSignalHandler()
        assert h.signal_type == SignalType.TOPIC
        s = h.compute({"approval_rate": 0.6, "sample_size": 10})
        assert s.value > 0

    def test_time_handler(self):
        h = TimeSignalHandler()
        assert h.signal_type == SignalType.TIME
        s = h.compute({"approval_rate": 0.5, "sample_size": 25})
        assert s.value > 0
        assert s.decay_factor == 0.3

    def test_zero_sample_gives_zero_strength(self):
        h = KeywordSignalHandler()
        s = h.compute({"approval_rate": 0.8, "sample_size": 0})
        assert s.value == 0.0

    def test_high_sample_high_strength(self):
        h = KeywordSignalHandler()
        s = h.compute({"approval_rate": 1.0, "sample_size": 100})
        assert s.value == pytest.approx(1.0, abs=0.01)


class TestSignalRegistry:
    def test_all_built_in_handlers_registered(self):
        reg = SignalRegistry()
        assert len(reg) == 5

    def test_get_handler(self):
        reg = SignalRegistry()
        h = reg.get_handler(SignalType.KEYWORD)
        assert isinstance(h, KeywordSignalHandler)

    def test_has_handler(self):
        reg = SignalRegistry()
        assert reg.has_handler(SignalType.KEYWORD)
        assert not reg.has_handler("NONEXISTENT")  # type: ignore[arg-type]

    def test_register_custom_handler(self):
        """Open/Closed: adding a new handler doesn't modify existing code."""
        class CustomHandler:
            @property
            def signal_type(self):
                return "CUSTOM"  # type: ignore[return-value]

            def compute(self, data):
                return SignalStrength(value=0.5, decay_factor=0.0)

        reg = SignalRegistry()
        reg.register(CustomHandler())  # type: ignore[arg-type]
        assert len(reg) == 6

    def test_registered_types(self):
        reg = SignalRegistry()
        types = reg.registered_types
        assert SignalType.KEYWORD in types
        assert SignalType.SOURCE in types

    def test_get_handler_raises_for_unknown(self):
        from unittest.mock import MagicMock
        reg = SignalRegistry()
        fake_type = MagicMock(spec=SignalType)
        fake_type.value = "NONEXISTENT"
        with pytest.raises(KeyError, match="No handler registered"):
            reg.get_handler(fake_type)

    def test_contains(self):
        reg = SignalRegistry()
        assert SignalType.KEYWORD in reg
