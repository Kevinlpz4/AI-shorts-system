"""
PostgresScriptRepository — Implementación SQLAlchemy de ScriptRepository
=======================================================================
Implementa el Protocol ScriptRepository usando SQLAlchemy + PostgreSQL.

Misma interfaz que SQLiteScriptRepository, pero con sesiones SQLAlchemy.
"""
from __future__ import annotations

from typing import Optional, Sequence

from domain.entities.script import Script
from domain.value_objects.duration import Duration
from infrastructure.persistence.database import SessionLocal
from infrastructure.persistence.models import ScriptModel


class PostgresScriptRepository:
    """
    Repositorio PostgreSQL para Script entities.

    No hereda de ScriptRepository explícitamente (Protocol match).
    """

    def __init__(self):
        self._ensure_table()

    @staticmethod
    def _ensure_table() -> None:
        """Asegura que la tabla existe (idempotente)."""
        from infrastructure.persistence.database import ensure_tables
        ensure_tables()

    # ── Persistencia ─────────────────────────────────

    async def save(self, script: Script) -> None:
        """Guarda un script (merge = insert or update)."""
        with SessionLocal() as session:
            row = ScriptModel(
                id=script.id,
                topic_id=script.topic_id,
                hook=script.hook,
                body=script.body,
                cta=script.cta,
                duration=int(script.duration),
                tone=script.tone,
                format=script.format,
                created_at=script.created_at,
                updated_at=script.updated_at,
            )
            session.merge(row)
            session.commit()

    # ── Lectura ──────────────────────────────────────

    async def find_by_topic_id(self, topic_id: str) -> Optional[Script]:
        """Busca un script por topic_id."""
        with SessionLocal() as session:
            row = session.query(ScriptModel).filter(
                ScriptModel.topic_id == topic_id
            ).first()
            return self._row_to_script(row) if row else None

    async def find_all(
        self, limit: int = 50, offset: int = 0
    ) -> Sequence[Script]:
        """Lista todos los scripts ordenados por fecha descendente."""
        with SessionLocal() as session:
            rows = (
                session.query(ScriptModel)
                .order_by(ScriptModel.created_at.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )
            return [self._row_to_script(r) for r in rows]

    async def count_all(self) -> int:
        """Cuenta el total de scripts."""
        with SessionLocal() as session:
            return session.query(ScriptModel).count()

    # ── Eliminación ──────────────────────────────────

    async def delete_by_topic_id(self, topic_id: str) -> None:
        """Elimina un script por topic_id."""
        with SessionLocal() as session:
            session.query(ScriptModel).filter(
                ScriptModel.topic_id == topic_id
            ).delete()
            session.commit()

    # ── Mappers ──────────────────────────────────────

    @staticmethod
    def _row_to_script(row: ScriptModel) -> Script:
        """Convierte un modelo SQLAlchemy → entidad Script."""
        return Script(
            id=row.id,
            topic_id=row.topic_id,
            hook=row.hook,
            body=row.body,
            cta=row.cta,
            duration=Duration(row.duration),
            tone=row.tone,
            format=row.format,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
