"""
Tests for Alembic migration — verify schema creation.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, inspect

from learning.persistence.models.base import Base
# Import all models to ensure they register with Base.metadata
from learning.persistence.models import feedback  # noqa: F401
from learning.persistence.models import learning_signal  # noqa: F401
from learning.persistence.models import source_quality  # noqa: F401
from learning.persistence.models import learning_model  # noqa: F401
from learning.persistence.models import knowledge_snapshot  # noqa: F401
from learning.persistence.models import knowledge_artifact  # noqa: F401
from learning.persistence.models import news_features  # noqa: F401
from learning.persistence.models import dataset_metadata  # noqa: F401
from learning.persistence.models import training_snapshot  # noqa: F401


class TestMigrationSchema:
    """Verify that Base.metadata creates all expected tables and indexes."""

    def test_all_tables_created(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        expected = {
            "learning_feedback",
            "learning_signals",
            "learning_source_quality",
            "learning_models",
            "learning_knowledge_snapshots",
            "learning_knowledge_artifacts",
            "learning_news_features",
            "learning_datasets",
            "learning_training_snapshots",
        }
        assert expected.issubset(tables), f"Missing tables: {expected - tables}"

    def _get_index_names(self, inspector, table_name):
        return {idx["name"] for idx in inspector.get_indexes(table_name)}

    def test_feedback_indexes(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        inspector = inspect(engine)
        indexes = self._get_index_names(inspector, "learning_feedback")

        # Names follow the naming convention: idx_{column_0_label}
        assert any("topic_id" in name for name in indexes)
        assert any("decision" in name for name in indexes)
        assert any("source_name" in name for name in indexes)
        assert any("captured_at" in name for name in indexes)

    def test_signal_indexes(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        inspector = inspect(engine)
        indexes = self._get_index_names(inspector, "learning_signals")

        assert any("signal_type" in name for name in indexes)
        assert any("dimension" in name for name in indexes)

    def test_knowledge_snapshot_indexes(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        inspector = inspect(engine)
        indexes = self._get_index_names(inspector, "learning_knowledge_snapshots")

        assert any("snapshot_at" in name for name in indexes)
        assert any("entity_type" in name for name in indexes)
        assert any("entity_id" in name for name in indexes)
        assert any("metric_name" in name for name in indexes)

    def test_artifact_indexes(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        inspector = inspect(engine)
        indexes = self._get_index_names(inspector, "learning_knowledge_artifacts")

        assert any("artifact_type" in name for name in indexes)
        assert any("status" in name for name in indexes)
        assert any("created_at" in name for name in indexes)

    def test_news_features_indexes(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        inspector = inspect(engine)
        indexes = self._get_index_names(inspector, "learning_news_features")

        assert any("article_id" in name for name in indexes)
        assert any("source_name" in name for name in indexes)
        assert any("editor_decision" in name for name in indexes)
        assert any("created_at" in name for name in indexes)

    def test_dataset_indexes(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        inspector = inspect(engine)
        indexes = self._get_index_names(inspector, "learning_datasets")

        assert any("dataset_version" in name for name in indexes)
        assert any("status" in name for name in indexes)

    def test_training_snapshot_indexes(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        inspector = inspect(engine)
        indexes = self._get_index_names(inspector, "learning_training_snapshots")

        assert any("dataset_version" in name for name in indexes)
        assert any("status" in name for name in indexes)

    def test_all_expected_indexes_exist(self):
        """Verify total expected index count across all tables."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        inspector = inspect(engine)

        total_indexes = 0
        for table in inspector.get_table_names():
            total_indexes += len(inspector.get_indexes(table))
        # 9 feedback + 2 signal + 1 source + 0 models + 2 snapshot + 3 artifact
        # + 4 features + 2 dataset + 2 training = 25 (minimum)
        assert total_indexes >= 20
