"""
FeatureStoreRepository — Persistence for article features (Feature Store).

Supports upsert by article_id and filtered queries.
"""
from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from learning.persistence.mappers.news_features_mapper import (
    NewsFeaturesMapper,
    _NewsFeatures,
)
from learning.persistence.models.news_features import NewsFeaturesModel


class FeatureStoreRepository:
    """Repository for news article features (Feature Store)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert(self, features: _NewsFeatures) -> _NewsFeatures:
        """Insert or update features for an article (by article_id).

        If an article already has features, update all fields.
        """
        existing = (
            self._session.query(NewsFeaturesModel)
            .filter(NewsFeaturesModel.article_id == features.article_id)
            .first()
        )
        if existing is not None:
            model = NewsFeaturesMapper.to_model(features, version=existing.version + 1)
            existing.source_name = model.source_name
            existing.title = model.title
            existing.source_quality = model.source_quality
            existing.keyword_strength = model.keyword_strength
            existing.freshness = model.freshness
            existing.duplicates = model.duplicates
            existing.topic_strength = model.topic_strength
            existing.category_strength = model.category_strength
            existing.historical_success = model.historical_success
            existing.confidence = model.confidence
            existing.final_score = model.final_score
            existing.editor_decision = model.editor_decision
            existing.metadata_json = model.metadata_json
            existing.feature_version = model.feature_version
            existing.version = model.version
            self._session.flush()
            return NewsFeaturesMapper.to_domain(existing)
        else:
            model = NewsFeaturesMapper.to_model(features)
            if not model.id:
                model.id = str(features.article_id)
            self._session.add(model)
            self._session.flush()
            return NewsFeaturesMapper.to_domain(model)

    def find_by_article_id(self, article_id: str) -> _NewsFeatures | None:
        """Find features by article ID."""
        model = (
            self._session.query(NewsFeaturesModel)
            .filter(NewsFeaturesModel.article_id == article_id)
            .first()
        )
        if model is None:
            return None
        return NewsFeaturesMapper.to_domain(model)

    def query(
        self,
        source_name: str | None = None,
        editor_decision: str | None = None,
        min_score: float | None = None,
        max_score: float | None = None,
        limit: int = 100,
    ) -> list[_NewsFeatures]:
        """Query features with optional filters."""
        q = self._session.query(NewsFeaturesModel)
        if source_name is not None:
            q = q.filter(NewsFeaturesModel.source_name == source_name)
        if editor_decision is not None:
            q = q.filter(NewsFeaturesModel.editor_decision == editor_decision)
        if min_score is not None:
            q = q.filter(NewsFeaturesModel.final_score >= min_score)
        if max_score is not None:
            q = q.filter(NewsFeaturesModel.final_score <= max_score)
        models = q.order_by(NewsFeaturesModel.created_at.desc()).limit(limit).all()
        return [NewsFeaturesMapper.to_domain(m) for m in models]

    def count_by_decision(self, decision: str) -> int:
        """Count features with a specific editor decision."""
        count = (
            self._session.query(func.count(NewsFeaturesModel.id))
            .filter(NewsFeaturesModel.editor_decision == decision)
            .scalar()
        )
        return count or 0

    def count_all(self) -> int:
        """Count all feature records."""
        count = self._session.query(func.count(NewsFeaturesModel.id)).scalar()
        return count or 0

    def get_average_score(self) -> float:
        """Get average final_score across all features."""
        avg = self._session.query(func.avg(NewsFeaturesModel.final_score)).scalar()
        return float(avg) if avg is not None else 0.0

    def delete_by_article_id(self, article_id: str) -> bool:
        """Delete features for a specific article. Returns True if deleted."""
        model = (
            self._session.query(NewsFeaturesModel)
            .filter(NewsFeaturesModel.article_id == article_id)
            .first()
        )
        if model is None:
            return False
        self._session.delete(model)
        self._session.flush()
        return True
