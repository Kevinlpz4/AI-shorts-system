"""Tests for AlgorithmVersion Value Object."""
import pytest
from learning.domain.value_objects.algorithm_version import AlgorithmVersion


class TestAlgorithmVersion:
    def test_valid_construction(self):
        v = AlgorithmVersion(major=1, minor=2, patch=3)
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3

    def test_str_representation(self):
        v = AlgorithmVersion(major=2, minor=0, patch=1)
        assert str(v) == "2.0.1"

    def test_rejects_negative(self):
        with pytest.raises(ValueError, match=">= 0"):
            AlgorithmVersion(major=-1, minor=0, patch=0)

    def test_rejects_non_int(self):
        with pytest.raises(TypeError, match="int"):
            AlgorithmVersion(major=1.0, minor=0, patch=0)  # type: ignore[arg-type]

    def test_comparison_gt(self):
        assert AlgorithmVersion(major=2, minor=0, patch=0) > AlgorithmVersion(major=1, minor=0, patch=0)
        assert AlgorithmVersion(major=1, minor=1, patch=0) > AlgorithmVersion(major=1, minor=0, patch=0)

    def test_comparison_lt(self):
        assert AlgorithmVersion(major=1, minor=0, patch=0) < AlgorithmVersion(major=2, minor=0, patch=0)

    def test_comparison_ge(self):
        assert AlgorithmVersion(major=1, minor=0, patch=0) >= AlgorithmVersion(major=1, minor=0, patch=0)

    def test_comparison_le(self):
        assert AlgorithmVersion(major=1, minor=0, patch=0) <= AlgorithmVersion(major=1, minor=0, patch=0)

    def test_next_major(self):
        v = AlgorithmVersion(major=1, minor=2, patch=3)
        assert v.next_major() == AlgorithmVersion(major=2, minor=0, patch=0)

    def test_next_minor(self):
        v = AlgorithmVersion(major=1, minor=2, patch=3)
        assert v.next_minor() == AlgorithmVersion(major=1, minor=3, patch=0)

    def test_next_patch(self):
        v = AlgorithmVersion(major=1, minor=2, patch=3)
        assert v.next_patch() == AlgorithmVersion(major=1, minor=2, patch=4)

    def test_parse_valid(self):
        v = AlgorithmVersion.parse("1.2.3")
        assert v == AlgorithmVersion(major=1, minor=2, patch=3)

    def test_parse_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid version format"):
            AlgorithmVersion.parse("1.2")

    def test_parse_non_numeric(self):
        with pytest.raises(ValueError, match="Invalid version format"):
            AlgorithmVersion.parse("a.b.c")

    def test_immutable(self):
        v = AlgorithmVersion(major=1, minor=0, patch=0)
        with pytest.raises(AttributeError):
            v.major = 2  # type: ignore[misc]

    def test_equality(self):
        a = AlgorithmVersion(major=1, minor=2, patch=3)
        b = AlgorithmVersion(major=1, minor=2, patch=3)
        assert a == b
