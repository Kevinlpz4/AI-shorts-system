"""
NewsFeaturesModel — SQLAlchemy model for Feature Store persistence.
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from learning.persistence.models.base import Base


class NewsFeaturesModel(Base):
    """Persistence model for article features (Feature Store)."""

    __tablename__ = "learning_news_features"

    id = Column(String(36), primary_key=True)
    article_id = Column(String(255), nullable=False, unique=True, index=True)
    source_name = Column(String(255), nullable=False, index=True)
    title = Column(Text, nullable=False, default="")
    source_quality = Column(Float, nullable=False, default=0.0)
    keyword_strength = Column(Float, nullable=False, default=0.0)
    freshness = Column(Float, nullable=False, default=0.0)
    duplicates = Column(Float, nullable=False, default=0.0)
    topic_strength = Column(Float, nullable=False, default=0.0)
    category_strength = Column(Float, nullable=False, default=0.0)
    historical_success = Column(Float, nullable=False, default=0.0)
    confidence = Column(Float, nullable=False, default=0.0)
    final_score = Column(Float, nullable=False, default=0.0)
    editor_decision = Column(String(20), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)
    metadata_json = Column(Text, nullable=False, default="{}")  # JSON
    feature_version = Column(String(20), nullable=False, default="1.0.0")
    version = Column(Integer, nullable=False, default=1)
