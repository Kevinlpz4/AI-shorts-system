"""
PostgresResearchRepository — Implementación SQLAlchemy de ResearchRepository
==============================================================================
Implementa el Protocol ResearchRepository usando SQLAlchemy + PostgreSQL.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import text

from infrastructure.persistence.database import SessionLocal
from infrastructure.persistence.models import ResearchTopicModel, ScriptModel
from research.domain.entities.research_topic import ResearchTopic
from research.domain.value_objects.research_score import ResearchScore
from research.domain.value_objects.research_source import ResearchSource, SourceType
from research.domain.value_objects.research_status import ResearchStatus

# Límite para contenido muy largo
_MAX_CONTENT_LENGTH = 500_000


class PostgresResearchRepository:
    """
    Repositorio PostgreSQL para ResearchTopics.

    No hereda de ResearchRepository explícitamente (Protocol match).
    """

    def __init__(self):
        self._ensure_table()

    @staticmethod
    def _ensure_table() -> None:
        """Asegura que la tabla existe (idempotente)."""
        from infrastructure.persistence.database import ensure_tables
        ensure_tables()

    # ── Persistencia ─────────────────────────────────

    async def save(self, topic: ResearchTopic) -> None:
        """Guarda un topic (merge = insert or update)."""
        with SessionLocal() as session:
            row = ResearchTopicModel(
                id=str(topic.id),
                title=topic.title,
                description=topic.description,
                content=topic.content[:_MAX_CONTENT_LENGTH],
                source_name=topic.source.name,
                source_type=topic.source.type.value,
                source_reliability=topic.source.reliability,
                score_relevance=topic.score.relevance,
                score_popularity=topic.score.popularity,
                score_recency=topic.score.recency,
                score_reliability=topic.score.source_reliability,
                status=topic.status.value,
                url=topic.url,
                author=topic.author,
                published_at=topic.published_at.isoformat() if topic.published_at else None,
                created_at=topic.created_at.isoformat() if topic.created_at else None,
                reviewed_at=topic.reviewed_at.isoformat() if topic.reviewed_at else None,
                duplicate_hash=topic.duplicate_hash,
            )
            session.merge(row)
            session.commit()

    async def save_many(self, topics: list[ResearchTopic]) -> None:
        """Guarda múltiples topics en una transacción."""
        with SessionLocal() as session:
            for topic in topics:
                row = ResearchTopicModel(
                    id=str(topic.id),
                    title=topic.title,
                    description=topic.description,
                    content=topic.content[:_MAX_CONTENT_LENGTH],
                    source_name=topic.source.name,
                    source_type=topic.source.type.value,
                    source_reliability=topic.source.reliability,
                    score_relevance=topic.score.relevance,
                    score_popularity=topic.score.popularity,
                    score_recency=topic.score.recency,
                    score_reliability=topic.score.source_reliability,
                    status=topic.status.value,
                    url=topic.url,
                    author=topic.author,
                    published_at=topic.published_at.isoformat() if topic.published_at else None,
                    created_at=topic.created_at.isoformat() if topic.created_at else None,
                    reviewed_at=topic.reviewed_at.isoformat() if topic.reviewed_at else None,
                    duplicate_hash=topic.duplicate_hash,
                )
                session.merge(row)
            session.commit()

    # ── Lectura ──────────────────────────────────────

    async def find_by_id(self, topic_id: UUID) -> Optional[ResearchTopic]:
        """Busca un topic por ID."""
        with SessionLocal() as session:
            row = session.query(ResearchTopicModel).filter(
                ResearchTopicModel.id == str(topic_id)
            ).first()
            return self._row_to_topic(row) if row else None

    async def find_by_status(
        self, status: ResearchStatus, limit: int = 50
    ) -> list[ResearchTopic]:
        """Busca topics por estado, ordenados por score descendente."""
        with SessionLocal() as session:
            rows = (
                session.query(ResearchTopicModel)
                .filter(ResearchTopicModel.status == status.value)
                .order_by(
                    (
                        ResearchTopicModel.score_relevance * 0.35
                        + ResearchTopicModel.score_popularity * 0.25
                        + ResearchTopicModel.score_recency * 0.25
                        + ResearchTopicModel.score_reliability * 0.15
                    ).desc(),
                    ResearchTopicModel.created_at.desc(),
                )
                .limit(limit)
                .all()
            )
            return [self._row_to_topic(r) for r in rows]

    async def find_by_duplicate_hash(
        self, duplicate_hash: str
    ) -> list[ResearchTopic]:
        """Busca topics que compartan el mismo hash."""
        with SessionLocal() as session:
            rows = (
                session.query(ResearchTopicModel)
                .filter(ResearchTopicModel.duplicate_hash == duplicate_hash)
                .all()
            )
            return [self._row_to_topic(r) for r in rows]

    async def find_pending_review(
        self, limit: int = 20
    ) -> list[ResearchTopic]:
        """Busca topics pendientes de revisión."""
        return await self.find_by_status(
            ResearchStatus.PENDING_REVIEW, limit=limit
        )

    async def find_all(
        self, limit: int = 50, offset: int = 0
    ) -> list[ResearchTopic]:
        """Lista todos los topics ordenados por fecha descendente."""
        with SessionLocal() as session:
            rows = (
                session.query(ResearchTopicModel)
                .order_by(ResearchTopicModel.created_at.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )
            return [self._row_to_topic(r) for r in rows]

    async def find_approved_without_script(self) -> list[ResearchTopic]:
        """Approved topics sin script asociado, ordenados por score."""
        with SessionLocal() as session:
            subq = (
                session.query(ScriptModel.topic_id)
                .subquery()
            )
            rows = (
                session.query(ResearchTopicModel)
                .outerjoin(subq, ResearchTopicModel.id == subq.c.topic_id)
                .filter(
                    ResearchTopicModel.status == "approved",
                    subq.c.topic_id.is_(None),
                )
                .order_by(
                    (
                        ResearchTopicModel.score_relevance * 0.35
                        + ResearchTopicModel.score_popularity * 0.25
                        + ResearchTopicModel.score_recency * 0.25
                        + ResearchTopicModel.score_reliability * 0.15
                    ).desc(),
                )
                .limit(50)
                .all()
            )
            return [self._row_to_topic(r) for r in rows]

    async def count_by_status(self, status: ResearchStatus) -> int:
        """Cuenta topics en un estado dado."""
        with SessionLocal() as session:
            return (
                session.query(ResearchTopicModel)
                .filter(ResearchTopicModel.status == status.value)
                .count()
            )

    async def delete(self, topic_id: UUID) -> None:
        """Elimina un topic por ID."""
        with SessionLocal() as session:
            session.query(ResearchTopicModel).filter(
                ResearchTopicModel.id == str(topic_id)
            ).delete()
            session.commit()

    # ── Mappers ──────────────────────────────────────

    @staticmethod
    def _row_to_topic(row: ResearchTopicModel) -> ResearchTopic:
        """Convierte un modelo SQLAlchemy → entidad ResearchTopic."""
        source = ResearchSource(
            name=row.source_name,
            type=SourceType(row.source_type),
            reliability=row.source_reliability,
        )

        score = ResearchScore(
            relevance=row.score_relevance,
            popularity=row.score_popularity,
            recency=row.score_recency,
            source_reliability=row.score_reliability,
        )

        return ResearchTopic(
            id=UUID(row.id),
            title=row.title,
            description=row.description,
            content=row.content,
            source=source,
            score=score,
            status=ResearchStatus(row.status),
            url=row.url,
            author=row.author,
            published_at=_parse_datetime(row.published_at),
            created_at=_parse_datetime(row.created_at) or datetime.now(timezone.utc),
            reviewed_at=_parse_datetime(row.reviewed_at),
            duplicate_hash=row.duplicate_hash,
        )


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parsea string ISO → datetime."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None
