"""
Application Commands — 7 commandos CQRS para el BC Learning.

Cada comando es un ``@dataclass(frozen=True)`` sin lógica ni validaciones.
Solo transporte de datos.

Uso::

    from learning.application.commands import (
        RecordFeedbackCommand,
        ArchiveFeedbackCommand,
    )
"""
from __future__ import annotations

from learning.application.commands.dataset_commands import GenerateDatasetCommand
from learning.application.commands.feedback_commands import (
    ArchiveFeedbackCommand,
    RecordFeedbackCommand,
)
from learning.application.commands.score_commands import (
    AdjustScoreWeightsCommand,
    RecalculateSignalsCommand,
)
from learning.application.commands.signal_commands import RegisterSignalCommand
from learning.application.commands.source_commands import UpdateSourceProfileCommand

__all__ = [
    # Feedback commands
    "RecordFeedbackCommand",
    "ArchiveFeedbackCommand",
    # Score commands
    "AdjustScoreWeightsCommand",
    "RecalculateSignalsCommand",
    # Signal commands
    "RegisterSignalCommand",
    # Source commands
    "UpdateSourceProfileCommand",
    # Dataset commands
    "GenerateDatasetCommand",
]
