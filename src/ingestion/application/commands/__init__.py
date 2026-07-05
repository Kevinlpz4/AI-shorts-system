"""
Application Commands — 15 commandos CQRS para el BC Ingestion.

Cada comando es un ``@dataclass(frozen=True)`` sin lógica ni validaciones.
Solo transporte de datos.

Uso::

    from ingestion.application.commands import (
        RegisterSourceCommand,
        FindSourceQuery,
    )
"""
from __future__ import annotations

from ingestion.application.commands.article_commands import CreateRawArticleCommand
from ingestion.application.commands.feed_category_commands import (
    AssignCategoryToFeedCommand,
    AssignTopicToFeedCommand,
)
from ingestion.application.commands.feed_commands import (
    ActivateFeedCommand,
    PauseFeedCommand,
    RecordCollectionCommand,
    RecordFailureCommand,
    RegisterFeedCommand,
    UpdateFeedCommand,
)
from ingestion.application.commands.source_category_commands import (
    AssignCategoryToSourceCommand,
    AssignTopicToSourceCommand,
)
from ingestion.application.commands.source_commands import (
    DisableSourceCommand,
    EnableSourceCommand,
    RegisterSourceCommand,
    UpdateSourceCommand,
)

__all__ = [
    # Source commands
    "RegisterSourceCommand",
    "UpdateSourceCommand",
    "EnableSourceCommand",
    "DisableSourceCommand",
    # Source category commands
    "AssignCategoryToSourceCommand",
    "AssignTopicToSourceCommand",
    # Feed commands
    "RegisterFeedCommand",
    "UpdateFeedCommand",
    "PauseFeedCommand",
    "ActivateFeedCommand",
    "RecordCollectionCommand",
    "RecordFailureCommand",
    # Feed category commands
    "AssignCategoryToFeedCommand",
    "AssignTopicToFeedCommand",
    # Article commands
    "CreateRawArticleCommand",
]
