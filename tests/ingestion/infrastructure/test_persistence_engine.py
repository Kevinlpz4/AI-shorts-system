"""
Tests for engine factory (create_engine / create_session_factory).

Validates:
  - create_engine accepts any URL and returns an Engine
  - No dialect-specific if/else in the implementation
  - create_session_factory binds and returns a sessionmaker
  - Basic roundtrip (create tables, insert, query)
  - Parametrized engine_factory pattern (extensible to PostgreSQL)
"""

import sys
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker

# Ensure src/ is on sys.path
_src_path = str(Path(__file__).resolve().parent.parent.parent.parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from ingestion.infrastructure.persistence import PersistenceBase, create_engine, create_session_factory

# ── Test Model (used in parametrized engine factory tests) ─────────────────

class ParamModel(PersistenceBase):
    """Simple model for engine roundtrip tests."""
    __tablename__ = "param_test"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


class TestCreateEngine:
    """Tests for create_engine()."""

    def test_returns_engine(self):
        """create_engine debe retornar una instancia de Engine."""
        engine = create_engine("sqlite:///:memory:")
        assert isinstance(engine, Engine)
        engine.dispose()

    def test_accepts_sqlite_memory_url(self):
        """Debe aceptar sqlite:///:memory:."""
        engine = create_engine("sqlite:///:memory:")
        # Prove it works by executing a query
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 AS x")).scalar()
            assert result == 1
        engine.dispose()

    def test_accepts_sqlite_file_url(self, tmp_path):
        """Debe aceptar sqlite+pysqlite:///path/to/file.db."""
        db_path = tmp_path / "test_engine.db"
        engine = create_engine(f"sqlite+pysqlite:///{db_path}")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 AS x")).scalar()
            assert result == 1
        engine.dispose()
        assert db_path.exists()

    def test_accepts_extra_kwargs(self):
        """Debe aceptar kwargs adicionales (como echo)."""
        import io
        import logging

        # Capture log output
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger = logging.getLogger("sqlalchemy.engine")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        engine = create_engine("sqlite:///:memory:", echo=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()

        logger.removeHandler(handler)
        output = stream.getvalue()
        assert "SELECT 1" in output, f"Expected SQL log, got: {output}"

    def test_no_dialect_specific_logic(self):
        """La implementación no debe tener if/else por dialecto.

        Este test lee el código fuente para verificar que no hay
        condicionales basados en 'sqlite', 'postgres', etc.
        """
        import ast

        engine_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "src"
            / "ingestion"
            / "infrastructure"
            / "persistence"
            / "engine.py"
        )
        source = engine_path.read_text()
        tree = ast.parse(source)

        class DialectCheck(ast.NodeVisitor):
            def __init__(self):
                self.found_dialect_ifs: list = []

            def visit_If(self, node):
                # Check if the 'if' compares against a string like 'sqlite'
                if isinstance(node.test, ast.Compare):
                    for comparator in node.test.comparators:
                        if isinstance(comparator, ast.Constant) and isinstance(
                            comparator.value, str
                        ):
                            dialect_keywords = {
                                "sqlite", "postgres", "postgresql",
                                "mysql", "oracle", "mssql",
                            }
                            if comparator.value.lower() in dialect_keywords:
                                self.found_dialect_ifs.append(
                                    (node.lineno, comparator.value)
                                )
                self.generic_visit(node)

        checker = DialectCheck()
        checker.visit(tree)

        assert not checker.found_dialect_ifs, (
            f"Engine factory should not have dialect-specific if/else. "
            f"Found at lines: {checker.found_dialect_ifs}"
        )

    def test_engine_is_reusable(self):
        """El mismo engine debe poder abrir múltiples conexiones."""
        engine = create_engine("sqlite:///:memory:")
        with engine.connect() as conn1:
            conn1.execute(text("CREATE TABLE t (x INTEGER)"))
            conn1.execute(text("INSERT INTO t VALUES (42)"))
            conn1.commit()

        with engine.connect() as conn2:
            result = conn2.execute(text("SELECT x FROM t")).scalar()
            assert result == 42

        engine.dispose()

    def test_dispose_cleans_up(self):
        """engine.dispose() debe liberar recursos sin error."""
        engine = create_engine("sqlite:///:memory:")
        engine.connect().close()
        # Should not raise
        engine.dispose()


class TestCreateSessionFactory:
    """Tests for create_session_factory()."""

    def test_returns_sessionmaker(self):
        """create_session_factory debe retornar un sessionmaker."""
        engine = create_engine("sqlite:///:memory:")
        factory = create_session_factory(engine)
        assert isinstance(factory, sessionmaker)
        engine.dispose()

    def test_sessionmaker_binds_to_engine(self, sqlite_engine):
        """El sessionmaker debe estar vinculado al engine."""
        factory = create_session_factory(sqlite_engine)
        session = factory()
        assert session.bind is sqlite_engine
        session.close()

    def test_session_is_working(self, sqlite_engine):
        """La sesión debe poder ejecutar consultas."""
        factory = create_session_factory(sqlite_engine)
        with factory() as session:
            result = session.execute(text("SELECT 1 AS x")).scalar()
            assert result == 1

    def test_expire_on_commit_defaults_to_false(self):
        """expire_on_commit debe ser False por defecto."""
        engine = create_engine("sqlite:///:memory:")
        factory = create_session_factory(engine)
        # Create a session and check the default
        session = factory()
        assert session.expire_on_commit is False
        session.close()
        engine.dispose()

    def test_expire_on_commit_can_be_overridden(self):
        """expire_on_commit debe ser overridable."""
        engine = create_engine("sqlite:///:memory:")
        factory = create_session_factory(engine, expire_on_commit=True)
        session = factory()
        assert session.expire_on_commit is True
        session.close()
        engine.dispose()


class TestRoundtrip:
    """End-to-end test: engine + session factory + model."""

    def test_insert_and_select(self, sqlite_engine):
        """Insertar un registro y leerlo debe funcionar."""
        factory = create_session_factory(sqlite_engine)

        with factory.begin() as session:
            session.execute(text("CREATE TABLE roundtrip (id INTEGER PRIMARY KEY, val TEXT)"))
            session.execute(
                text("INSERT INTO roundtrip (id, val) VALUES (1, 'hello')")
            )

        with factory() as session:
            result = session.execute(
                text("SELECT val FROM roundtrip WHERE id = 1")
            ).scalar()
            assert result == "hello"

    def test_rollback_isolates_tests(self, sqlite_engine, sqlite_session):
        """Test fixture rollback debe aislar datos entre tests."""
        # This test assumes previous test ran and committed
        # But sqlite_session rolls back after each test
        result = sqlite_session.execute(
            text(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name='roundtrip'"
            )
        ).scalar()
        # roundtrip table should NOT exist because previous test
        # used sqlite_engine directly (different connection)
        # or if it used sqlite_session, rollback removed it
        assert result is None or result is False, (
            "Previous test data should not leak. "
            "If this fails, test isolation is broken."
        )


# ══════════════════════════════════════════════════════════════════════════════
# Parametrized Engine Factory (cross-dialect readiness)
# ══════════════════════════════════════════════════════════════════════════════

class TestParametrizedEngineFactory:
    """Tests that use the parametrized ``engine_factory`` fixture.

    These tests will automatically run against all registered engine
    factories (SQLite today, PostgreSQL in the future).
    """

    def test_factory_returns_engine(self, engine_factory):
        """engine_factory() debe retornar un Engine."""
        engine = engine_factory()
        assert isinstance(engine, Engine)
        engine.dispose()

    def test_factory_produces_working_engine(self, engine_factory):
        """El engine producido debe poder ejecutar SELECT 1."""
        engine = engine_factory()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 AS x")).scalar()
            assert result == 1
        engine.dispose()

    def test_create_tables_and_query(self, engine_factory):
        """Crear tabla + insert + select debe funcionar."""
        engine = engine_factory()

        PersistenceBase.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        with Session.begin() as session:
            session.execute(text("INSERT INTO param_test (id, name) VALUES (1, 'test')"))

        with Session() as session:
            row = session.execute(
                text("SELECT name FROM param_test WHERE id = 1")
            ).scalar()
            assert row == "test"

        engine.dispose()
