"""
Tests for RuntimeConfig — frozen dataclass configuration.

Covers:
- Default construction
- Custom construction
- Immutability (frozen)
- Field access
"""
from __future__ import annotations

from pathlib import Path

import pytest

from runtime.config import RuntimeConfig
from runtime.contracts.source_definition import SourceDefinition


class TestRuntimeConfig:
    """Tests for RuntimeConfig frozen dataclass."""

    def test_default_construction(self) -> None:
        """RuntimeConfig has sensible defaults when constructed empty."""
        config = RuntimeConfig()

        assert config.sources == []
        assert config.database_url == "postgresql+psycopg2://localhost:5432/ai_shorts"
        assert config.pipeline_interval_minutes == 30
        assert config.event_bridge_max_buffer == 1000
        assert config.storage_base_path == Path("./runtime_storage")
        assert config.log_level == "INFO"
        assert config.enabled_jobs == ["ingestion", "learning"]

    def test_custom_construction(self) -> None:
        """RuntimeConfig accepts custom values."""
        sources = [
            SourceDefinition(id="src-1", provider="rss", technology="rss"),
            SourceDefinition(id="src-2", provider="api", technology="api"),
        ]
        config = RuntimeConfig(
            sources=sources,
            database_url="postgresql+psycopg2://prod:5432/ai_shorts",
            pipeline_interval_minutes=15,
            event_bridge_max_buffer=5000,
            storage_base_path=Path("/data/storage"),
            log_level="DEBUG",
            enabled_jobs=["ingestion"],
        )

        assert len(config.sources) == 2
        assert config.sources[0].id == "src-1"
        assert config.database_url == "postgresql+psycopg2://prod:5432/ai_shorts"
        assert config.pipeline_interval_minutes == 15
        assert config.event_bridge_max_buffer == 5000
        assert config.storage_base_path == Path("/data/storage")
        assert config.log_level == "DEBUG"
        assert config.enabled_jobs == ["ingestion"]

    def test_frozen_immutability(self) -> None:
        """RuntimeConfig is frozen — attribute assignment raises."""
        config = RuntimeConfig()

        with pytest.raises(AttributeError):
            config.log_level = "DEBUG"  # type: ignore[misc]

    def test_frozen_sources_immutable(self) -> None:
        """RuntimeConfig.sources list is frozen (tuple semantics)."""
        config = RuntimeConfig()

        with pytest.raises(AttributeError):
            config.sources = []  # type: ignore[misc]

    def test_enabled_jobs_default(self) -> None:
        """Default enabled_jobs includes ingestion and learning."""
        config = RuntimeConfig()
        assert "ingestion" in config.enabled_jobs
        assert "learning" in config.enabled_jobs
