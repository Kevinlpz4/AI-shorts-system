"""
Alembic env.py — Migration environment for Learning BC.

Configured to work with the Learning BC models.
"""
from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure src/ is on the path for model imports
_src_path = str(Path(__file__).resolve().parent.parent.parent.parent)
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from learning.persistence.models.base import Base  # noqa: E402
from learning.persistence.models import (  # noqa: E402
    feedback,  # noqa: F401
    learning_signal,  # noqa: F401
    source_quality,  # noqa: F401
    learning_model,  # noqa: F401
    knowledge_snapshot,  # noqa: F401
    knowledge_artifact,  # noqa: F401
    news_features,  # noqa: F401
    dataset_metadata,  # noqa: F401
    training_snapshot,  # noqa: F401
)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
