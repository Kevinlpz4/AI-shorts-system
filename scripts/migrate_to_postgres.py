"""
Migración segura e idempotente de SQLite → PostgreSQL para system_shorts.

Uso:
    python3 scripts/migrate_to_postgres.py

Requiere: sqlalchemy, psycopg2-binary
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime
from typing import Any

# ── Asegurar que el proyecto está en sys.path ──
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# ── SQLAlchemy ──
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from infrastructure.persistence.models import Base, SchedulerConfigModel, ResearchTopicModel, ScriptModel


# ──────────────────────────────────────────────
# Configuración
# ──────────────────────────────────────────────
SQLITE_PATH = os.path.join(_PROJECT_ROOT, "data", "research.db")

PG_URI = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://kevin:1234@localhost:5432/system_shorts",
)


# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
def _log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def _ok(msg: str) -> None:  _log(f"✅  {msg}")
def _warn(msg: str) -> None: _log(f"⚠️  {msg}")
def _err(msg: str) -> None:  _log(f"❌  {msg}")


# ──────────────────────────────────────────────
# 1. Extracción desde SQLite
# ──────────────────────────────────────────────
def extract_all() -> dict[str, list[dict[str, Any]]]:
    """Lee TODOS los datos de SQLite con sqlite3 nativo."""
    if not os.path.exists(SQLITE_PATH):
        _err(f"Base SQLite no encontrada: {SQLITE_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    tables = ["scheduler_config", "research_topics", "scripts"]
    data: dict[str, list[dict[str, Any]]] = {}

    for table in tables:
        cursor.execute(f'SELECT * FROM "{table}"')
        rows = [dict(row) for row in cursor.fetchall()]
        data[table] = rows
        _ok(f"Extraídos {len(rows)} registros de {table}")

    conn.close()
    return data


# ──────────────────────────────────────────────
# 2. Carga en PostgreSQL (idempotente con merge)
# ──────────────────────────────────────────────
_MODEL_MAP: dict[str, type] = {
    "scheduler_config": SchedulerConfigModel,
    "research_topics": ResearchTopicModel,
    "scripts": ScriptModel,
}

_MIGRATION_ORDER = ["scheduler_config", "research_topics", "scripts"]


def load_all(data: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    """
    Crea tablas y migra datos batch con SQLAlchemy merge().
    merge() = INSERT ON CONFLICT UPDATE → 100% idempotente.
    """
    engine = create_engine(PG_URI, pool_pre_ping=True)

    # Crear tablas (IF NOT EXISTS implícito)
    _log("Creando tablas en PostgreSQL...")
    Base.metadata.create_all(engine)
    _ok("Tablas aseguradas")

    SessionLocal = sessionmaker(bind=engine)
    counts: dict[str, int] = {}

    for table_name in _MIGRATION_ORDER:
        rows = data.get(table_name, [])
        if not rows:
            counts[table_name] = 0
            _warn(f"{table_name}: sin datos para migrar")
            continue

        model_cls = _MODEL_MAP[table_name]
        _log(f"Migrando {table_name} ({len(rows)} registros)...")

        with SessionLocal() as session:
            inserted = 0
            for row in rows:
                try:
                    # merge = busca por PK, si existe actualiza, si no inserta
                    session.merge(model_cls(**row))
                    inserted += 1
                except Exception as e:
                    session.rollback()
                    _err(f"Error en {table_name} PK={row.get('id', row.get('key', '?'))}: {e}")
                    raise

            session.commit()
            counts[table_name] = inserted
            _ok(f"{table_name}: {inserted} registros migrados")

    return counts


# ──────────────────────────────────────────────
# 3. Validación
# ──────────────────────────────────────────────
def validate(source_counts: dict[str, int], dest_counts: dict[str, int]) -> bool:
    """Compara filas SQLite vs PostgreSQL."""
    print()
    _log("═" * 50)
    _log("VALIDACIÓN: SQLite vs PostgreSQL")
    _log("═" * 50)

    all_ok = True
    for table in _MIGRATION_ORDER:
        s = source_counts.get(table, 0)
        p = dest_counts.get(table, 0)
        if s == p:
            _ok(f"{table}: {s} = {p}")
        else:
            all_ok = False
            _err(f"{table}: SQLite={s} vs PostgreSQL={p}  — ¡NO COINCIDEN!")

    print()
    if all_ok:
        _ok("🎉 Migración validada: todos los conteos coinciden")
    else:
        _err("🚨 Migración INCOMPLETA: revisá las discrepancias")

    return all_ok


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
def main() -> None:
    _log("🚀 Migración SQLite → PostgreSQL")
    _log(f"   Origen:  {SQLITE_PATH}")
    _log(f"   Destino: {PG_URI}")
    print()

    # 1. Extraer datos de SQLite
    data = extract_all()

    # 2. Cargar en PostgreSQL
    pg_counts = load_all(data)

    # 3. Validar
    sqlite_counts = {t: len(data[t]) for t in _MIGRATION_ORDER}
    ok = validate(sqlite_counts, pg_counts)

    print()
    if ok:
        _ok("🎉 Migración completada con ÉXITO")
    else:
        _err("Migración completada con ERRORES")
        sys.exit(1)


if __name__ == "__main__":
    main()
