"""
Tests for RuntimeEngine — SQLAlchemy engine factory.

Covers:
- Engine construction
- Table creation
- Session creation
"""
from __future__ import annotations

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy import text  # noqa: E402

from runtime.persistence.engine import RuntimeEngine


class TestRuntimeEngine:
    """Tests for RuntimeEngine."""

    def test_construction(self) -> None:
        """RuntimeEngine accepts a database URL."""
        engine = RuntimeEngine("sqlite:///:memory:")

        assert engine is not None

    def test_create_tables(self) -> None:
        """create_tables creates all tables from Base metadata."""
        engine = RuntimeEngine("sqlite:///:memory:")
        engine.create_tables()

        # Verify tables exist by querying sqlite_master
        with engine.get_session() as session:
            result = session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            table_names = {row[0] for row in result.fetchall()}
            assert "runtime_validation_metrics" in table_names
            assert "runtime_dataset_versions" in table_names
            assert "runtime_configuration" in table_names

    def test_get_session(self) -> None:
        """get_session returns a usable SQLAlchemy session."""
        engine = RuntimeEngine("sqlite:///:memory:")
        engine.create_tables()

        session = engine.get_session()
        try:
            assert session is not None
            # Basic smoke test — execute a raw query
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1
        finally:
            session.close()
