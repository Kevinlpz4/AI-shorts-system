"""
Tests for Runtime persistence models — SQLAlchemy ORM.

Covers:
- ValidationMetricsModel creation and query
- DatasetVersionModel creation and query
- RuntimeConfigurationModel creation and query
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

pytest.importorskip("sqlalchemy")


from runtime.persistence.engine import RuntimeEngine  # noqa: E402
from runtime.persistence.models import (  # noqa: E402
    DatasetVersionModel,
    RuntimeConfigurationModel,
    ValidationMetricsModel,
)


@pytest.fixture
def engine() -> RuntimeEngine:
    """Create an in-memory SQLite engine with tables."""
    eng = RuntimeEngine("sqlite:///:memory:")
    eng.create_tables()
    return eng


class TestValidationMetricsModel:
    """Tests for ValidationMetricsModel ORM mapping."""

    def test_create_and_query(self, engine: RuntimeEngine) -> None:
        """Insert and retrieve a ValidationMetricsModel."""
        session = engine.get_session()
        try:
            model = ValidationMetricsModel(
                metric_name="accuracy",
                metric_value=0.95,
                window_days=7,
                algorithm_version="v1.0",
            )
            session.add(model)
            session.commit()

            result = session.query(ValidationMetricsModel).first()
            assert result is not None
            assert result.metric_name == "accuracy"
            assert result.metric_value == 0.95
            assert result.window_days == 7
            assert result.algorithm_version == "v1.0"
            assert result.id is not None
        finally:
            session.close()

    def test_metadata_json_default(self, engine: RuntimeEngine) -> None:
        """metadata_json defaults to empty dict."""
        session = engine.get_session()
        try:
            model = ValidationMetricsModel(
                metric_name="recall",
                metric_value=0.88,
                window_days=30,
                algorithm_version="v1.0",
            )
            session.add(model)
            session.commit()

            result = session.query(ValidationMetricsModel).first()
            assert result.metadata_json == {}
        finally:
            session.close()


class TestDatasetVersionModel:
    """Tests for DatasetVersionModel ORM mapping."""

    def test_create_and_query(self, engine: RuntimeEngine) -> None:
        """Insert and retrieve a DatasetVersionModel."""
        session = engine.get_session()
        try:
            now = datetime.now(timezone.utc)
            model = DatasetVersionModel(
                version="v2026.07.001",
                snapshot_date=now,
                total_samples=1000,
                labeled_samples=800,
                checksum="abc123def456",
            )
            session.add(model)
            session.commit()

            result = session.query(DatasetVersionModel).first()
            assert result is not None
            assert result.version == "v2026.07.001"
            assert result.total_samples == 1000
            assert result.labeled_samples == 800
            assert result.checksum == "abc123def456"
        finally:
            session.close()

    def test_unique_version_constraint(self, engine: RuntimeEngine) -> None:
        """Duplicate version raises IntegrityError."""
        session = engine.get_session()
        try:
            now = datetime.now(timezone.utc)
            m1 = DatasetVersionModel(
                version="v1",
                snapshot_date=now,
                checksum="a",
            )
            m2 = DatasetVersionModel(
                version="v1",
                snapshot_date=now,
                checksum="b",
            )
            session.add(m1)
            session.commit()

            session.add(m2)
            with pytest.raises(Exception):  # IntegrityError
                session.commit()
        finally:
            session.close()


class TestRuntimeConfigurationModel:
    """Tests for RuntimeConfigurationModel ORM mapping."""

    def test_create_and_query(self, engine: RuntimeEngine) -> None:
        """Insert and retrieve a RuntimeConfigurationModel."""
        session = engine.get_session()
        try:
            model = RuntimeConfigurationModel(
                key="pipeline.interval_minutes",
                value="30",
            )
            session.add(model)
            session.commit()

            result = session.query(RuntimeConfigurationModel).first()
            assert result is not None
            assert result.key == "pipeline.interval_minutes"
            assert result.value == "30"
            assert result.id is not None
        finally:
            session.close()

    def test_unique_key_constraint(self, engine: RuntimeEngine) -> None:
        """Duplicate key raises IntegrityError."""
        session = engine.get_session()
        try:
            m1 = RuntimeConfigurationModel(key="k1", value="v1")
            m2 = RuntimeConfigurationModel(key="k1", value="v2")
            session.add(m1)
            session.commit()

            session.add(m2)
            with pytest.raises(Exception):  # IntegrityError
                session.commit()
        finally:
            session.close()
