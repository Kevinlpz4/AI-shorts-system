"""
RegistryManager — unified entry point for all Runtime sub-registries.

Provides access to SourceRegistry, ProviderRegistry, StepRegistry,
and JobRegistry through a single facade.

Usage::

    from runtime.registry.registry_manager import RegistryManager

    manager = RegistryManager()
    manager.sources.register(source)
    manager.steps.register(step)
    manager.jobs.register(job)
"""
from __future__ import annotations

from runtime.registry.job_registry import JobRegistry
from runtime.registry.provider_registry import ProviderRegistry
from runtime.registry.source_registry import SourceRegistry
from runtime.registry.step_registry import StepRegistry


class RegistryManager:
    """Unified facade for all Runtime sub-registries.

    Creates and owns all four sub-registries. Provides both direct
    attribute access and accessor methods for convenience.
    """

    def __init__(self) -> None:
        self.sources = SourceRegistry()
        self.providers = ProviderRegistry()
        self.steps = StepRegistry()
        self.jobs = JobRegistry()

    def get_source_registry(self) -> SourceRegistry:
        """Return the SourceRegistry instance."""
        return self.sources

    def get_provider_registry(self) -> ProviderRegistry:
        """Return the ProviderRegistry instance."""
        return self.providers

    def get_step_registry(self) -> StepRegistry:
        """Return the StepRegistry instance."""
        return self.steps

    def get_job_registry(self) -> JobRegistry:
        """Return the JobRegistry instance."""
        return self.jobs
