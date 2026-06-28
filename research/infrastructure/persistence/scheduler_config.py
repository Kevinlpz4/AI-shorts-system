"""
SchedulerConfig — Persistencia de configuración del scheduler en SQLite
========================================================================
Guarda y recupera la configuración del scheduler de descubrimiento automático.

Usa una tabla key-value en la misma DB que el repositorio de research.
No contiene lógica de negocio — solo persistencia.

Tabla: scheduler_config
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
"""
import sqlite3
from typing import Optional


class SchedulerConfig:
    """
    Configuración persistente del scheduler.

    Uses same DB as SQLiteResearchRepository, separate table.
    """

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._ensure_table()

    # ── Setup ────────────────────────────────────────

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _ensure_table(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scheduler_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

    # ── CRUD ─────────────────────────────────────────

    def _get_config(self, key: str, default: str = "") -> str:
        """Obtiene un valor de configuración."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT value FROM scheduler_config WHERE key = ?",
                (key,)
            ).fetchone()
            return row["value"] if row else default

    def _set_config(self, key: str, value: str) -> None:
        """Guarda un valor de configuración (upsert)."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO scheduler_config (key, value)
                VALUES (?, ?)
            """, (key, value))

    def _delete_config(self, key: str) -> None:
        """Elimina un valor de configuración."""
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM scheduler_config WHERE key = ?",
                (key,)
            )

    # ── API pública ──────────────────────────────────

    def get_interval(self) -> int:
        """Intervalo en minutos entre ejecuciones."""
        val = self._get_config("interval_minutes", "60")
        try:
            return max(1, int(val))
        except (ValueError, TypeError):
            return 60

    def set_interval(self, minutes: int) -> None:
        """Configura el intervalo en minutos."""
        self._set_config("interval_minutes", str(max(1, minutes)))

    def is_enabled(self) -> bool:
        """Si el scheduler está habilitado."""
        return self._get_config("enabled", "false").lower() == "true"

    def set_enabled(self, enabled: bool) -> None:
        """Habilita/deshabilita el scheduler."""
        self._set_config("enabled", "true" if enabled else "false")

    def get_queries(self) -> list[str]:
        """Lista de queries a ejecutar en cada ciclo."""
        val = self._get_config("queries", "tecnología,inteligencia artificial,ciencia")
        return [q.strip() for q in val.split(",") if q.strip()]

    def set_queries(self, queries: list[str]) -> None:
        """Configura las queries del scheduler."""
        self._set_config("queries", ",".join(queries))

    def get_last_run(self) -> Optional[str]:
        """Timestamp ISO del último ciclo ejecutado."""
        val = self._get_config("last_run", "")
        return val or None

    def set_last_run(self, timestamp: str) -> None:
        """Registra el timestamp del último ciclo."""
        self._set_config("last_run", timestamp)

    def get_status(self) -> dict:
        """Retorna estado completo del scheduler."""
        return {
            "enabled": self.is_enabled(),
            "interval_minutes": self.get_interval(),
            "queries": self.get_queries(),
            "last_run": self.get_last_run(),
        }
