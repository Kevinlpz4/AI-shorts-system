"""
Tests for Category entity.

Covers:
  - Construction (valid/invalid)
  - Invariants (I-18 to I-21)
  - Behavior (activate, deactivate, change_parent)
  - Equality and hash
"""

from __future__ import annotations

import pytest

from foundation.base.entity import Entity

from ingestion.domain.entities.category import Category
from ingestion.domain.entities.ids import CategoryId
from ingestion.domain.value_objects.category_name import CategoryName


class TestCategoryCreation:
    def test_create_valid_category(
        self, category_id: CategoryId, category_name: CategoryName
    ) -> None:
        category = Category(
            id=category_id,
            name=category_name,
            slug="technology",
        )
        assert category.id == category_id
        assert category.name == category_name
        assert category.slug == "technology"
        assert category.parent_id is None
        assert category.is_active is True

    def test_create_with_parent(
        self, category_id: CategoryId, category_name: CategoryName
    ) -> None:
        parent_id = CategoryId.generate()
        category = Category(
            id=category_id,
            name=category_name,
            slug="sub-tech",
            parent_id=parent_id,
        )
        assert category.parent_id == parent_id

    def test_create_inactive(
        self, category_id: CategoryId, category_name: CategoryName
    ) -> None:
        category = Category(
            id=category_id,
            name=category_name,
            slug="tech",
            is_active=False,
        )
        assert category.is_active is False

    def test_self_parent_raises(
        self, category_id: CategoryId, category_name: CategoryName
    ) -> None:
        with pytest.raises(ValueError, match="cannot be its own parent"):
            Category(
                id=category_id,
                name=category_name,
                slug="tech",
                parent_id=category_id,
            )

    def test_inherits_entity(self, category: Category) -> None:
        assert isinstance(category, Entity)

    def test_equality_by_id(
        self, category_id: CategoryId, category_name: CategoryName
    ) -> None:
        cat1 = Category(id=category_id, name=category_name, slug="tech")
        cat2 = Category(
            id=category_id,
            name=CategoryName("Different"),
            slug="different",
        )
        assert cat1 == cat2

    def test_inequality(
        self, category_id: CategoryId, category_name: CategoryName
    ) -> None:
        cat1 = Category(id=category_id, name=category_name, slug="tech")
        cat2 = Category(
            id=CategoryId.generate(),
            name=category_name,
            slug="tech",
        )
        assert cat1 != cat2


class TestCategoryBehavior:
    def test_activate(self, category: Category) -> None:
        category.is_active = False
        category.activate()
        assert category.is_active is True

    def test_deactivate(self, category: Category) -> None:
        category.deactivate()
        assert category.is_active is False

    def test_change_parent_to_none(self, category: Category) -> None:
        parent_id = CategoryId.generate()
        category.parent_id = parent_id
        category.change_parent(None)
        assert category.parent_id is None

    def test_change_parent_valid(self, category: Category) -> None:
        new_parent = CategoryId.generate()
        category.change_parent(new_parent)
        assert category.parent_id == new_parent

    def test_change_parent_to_self_raises(self, category: Category) -> None:
        with pytest.raises(ValueError, match="cannot be its own parent"):
            category.change_parent(category.id)
