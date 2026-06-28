"""
SQLiteResearchRepository — Implementación concreta de ResearchRepository
===========================================================================
Guarda ResearchTopics en SQLite.

Trade-offs:
  + Zero dependencies (sqlite3 es built-in de Python)
  + Rápido para desarrollo y single-user
  - No es async (bloqueante, pero ok para CLI)
  - No escala a multi-proceso

Si en el futuro se necesita async → cambiar a aiosqlite.
Si se necesita multi-proceso → cambiar a PostgreSQL.

El repositorio:
  - Serializa/deserializa entidades completas (Aggregate Root)
  - No conoce eventos de dominio (son transientes)
  - TRUNCATE texto muy largo para evitar SQLite limits
"""

import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from research.domain.entities.research_topic import ResearchTopic
from research.domain.value_objects.research_score import ResearchScore
from research.domain.value_objects.research_source import ResearchSource, SourceType
from research.domain.value_objects.research_status import ResearchStatus


# Limite de SQLite para TEXT es ~1e9 bytes, pero es buena práctica
# truncar contenido muy largo en la base de datos
_MAX_CONTENT_LENGTH = 500_000  # ~500KB


class SQLiteResearchRepository:
    """
    Repositorio SQLite para ResearchTopics.

    No hereda de ResearchRepository explícitamente (Protocol match).
    """

    def __init__(self, db_path: str = "research.db"):
        self._db_path = db_path
        self._ensure_table()

    # ── Setup ────────────────────────────────────────

    def _get_connection(self) -> sqlite3.Connection:
        """Obtiene conexión SQLite."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")  # Mejor performance concurrente
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _ensure_table(self) -> None:
        """Crea la tabla si no existe."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS research_topics (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL DEFAULT '',
                    description TEXT NOT NULL DEFAULT '',
                    content TEXT NOT NULL DEFAULT '',
                    source_name TEXT NOT NULL DEFAULT 'manual',
                    source_type TEXT NOT NULL DEFAULT 'manual',
                    source_reliability INTEGER NOT NULL DEFAULT 50,
                    score_relevance INTEGER NOT NULL DEFAULT 0,
                    score_popularity INTEGER NOT NULL DEFAULT 0,
                    score_recency INTEGER NOT NULL DEFAULT 0,
                    score_reliability INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'pending_review',
                    url TEXT,
                    author TEXT,
                    published_at TEXT,
                    created_at TEXT NOT NULL,
                    reviewed_at TEXT,
                    duplicate_hash TEXT
                )
            """)
            # Índices para queries frecuentes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_topics_status
                ON research_topics(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_topics_duplicate_hash
                ON research_topics(duplicate_hash)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_topics_created_at
                ON research_topics(created_at)
            """)

    # ── Pesistencia ──────────────────────────────────

    async def save(self, topic: ResearchTopic) -> None:
        """Guarda un topic (upsert)."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO research_topics (
                    id, title, description, content,
                    source_name, source_type, source_reliability,
                    score_relevance, score_popularity, score_recency, score_reliability,
                    status, url, author, published_at, created_at, reviewed_at,
                    duplicate_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(topic.id),
                topic.title,
                topic.description,
                topic.content[:_MAX_CONTENT_LENGTH],
                topic.source.name,
                topic.source.type.value,
                topic.source.reliability,
                topic.score.relevance,
                topic.score.popularity,
                topic.score.recency,
                topic.score.source_reliability,
                topic.status.value,
                topic.url,
                topic.author,
                topic.published_at.isoformat() if topic.published_at else None,
                topic.created_at.isoformat() if topic.created_at else None,
                topic.reviewed_at.isoformat() if topic.reviewed_at else None,
                topic.duplicate_hash,
            ))

    async def save_many(self, topics: list[ResearchTopic]) -> None:
        """Guarda múltiples topics en una transacción."""
        with self._get_connection() as conn:
            conn.execute("BEGIN")
            try:
                for topic in topics:
                    conn.execute("""
                        INSERT OR REPLACE INTO research_topics (
                            id, title, description, content,
                            source_name, source_type, source_reliability,
                            score_relevance, score_popularity, score_recency, score_reliability,
                            status, url, author, published_at, created_at, reviewed_at,
                            duplicate_hash
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(topic.id),
                        topic.title,
                        topic.description,
                        topic.content[:_MAX_CONTENT_LENGTH],
                        topic.source.name,
                        topic.source.type.value,
                        topic.source.reliability,
                        topic.score.relevance,
                        topic.score.popularity,
                        topic.score.recency,
                        topic.score.source_reliability,
                        topic.status.value,
                        topic.url,
                        topic.author,
                        topic.published_at.isoformat() if topic.published_at else None,
                        topic.created_at.isoformat() if topic.created_at else None,
                        topic.reviewed_at.isoformat() if topic.reviewed_at else None,
                        topic.duplicate_hash,
                    ))
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise

    # ── Lectura ──────────────────────────────────────

    async def find_by_id(self, topic_id: UUID) -> Optional[ResearchTopic]:
        """Busca un topic por ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM research_topics WHERE id = ?",
                (str(topic_id),)
            ).fetchone()
            return self._row_to_topic(row) if row else None

    async def find_by_status(
        self, status: ResearchStatus, limit: int = 50
    ) -> list[ResearchTopic]:
        """Busca topics por estado, ordenados por score descendente."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM research_topics
                WHERE status = ?
                ORDER BY
                    (score_relevance * 0.35 + score_popularity * 0.25 +
                     score_recency * 0.25 + score_reliability * 0.15) DESC,
                    created_at DESC
                LIMIT ?
            """, (status.value, limit))
            return [self._row_to_topic(r) for r in rows.fetchall()]

    async def find_by_duplicate_hash(
        self, duplicate_hash: str
    ) -> list[ResearchTopic]:
        """Busca topics que compartan el mismo hash."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM research_topics WHERE duplicate_hash = ?",
                (duplicate_hash,)
            )
            return [self._row_to_topic(r) for r in rows.fetchall()]

    async def find_pending_review(
        self, limit: int = 20
    ) -> list[ResearchTopic]:
        """Busca topics pendientes de revisión, mejores scores primero."""
        return await self.find_by_status(
            ResearchStatus.PENDING_REVIEW, limit=limit
        )

    async def find_all(
        self, limit: int = 50, offset: int = 0
    ) -> list[ResearchTopic]:
        """Lista todos los topics ordenados por fecha descendente."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM research_topics
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            return [self._row_to_topic(r) for r in rows.fetchall()]

    async def count_by_status(self, status: ResearchStatus) -> int:
        """Cuenta topics en un estado dado."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM research_topics WHERE status = ?",
                (status.value,)
            ).fetchone()
            return row["cnt"] if row else 0

    async def delete(self, topic_id: UUID) -> None:
        """Elimina un topic por ID."""
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM research_topics WHERE id = ?",
                (str(topic_id),)
            )

    # ── Mappers ──────────────────────────────────────

    def _row_to_topic(self, row: sqlite3.Row) -> ResearchTopic:
        """Convierte una fila SQL → entidad ResearchTopic."""
        source = ResearchSource(
            name=row["source_name"],
            type=SourceType(row["source_type"]),
            reliability=row["source_reliability"],
        )

        score = ResearchScore(
            relevance=row["score_relevance"],
            popularity=row["score_popularity"],
            recency=row["score_recency"],
            source_reliability=row["score_reliability"],
        )

        return ResearchTopic(
            id=UUID(row["id"]),
            title=row["title"],
            description=row["description"],
            content=row["content"],
            source=source,
            score=score,
            status=ResearchStatus(row["status"]),
            url=row["url"],
            author=row["author"],
            published_at=self._parse_datetime(row["published_at"]),
            created_at=self._parse_datetime(row["created_at"]) or datetime.now(timezone.utc),
            reviewed_at=self._parse_datetime(row["reviewed_at"]),
            duplicate_hash=row["duplicate_hash"],
        )

    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        """Parsea string ISO → datetime."""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return None
