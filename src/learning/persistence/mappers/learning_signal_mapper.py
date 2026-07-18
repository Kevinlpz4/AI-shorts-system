"""
LearningSignalMapper — Domain <-> SQLAlchemy model mapping for LearningSignal.

LearningSignal uses object.__setattr__ internally.
The mapper reconstructs via __init__ with all fields.
"""
from __future__ import annotations

import json
from datetime import datetime

from learning.domain.entities.ids import LearningSignalId
from learning.domain.entities.learning_signal import LearningSignal
from learning.domain.value_objects.signal_strength import SignalStrength
from learning.domain.value_objects.signal_type import SignalType
from learning.domain.value_objects.time_window import TimeWindow
from learning.persistence.models.learning_signal import LearningSignalModel


class LearningSignalMapper:
    """Maps LearningSignal domain entity <-> LearningSignalModel."""

    @staticmethod
    def to_domain(model: LearningSignalModel) -> LearningSignal:
        """Convert SQLAlchemy model to domain entity."""
        strength_data = json.loads(model.strength_json)
        strength = SignalStrength(
            value=strength_data["value"], decay_factor=strength_data["decay_factor"]
        )

        window_data = json.loads(model.window_json)
        window = TimeWindow(
            start=datetime.fromisoformat(window_data["start"]),
            end=datetime.fromisoformat(window_data["end"]),
        )

        return LearningSignal(
            id=LearningSignalId.from_string(model.id),
            signal_type=SignalType(model.signal_type),
            dimension=model.dimension,
            strength=strength,
            sample_size=model.sample_size,
            approval_rate=model.approval_rate,
            window=window,
            last_updated=model.last_updated,
        )

    @staticmethod
    def to_model(entity: LearningSignal, version: int = 1) -> LearningSignalModel:
        """Convert domain entity to SQLAlchemy model."""
        strength_json = json.dumps(
            {"value": entity.strength.value, "decay_factor": entity.strength.decay_factor}
        )

        window_json = json.dumps(
            {"start": entity.window.start.isoformat(), "end": entity.window.end.isoformat()}
        )

        return LearningSignalModel(
            id=str(entity.id),
            signal_type=entity.signal_type.value,
            dimension=entity.dimension,
            strength_json=strength_json,
            sample_size=entity.sample_size,
            approval_rate=entity.approval_rate,
            window_json=window_json,
            last_updated=entity.last_updated,
            version=version,
        )
