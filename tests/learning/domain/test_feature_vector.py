"""Tests for FeatureVector Value Object."""
import pytest
from learning.domain.value_objects.feature_vector import FeatureVector


class TestFeatureVector:
    def test_valid_construction(self):
        fv = FeatureVector(features={"relevance": 0.8, "popularity": 0.6})
        assert fv.get("relevance") == 0.8
        assert len(fv) == 2

    def test_empty_features(self):
        fv = FeatureVector()
        assert len(fv) == 0

    def test_get_default(self):
        fv = FeatureVector(features={"relevance": 0.8})
        assert fv.get("missing", 0.0) == 0.0
        assert fv.get("missing") == 0.0

    def test_contains(self):
        fv = FeatureVector(features={"relevance": 0.8})
        assert "relevance" in fv
        assert "missing" not in fv

    def test_keys_values_items(self):
        fv = FeatureVector(features={"a": 1.0, "b": 2.0})
        assert set(fv.keys()) == {"a", "b"}
        assert set(fv.values()) == {1.0, 2.0}

    def test_rejects_non_string_keys(self):
        with pytest.raises(TypeError, match="string"):
            FeatureVector(features={1: 1.0})  # type: ignore[dict-item]

    def test_rejects_non_numeric_values(self):
        with pytest.raises(TypeError, match="numeric"):
            FeatureVector(features={"a": "high"})  # type: ignore[dict-item]

    def test_immutable_features(self):
        fv = FeatureVector(features={"relevance": 0.8})
        with pytest.raises(TypeError):
            fv.features["new"] = 1.0  # type: ignore[index]

    def test_immutable_dataclass(self):
        fv = FeatureVector(features={"relevance": 0.8})
        with pytest.raises(AttributeError):
            fv.features = {}  # type: ignore[misc]

    def test_equality(self):
        a = FeatureVector(features={"x": 1.0})
        b = FeatureVector(features={"x": 1.0})
        assert a == b
