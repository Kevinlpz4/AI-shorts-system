---
title: "ARB Pre-Implementation Report — Sprint 5.1 Persistence Foundation"
status: "APPROVED FOR IMPLEMENTATION"
date: "2026-07-05"
---

# ARB Pre-Implementation Report: Sprint 5.1 — Persistence Foundation

> **Verificación de componentes FROZEN, revisión de alcance, y autorización para comenzar implementación**

---

## 1. Verificación de Componentes FROZEN

### Foundation v1.0 — ✅ FROZEN, 0 modificaciones requeridas

| Componente | Verificación |
|------------|-------------|
| `EntityId` (`@dataclass(frozen=True)`, `value: UUID`) | ✅ El TypeDecorator genérico usa `entity_id.value` para bind y `cls(value=uuid)` para result. NO modifica Foundation. |
| `AggregateRoot` | ✅ No se toca. Sprint 5.1 no implementa repositorios. |
| `DomainEvent` | ✅ No se toca. Sprint 5.1 no implementa event publication. |
| `Result[T]` | ✅ No se toca. Los repositorios no se implementan en este sprint. |
| `ValueObject` | ✅ No se toca. No se implementan TypeDecorators de VOs todavía. |

**Conclusión**: Foundation no necesita cambios. Zero archivos modificados.

### Ingestion Domain v2.0 — ✅ FROZEN, 0 modificaciones requeridas

| Componente | Verificación |
|------------|-------------|
| `ids.py` (SourceId, FeedId, RawArticleId, CategoryId, TopicId) | ✅ El TypeDecorator recibe el tipo concreto como parámetro. NO modifica los IDs. |
| `ports/repositories.py` (5 Protocols) | ✅ No se implementan repositorios en este sprint. |
| `entities/`, `value_objects/`, `events/`, `exceptions/` | ✅ Ninguno se modifica. |

**Conclusión**: Domain no necesita cambios. Zero archivos modificados.

### Application Layer — ✅ FROZEN, 0 modificaciones requeridas

| Componente | Verificación |
|------------|-------------|
| `ports/unit_of_work.py` | ✅ No se implementa UoW SQLAlchemy todavía. |
| `ports/event_publisher.py` | ✅ No se implementa event publisher todavía. |
| `services/`, `commands/`, `queries/`, `dto/`, `mappers/` | ✅ Ninguno se modifica. |

**Conclusión**: Application Layer no necesita cambios. Zero archivos modificados.

---

## 2. Revisión de Warnings del ARB

| W | Título | ¿Bloquea Sprint 5.1? | Acción |
|---|--------|---------------------|--------|
| W-01 | SyncPolicy composite wrapper | ❌ No (Sprint 5.2) | Pospuesto |
| W-02 | UUID v7 para RawArticleId | ❌ No (Sprint 5.3) | Pospuesto |
| W-03 | InMemory ↔ SQLAlchemy tests | ❌ No (Sprint 5.3) | Pospuesto |
| W-04 | Post-commit event loss | ❌ No (Sprint 5.4) | Pospuesto |

**Ningún warning requiere resolución pre-implementación.**

---

## 3. Confirmación de Alcance (Sprint 5.1)

### ✅ IN SCOPE

| Componente | Archivo destino | Dependencias |
|-----------|----------------|--------------|
| DeclarativeBase + Metadata | `persistence/base.py` | SQLAlchemy 2.x |
| Engine Factory | `persistence/engine.py` | `base.py`, config |
| Session Factory | `persistence/engine.py` | Engine |
| Configuration (Pydantic) | `persistence/config.py` | Pydantic Settings |
| Persistence Exceptions | `persistence/exceptions.py` | Foundation (DomainError) |
| TypeDecorator Base (EntityIdType genérico) | `persistence/types.py` | `EntityId`, Foundation |
| Testing Utilities | `tests/infrastructure/conftest.py` | Engine, Session |

### ❌ OUT OF SCOPE (para sprints posteriores)

