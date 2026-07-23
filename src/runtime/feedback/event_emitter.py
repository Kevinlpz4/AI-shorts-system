"""
Event emitter — bridges feedback decisions to Learning BC via EventBridge.

Design principles:
    1. Uses RoutingEvent (not Foundation IntegrationEvent) for lightweight transport.
    2. Approved items emit positive learning signals.
    3. Rejected items emit negative learning signals with reason.
    4. Skipped items emit no learning signal (neutral action).
"""
from __future__ import annotations

from typing import Any, Dict

from runtime.event_bridge import EventBridge, RoutingEvent
from runtime.feedback.models import Decision, FeedbackRecord


class FeedbackEventEmitter:
    """Emits feedback events to Learning BC via EventBridge.

    All events are routed as ``RoutingEvent`` through the bridge.
    """

    def __init__(self, event_bridge: EventBridge) -> None:
        self._event_bridge = event_bridge

    def emit_feedback_recorded(self, record: FeedbackRecord) -> None:
        """Emit event when a feedback record is created."""
        self._event_bridge.route(RoutingEvent(
            event_type="feedback.recorded",
            payload={
                "record_id": record.id,
                "article_id": record.article_id,
                "provider": record.provider,
                "decision": record.decision.value,
                "reason": record.reason,
                "timestamp": record.timestamp.isoformat(),
            },
            source="feedback",
        ))

    def emit_decision_session_started(self, session_id: str, user_id: str) -> None:
        """Emit event when a decision session starts."""
        self._event_bridge.route(RoutingEvent(
            event_type="feedback.session.started",
            payload={
                "session_id": session_id,
                "user_id": user_id,
            },
            source="feedback",
        ))

    def emit_decision_session_ended(self, session_id: str, stats: Dict[str, Any]) -> None:
        """Emit event when a decision session ends."""
        self._event_bridge.route(RoutingEvent(
            event_type="feedback.session.ended",
            payload={
                "session_id": session_id,
                "stats": stats,
            },
            source="feedback",
        ))

    def emit_learning_signal(self, record: FeedbackRecord) -> None:
        """Emit learning signal for approved or rejected items.

        Approved → positive signal (reinforce scoring).
        Rejected → negative signal (adjust scoring by reason).
        Skipped → no signal (neutral action).
        """
        if record.decision == Decision.APPROVE:
            self._event_bridge.route(RoutingEvent(
                event_type="learning.signal.approved",
                payload={
                    "article_id": record.article_id,
                    "provider": record.provider,
                    "category": record.category,
                    "topic": record.topic,
                    "score": record.recommended_score,
                },
                source="feedback",
            ))
        elif record.decision == Decision.REJECT:
            self._event_bridge.route(RoutingEvent(
                event_type="learning.signal.rejected",
                payload={
                    "article_id": record.article_id,
                    "provider": record.provider,
                    "category": record.category,
                    "topic": record.topic,
                    "reason": record.reason,
                },
                source="feedback",
            ))
        # SKIP → no event emitted
