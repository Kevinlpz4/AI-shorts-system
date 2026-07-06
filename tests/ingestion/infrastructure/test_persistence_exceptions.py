"""
Tests for persistence exception hierarchy.

Validates:
  - PersistenceError inherits from RuntimeError
  - EntityNotFoundError and DuplicateEntityError inherit from PersistenceError
  - Message formatting
  - Attribute access
  - Distinction from domain errors
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure src/ is on sys.path
_src_path = str(Path(__file__).resolve().parent.parent.parent.parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from ingestion.infrastructure.persistence import (
    DuplicateEntityError,
    EntityNotFoundError,
    PersistenceError,
)


# ══════════════════════════════════════════════════════════════════════════════
# Inheritance
# ══════════════════════════════════════════════════════════════════════════════

class TestInheritance:
    """Validates the exception hierarchy."""

    def test_persistence_error_is_runtime_error(self):
        """PersistenceError debe heredar de RuntimeError."""
        assert issubclass(PersistenceError, RuntimeError)

    def test_entity_not_found_is_persistence_error(self):
        """EntityNotFoundError debe heredar de PersistenceError."""
        assert issubclass(EntityNotFoundError, PersistenceError)

    def test_duplicate_entity_is_persistence_error(self):
        """DuplicateEntityError debe heredar de PersistenceError."""
        assert issubclass(DuplicateEntityError, PersistenceError)

    def test_entity_not_found_is_not_runtime_error_directly(self):
        """EntityNotFoundError debe pasar por PersistenceError, no directo."""
        # It should be a PersistenceError first, then RuntimeError
        assert EntityNotFoundError.__mro__.index(PersistenceError) < (
            EntityNotFoundError.__mro__.index(RuntimeError)
        )


# ══════════════════════════════════════════════════════════════════════════════
# PersistenceError
# ══════════════════════════════════════════════════════════════════════════════

class TestPersistenceError:
    """Base exception tests."""

    def test_can_be_raised_with_message(self):
        """PersistenceError debe aceptar un mensaje."""
        err = PersistenceError("something went wrong")
        assert str(err) == "something went wrong"

    def test_can_be_raised_without_message(self):
        """PersistenceError debe poder crearse sin argumentos."""
        err = PersistenceError()
        assert str(err) == ""

    def test_can_be_caught_as_runtime_error(self):
        """PersistenceError debe poder atraparse como RuntimeError."""
        try:
            raise PersistenceError("test")
        except RuntimeError as e:
            assert str(e) == "test"

    def test_can_be_caught_as_base_exception(self):
        """PersistenceError debe poder atraparse como Exception."""
        try:
            raise PersistenceError("test")
        except Exception as e:
            assert str(e) == "test"


# ══════════════════════════════════════════════════════════════════════════════
# EntityNotFoundError
# ══════════════════════════════════════════════════════════════════════════════

class TestEntityNotFoundError:
    """EntityNotFoundError tests."""

    def test_constructor_sets_entity_name_and_id(self):
        """El constructor debe guardar entity_name y entity_id."""
        err = EntityNotFoundError("Source", "src-123")
        assert err.entity_name == "Source"
        assert err.entity_id == "src-123"

    def test_default_message_format(self):
        """El mensaje debe ser '<entity_name> not found: <entity_id>'."""
        err = EntityNotFoundError("Source", "src-123")
        assert str(err) == "Source not found: src-123"

    def test_with_uuid_string(self):
        """Debe funcionar con UUID como string."""
        err = EntityNotFoundError("Feed", "aaaaaaaa-1234-5678-1234-567812345678")
        assert str(err) == "Feed not found: aaaaaaaa-1234-5678-1234-567812345678"

    def test_with_empty_id(self):
        """Debe funcionar con ID vacío."""
        err = EntityNotFoundError("Article", "")
        assert str(err) == "Article not found: "

    def test_is_catchable_as_persistence_error(self):
        """Debe poder atraparse como PersistenceError."""
        try:
            raise EntityNotFoundError("X", "1")
        except PersistenceError as e:
            assert isinstance(e, EntityNotFoundError)

    def test_is_catchable_as_runtime_error(self):
        """Debe poder atraparse como RuntimeError."""
        try:
            raise EntityNotFoundError("X", "1")
        except RuntimeError as e:
            assert isinstance(e, EntityNotFoundError)


# ══════════════════════════════════════════════════════════════════════════════
# DuplicateEntityError
# ══════════════════════════════════════════════════════════════════════════════

class TestDuplicateEntityError:
    """DuplicateEntityError tests."""

    def test_constructor_sets_fields(self):
        """El constructor debe guardar entity_name, field, value."""
        err = DuplicateEntityError("Source", "name", "my-source")
        assert err.entity_name == "Source"
        assert err.field == "name"
        assert err.value == "my-source"

    def test_default_message_format(self):
        """El mensaje debe ser 'Duplicate <entity>.<field>: <value>'."""
        err = DuplicateEntityError("Source", "name", "my-source")
        assert str(err) == "Duplicate Source.name: my-source"

    def test_with_slug_field(self):
        """Debe funcionar con campo 'slug'."""
        err = DuplicateEntityError("Category", "slug", "tech-news")
        assert str(err) == "Duplicate Category.slug: tech-news"

    def test_with_special_characters(self):
        """Debe funcionar con valores que contengan caracteres especiales."""
        err = DuplicateEntityError("Topic", "name", "AI & Machine Learning")
        assert str(err) == "Duplicate Topic.name: AI & Machine Learning"

    def test_is_catchable_as_persistence_error(self):
        """Debe poder atraparse como PersistenceError."""
        try:
            raise DuplicateEntityError("X", "y", "z")
        except PersistenceError as e:
            assert isinstance(e, DuplicateEntityError)

    def test_is_catchable_as_runtime_error(self):
        """Debe poder atraparse como RuntimeError."""
        try:
            raise DuplicateEntityError("X", "y", "z")
        except RuntimeError as e:
            assert isinstance(e, DuplicateEntityError)


# ══════════════════════════════════════════════════════════════════════════════
# Distinction from Domain Errors
# ══════════════════════════════════════════════════════════════════════════════

class TestDistinctionFromDomainErrors:
    """Persistence errors must NOT be domain errors."""

    def test_persistence_error_is_not_domain_error(self):
        """PersistenceError NO debe ser un DomainError (de foundation)."""
        # Import foundation domain error
        from foundation.errors import DomainError

        assert not issubclass(PersistenceError, DomainError)

    def test_catch_persistence_separately_from_domain(self):
        """Debe poder atrapar PersistenceError sin atrapar DomainError."""
        from foundation.errors import DomainError

        persistence_caught = False
        domain_caught = False

        try:
            raise PersistenceError("infra failure")
        except DomainError:
            domain_caught = True
        except PersistenceError:
            persistence_caught = True

        assert persistence_caught, "PersistenceError should be caught by PersistenceError handler"
        assert not domain_caught, "PersistenceError should NOT be caught by DomainError handler"
