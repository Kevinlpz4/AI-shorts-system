"""
Database — Engine y session factory para PostgreSQL con SQLAlchemy.

Uso:
    from infrastructure.persistence.database import SessionLocal

    with SessionLocal() as session:
        rows = session.query(Model).all()

Para async (futuro):
    cambiar a AsyncSession + asyncpg
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from infrastructure.persistence.models import Base

# ── Engine ──────────────────────────────────────────
DATABASE_URL = str(settings.DATABASE_URL)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,        # verifica conexión antes de usar
    pool_size=5,               # conexiones simultáneas
    max_overflow=10,           # conexiones extra bajo demanda
    echo=False,                # True para debug SQL
)

# ── Session factory ─────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def ensure_tables() -> None:
    """Crea las tablas si no existen (idempotente)."""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Dependency injection helper."""
    with SessionLocal() as session:
        yield session
