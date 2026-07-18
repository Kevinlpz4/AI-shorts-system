"""
InMemoryTypedEventPublisher — typed event publisher for testing.

Stores events in separate typed lists for easy inspection by event type.
Complements ``InMemoryLearningEventPublisher`` (generic) with type-safe
routing by event kind.

Uso::

    publisher = InMemoryTypedEventPublisher()
    publisher.publish_feedback_captured(event)
    assert publisher.has_feedback_events()
    publisher.clear()
"""
from __future__ import annotations

from learning.domain.events.learning_events import (
    DatasetGenerated,
    FeedbackCaptured,
    LearningModelUpdated,
    ScoreAdjusted,
    SignalAggregated,
)


class InMemoryTypedEventPublisher:
    """Typed event publisher that stores events in separate typed lists.

    Each event type has its own list, enabling precise inspection
    in tests without type-checking.
    """

    def __init__(self) -> None:
        self._feedback_events: list[FeedbackCaptured] = []
        self._signal_events: list[SignalAggregated] = []
        self._score_events: list[ScoreAdjusted] = []
        self._dataset_events: list[DatasetGenerated] = []
        self._model_events: list[LearningModelUpdated] = []

    def publish_feedback_captured(self, event: FeedbackCaptured) -> None:
        """Publish a FeedbackCaptured event."""
        self._feedback_events.append(event)

    def publish_signal_aggregated(self, event: SignalAggregated) -> None:
        """Publish a SignalAggregated event."""
        self._signal_events.append(event)

    def publish_score_adjusted(self, event: ScoreAdjusted) -> None:
        """Publish a ScoreAdjusted event."""
        self._score_events.append(event)

    def publish_dataset_generated(self, event: DatasetGenerated) -> None:
        """Publish a DatasetGenerated event."""
        self._dataset_events.append(event)

    def publish_learning_model_updated(
        self, event: LearningModelUpdated
    ) -> None:
        """Publish a LearningModelUpdated event."""
        self._model_events.append(event)

    @property
    def feedback_events(self) -> list[FeedbackCaptured]:
        """Return copy of published feedback events."""
        return list(self._feedback_events)

    @property
    def signal_events(self) -> list[SignalAggregated]:
        """Return copy of published signal events."""
        return list(self._signal_events)

    @property
    def score_events(self) -> list[ScoreAdjusted]:
        """Return copy of published score events."""
        return list(self._score_events)

    @property
    def dataset_events(self) -> list[DatasetGenerated]:
        """Return copy of published dataset events."""
        return list(self._dataset_events)

    @property
    def model_events(self) -> list[LearningModelUpdated]:
        """Return copy of published model events."""
        return list(self._model_events)

    def has_feedback_events(self) -> bool:
        """Check if any feedback events have been published."""
        return len(self._feedback_events) > 0

    def has_signal_events(self) -> bool:
        """Check if any signal events have been published."""
        return len(self._signal_events) > 0

    def has_score_events(self) -> bool:
        """Check if any score events have been published."""
        return len(self._score_events) > 0

    def has_dataset_events(self) -> bool:
        """Check if any dataset events have been published."""
        return len(self._dataset_events) > 0

    def has_model_events(self) -> bool:
        """Check if any model events have been published."""
        return len(self._model_events) > 0

    def clear(self) -> None:
        """Clear all events from all typed lists."""
        self._feedback_events.clear()
        self._signal_events.clear()
        self._score_events.clear()
        self._dataset_events.clear()
        self._model_events.clear()
