"""
Tests for RegistryManager — unified entry point for all sub-registries.

Covers:
- Construction with all sub-registries
- Accessor methods
- Sub-registries are independent
- Dynamic registration (Open/Closed)
"""
from __future__ import annotations

import pytest

from runtime.registry.registry_manager import RegistryManager


class TestRegistryManager:
    """Tests for RegistryManager."""

    def test_construction(self) -> None:
        """RegistryManager creates all sub-registries on construction."""
        manager = RegistryManager()

        assert manager.sources is not None
        assert manager.providers is not None
        assert manager.steps is not None
        assert manager.jobs is not None

    def test_get_source_registry(self) -> None:
        """get_source_registry returns the SourceRegistry instance."""
        manager = RegistryManager()

        registry = manager.get_source_registry()
        assert registry is manager.sources

    def test_get_provider_registry(self) -> None:
        """get_provider_registry returns the ProviderRegistry instance."""
        manager = RegistryManager()

        registry = manager.get_provider_registry()
        assert registry is manager.providers

    def test_get_step_registry(self) -> None:
        """get_step_registry returns the StepRegistry instance."""
        manager = RegistryManager()

        registry = manager.get_step_registry()
        assert registry is manager.steps

    def test_get_job_registry(self) -> None:
        """get_job_registry returns the JobRegistry instance."""
        manager = RegistryManager()

        registry = manager.get_job_registry()
        assert registry is manager.jobs

    def test_sub_registries_are_independent(self) -> None:
        """Each sub-registry operates independently."""
        from runtime.contracts.source_definition import SourceDefinition

        manager = RegistryManager()

        manager.sources.register(
            SourceDefinition(id="s1", provider="rss", technology="rss")
        )

        class FakeJob:
            name = "test"

        manager.jobs.register(FakeJob())

        assert len(manager.sources.get_all()) == 1
        assert len(manager.jobs.get_all()) == 1
        assert manager.providers.get_all() == []
        assert manager.steps.get_ordered_steps() == []

    def test_shared_state(self) -> None:
        """Direct attribute access and accessor return same instance."""
        manager = RegistryManager()

        assert manager.sources is manager.get_source_registry()
        assert manager.providers is manager.get_provider_registry()
        assert manager.steps is manager.get_step_registry()
        assert manager.jobs is manager.get_job_registry()


class TestDynamicRegistry:
    """Tests for dynamic registry registration (Open/Closed)."""

    def test_register_and_get_dynamic_registry(self) -> None:
        """register_registry adds a custom registry retrievable by name."""
        manager = RegistryManager()

        class FakeMetricsRegistry:
            pass

        fake = FakeMetricsRegistry()
        manager.register_registry("metrics", fake)

        assert manager.get_registry("metrics") is fake

    def test_get_dynamic_registry_returns_none_for_missing(self) -> None:
        """get_registry returns None for unregistered names."""
        manager = RegistryManager()

        assert manager.get_registry("nonexistent") is None

    def test_core_registries_accessible_via_get_registry(self) -> None:
        """get_registry works for all four core registries."""
        manager = RegistryManager()

        assert manager.get_registry("sources") is manager.sources
        assert manager.get_registry("providers") is manager.providers
        assert manager.get_registry("steps") is manager.steps
        assert manager.get_registry("jobs") is manager.jobs

    def test_cannot_override_core_registry(self) -> None:
        """register_registry raises ValueError for core names."""
        manager = RegistryManager()

        with pytest.raises(ValueError, match="Cannot override core registry"):
            manager.register_registry("sources", object())

        with pytest.raises(ValueError, match="Cannot override core registry"):
            manager.register_registry("steps", object())

    def test_list_registries_includes_dynamic(self) -> None:
        """list_registries returns both core and dynamic names."""
        manager = RegistryManager()
        manager.register_registry("metrics", object())
        manager.register_registry("cache", object())

        names = manager.list_registries()
        assert "sources" in names
        assert "providers" in names
        assert "steps" in names
        assert "jobs" in names
        assert "metrics" in names
        assert "cache" in names

    def test_dynamic_registries_are_independent(self) -> None:
        """Dynamic registries don't affect core or each other."""
        manager = RegistryManager()

        class RegistryA:
            pass

        class RegistryB:
            pass

        a = RegistryA()
        b = RegistryB()
        manager.register_registry("a", a)
        manager.register_registry("b", b)

        assert manager.get_registry("a") is a
        assert manager.get_registry("b") is b
        assert manager.get_registry("a") is not b
        assert len(manager.list_registries()) == 6  # 4 core + 2 dynamic
