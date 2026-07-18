"""
Tests for InMemoryDatasetExporter.

Covers export, export_count, last_export, and all_exports.
"""
from __future__ import annotations

from learning.infrastructure.inmemory.dataset_exporter import (
    InMemoryDatasetExporter,
)


class TestInMemoryDatasetExporter:
    """Tests for InMemoryDatasetExporter."""

    def test_export_returns_path(self) -> None:
        exporter = InMemoryDatasetExporter()

        path = exporter.export(
            samples=[{"x": 1}, {"x": 2}],
            metadata={"version": "1.0"},
        )

        assert isinstance(path, str)
        assert path.startswith("/tmp/datasets/")
        assert path.endswith(".json")

    def test_export_count(self) -> None:
        exporter = InMemoryDatasetExporter()

        assert exporter.export_count == 0

        exporter.export(samples=[], metadata={})
        assert exporter.export_count == 1

        exporter.export(samples=[{"a": 1}], metadata={"b": 2})
        assert exporter.export_count == 2

    def test_last_export(self) -> None:
        exporter = InMemoryDatasetExporter()

        assert exporter.last_export is None

        samples1 = [{"x": 1}]
        meta1 = {"v": "1"}
        exporter.export(samples=samples1, metadata=meta1)

        result = exporter.last_export
        assert result is not None
        assert result[0] == samples1
        assert result[1] == meta1
        assert result[2].startswith("/tmp/datasets/")

    def test_last_export_returns_most_recent(self) -> None:
        exporter = InMemoryDatasetExporter()

        exporter.export(samples=[{"first": True}], metadata={})
        exporter.export(samples=[{"second": True}], metadata={})

        _, _, last_path = exporter.last_export  # type: ignore[misc]
        assert last_path == "/tmp/datasets/1.json"

    def test_all_exports(self) -> None:
        exporter = InMemoryDatasetExporter()

        exporter.export(samples=[{"a": 1}], metadata={})
        exporter.export(samples=[{"b": 2}], metadata={})

        all_exp = exporter.all_exports
        assert len(all_exp) == 2
        # Returns a copy
        assert all_exp is not exporter._exports
