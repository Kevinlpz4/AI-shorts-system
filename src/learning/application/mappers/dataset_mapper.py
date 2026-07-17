"""
DatasetMapper — convierte Dataset entity (domain) → ``DatasetDTO``.

Solo mapping. Sin lógica de negocio, sin repositorios, sin persistencia.

Nota: El Dataset entity se definirá en una futura iteración.
Este mapper espera un objeto con los siguientes atributos:
- id: str
- name: str
- time_window_start: str
- time_window_end: str
- sample_count: int
- created_at: datetime
"""
from __future__ import annotations

from typing import Any

from learning.application.dto.dataset_dto import DatasetDTO


class DatasetMapper:
    """Mapea Dataset entity a DatasetDTO."""

    @staticmethod
    def to_dto(entity: Any) -> DatasetDTO:
        """Convierte un Dataset entity a DatasetDTO.

        Args:
            entity: Dataset entity de dominio (con atributos id, name, etc.).

        Returns:
            DatasetDTO con datos del dataset.
        """
        return DatasetDTO(
            id=str(entity.id),
            name=entity.name,
            time_window_start=entity.time_window_start,
            time_window_end=entity.time_window_end,
            sample_count=entity.sample_count,
            created_at=entity.created_at.isoformat(),
        )
