"""
Tests for StepRegistry — register, get, get_ordered_steps.

Covers:
- Register and get steps
- Get ordered steps (by order field)
- List names
- Get missing step returns None
- Register overwrites
"""
from __future__ import annotations


from runtime.registry.step_registry import StepRegistry


class FakeStep:
    """Minimal fake step that satisfies PipelineStep protocol."""

    def __init__(self, name: str, order: int, is_fatal: bool = False) -> None:
        self.name = name
        self.order = order
        self.is_fatal = is_fatal


class TestStepRegistry:
    """Tests for StepRegistry."""

    def test_empty_registry(self) -> None:
        """New registry has no steps."""
        registry = StepRegistry()

        assert registry.get_ordered_steps() == []
        assert registry.list_names() == []
        assert registry.get("missing") is None

    def test_register_and_get(self) -> None:
        """Register a step and retrieve by name."""
        registry = StepRegistry()
        step = FakeStep("fetch", order=1)

        registry.register(step)

        assert registry.get("fetch") is step

    def test_get_missing_returns_none(self) -> None:
        """Getting a nonexistent step returns None."""
        registry = StepRegistry()

        assert registry.get("nonexistent") is None

    def test_get_ordered_steps(self) -> None:
        """get_ordered_steps returns steps sorted by order field."""
        registry = StepRegistry()
        step3 = FakeStep("store", order=3)
        step1 = FakeStep("fetch", order=1)
        step2 = FakeStep("transform", order=2)

        registry.register(step3)
        registry.register(step1)
        registry.register(step2)

        ordered = registry.get_ordered_steps()
        assert [s.name for s in ordered] == ["fetch", "transform", "store"]

    def test_get_ordered_steps_same_order(self) -> None:
        """Steps with same order maintain insertion order."""
        registry = StepRegistry()
        step_a = FakeStep("a", order=1)
        step_b = FakeStep("b", order=1)

        registry.register(step_a)
        registry.register(step_b)

        ordered = registry.get_ordered_steps()
        assert [s.name for s in ordered] == ["a", "b"]

    def test_list_names(self) -> None:
        """list_names returns all step names."""
        registry = StepRegistry()
        registry.register(FakeStep("fetch", order=1))
        registry.register(FakeStep("transform", order=2))

        names = registry.list_names()
        assert set(names) == {"fetch", "transform"}

    def test_register_overwrites(self) -> None:
        """Registering same name overwrites previous step."""
        registry = StepRegistry()
        original = FakeStep("fetch", order=1)
        replacement = FakeStep("fetch", order=2)

        registry.register(original)
        registry.register(replacement)

        assert registry.get("fetch") is replacement
        assert registry.get("fetch").order == 2
