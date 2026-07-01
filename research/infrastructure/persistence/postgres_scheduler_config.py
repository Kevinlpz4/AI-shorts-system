"""
PostgresSchedulerConfig — Configuración del scheduler en PostgreSQL
====================================================================
Misma API que SchedulerConfig (SQLite), pero con SQLAlchemy + PostgreSQL.
"""
from __future__ import annotations

from typing import Optional

from infrastructure.persistence.database import SessionLocal
from infrastructure.persistence.models import SchedulerConfigModel


class PostgresSchedulerConfig:
    """
    Configuración persistente del scheduler sobre PostgreSQL.
    """

    def __init__(self):
        self._ensure_table()

    @staticmethod
    def _ensure_table() -> None:
        from infrastructure.persistence.database import ensure_tables
        ensure_tables()

    # ── CRUD interno ─────────────────────────────────

    def _get_config(self, key: str, default: str = "") -> str:
        with SessionLocal() as session:
            row = session.query(SchedulerConfigModel).filter(
                SchedulerConfigModel.key == key
            ).first()
            return row.value if row else default

    def _set_config(self, key: str, value: str) -> None:
        with SessionLocal() as session:
            session.merge(SchedulerConfigModel(key=key, value=value))
            session.commit()

    def _delete_config(self, key: str) -> None:
        with SessionLocal() as session:
            session.query(SchedulerConfigModel).filter(
                SchedulerConfigModel.key == key
            ).delete()
            session.commit()

    # ── API pública ──────────────────────────────────

    def get_interval(self) -> int:
        val = self._get_config("interval_minutes", "60")
        try:
            return max(1, int(val))
        except (ValueError, TypeError):
            return 60

    def set_interval(self, minutes: int) -> None:
        self._set_config("interval_minutes", str(max(1, minutes)))

    def is_enabled(self) -> bool:
        return self._get_config("enabled", "false").lower() == "true"

    def set_enabled(self, enabled: bool) -> None:
        self._set_config("enabled", "true" if enabled else "false")

    def get_queries(self) -> list[str]:
        val = self._get_config("queries", "tecnología,inteligencia artificial,ciencia")
        return [q.strip() for q in val.split(",") if q.strip()]

    def set_queries(self, queries: list[str]) -> None:
        self._set_config("queries", ",".join(queries))

    def get_last_run(self) -> Optional[str]:
        val = self._get_config("last_run", "")
        return val or None

    def set_last_run(self, timestamp: str) -> None:
        self._set_config("last_run", timestamp)

    def is_auto_generate_enabled(self) -> bool:
        return self._get_config("auto_generate_script", "false").lower() == "true"

    def set_auto_generate(self, enabled: bool) -> None:
        self._set_config("auto_generate_script", "true" if enabled else "false")

    def get_status(self) -> dict:
        return {
            "enabled": self.is_enabled(),
            "interval_minutes": self.get_interval(),
            "queries": self.get_queries(),
            "last_run": self.get_last_run(),
        }
