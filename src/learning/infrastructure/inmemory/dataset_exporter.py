"""
InMemoryDatasetExporter — dataset exporter for testing.

Stores exported datasets in memory for inspection. Does NOT write to disk.
Each export call records the samples, metadata, and a generated path.

Uso::

    exporter = InMemoryDatasetExporter()
    path = exporter.export(samples=[...], metadata={...})
    assert exporter.export_count == 1
    assert exporter.last_export is not None
"""
from __future__ import annotations


class InMemoryDatasetExporter:
    """DatasetExporter en memoria que acumula exports para inspección.

    Cada llamada a ``export()`` registra los samples, metadata y una ruta
    generada. Los datos NO se escriben a disco.

    Attributes:
        _exports: Lista de tuplas (samples, metadata, path).
    """

    def __init__(self) -> None:
        self._exports: list[tuple[list[dict], dict, str]] = []

    def export(self, samples: list[dict], metadata: dict) -> str:
        """Record an export and return a generated path.

        Args:
            samples: Training data samples.
            metadata: Dataset metadata.

        Returns:
            A generated path string for this export.
        """
        path = f"/tmp/datasets/{len(self._exports)}.json"
        self._exports.append((samples, metadata, path))
        return path

    @property
    def export_count(self) -> int:
        """Number of exports performed."""
        return len(self._exports)

    @property
    def last_export(self) -> tuple[list[dict], dict, str] | None:
        """The most recent export, or None if no exports have been made."""
        return self._exports[-1] if self._exports else None

    @property
    def all_exports(self) -> list[tuple[list[dict], dict, str]]:
        """Return a copy of all exports."""
        return list(self._exports)
