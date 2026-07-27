"""
Feedback & Decision Intelligence — Human feedback loop for Runtime BC.

Provides queue management, reason catalog, analytics, and event emission
for human review of recommended items.
"""
from __future__ import annotations

from runtime.feedback.analytics import AnalyticsCollector
from runtime.feedback.cli import FeedbackCLI, SessionDecision
from runtime.feedback.event_emitter import FeedbackEventEmitter
from runtime.feedback.models import Decision, DecisionSession, FeedbackRecord
from runtime.feedback.queue import DecisionQueue, QueueItem
from runtime.feedback.reasons import FeedbackReasons, RejectionReason

__all__ = [
    "AnalyticsCollector",
    "Decision",
    "DecisionQueue",
    "DecisionSession",
    "FeedbackCLI",
    "FeedbackEventEmitter",
    "FeedbackRecord",
    "FeedbackReasons",
    "QueueItem",
    "RejectionReason",
    "SessionDecision",
]
