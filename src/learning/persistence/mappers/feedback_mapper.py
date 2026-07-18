"""
FeedbackRecordMapper — Domain <-> SQLAlchemy model mapping for FeedbackRecord.

FeedbackRecord is IMMUTABLE. The mapper reconstructs the entity via
FeedbackRecord.__init__() with all fields, not dataclass syntax.
"""
from __future__ import annotations

import json
from datetime import datetime

from learning.domain.entities.feedback_record import FeedbackRecord
from learning.domain.entities.ids import FeedbackId
from learning.domain.value_objects.decision_type import DecisionType
from learning.domain.value_objects.feature_snapshot import FeatureSnapshot
from learning.persistence.models.feedback import FeedbackRecordModel


class FeedbackRecordMapper:
    """Maps FeedbackRecord domain entity <-> FeedbackRecordModel."""

    @staticmethod
    def to_domain(model: FeedbackRecordModel) -> FeedbackRecord:
        """Convert SQLAlchemy model to domain entity.

        Reconstructs the immutable FeedbackRecord via __init__.
        """
        feature_data = json.loads(model.feature_snapshot_json)
        feature_data["timestamp"] = datetime.fromisoformat(feature_data["timestamp"])
        feature_snapshot = FeatureSnapshot(**feature_data)

        score_snapshot = json.loads(model.score_snapshot_json)

        return FeedbackRecord(
            id=FeedbackId.from_string(model.id),
            topic_id=model.topic_id,
            decision=DecisionType(model.decision),
            reason=model.reason,
            feature_snapshot=feature_snapshot,
            source_name=model.source_name,
            title=model.title,
            score_snapshot=score_snapshot,
            captured_at=model.captured_at,
        )

    @staticmethod
    def to_model(entity: FeedbackRecord, version: int = 1) -> FeedbackRecordModel:
        """Convert domain entity to SQLAlchemy model."""
        feature_data = entity.feature_snapshot.as_dict()
        # Convert datetime to ISO string for JSON serialization
        feature_data["timestamp"] = feature_data["timestamp"].isoformat()

        return FeedbackRecordModel(
            id=str(entity.id),
            topic_id=entity.topic_id,
            decision=entity.decision.value,
            reason=entity.reason,
            feature_snapshot_json=json.dumps(feature_data),
            source_name=entity.source_name,
            title=entity.title,
            score_snapshot_json=json.dumps(entity.score_snapshot),
            captured_at=entity.captured_at,
            version=version,
        )
