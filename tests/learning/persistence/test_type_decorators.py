"""
Unit tests for TypeDecorators — each decorator's bind/result roundtrip + None handling.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase

from learning.domain.entities.ids import FeedbackId, LearningSignalId
from learning.domain.value_objects.algorithm_version import AlgorithmVersion
from learning.domain.value_objects.confidence import Confidence
from learning.domain.value_objects.feature_snapshot import FeatureSnapshot
from learning.domain.value_objects.feature_vector import FeatureVector
from learning.domain.value_objects.keyword_stat_vo import KeywordStat
from learning.domain.value_objects.score_weights import ScoreWeights
from learning.domain.value_objects.signal_strength import SignalStrength
from learning.domain.value_objects.time_window import TimeWindow
from learning.domain.value_objects.decision_type import DecisionType
from learning.domain.value_objects.signal_type import SignalType
from learning.persistence.type_decorators import (
    AlgorithmVersionDecorator,
    ConfidenceDecorator,
    EntityIdDecorator,
    EnumDecorator,
    FeatureSnapshotDecorator,
    FeatureVectorDecorator,
    KeywordStatDecorator,
    ScoreWeightsDecorator,
    SignalStrengthDecorator,
    TimeWindowDecorator,
)


# ── Test model for TypeDecorator roundtrips ────────────────────────────


class _TestBase(DeclarativeBase):
    pass


class _TestEntityIdModel(_TestBase):
    __tablename__ = "test_entity_id"
    id = Column(String(36), primary_key=True)
    feedback_id = Column(EntityIdDecorator(FeedbackId), nullable=True)
    signal_id = Column(EntityIdDecorator(LearningSignalId), nullable=True)


class _TestConfidenceModel(_TestBase):
    __tablename__ = "test_confidence"
    id = Column(String(36), primary_key=True)
    confidence = Column(ConfidenceDecorator(), nullable=True)


class _TestFeatureVectorModel(_TestBase):
    __tablename__ = "test_feature_vector"
    id = Column(String(36), primary_key=True)
    vector = Column(FeatureVectorDecorator(), nullable=True)


class _TestAlgorithmVersionModel(_TestBase):
    __tablename__ = "test_algorithm_version"
    id = Column(String(36), primary_key=True)
    version = Column(AlgorithmVersionDecorator(), nullable=True)


class _TestScoreWeightsModel(_TestBase):
    __tablename__ = "test_score_weights"
    id = Column(String(36), primary_key=True)
    weights = Column(ScoreWeightsDecorator(), nullable=True)


class _TestSignalStrengthModel(_TestBase):
    __tablename__ = "test_signal_strength"
    id = Column(String(36), primary_key=True)
    strength = Column(SignalStrengthDecorator(), nullable=True)


class _TestTimeWindowModel(_TestBase):
    __tablename__ = "test_time_window"
    id = Column(String(36), primary_key=True)
    window = Column(TimeWindowDecorator(), nullable=True)


class _TestKeywordStatModel(_TestBase):
    __tablename__ = "test_keyword_stat"
    id = Column(String(36), primary_key=True)
    stat = Column(KeywordStatDecorator(), nullable=True)


class _TestFeatureSnapshotModel(_TestBase):
    __tablename__ = "test_feature_snapshot"
    id = Column(String(36), primary_key=True)
    snapshot = Column(FeatureSnapshotDecorator(), nullable=True)


class _TestEnumModel(_TestBase):
    __tablename__ = "test_enum"
    id = Column(String(36), primary_key=True)
    decision = Column(EnumDecorator(DecisionType), nullable=True)
    signal_type = Column(EnumDecorator(SignalType), nullable=True)


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:")
    _TestBase.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    SessionLocal = sessionmaker(bind=engine)
    s = SessionLocal()
    yield s
    s.close()


# ── EntityIdDecorator tests ───────────────────────────────────────────


class TestEntityIdDecorator:
    def test_feedback_id_roundtrip(self, session):
        fid = FeedbackId.generate()
        model = _TestEntityIdModel(id="1", feedback_id=fid)
        session.add(model)
        session.flush()

        loaded = session.query(_TestEntityIdModel).first()
        assert loaded.feedback_id == fid
        assert type(loaded.feedback_id) is FeedbackId

    def test_signal_id_roundtrip(self, session):
        sid = LearningSignalId.generate()
        model = _TestEntityIdModel(id="2", signal_id=sid)
        session.add(model)
        session.flush()

        loaded = session.query(_TestEntityIdModel).first()
        assert loaded.signal_id == sid
        assert type(loaded.signal_id) is LearningSignalId

    def test_none_handling(self, session):
        model = _TestEntityIdModel(id="3", feedback_id=None)
        session.add(model)
        session.flush()

        loaded = session.query(_TestEntityIdModel).first()
        assert loaded.feedback_id is None


# ── ConfidenceDecorator tests ─────────────────────────────────────────


class TestConfidenceDecorator:
    def test_roundtrip(self, session):
        conf = Confidence(value=0.85, sample_size=42)
        model = _TestConfidenceModel(id="1", confidence=conf)
        session.add(model)
        session.flush()

        loaded = session.query(_TestConfidenceModel).first()
        assert loaded.confidence == conf
        assert loaded.confidence.value == 0.85
        assert loaded.confidence.sample_size == 42

    def test_none_handling(self, session):
        model = _TestConfidenceModel(id="2", confidence=None)
        session.add(model)
        session.flush()

        loaded = session.query(_TestConfidenceModel).first()
        assert loaded.confidence is None

    def test_zero_confidence(self, session):
        conf = Confidence(value=0.0, sample_size=0)
        model = _TestConfidenceModel(id="3", confidence=conf)
        session.add(model)
        session.flush()

        loaded = session.query(_TestConfidenceModel).first()
        assert loaded.confidence.value == 0.0
        assert loaded.confidence.sample_size == 0


# ── FeatureVectorDecorator tests ──────────────────────────────────────


class TestFeatureVectorDecorator:
    def test_roundtrip(self, session):
        vec = FeatureVector(features={"a": 1.0, "b": 2.5})
        model = _TestFeatureVectorModel(id="1", vector=vec)
        session.add(model)
        session.flush()

        loaded = session.query(_TestFeatureVectorModel).first()
        assert loaded.vector.features["a"] == 1.0
        assert loaded.vector.features["b"] == 2.5

    def test_none_handling(self, session):
        model = _TestFeatureVectorModel(id="2", vector=None)
        session.add(model)
        session.flush()

        loaded = session.query(_TestFeatureVectorModel).first()
        assert loaded.vector is None

    def test_empty_features(self, session):
        vec = FeatureVector(features={})
        model = _TestFeatureVectorModel(id="3", vector=vec)
        session.add(model)
        session.flush()

        loaded = session.query(_TestFeatureVectorModel).first()
        assert len(loaded.vector) == 0


# ── AlgorithmVersionDecorator tests ───────────────────────────────────


class TestAlgorithmVersionDecorator:
    def test_roundtrip(self, session):
        ver = AlgorithmVersion(major=2, minor=3, patch=1)
        model = _TestAlgorithmVersionModel(id="1", version=ver)
        session.add(model)
        session.flush()

        loaded = session.query(_TestAlgorithmVersionModel).first()
        assert loaded.version == ver
        assert str(loaded.version) == "2.3.1"

    def test_none_handling(self, session):
        model = _TestAlgorithmVersionModel(id="2", version=None)
        session.add(model)
        session.flush()

        loaded = session.query(_TestAlgorithmVersionModel).first()
        assert loaded.version is None

    def test_parse_roundtrip(self, session):
        ver = AlgorithmVersion.parse("0.1.0")
        model = _TestAlgorithmVersionModel(id="3", version=ver)
        session.add(model)
        session.flush()

        loaded = session.query(_TestAlgorithmVersionModel).first()
        assert loaded.version.major == 0
        assert loaded.version.minor == 1
        assert loaded.version.patch == 0


# ── ScoreWeightsDecorator tests ───────────────────────────────────────


class TestScoreWeightsDecorator:
    def test_roundtrip(self, session):
        weights = ScoreWeights(
            relevance=0.4, popularity=0.2, recency=0.2, source_reliability=0.2
        )
        model = _TestScoreWeightsModel(id="1", weights=weights)
        session.add(model)
        session.flush()

        loaded = session.query(_TestScoreWeightsModel).first()
        assert loaded.weights.relevance == 0.4
        assert loaded.weights.popularity == 0.2
        assert loaded.weights.recency == 0.2
        assert loaded.weights.source_reliability == 0.2

    def test_none_handling(self, session):
        model = _TestScoreWeightsModel(id="2", weights=None)
        session.add(model)
        session.flush()

        loaded = session.query(_TestScoreWeightsModel).first()
        assert loaded.weights is None


# ── SignalStrengthDecorator tests ─────────────────────────────────────


class TestSignalStrengthDecorator:
    def test_roundtrip(self, session):
        strength = SignalStrength(value=0.75, decay_factor=0.15)
        model = _TestSignalStrengthModel(id="1", strength=strength)
        session.add(model)
        session.flush()

        loaded = session.query(_TestSignalStrengthModel).first()
        assert loaded.strength.value == 0.75
        assert loaded.strength.decay_factor == 0.15

    def test_none_handling(self, session):
        model = _TestSignalStrengthModel(id="2", strength=None)
        session.add(model)
        session.flush()

        loaded = session.query(_TestSignalStrengthModel).first()
        assert loaded.strength is None


# ── TimeWindowDecorator tests ─────────────────────────────────────────


class TestTimeWindowDecorator:
    def test_roundtrip(self, session):
        now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(day=start.day + 1)
        window = TimeWindow(start=start, end=end)
        model = _TestTimeWindowModel(id="1", window=window)
        session.add(model)
        session.flush()

        loaded = session.query(_TestTimeWindowModel).first()
        assert loaded.window.start == start
        assert loaded.window.end == end

    def test_none_handling(self, session):
        model = _TestTimeWindowModel(id="2", window=None)
        session.add(model)
        session.flush()

        loaded = session.query(_TestTimeWindowModel).first()
        assert loaded.window is None


# ── KeywordStatDecorator tests ────────────────────────────────────────


class TestKeywordStatDecorator:
    def test_roundtrip(self, session):
        stat = KeywordStat(keyword="python", count=10, approved_count=8)
        model = _TestKeywordStatModel(id="1", stat=stat)
        session.add(model)
        session.flush()

        loaded = session.query(_TestKeywordStatModel).first()
        assert loaded.stat.keyword == "python"
        assert loaded.stat.count == 10
        assert loaded.stat.approved_count == 8

    def test_none_handling(self, session):
        model = _TestKeywordStatModel(id="2", stat=None)
        session.add(model)
        session.flush()

        loaded = session.query(_TestKeywordStatModel).first()
        assert loaded.stat is None


# ── FeatureSnapshotDecorator tests ────────────────────────────────────


class TestFeatureSnapshotDecorator:
    def test_roundtrip(self, session):
        ts = datetime.now(timezone.utc)
        snapshot = FeatureSnapshot(
            base_score=0.7,
            freshness_score=0.8,
            keyword_bonus=0.3,
            source_bonus=0.5,
            topic_penalty=0.1,
            confidence=0.9,
            final_score=0.65,
            timestamp=ts,
        )
        model = _TestFeatureSnapshotModel(id="1", snapshot=snapshot)
        session.add(model)
        session.flush()

        loaded = session.query(_TestFeatureSnapshotModel).first()
        assert loaded.snapshot.base_score == 0.7
        assert loaded.snapshot.freshness_score == 0.8
        assert loaded.snapshot.final_score == 0.65

    def test_none_handling(self, session):
        model = _TestFeatureSnapshotModel(id="2", snapshot=None)
        session.add(model)
        session.flush()

        loaded = session.query(_TestFeatureSnapshotModel).first()
        assert loaded.snapshot is None


# ── EnumDecorator tests ───────────────────────────────────────────────


class TestEnumDecorator:
    def test_decision_type_roundtrip(self, session):
        model = _TestEnumModel(id="1", decision=DecisionType.APPROVED)
        session.add(model)
        session.flush()

        loaded = session.query(_TestEnumModel).first()
        assert loaded.decision == DecisionType.APPROVED
        assert loaded.decision is DecisionType.APPROVED

    def test_signal_type_roundtrip(self, session):
        model = _TestEnumModel(id="2", signal_type=SignalType.KEYWORD)
        session.add(model)
        session.flush()

        loaded = session.query(_TestEnumModel).first()
        assert loaded.signal_type == SignalType.KEYWORD

    def test_none_handling(self, session):
        model = _TestEnumModel(id="3", decision=None, signal_type=None)
        session.add(model)
        session.flush()

        loaded = session.query(_TestEnumModel).first()
        assert loaded.decision is None
        assert loaded.signal_type is None

    def test_all_decision_types(self, session):
        for i, dt in enumerate(DecisionType):
            model = _TestEnumModel(id=f"dt-{i}", decision=dt)
            session.add(model)
        session.flush()

        for i, dt in enumerate(DecisionType):
            loaded = session.query(_TestEnumModel).filter_by(id=f"dt-{i}").first()
            assert loaded.decision == dt
