"""
DatasetExporter Port — Abstracción de exportación de datasets de entrenamiento.

Define el contrato para exportar datos de entrenamiento a diferentes formatos
(CSV, JSONL, etc.). La implementación concreta maneja la serialización.

Uso::

    exporter = CSVExporter("/data/training")
    path = exporter.export(samples=[{"input": "...", "label": 1}], metadata={"version": "1.0"})
    # path = "/data/training/dataset_v1.csv"
"""

from __future__ import annotations

from typing import Protocol


class DatasetExporter(Protocol):
    """Port para exportar datasets de entrenamiento.

    Responsabilidades:
        - export(): Serializar samples y metadata a un formato de archivo.
        - Retornar la ruta o ID del archivo exportado.

    NO hace:
        - No genera los samples (eso es responsabilidad del servicio).
        - No valida los datos (eso es responsabilidad del dominio).
        - No almacena el archivo permanentemente (eso es infraestructura).
    """

    def export(self, samples: list[dict], metadata: dict) -> str:
        """Exporta samples de entrenamiento junto con metadata.

        Args:
            samples: Lista de diccionarios con los datos de entrenamiento.
            metadata: Diccionario con metadata del dataset (versión, fecha, etc.).

        Returns:
            Ruta o ID del archivo exportado.
        """
        ...