| Componente | Sprint |
|-----------|--------|
| ORM Models (NewsSourceModel, etc.) | 5.2 |
| TypeDecorators de Value Objects (ArticleTitleType, etc.) | 5.1/5.2 |
| `composite()` para SyncPolicy | 5.2 |
| Repository Implementations | 5.3 |
| UnitOfWork SQLAlchemy | 5.4 |
| Event Publisher + Post-commit hooks | 5.4 |
| Alembic + Migrations | 5.5 |

---

## 4. TypeDecorator Base — Diseño Confirmado

```python
from typing import TypeVar
from uuid import UUID

from sqlalchemy.types import TypeDecorator, Uuid

from foundation.entity_id import EntityId

T = TypeVar("T", bound=EntityId)

class EntityIdType(TypeDecorator[T]):
    """Generic TypeDecorator for any EntityId subtype.
    
    Usage::
    
        class SourceIdType(EntityIdType[SourceId]):
            pass  # inherits everything
    """
    
    impl = Uuid
    cache_ok = True
    
    def process_bind_param(self, value: T | None, dialect) -> UUID | None:
        if value is None:
            return None
        return value.value  # EntityId.value: UUID
    
    def process_result_value(self, value: UUID | None, dialect) -> T | None:
        if value is None:
            return None
        return self._id_type(value=value)  # constructor: EntityId(value=UUID)
```

**Nota**: `impl = Uuid` (SQLAlchemy 2.x native UUID type) en lugar de `UUID` (postgres-only) para portabilidad con SQLite.

**Nota 2**: No se implementan subclases concretas en Sprint 5.1 — solo el base `EntityIdType[T]`. Las subclases se crean en Sprint 5.2 cuando se mapeen los modelos ORM.

---

## 5. Estructura de Archivos Propuesta

```
src/ingestion/infrastructure/persistence/
├── __init__.py              # Public exports
├── base.py                  # IngestionBase (DeclarativeBase), metadata, naming_convention
├── engine.py                # create_ingestion_engine(), create_session_factory()
├── config.py                # IngestionSettings (Pydantic BaseSettings)
├── exceptions.py            # PersistenceError, IngestionPersistenceError
└── types.py                 # EntityIdType[T], base TypeDecorator
```

---

## 6. Dependencias Externas

```python
# requirements.txt (additions)
sqlalchemy>=2.0.30
pydantic-settings>=2.2.0
```

SQLAlchemy para ORM + Core.
Pydantic Settings para configuración.
**No se requiere Alembic todavía.**

---

## 7. Testing Plan

| Test | Archivo | Verifica |
|------|---------|----------|
| Engine creation (SQLite) | `test_engine.py` | `create_ingestion_engine()` con URL SQLite |
| Engine creation (PostgreSQL) | `test_engine.py` | `create_ingestion_engine()` con URL PostgreSQL (mock) |
| Session lifecycle | `test_session.py` | `sessionmaker`, context manager, commit, rollback |
| Configuration loading | `test_config.py` | defaults, env vars, `.env` override |
| TypeDecorator round-trip | `test_types.py` | EntityIdType con SourceId, FeedId, etc. |
| DeclarativeBase metadata | `test_base.py` | naming_convention, table names |
| Exceptions | `test_exceptions.py` | inheritance, str representation |
| Engine isolation (test) | `test_engine.py` | `create_test_engine()` with `:memory:` |

---

## ✅ Veredicto: APROBADO PARA IMPLEMENTACIÓN

> Sprint 5.1 ha sido verificado contra todos los componentes FROZEN:
> - **Foundation v1.0**: 0 modificaciones ✅
> - **Ingestion Domain v2.0**: 0 modificaciones ✅
> - **Application Layer**: 0 modificaciones ✅
> - **ADR-021, ADR-023, ADR-024, ADR-025**: Respetados ✅
>
> **Ningún warning es blocker para este sprint.** Los 4 warnings corresponden a sprints posteriores.
>
> **Alcance confirmado**: Solo Persistence Base, Engine, Session, Config, Exceptions, TypeDecorator Base, Testing Utilities. Sin modelos ORM, sin repositorios, sin migraciones.
>
> **Riesgos**: 0 (todos los componentes son ortogonales y no tocan capas existentes).
>
> **Se autoriza el inicio de la implementación.**
