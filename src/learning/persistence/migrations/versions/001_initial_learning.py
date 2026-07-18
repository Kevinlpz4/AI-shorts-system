"""Initial Learning BC schema — all tables with indexes.

Revision ID: 001_initial_learning
Revises: None
Create Date: 2026-07-18
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_initial_learning"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── learning_feedback ──────────────────────────────────────────────
    op.create_table(
        "learning_feedback",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("topic_id", sa.String(255), nullable=False),
        sa.Column("decision", sa.String(50), nullable=False),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("feature_snapshot_json", sa.Text, nullable=False),
        sa.Column("source_name", sa.String(255), nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("score_snapshot_json", sa.Text, nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
    )
    op.create_index("idx_feedback_topic_id", "learning_feedback", ["topic_id"])
    op.create_index("idx_feedback_decision", "learning_feedback", ["decision"])
    op.create_index("idx_feedback_source_name", "learning_feedback", ["source_name"])
    op.create_index("idx_feedback_captured_at", "learning_feedback", ["captured_at"])

    # ── learning_signals ───────────────────────────────────────────────
    op.create_table(
        "learning_signals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("signal_type", sa.String(50), nullable=False),
        sa.Column("dimension", sa.String(255), nullable=False),
        sa.Column("strength_json", sa.Text, nullable=False),
        sa.Column("sample_size", sa.Integer, nullable=False, server_default="0"),
        sa.Column("approval_rate", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("window_json", sa.Text, nullable=False),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
    )
    op.create_index("idx_signal_type", "learning_signals", ["signal_type"])
    op.create_index("idx_signal_dimension", "learning_signals", ["dimension"])

    # ── learning_source_quality ────────────────────────────────────────
    op.create_table(
        "learning_source_quality",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_name", sa.String(255), nullable=False, unique=True),
        sa.Column("total_decisions", sa.Integer, nullable=False, server_default="0"),
        sa.Column("approved_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("rejected_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("auto_approved_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("auto_rejected_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("overridden_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("approval_rate", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("keywords_json", sa.Text, nullable=False, server_default="{}"),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
    )
    op.create_index("idx_source_name", "learning_source_quality", ["source_name"])

    # ── learning_models ────────────────────────────────────────────────
    op.create_table(
        "learning_models",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("algorithm_version_str", sa.String(20), nullable=False),
        sa.Column("weights_json", sa.Text, nullable=False),
        sa.Column("minimum_confidence", sa.Float, nullable=False, server_default="0.5"),
        sa.Column("minimum_sample_size", sa.Integer, nullable=False, server_default="10"),
        sa.Column("active_rules_json", sa.Text, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
    )

    # ── learning_knowledge_snapshots (append-only) ─────────────────────
    op.create_table(
        "learning_knowledge_snapshots",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(255), nullable=False),
        sa.Column("metric_name", sa.String(100), nullable=False),
        sa.Column("metric_value", sa.Float, nullable=False),
        sa.Column("sample_size", sa.Integer, nullable=False, server_default="0"),
        sa.Column("snapshot_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.Text, nullable=False, server_default="{}"),
    )
    op.create_index(
        "idx_snapshot_entity",
        "learning_knowledge_snapshots",
        ["entity_type", "entity_id", "metric_name"],
    )
    op.create_index("idx_snapshot_at", "learning_knowledge_snapshots", ["snapshot_at"])

    # ── learning_knowledge_artifacts ───────────────────────────────────
    op.create_table(
        "learning_knowledge_artifacts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("artifact_type", sa.String(20), nullable=False),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("source_dataset", sa.String(255), nullable=False, server_default=""),
        sa.Column("algorithm_version", sa.String(20), nullable=False, server_default=""),
        sa.Column("feature_version", sa.String(20), nullable=False, server_default=""),
        sa.Column("checksum", sa.String(255), nullable=False, server_default=""),
        sa.Column("metadata_json", sa.Text, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("version_int", sa.Integer, nullable=False, server_default="1"),
    )
    op.create_index("idx_artifact_type", "learning_knowledge_artifacts", ["artifact_type"])
    op.create_index("idx_artifact_status", "learning_knowledge_artifacts", ["status"])
    op.create_index("idx_artifact_created_at", "learning_knowledge_artifacts", ["created_at"])

    # ── learning_news_features (Feature Store) ─────────────────────────
    op.create_table(
        "learning_news_features",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("article_id", sa.String(255), nullable=False, unique=True),
        sa.Column("source_name", sa.String(255), nullable=False),
        sa.Column("title", sa.Text, nullable=False, server_default=""),
        sa.Column("source_quality", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("keyword_strength", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("freshness", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("duplicates", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("topic_strength", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("category_strength", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("historical_success", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("final_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("editor_decision", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.Text, nullable=False, server_default="{}"),
        sa.Column("feature_version", sa.String(20), nullable=False, server_default="1.0.0"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
    )
    op.create_index("idx_features_article_id", "learning_news_features", ["article_id"])
    op.create_index("idx_features_source", "learning_news_features", ["source_name"])
    op.create_index("idx_features_decision", "learning_news_features", ["editor_decision"])
    op.create_index("idx_features_created_at", "learning_news_features", ["created_at"])

    # ── learning_datasets (Dataset Registry) ───────────────────────────
    op.create_table(
        "learning_datasets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_version", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("algorithm_version", sa.String(20), nullable=False),
        sa.Column("feature_schema_version", sa.String(20), nullable=False),
        sa.Column("record_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("approved_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("rejected_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("export_format", sa.String(20), nullable=False, server_default="JSON"),
        sa.Column("checksum", sa.String(255), nullable=False, server_default=""),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
    )
    op.create_index("idx_dataset_version", "learning_datasets", ["dataset_version"])
    op.create_index("idx_dataset_status", "learning_datasets", ["status"])

    # ── learning_training_snapshots ────────────────────────────────────
    op.create_table(
        "learning_training_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_version", sa.String(20), nullable=False),
        sa.Column("algorithm_version", sa.String(20), nullable=False),
        sa.Column("feature_version", sa.String(20), nullable=False),
        sa.Column("weights_json", sa.Text, nullable=False),
        sa.Column("confidence_threshold", sa.Float, nullable=False, server_default="0.5"),
        sa.Column("training_parameters_json", sa.Text, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
    )
    op.create_index(
        "idx_training_dataset_version",
        "learning_training_snapshots",
        ["dataset_version"],
    )
    op.create_index("idx_training_status", "learning_training_snapshots", ["status"])


def downgrade() -> None:
    op.drop_table("learning_training_snapshots")
    op.drop_table("learning_datasets")
    op.drop_table("learning_news_features")
    op.drop_table("learning_knowledge_artifacts")
    op.drop_table("learning_knowledge_snapshots")
    op.drop_table("learning_models")
    op.drop_table("learning_source_quality")
    op.drop_table("learning_signals")
    op.drop_table("learning_feedback")
