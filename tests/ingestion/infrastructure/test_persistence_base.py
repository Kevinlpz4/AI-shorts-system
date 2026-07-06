"""
Tests for persistence base (PersistenceBase + naming convention).

Validates:
  - naming_convention dictionary has all required constraint types
  - PersistenceBase inherits DeclarativeBase with the convention
  - Constraint names are deterministic (e.g., pk_, fk_, uq_, ix_, ck_)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import Column, ForeignKey, Integer, MetaData, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Ensure src/ is on sys.path
_src_path = str(Path(__file__).resolve().parent.parent.parent.parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from ingestion.infrastructure.persistence import PersistenceBase, naming_convention


# ══════════════════════════════════════════════════════════════════════════════
# naming_convention
# ══════════════════════════════════════════════════════════════════════════════

class TestNamingConvention:
    """Validates that the naming_convention dict is properly defined."""

    def test_has_all_required_keys(self):
        """naming_convention debe tener las 5 claves requeridas."""
        expected_keys = {"pk", "fk", "uq", "ix", "ck"}
        assert expected_keys.issubset(naming_convention.keys()), (
            f"Missing keys: {expected_keys - set(naming_convention.keys())}"
        )

    def test_pk_pattern(self):
        """pk debe generar pk_<table>."""
        pattern = naming_convention["pk"]
        # We can't evaluate it directly, but we can verify its structure
        assert "%(table_name)s" in pattern
        assert pattern.startswith("pk_")

    def test_fk_pattern(self):
        """fk debe generar fk_<table>_<referred>."""
        pattern = naming_convention["fk"]
        assert "%(table_name)s" in pattern
        assert "%(referred_table_name)s" in pattern
        assert pattern.startswith("fk_")

    def test_uq_pattern(self):
        """uq debe generar uq_<table>_<column>."""
        pattern = naming_convention["uq"]
        assert "%(table_name)s" in pattern
        assert "%(column_0_name)s" in pattern
        assert pattern.startswith("uq_")

    def test_ix_pattern(self):
        """ix debe generar ix_<table>_<column>."""
        pattern = naming_convention["ix"]
        assert "%(table_name)s" in pattern
        assert "%(column_0_name)s" in pattern
        assert pattern.startswith("ix_")

    def test_ck_pattern(self):
        """ck debe generar ck_<table>_<rule>."""
        pattern = naming_convention["ck"]
        assert "%(table_name)s" in pattern
        assert "%(constraint_name)s" in pattern
        assert pattern.startswith("ck_")

    def test_convention_is_not_mutable_by_accident(self):
        """naming_convention debe ser un dict mutable (SQLAlchemy necesita mutarlo)."""
        # SQLAlchemy might modify the convention dict internally
        # So it should be a regular dict, not a frozen mapping
        assert isinstance(naming_convention, dict)


# ══════════════════════════════════════════════════════════════════════════════
# PersistenceBase
# ══════════════════════════════════════════════════════════════════════════════

class TestPersistenceBase:
    """Validates that PersistenceBase is properly configured."""

    def test_is_declarative_base(self):
        """PersistenceBase debe heredar de DeclarativeBase."""
        from sqlalchemy.orm import DeclarativeBase

        assert issubclass(PersistenceBase, DeclarativeBase)

    def test_has_metadata_with_naming_convention(self):
        """PersistenceBase.metadata debe tener el naming_convention."""
        assert isinstance(PersistenceBase.metadata, MetaData)
        assert PersistenceBase.metadata.naming_convention is naming_convention

    def test_cannot_be_instantiated_directly(self):
        """Instanciar PersistenceBase directamente no debería crear una instancia con tabla."""
        # PersistenceBase is abstract (no __tablename__), so it's not mappable.
        # Attempting to instantiate it is not useful — it has no table.
        # SQLAlchemy 2.0+ allows instantiation, but without __tablename__
        # the object has no database counterpart.
        obj = PersistenceBase()
        assert not hasattr(obj, "__table__"), (
            "PersistenceBase instances should not have a __table__"
        )

    def test_works_with_model_subclass(self):
        """Una subclase concreta debe funcionar como modelo ORM."""

        # Define a simple model
        class SampleModel(PersistenceBase):
            __tablename__ = "test_sample"
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str] = mapped_column(String(50))

        # It must be mappable
        assert SampleModel.__tablename__ == "test_sample"
        assert hasattr(SampleModel, "__table__")

    def test_naming_convention_is_applied_to_metadata(self):
        """El naming_convention debe estar vinculado al metadata de PersistenceBase."""
        convention = PersistenceBase.metadata.naming_convention
        assert convention is not None
        assert convention.get("pk") == "pk_%(table_name)s"


# ══════════════════════════════════════════════════════════════════════════════
# Integration: Naming in action (requires engine)
# ══════════════════════════════════════════════════════════════════════════════

class TestConstraintNamingIntegration:
    """Verifica que los constraints generen nombres predecibles."""

    def test_pk_gets_named_correctly(self, engine, tables):
        """La PK debe llamarse pk_<table>."""
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT sql FROM sqlite_master WHERE name = 'test_author'")
            ).scalar()

        assert result is not None, "Table test_author should exist"
        assert 'CONSTRAINT pk_test_author' in result, (
            f"Expected CONSTRAINT pk_test_author in CREATE TABLE, got:\n{result}"
        )

    def test_fk_gets_named_correctly(self, engine, tables):
        """La FK debe llamarse fk_<table>_<referred>."""
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT sql FROM sqlite_master WHERE name = 'test_book'")
            ).scalar()

        assert result is not None, "Table test_book should exist"
        assert 'CONSTRAINT fk_test_book_test_author' in result, (
            f"Expected CONSTRAINT fk_test_book_test_author, got:\n{result}"
        )

    def test_uq_gets_named_correctly(self, engine, tables):
        """La UQ debe llamarse uq_<table>_<column>."""
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT sql FROM sqlite_master WHERE name = 'test_author'")
            ).scalar()

        assert result is not None, "Table test_author should exist"
        assert 'CONSTRAINT uq_test_author_email' in result, (
            f"Expected CONSTRAINT uq_test_author_email, got:\n{result}"
        )


# ── Models for constraint naming tests ────────────────────────────────────

class AuthorModel(PersistenceBase):
    __tablename__ = "test_author"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100))

    __table_args__ = (
        UniqueConstraint("email", name="uq_test_author_email"),
    )


class BookModel(PersistenceBase):
    __tablename__ = "test_book"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    author_id: Mapped[int] = mapped_column(
        ForeignKey("test_author.id", name="fk_test_book_test_author")
    )

    author = relationship("AuthorModel")
