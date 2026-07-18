"""
NewsFeaturesMapper — Domain <-> SQLAlchemy model mapping for Feature Store.

A lightweight domain class is used for round-tripping since
NewsFeatures doesn't have a dedicated domain entity yet.
"""
from __future__ import annotations

import json
from datetime import datetime

from learning.persistence.models.news_features import NewsFeaturesModel


class _NewsFeatures:
    """Lightweight domain representation of article features."""

    def __init__(
        self,
        article_id: str,
        source_name: str,
        title: str = "",
        source_quality: float = 0.0,
        keyword_strength: float = 0.0,
        freshness: float = 0.0,
        duplicates: float = 0.0,
        topic_strength: float = 0.0,
        category_strength: float = 0.0,
        historical_success: float = 0.0,
        confidence: float = 0.0,
        final_score: float = 0.0,
        editor_decision: str | None = None,
        created_at: datetime | None = None,
        metadata: dict | None = None,
        feature_version: str = "1.0.0",
        id: str | None = None,
    ) -> None:
        self.id = id
        self.article_id = article_id
        self.source_name = source_name
        self.title = title
        self.source_quality = source_quality
        self.keyword_strength = keyword_strength
        self.freshness = freshness
        self.duplicates = duplicates
        self.topic_strength = topic_strength
        self.category_strength = category_strength
        self.historical_success = historical_success
        self.confidence = confidence
        self.final_score = final_score
        self.editor_decision = editor_decision
        self.created_at = created_at or datetime.now()
        self.metadata = metadata or {}
        self.feature_version = feature_version


class NewsFeaturesMapper:
    """Maps news features domain <-> NewsFeaturesModel."""

    @staticmethod
    def to_domain(model: NewsFeaturesModel) -> _NewsFeatures:
        """Convert SQLAlchemy model to domain representation."""
        metadata = json.loads(model.metadata_json)
        return _NewsFeatures(
            id=model.id,
            article_id=model.article_id,
            source_name=model.source_name,
            title=model.title,
            source_quality=model.source_quality,
            keyword_strength=model.keyword_strength,
            freshness=model.freshness,
            duplicates=model.duplicates,
            topic_strength=model.topic_strength,
            category_strength=model.category_strength,
            historical_success=model.historical_success,
            confidence=model.confidence,
            final_score=model.final_score,
            editor_decision=model.editor_decision,
            created_at=model.created_at,
            metadata=metadata,
            feature_version=model.feature_version,
        )

    @staticmethod
    def to_model(entity: _NewsFeatures, version: int = 1) -> NewsFeaturesModel:
        """Convert domain representation to SQLAlchemy model."""
        return NewsFeaturesModel(
            id=entity.id or "",
            article_id=entity.article_id,
            source_name=entity.source_name,
            title=entity.title,
            source_quality=entity.source_quality,
            keyword_strength=entity.keyword_strength,
            freshness=entity.freshness,
            duplicates=entity.duplicates,
            topic_strength=entity.topic_strength,
            category_strength=entity.category_strength,
            historical_success=entity.historical_success,
            confidence=entity.confidence,
            final_score=entity.final_score,
            editor_decision=entity.editor_decision,
            created_at=entity.created_at,
            metadata_json=json.dumps(entity.metadata),
            feature_version=entity.feature_version,
            version=version,
        )
