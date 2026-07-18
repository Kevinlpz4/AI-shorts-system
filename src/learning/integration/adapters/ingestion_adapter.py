"""
Ingestion Event Adapter — translates Ingestion integration events into Learning commands.

Never exposes domain entities from Ingestion.
Only produces Learning commands and DTOs.
"""
from __future__ import annotations

from typing import Callable

from learning.application.commands.dataset_commands import GenerateDatasetCommand
from learning.application.commands.signal_commands import RegisterSignalCommand
from learning.application.commands.source_commands import UpdateSourceProfileCommand
from learning.application.dto.recommendation_dto import RecommendationDTO
from learning.integration.events.ingestion_events import (
    ArticleCreated,
    FeedRegistered,
    RawArticleCollected,
    RawArticleRejected,
    SourceRegistered,
)


class IngestionEventAdapter:
    """Translates Ingestion integration events into Learning commands.

    This adapter is the bridge between Ingestion BC events and Learning
    BC application commands. It ensures:

    - No Ingestion domain objects leak into Learning
    - Events are translated into the appropriate Learning commands
    - Missing or invalid data returns None (no command generated)

    Usage:
        adapter = IngestionEventAdapter(on_recommend=my_predictor)
        command = adapter.handle_raw_article_collected(event)
        if command:
            signal_service.register_signal(command)
    """

    def __init__(
        self,
        on_recommend: Callable[[str, str, dict | None], RecommendationDTO | None] | None = None,
    ) -> None:
        """Initialize the adapter.

        Args:
            on_recommend: Optional callback for generating recommendations.
                Signature: (article_id, source_name, metadata) -> RecommendationDTO | None.
                If None, recommendation generation is skipped.
        """
        self._on_recommend = on_recommend

    def handle_raw_article_collected(self, event: RawArticleCollected) -> RegisterSignalCommand | None:
        """Convert article collection into a signal registration command.

        Registers a SOURCE dimension signal with neutral value (0.5)
        to track that a new article was collected from this source.

        Args:
            event: The RawArticleCollected integration event.

        Returns:
            RegisterSignalCommand for the SOURCE dimension, or None if
            the event lacks required data.
        """
        if not event.source_name:
            return None

        return RegisterSignalCommand(
            dimension="SOURCE",
            source=event.source_name,
            value=0.5,
        )

    def handle_raw_article_rejected(self, event: RawArticleRejected) -> UpdateSourceProfileCommand | None:
        """Convert article rejection into source profile update.

        Updates the source quality profile with a rejection signal,
        which will lower the source's quality score over time.

        Args:
            event: The RawArticleRejected integration event.

        Returns:
            UpdateSourceProfileCommand, or None if the event lacks
            required data.
        """
        if not event.source_name:
            return None

        return UpdateSourceProfileCommand(
            source_id=event.source_name,
            decision="rejected",
        )

    def handle_source_registered(self, event: SourceRegistered) -> None:
        """Log source registration (no command needed yet).

        Source registration doesn't require immediate action from Learning.
        Future iterations may initialize a SourceQualityProfile here.

        Args:
            event: The SourceRegistered integration event.

        Returns:
            None — no command generated.
        """
        return None

    def handle_article_created(self, event: ArticleCreated) -> RegisterSignalCommand | None:
        """Convert article creation into signal registration.

        Registers a SOURCE dimension signal with neutral value (0.5)
        to track that a processed article was created from this source.

        Args:
            event: The ArticleCreated integration event.

        Returns:
            RegisterSignalCommand for the SOURCE dimension, or None if
            the event lacks required data.
        """
        if not event.source_name:
            return None

        return RegisterSignalCommand(
            dimension="SOURCE",
            source=event.source_name,
            value=0.5,
        )
