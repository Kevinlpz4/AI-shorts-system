"""
Feedback Pipeline — orchestrates Decision → Feedback → Signal Recalculation → New Event.

Flow: Manual decision → RecordFeedbackCommand → DecisionService → SignalService → FeedbackRecorded

When a manual decision is recorded, this pipeline:
    1. Creates a RecordFeedbackCommand from the provided data
    2. Executes via DecisionService.execute_record_feedback()
    3. Triggers signal recalculation via SignalService.execute_recalculate_signals()
    4. Emits a FeedbackRecorded outbound integration event

Design note:
    This pipeline is NOT event-driven (no IntegrationEvent input). It is
    called programmatically by the UI layer or API adapter. The
    DecisionRecorded concept is represented by the method parameters
    (not a formal IntegrationEvent) because manual decisions originate
    within the Learning BC boundary itself.
"""
from __future__ import annotations

import logging
from typing import Callable

from learning.application.commands.feedback_commands import RecordFeedbackCommand
from learning.application.commands.score_commands import RecalculateSignalsCommand
from learning.application.services.decision_service import DecisionService
from learning.application.services.signal_service import SignalService
from learning.integration.events.learning_outbound_events import FeedbackRecorded
from learning.integration.observability.event_context import EventContext

logger = logging.getLogger(__name__)


class FeedbackPipeline:
    """Pipeline: User decision → Feedback → Signal recalculation.

    When a manual decision is recorded:
        1. Create RecordFeedbackCommand from event data
        2. Execute via DecisionService
        3. Trigger signal recalculation via SignalService
        4. Emit FeedbackRecorded event
    """

    def __init__(
        self,
        decision_service: DecisionService,
        signal_service: SignalService,
        on_feedback_recorded: Callable[[FeedbackRecorded], None] | None = None,
    ) -> None:
        self._decision_service = decision_service
        self._signal_service = signal_service
        self._on_feedback_recorded = on_feedback_recorded

    def handle_manual_decision(
        self,
        topic_id: str,
        decision: str,
        source_name: str,
        title: str,
        reason: str | None = None,
        context: EventContext | None = None,
    ) -> FeedbackRecorded | None:
        """Process a manual decision through the feedback pipeline.

        Args:
            topic_id: ID of the topic being decided on.
            decision: Decision type string (APPROVED, REJECTED, etc.).
            source_name: Name of the content source.
            title: Title of the content being decided on.
            reason: Optional reason for the decision.
            context: Optional observability context for traceability.

        Returns:
            FeedbackRecorded event on success, None on failure.
            Exceptions are caught and logged — never propagated.
        """
        try:
            # 1. Create RecordFeedbackCommand
            cmd = RecordFeedbackCommand(
                topic_id=topic_id,
                decision=decision,
                reason=reason,
                source_name=source_name,
                title=title,
                features=None,  # No feature snapshot available at pipeline level
            )

            # 2. Execute via DecisionService
            result = self._decision_service.execute_record_feedback(cmd)

            if result.is_failure:
                logger.warning(
                    "FeedbackPipeline: record feedback failed for "
                    "topic=%s source=%s: %s",
                    topic_id,
                    source_name,
                    result.error.message if result.error else "unknown error",
                )
                return None

            feedback_dto = result.value

            # 3. Trigger signal recalculation (best effort — don't fail pipeline)
            try:
                recalc_cmd = RecalculateSignalsCommand(
                    source_id=source_name,
                    signal_type=None,
                )
                recalc_result = self._signal_service.execute_recalculate_signals(
                    recalc_cmd
                )
                if recalc_result.is_success:
                    logger.debug(
                        "FeedbackPipeline: recalculated %d signals",
                        recalc_result.value,
                    )
                else:
                    logger.warning(
                        "FeedbackPipeline: signal recalculation failed: %s",
                        (
                            recalc_result.error.message
                            if recalc_result.error
                            else "unknown"
                        ),
                    )
            except Exception as recalc_error:
                # Signal recalculation failure should NOT block the pipeline
                logger.warning(
                    "FeedbackPipeline: signal recalculation error: %s",
                    recalc_error,
                )

            # 4. Build outbound integration event
            outbound_event = FeedbackRecorded(
                source_boundary="learning",
                feedback_id=feedback_dto.id,
                topic_id=topic_id,
                decision=decision,
                source_name=source_name,
            )

            # 5. Fire callback if registered
            if self._on_feedback_recorded is not None:
                try:
                    self._on_feedback_recorded(outbound_event)
                except Exception as cb_error:
                    logger.error(
                        "FeedbackPipeline: callback failed: %s",
                        cb_error,
                    )

            return outbound_event

        except Exception as exc:
            logger.error(
                "FeedbackPipeline: unexpected error for topic=%s: %s",
                topic_id,
                exc,
            )
            return None
