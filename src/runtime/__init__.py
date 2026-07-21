"""Runtime — thin orchestration layer for EPIC 8.0.

Runtime is NOT a Bounded Context. It's a coordination layer that wires
the four frozen BCs (Foundation, Ingestion, Research, Learning) together
through registries, pipelines, jobs, and an event bridge.

Architecture:
    - contracts/     — data definitions (SourceDefinition, ProviderResult, etc.)
    - config.py      — RuntimeConfig frozen dataclass
    - errors.py      — RuntimeErrorCode + RuntimeError
    - persistence/   — SQLAlchemy models + engine factory
    - registry/      — Source, Provider, Step, Job registries + RegistryManager
    - event_bridge.py — IntegrationEvent routing + decorator publisher
    - pipelines/     — PipelineStep Protocol
    - jobs/          — Job Protocol

Usage::

    from runtime.config import RuntimeConfig
    from runtime.registry.registry_manager import RegistryManager

    config = RuntimeConfig(...)
    manager = RegistryManager()
"""
from __future__ import annotations
