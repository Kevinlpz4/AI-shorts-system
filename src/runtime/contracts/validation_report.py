"""
Validation report contract — output of accuracy tracking and validation.

Usage::

    from runtime.contracts.validation_report import ValidationReport
    from datetime import datetime, timezone

    report = ValidationReport(
        generated_at=datetime.now(timezone.utc),
        accuracy=0.95,
        f1_score=0.90,
    )
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class ValidationReport:
    """Immutable validation metrics report.

    Captures the accuracy, precision, recall, and F1 score of the
    learning system at a point in time.

    Attributes:
        generated_at: Timestamp when this report was generated.
        accuracy: Overall accuracy (correct / total).
        precision: Precision (true positives / predicted positives).
        recall: Recall (true positives / actual positives).
        f1_score: Harmonic mean of precision and recall.
        total_predictions: Total number of predictions made.
        total_feedback: Total number of feedback records received.
        improvement_pct: Percentage improvement over baseline.
        metadata: Report-specific metadata.
    """

    generated_at: datetime
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    total_predictions: int = 0
    total_feedback: int = 0
    improvement_pct: float = 0.0
    metadata: dict[str, str] = field(default_factory=dict)
