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

    Also supports dynamic registration of additional registries via
    ``register_registry()`` and ``get_registry()`` for extensibility
    without modifying the class.
    """

    def __init__(self) -> None:
        self.sources = SourceRegistry()
        self.providers = ProviderRegistry()
        self.steps = StepRegistry()
        self.jobs = JobRegistry()
        self._dynamic_registries: dict[str, object] = {}

    def register_registry(self, name: str, registry: object) -> None:
        """Register a custom sub-registry dynamically.

        This enables the Open/Closed Principle — new registries can be
        added without modifying this class. For the four core registries,
        prefer direct attribute access (``manager.sources``, etc.).

        Args:
            name: Unique name for this registry (e.g., ``"metrics"``).
            registry: The registry instance to store.

        Raises:
            ValueError: If ``name`` collides with a core attribute
                (``sources``, ``providers``, ``steps``, ``jobs``).
        """
        core_names = {"sources", "providers", "steps", "jobs"}
        if name in core_names:
            raise ValueError(
                f"Cannot override core registry '{name}'. "
                f"Core registries: {sorted(core_names)}"
            )
        self._dynamic_registries[name] = registry

    def get_registry(self, name: str) -> object | None:
        """Retrieve any registry by name — core or dynamic.

        First checks the four core registries, then falls back to
        dynamically registered ones.

        Args:
            name: Registry name to look up.

        Returns:
            The registry instance, or None if not found.
        """
        if name == "sources":
            return self.sources
        if name == "providers":
            return self.providers
        if name == "steps":
            return self.steps
        if name == "jobs":
            return self.jobs
        return self._dynamic_registries.get(name)

    def list_registries(self) -> list[str]:
        """Return all registered registry names (core + dynamic)."""
        return ["sources", "providers", "steps", "jobs"] + list(
            self._dynamic_registries.keys()
        )

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
