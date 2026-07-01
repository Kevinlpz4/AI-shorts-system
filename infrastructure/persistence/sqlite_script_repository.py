"""
SQLiteScriptRepository — Implementación concreta de ScriptRepository (DEPRECATED)
==================================================================================
⚠️  DEPRECATED: Usar PostgresScriptRepository en su lugar.
    Se mantiene para tests y referencia.

Guarda Script entities en SQLite (misma DB que research_topics).

Trade-offs:
  + Zero dependencies (sqlite3 es built-in de Python)
  + Rápido para desarrollo y single-user
  - No es async (bloqueante, pero ok para CLI/API)
  - No escala a multi-proceso

Sigue el mismo patrón que SQLiteResearchRepository.
"""

import sqlite3
from datetime import datetime, timezone
from typing import Optional, Sequence

from domain.entities.script import Script
from domain.value_objects.duration import Duration


class SQLiteScriptRepository:
    """
    Repositorio SQLite para Script entities.

    No hereda de ScriptRepository explícitamente (Protocol match).
    Usa la misma DB que research_topics para mantener la FK constraint.
    """

    def __init__(self, db_path: str = "research.db"):
        self._db_path = db_path
        self._ensure_table()

    # ── Setup ────────────────────────────────────────

    def _get_connection(self) -> sqlite3.Connection:
        """Obtiene conexión SQLite."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _ensure_table(self) -> None:
        """Crea la tabla scripts si no existe."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scripts (
                    id TEXT PRIMARY KEY,
                    topic_id TEXT UNIQUE NOT NULL,
                    hook TEXT NOT NULL DEFAULT '',
                    body TEXT NOT NULL DEFAULT '',
                    cta TEXT NOT NULL DEFAULT '',
                    duration INTEGER NOT NULL DEFAULT 45,
                    tone TEXT NOT NULL DEFAULT 'educational',
                    format TEXT NOT NULL DEFAULT 'story',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (topic_id) REFERENCES research_topics(id) ON DELETE CASCADE
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_scripts_topic_id
                ON scripts(topic_id)
            """)

    # ── Persistencia ─────────────────────────────────

    async def save(self, script: Script) -> None:
        """Guarda un script (INSERT OR REPLACE)."""
        with self._get_connection() as conn:
            now = datetime.now(timezone.utc).isoformat()
            conn.execute("""
                INSERT OR REPLACE INTO scripts (
                    id, topic_id, hook, body, cta,
                    duration, tone, format, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                script.id,
                script.topic_id,
                script.hook,
                script.body,
                script.cta,
                int(script.duration),
                script.tone,
                script.format,
                script.created_at or now,
                now,
            ))

    # ── Lectura ──────────────────────────────────────

    async def find_by_topic_id(self, topic_id: str) -> Optional[Script]:
        """Busca un script por topic_id."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM scripts WHERE topic_id = ?",
                (topic_id,)
            ).fetchone()
            return self._row_to_script(row) if row else None

    async def find_all(
        self, limit: int = 50, offset: int = 0
    ) -> Sequence[Script]:
        """Lista todos los scripts ordenados por fecha descendente."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM scripts
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset)).fetchall()
            return [self._row_to_script(r) for r in rows]

    async def count_all(self) -> int:
        """Cuenta el total de scripts."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM scripts"
            ).fetchone()
            return row["cnt"] if row else 0

    # ── Eliminación ──────────────────────────────────

    async def delete_by_topic_id(self, topic_id: str) -> None:
        """Elimina un script por topic_id."""
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM scripts WHERE topic_id = ?",
                (topic_id,)
            )

    # ── Mappers ──────────────────────────────────────

    @staticmethod
    def _row_to_script(row: sqlite3.Row) -> Script:
        """Convierte una fila SQL → entidad Script."""
        return Script(
            id=row["id"],
            topic_id=row["topic_id"],
            hook=row["hook"],
            body=row["body"],
            cta=row["cta"],
            duration=Duration(row["duration"]),
            tone=row["tone"],
            format=row["format"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
