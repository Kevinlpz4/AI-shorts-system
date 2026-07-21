"""
Runtime configuration — frozen dataclass for all Runtime settings.

Usage::

    from runtime.config import RuntimeConfig
    from runtime.contracts.source_definition import SourceDefinition

    config = RuntimeConfig(
        sources=[
            SourceDefinition(id="s1", provider="rss", technology="rss"),
        ],
        log_level="DEBUG",
    )
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from runtime.contracts.source_definition import SourceDefinition


@dataclass(frozen=True)
class RuntimeConfig:
    """Frozen configuration for the Runtime orchestration layer.

    All settings are immutable after construction. Use ``RuntimeConfig(...)``
    to create with custom values, or ``RuntimeConfig()`` for defaults.

    Attributes:
        sources: List of source definitions to manage.
        database_url: SQLAlchemy database connection URL.
        pipeline_interval_minutes: How often pipelines are scheduled.
        event_bridge_max_buffer: Maximum events buffered in EventBridge.
        storage_base_path: Base path for Runtime storage artifacts.
        log_level: Logging level (``"DEBUG"``, ``"INFO"``, ``"WARNING"``).
        enabled_jobs: Names of jobs to enable (e.g., ``"ingestion"``, ``"learning"``).
    """

    sources: list[SourceDefinition] = field(default_factory=list)
    database_url: str = "postgresql+psycopg2://localhost:5432/ai_shorts"
    pipeline_interval_minutes: int = 30
    event_bridge_max_buffer: int = 1000
    storage_base_path: Path = Path("./runtime_storage")
    log_level: str = "INFO"
    enabled_jobs: list[str] = field(default_factory=lambda: ["ingestion", "learning"])
