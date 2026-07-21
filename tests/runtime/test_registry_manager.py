"""
Tests for RegistryManager — unified entry point for all sub-registries.

Covers:
- Construction with all sub-registries
- Accessor methods
- Sub-registries are independent
"""
from __future__ import annotations

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
        from runtime.registry.job_registry import JobRegistry

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
