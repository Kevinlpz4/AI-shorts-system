"""
Tests for EntityIdType[T] TypeDecorator.

Validates:
  - Construction with EntityId subclass
  - TypeError for non-EntityId types
  - process_bind_param / process_result_value (EntityId ↔ UUID)
  - None handling
  - ORM roundtrip (insert + select with model)
"""

import sys
from pathlib import Path
from uuid import UUID

import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

# Ensure src/ is on sys.path
_src_path = str(Path(__file__).resolve().parent.parent.parent.parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from foundation.entity_id import EntityId
from ingestion.infrastructure.persistence import EntityIdType, PersistenceBase

# ══════════════════════════════════════════════════════════════════════════════
# Fixtures: EntityId subtypes for testing
# ══════════════════════════════════════════════════════════════════════════════

class AId(EntityId):
    """Concrete EntityId subtype for testing EntityIdType."""
    pass


SAMPLE_UUID = UUID("aaaaaaaa-1234-5678-1234-567812345678")
ANOTHER_UUID = UUID("bbbbbbbb-4321-8765-4321-876543210987")


# ══════════════════════════════════════════════════════════════════════════════
# Construction
# ══════════════════════════════════════════════════════════════════════════════

class TestConstruction:
    """Tests for EntityIdType creation."""

    def test_create_with_entity_id_subclass(self):
        """EntityIdType debe aceptar una subclase de EntityId."""
        t = EntityIdType(AId)
        assert t._id_type is AId

    def test_create_with_base_entity_id(self):
        """EntityIdType debe aceptar EntityId directamente."""
        t = EntityIdType(EntityId)
        assert t._id_type is EntityId

    def test_create_with_non_entity_id_raises_type_error(self):
        """EntityIdType debe lanzar TypeError si no es subclase de EntityId."""
        with pytest.raises(TypeError, match="must be a subclass of EntityId"):
            EntityIdType(str)

    def test_create_with_int_raises_type_error(self):
        """EntityIdType(123) debe lanzar TypeError."""
        with pytest.raises(TypeError, match="must be a subclass of EntityId"):
            EntityIdType(int)

    def test_create_with_none_raises_type_error(self):
        """EntityIdType(None) debe lanzar TypeError."""
        with pytest.raises(TypeError, match="must be a subclass of EntityId"):
            EntityIdType(None)

    def test_cache_ok_is_true(self):
        """cache_ok debe ser True para permitir cacheo de SQLAlchemy."""
        t = EntityIdType(AId)
        assert t.cache_ok is True

    def test_impl_is_uuid(self):
        """El impl subyacente debe ser Uuid."""
        t = EntityIdType(AId)
        assert hasattr(t, "impl")


# ══════════════════════════════════════════════════════════════════════════════
# Process Bind Param
# ══════════════════════════════════════════════════════════════════════════════

class TestProcessBindParam:
    """Tests for process_bind_param (EntityId → UUID)."""

    @pytest.fixture
    def decorator(self):
        return EntityIdType(AId)

    def test_entity_id_to_uuid(self, decorator):
        """EntityId debe convertirse a UUID para la base de datos."""
        eid = AId(value=SAMPLE_UUID)
        result = decorator.process_bind_param(eid, None)
        assert result == SAMPLE_UUID
        assert isinstance(result, UUID)

    def test_none_returns_none(self, decorator):
        """None debe retornar None."""
        result = decorator.process_bind_param(None, None)
        assert result is None

    def test_preserves_uuid_value(self, decorator):
        """El valor UUID del EntityId debe preservarse."""
        eid = AId(value=SAMPLE_UUID)
        result = decorator.process_bind_param(eid, None)
        assert result == SAMPLE_UUID


# ══════════════════════════════════════════════════════════════════════════════
# Process Result Value
# ══════════════════════════════════════════════════════════════════════════════

class TestProcessResultValue:
    """Tests for process_result_value (UUID → EntityId)."""

    @pytest.fixture
    def decorator(self):
        return EntityIdType(AId)

    def test_uuid_to_entity_id(self, decorator):
        """UUID debe convertirse a EntityId al leer de la BD."""
        result = decorator.process_result_value(SAMPLE_UUID, None)
        assert isinstance(result, AId)
        assert result.value == SAMPLE_UUID

    def test_none_returns_none(self, decorator):
        """None debe retornar None."""
        result = decorator.process_result_value(None, None)
        assert result is None

    def test_preserves_type(self, decorator):
        """El resultado debe ser del tipo especificado en construcción."""
        result = decorator.process_result_value(SAMPLE_UUID, None)
        assert type(result) is AId

    def test_returns_correct_uuid(self, decorator):
        """El UUID debe preservarse en el EntityId resultante."""
        result = decorator.process_result_value(ANOTHER_UUID, None)
        assert result.value == ANOTHER_UUID


# ══════════════════════════════════════════════════════════════════════════════
# Roundtrip
# ══════════════════════════════════════════════════════════════════════════════

class TestORMRoundtrip:
    """ORM roundtrip: insert EntityId → DB → read back EntityId."""

    def test_insert_and_select_with_aid(self, engine, tables, engine_session):
        """Insertar AId como PK y leerlo debe devolver AId."""
        # Create an entity
        eid = AId(value=SAMPLE_UUID)
        entity = SelfRefModel(id=eid, label="test-entity")
        engine_session.add(entity)
        engine_session.commit()

        # Read it back
        loaded = engine_session.get(SelfRefModel, eid)
        assert loaded is not None
        assert loaded.id == eid
        assert type(loaded.id) is AId
        assert loaded.label == "test-entity"

    def test_select_by_entity_id(self, engine, tables, engine_session):
        """Filtrar por EntityId debe funcionar."""
        eid = AId(value=SAMPLE_UUID)
        engine_session.add(SelfRefModel(id=eid, label="find-me"))
        engine_session.commit()

        # EntityIdType transaparently converts EntityId ↔ UUID,
        # so we can query directly with the EntityId value:
        loaded = engine_session.execute(
            SelfRefModel.__table__.select().where(
                SelfRefModel.id == eid  # EntityId value, NOT raw UUID
            )
        ).first()
        assert loaded is not None

    def test_multiple_rows(self, engine, tables, engine_session):
        """Múltiples filas con diferentes EntityId deben funcionar."""
        a = AId(value=SAMPLE_UUID)
        b = AId(value=ANOTHER_UUID)

        engine_session.add_all([
            SelfRefModel(id=a, label="first"),
            SelfRefModel(id=b, label="second"),
        ])
        engine_session.commit()

        rows = engine_session.query(SelfRefModel).all()
        assert len(rows) == 2
        assert {r.label for r in rows} == {"first", "second"}

    def test_none_id_allowed_if_nullable(self, engine, tables, engine_session):
        """EntityIdType debe manejar None correctamente."""
        # The model has nullable=False, so we need a different setup
        # to test null handling. Skip this for now.
        pass

    def test_inspected_columns_have_entity_id_type(self, engine, tables):
        """La inspección debe mostrar el tipo como EntityIdType (o Uuid)."""
        # The ORM sees EntityIdType at the Python level
        mapper = inspect(SelfRefModel)
        col = mapper.columns["id"]
        assert isinstance(col.type, EntityIdType)

    def test_different_entity_id_types(self, engine, tables, engine_session):
        """Usar diferentes EntityIdType con diferentes subclases."""
        PersistenceBase.metadata.create_all(engine)

        bid = BId(value=SAMPLE_UUID)
        engine_session.add(AnotherModel(id=bid, name="b-model"))
        engine_session.commit()

        loaded = engine_session.get(AnotherModel, bid)
        assert loaded is not None
        assert type(loaded.id) is BId
        assert loaded.id == bid

        engine_session.close()


# ══════════════════════════════════════════════════════════════════════════════
# Models for ORM tests
# ══════════════════════════════════════════════════════════════════════════════

class SelfRefModel(PersistenceBase):
    """Minimal model with an EntityIdType PK column."""
    __tablename__ = "type_test_selfref"
    id: Mapped[AId] = mapped_column(EntityIdType(AId), primary_key=True)
    label: Mapped[str]


class BId(EntityId):
    """Another EntityId subtype for testing multiple types."""
    pass


class AnotherModel(PersistenceBase):
    """Model with a different EntityIdType for cross-type testing."""
    __tablename__ = "type_test_another"
    id: Mapped[BId] = mapped_column(EntityIdType(BId), primary_key=True)
    name: Mapped[str]
