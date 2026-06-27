"""
Tests para Value Objects del dominio.
"""
import pytest
from domain.value_objects.viral_score import ViralScore
from domain.value_objects.duration import Duration
from domain.value_objects.hook_type import HookType
from domain.value_objects.platform import Platform


class TestViralScore:
    """Tests para ViralScore — valor inmutable entre 0-100."""

    def test_create_valid_score(self):
        assert ViralScore(75).value == 75

    def test_create_zero(self):
        assert ViralScore(0).value == 0

    def test_create_max(self):
        assert ViralScore(100).value == 100

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="entre 0 y 100"):
            ViralScore(-1)

    def test_above_100_raises(self):
        with pytest.raises(ValueError, match="entre 0 y 100"):
            ViralScore(101)

    def test_is_viral_threshold(self):
        assert ViralScore(80).is_viral() is True
        assert ViralScore(79).is_viral() is False

    def test_is_promising(self):
        assert ViralScore(60).is_promising() is True
        assert ViralScore(59).is_promising() is False

    def test_combine_averages(self):
        a = ViralScore(80)
        b = ViralScore(60)
        c = a.combine(b)
        assert c.value == 70  # (80 + 60) // 2 = 70
        assert isinstance(c, ViralScore)

    def test_combine_caps_at_100(self):
        a = ViralScore(100)
        b = ViralScore(100)
        assert a.combine(b).value == 100

    def test_improve_increases(self):
        s = ViralScore(50).improve(10)
        assert s.value == 60
        assert isinstance(s, ViralScore)

    def test_improve_caps_at_100(self):
        s = ViralScore(95).improve(10)
        assert s.value == 100

    def test_int_conversion(self):
        assert int(ViralScore(75)) == 75

    def test_str_representation(self):
        assert str(ViralScore(75)) == "75/100"

    def test_immutable(self):
        s = ViralScore(50)
        with pytest.raises(AttributeError):
            s.value = 60

    def test_equality(self):
        assert ViralScore(50) == ViralScore(50)
        assert ViralScore(50) != ViralScore(51)


class TestDuration:
    """Tests para Duration — valor en segundos."""

    def test_create(self):
        assert Duration(45).seconds == 45

    def test_zero_raises(self):
        with pytest.raises(ValueError, match="positiva"):
            Duration(0)

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            Duration(-1)

    def test_over_600_raises(self):
        with pytest.raises(ValueError, match="máxima"):
            Duration(601)

    def test_is_optimal_for_shorts(self):
        assert Duration(30).is_optimal_for_shorts() is True
        assert Duration(45).is_optimal_for_shorts() is True
        assert Duration(60).is_optimal_for_shorts() is True
        assert Duration(29).is_optimal_for_shorts() is False
        assert Duration(61).is_optimal_for_shorts() is False

    def test_hook_duration(self):
        d = Duration(60)
        assert 3 <= d.hook_duration <= 5
        assert d.hook_duration == 5  # min(5, int(60 * 0.1))

    def test_cta_duration(self):
        assert Duration(60).cta_duration == 5  # min(5, int(60 * 0.1))
        assert Duration(30).cta_duration == 3  # int(30 * 0.1) = 3

    def test_body_duration(self):
        d = Duration(60)
        assert d.body_duration == d.seconds - d.hook_duration - d.cta_duration

    def test_estimated_words(self):
        d = Duration(60)
        assert d.estimated_words() == 150  # 60 * 2.5

    def test_int_conversion(self):
        assert int(Duration(45)) == 45

    def test_str_seconds_only(self):
        assert str(Duration(45)) == "45s"

    def test_str_minutes_seconds(self):
        assert str(Duration(125)) == "2m5s"

    def test_immutable(self):
        d = Duration(30)
        with pytest.raises(AttributeError):
            d.seconds = 60

    def test_equality(self):
        assert Duration(30) == Duration(30)
        assert Duration(30) != Duration(60)


class TestHookType:
    """Tests para HookType — Enum de tipos de hooks."""

    def test_enum_values(self):
        assert HookType.QUESTION.value == "question"
        assert HookType.STATEMENT.value == "statement"
        assert HookType.REVEAL.value == "reveal"
        assert HookType.LIST.value == "list"
        assert HookType.TRENDING.value == "trending"
        assert HookType.CONTROVERSIAL.value == "controversial"

    def test_base_scores(self):
        assert HookType.QUESTION.base_score == 90
        assert HookType.CONTROVERSIAL.base_score == 70

    def test_descriptions(self):
        assert "curiosidad" in HookType.QUESTION.description.lower()
        assert "atención" in HookType.STATEMENT.description.lower()

    def test_from_string_valid(self):
        assert HookType.from_string("question") == HookType.QUESTION
        assert HookType.from_string("list") == HookType.LIST

    def test_from_string_invalid_returns_statement(self):
        assert HookType.from_string("invalid") == HookType.STATEMENT

    def test_from_string_case_insensitive(self):
        assert HookType.from_string("QUESTION") == HookType.QUESTION


class TestPlatform:
    """Tests para Platform — Enum de plataformas."""

    def test_enum_values(self):
        assert Platform.YOUTUBE.value == "youtube"
        assert Platform.TIKTOK.value == "tiktok"
        assert Platform.INSTAGRAM.value == "instagram"

    def test_aspect_ratio(self):
        assert Platform.YOUTUBE.aspect_ratio == "9:16"
        assert Platform.TIKTOK.aspect_ratio == "9:16"

    def test_max_duration(self):
        assert Platform.YOUTUBE.max_duration == 60
        assert Platform.TIKTOK.max_duration == 180
        assert Platform.INSTAGRAM.max_duration == 90

    def test_from_string_valid(self):
        assert Platform.from_string("youtube") == Platform.YOUTUBE

    def test_from_string_invalid_raises(self):
        with pytest.raises(ValueError, match="no soportada"):
            Platform.from_string("twitter")
