"""
Runtime registry package — sub-registries for sources, providers, steps, and jobs.

Usage::

    from runtime.registry.registry_manager import RegistryManager

    manager = RegistryManager()
    manager.sources.register(source)
    manager.steps.register(step)
"""
from __future__ import annotations
