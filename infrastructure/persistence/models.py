"""
Modelos SQLAlchemy para system_shorts.

Reflejan el esquema actual de SQLite (data/research.db) para migrar a PostgreSQL.
NO son los mismos que las entidades de dominio — estos son el mapa de la base de datos.
"""
from __future__ import annotations

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class SchedulerConfigModel(Base):
    """Configuración del scheduler (key-value)."""
    __tablename__ = "scheduler_config"

    key = Column(String(255), primary_key=True)
    value = Column(Text, nullable=False, default="")

    def __repr__(self) -> str:
        return f"<SchedulerConfig(key={self.key!r})>"


class ResearchTopicModel(Base):
    """Topic de investigación — aggregate root del módulo Research."""
    __tablename__ = "research_topics"

    id = Column(String(36), primary_key=True)  # UUID como string
    title = Column(Text, nullable=False, default="")
    description = Column(Text, nullable=False, default="")
    content = Column(Text, nullable=False, default="")
    source_name = Column(String(100), nullable=False, default="manual")
    source_type = Column(String(50), nullable=False, default="manual")
    source_reliability = Column(Integer, nullable=False, default=50)
    score_relevance = Column(Integer, nullable=False, default=0)
    score_popularity = Column(Integer, nullable=False, default=0)
    score_recency = Column(Integer, nullable=False, default=0)
    score_reliability = Column(Integer, nullable=False, default=0)
    status = Column(String(50), nullable=False, default="pending_review")
    url = Column(Text, nullable=True)
    author = Column(String(255), nullable=True)
    published_at = Column(Text, nullable=True)  # ISO string
    created_at = Column(Text, nullable=False)   # ISO string
    reviewed_at = Column(Text, nullable=True)   # ISO string
    duplicate_hash = Column(Text, nullable=True)

    # Relaciones
    scripts = relationship("ScriptModel", back_populates="topic",
                           cascade="all, delete-orphan", passive_deletes=True)

    def __repr__(self) -> str:
        return f"<ResearchTopic(id={self.id!r}, title={self.title[:40]!r})>"


class ScriptModel(Base):
    """Guion generado para un topic."""
    __tablename__ = "scripts"

    id = Column(String(36), primary_key=True)
    topic_id = Column(String(36),
                      ForeignKey("research_topics.id", ondelete="CASCADE"),
                      unique=True, nullable=False)
    hook = Column(Text, nullable=False, default="")
    body = Column(Text, nullable=False, default="")
    cta = Column(Text, nullable=False, default="")
    duration = Column(Integer, nullable=False, default=45)
    tone = Column(String(50), nullable=False, default="educational")
    format = Column(String(50), nullable=False, default="story")
    created_at = Column(Text, nullable=False)  # ISO string
    updated_at = Column(Text, nullable=False)  # ISO string

    # Relaciones
    topic = relationship("ResearchTopicModel", back_populates="scripts")

    def __repr__(self) -> str:
        return f"<Script(id={self.id!r}, topic_id={self.topic_id!r})>"
