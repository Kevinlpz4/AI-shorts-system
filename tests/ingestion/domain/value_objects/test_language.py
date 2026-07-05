"""Tests for Language value object."""

from __future__ import annotations

import pytest

from ingestion.domain.value_objects.language import Language


class TestLanguageValidation:
    def test_valid_en(self) -> None:
        lang = Language("en")
        assert lang.code == "en"

    def test_valid_es(self) -> None:
        lang = Language("es")
        assert lang.code == "es"

    def test_uppercase_normalizes(self) -> None:
        lang = Language("EN")
        assert lang.code == "en"

    def test_mixed_case_normalizes(self) -> None:
        lang = Language("Es")
        assert lang.code == "es"

    def test_invalid_language_raises(self) -> None:
        with pytest.raises(ValueError, match="not in the allowed list"):
            Language("xx")

    def test_too_long_raises(self) -> None:
        with pytest.raises(ValueError, match="exactly 2 letters"):
            Language("eng")

    def test_too_short_raises(self) -> None:
        with pytest.raises(ValueError, match="exactly 2 letters"):
            Language("e")

    def test_numeric_raises(self) -> None:
        with pytest.raises(ValueError, match="contain only letters"):
            Language("12")

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="exactly 2 letters"):
            Language("")

    def test_frozen_immutable(self) -> None:
        lang = Language("en")
        with pytest.raises(Exception):
            lang.code = "es"

    def test_equality_by_value(self) -> None:
        lang1 = Language("en")
        lang2 = Language("en")
        assert lang1 == lang2


class TestLanguageMethods:
    def test_display_name_english(self) -> None:
        assert Language("en").display_name() == "English"

    def test_display_name_spanish(self) -> None:
        assert Language("es").display_name() == "Spanish"

    def test_display_name_french(self) -> None:
        assert Language("fr").display_name() == "French"

    def test_is_rtl_arabic(self) -> None:
        assert Language("ar").is_rtl() is True

    def test_is_rtl_english(self) -> None:
        assert Language("en").is_rtl() is False

    def test_is_rtl_spanish(self) -> None:
        assert Language("es").is_rtl() is False
