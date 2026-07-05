"""Tests for CategoryName value object."""

from __future__ import annotations

import pytest

from ingestion.domain.value_objects.category_name import CategoryName


class TestCategoryNameValidation:
    def test_valid_name(self) -> None:
        name = CategoryName("Technology")
        assert name.value == "Technology"

    def test_valid_with_spaces(self) -> None:
        name = CategoryName("World News")
        assert name.value == "World News"

    def test_valid_with_hyphen(self) -> None:
        name = CategoryName("Machine-Learning")
        assert name.value == "Machine-Learning"

    def test_valid_with_underscore(self) -> None:
        name = CategoryName("AI_Research")
        assert name.value == "AI_Research"

    def test_valid_mixed(self) -> None:
        name = CategoryName("Tech 2024")
        assert name.value == "Tech 2024"

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            CategoryName("")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            CategoryName("   ")

    def test_too_long_raises(self) -> None:
        with pytest.raises(ValueError, match="must not exceed 100"):
            CategoryName("x" * 101)

    def test_special_chars_raises(self) -> None:
        with pytest.raises(ValueError, match="contain only letters"):
            CategoryName("Tech@2024!")

    def test_leading_spaces_trimmed(self) -> None:
        name = CategoryName("  Technology")
        assert name.value == "Technology"

    def test_trailing_spaces_trimmed(self) -> None:
        name = CategoryName("Technology  ")
        assert name.value == "Technology"

    def test_frozen_immutable(self) -> None:
        name = CategoryName("Tech")
        with pytest.raises(Exception):
            name.value = "Changed"
