"""Tests for LearningModel Aggregate Root."""
import pytest
from datetime import datetime, timezone
from learning.domain.entities.learning_model import LearningModel
from learning.domain.entities.ids import LearningModelId
from learning.domain.value_objects.algorithm_version import AlgorithmVersion
from learning.domain.value_objects.score_weights import ScoreWeights


def _make_weights(r=0.35, p=0.25, rc=0.25, sr=0.15):
    return ScoreWeights(relevance=r, popularity=p, recency=rc, source_reliability=sr)


def _make_model(**overrides):
    defaults = dict(
        id=LearningModelId.generate(),
        algorithm_version=AlgorithmVersion(major=1, minor=0, patch=0),
        current_weights=_make_weights(),
        minimum_confidence=0.5,
        minimum_sample_size=10,
        active_rules=["rule_a", "rule_b"],
    )
    defaults.update(overrides)
    return LearningModel(**defaults)


class TestLearningModel:
    def test_valid_construction(self):
        m = _make_model()
        assert m.algorithm_version == AlgorithmVersion(major=1, minor=0, patch=0)
        assert m.minimum_confidence == 0.5
        assert m.minimum_sample_size == 10
        assert m.active_rules == ["rule_a", "rule_b"]

    def test_rejects_confidence_below_zero(self):
        with pytest.raises(Exception, match="\\[0.0, 1.0\\]"):
            _make_model(minimum_confidence=-0.1)

    def test_rejects_confidence_above_one(self):
        with pytest.raises(Exception, match="\\[0.0, 1.0\\]"):
            _make_model(minimum_confidence=1.5)

    def test_rejects_sample_size_zero(self):
        with pytest.raises(Exception, match=">= 1"):
            _make_model(minimum_sample_size=0)

    def test_adjust_weights(self):
        m = _make_model()
        new_w = _make_weights(r=0.4, p=0.2, rc=0.25, sr=0.15)
        m.adjust_weights(new_w, reason="More relevance needed")
        assert m.current_weights == new_w

    def test_adjust_weights_emits_event(self):
        m = _make_model()
        new_w = _make_weights(r=0.4, p=0.2, rc=0.25, sr=0.15)
        m.adjust_weights(new_w, reason="test")
        events = m.pull_events()
        assert any(e.__class__.__name__ == "ScoreAdjusted" for e in events)

    def test_adjust_weights_requires_reason(self):
        m = _make_model()
        with pytest.raises(Exception, match="reason"):
            m.adjust_weights(_make_weights(), reason="")

    def test_update_version(self):
        m = _make_model()
        new_v = AlgorithmVersion(major=1, minor=1, patch=0)
        m.update_version(new_v)
        assert m.algorithm_version == new_v

    def test_update_version_emits_event(self):
        m = _make_model()
        m.update_version(AlgorithmVersion(major=1, minor=1, patch=0))
        events = m.pull_events()
        assert any(e.__class__.__name__ == "LearningModelUpdated" for e in events)

    def test_update_version_rejects_lower(self):
        m = _make_model(algorithm_version=AlgorithmVersion(major=2, minor=0, patch=0))
        with pytest.raises(Exception, match="must be greater"):
            m.update_version(AlgorithmVersion(major=1, minor=0, patch=0))

    def test_update_version_rejects_equal(self):
        m = _make_model(algorithm_version=AlgorithmVersion(major=1, minor=0, patch=0))
        with pytest.raises(Exception, match="must be greater"):
            m.update_version(AlgorithmVersion(major=1, minor=0, patch=0))

    def test_add_rule(self):
        m = _make_model(active_rules=[])
        m.add_rule("new_rule")
        assert "new_rule" in m.active_rules

    def test_add_rule_idempotent(self):
        m = _make_model(active_rules=["rule_a"])
        m.add_rule("rule_a")
        assert m.active_rules.count("rule_a") == 1

    def test_add_rule_rejects_empty(self):
        m = _make_model()
        with pytest.raises(Exception, match="empty"):
            m.add_rule("")

    def test_remove_rule(self):
        m = _make_model(active_rules=["rule_a", "rule_b"])
        m.remove_rule("rule_a")
        assert "rule_a" not in m.active_rules
        assert "rule_b" in m.active_rules

    def test_remove_rule_idempotent(self):
        m = _make_model(active_rules=["rule_a"])
        m.remove_rule("nonexistent")
        assert m.active_rules == ["rule_a"]

    def test_created_at_defaults_to_now(self):
        m = _make_model()
        assert m.created_at is not None
        assert m.created_at.tzinfo is not None

    def test_updated_at_defaults_to_now(self):
        m = _make_model()
        assert m.updated_at is not None
