# Design: Sprint 5.4B — Domain Event Publication (Post-Commit)

## Technical Approach

Integrar `EventPublisher` en `SQLAlchemyUnitOfWork.commit()` para publicar eventos
colectados post-commit. El publisher concreto es `SQLAlchemyEventPublisher`
(in-memory, sin IO, preparado para Outbox en 5.5). El Protocol NO se duplica —
se reusa el existente en `application.ports.event_publisher` (ya usado por
los services). Se elimina el stub local de `unit_of_work.py`.

## Architecture Decisions

### Decision 1: Protocol location — reuse application.ports, NOT duplicate

| Opción | Trade-off | Decisión |
|--------|-----------|----------|
| Mover Protocol a `infrastructure/event_publisher.py` | Duplica el contrato ya existente en `application.ports`; viola DIP (infrastructure definiendo ports) | ❌ |
| Reusar `application.ports.event_publisher.EventPublisher` | Ya es usado por `article_service`, `feed_service`, `source_service`; dirección de dependencia correcta (app → infra) | ✅ |
| Mantener stub local en `unit_of_work.py` | Duplicación; dos Protocols que evolucionan separados | ❌ |

**Rationale**: El Protocol ya existe en `application/ports/event_publisher.py` con
`publish()` y `publish_many()`. Reusarlo evita duplicación, mantiene DIP, y
unifica el contrato en toda la BC. El stub local se elimina.

### Decision 2: Naming — SQLAlchemyEventPublisher

| Opción | Trade-off | Decisión |
|--------|-----------|----------|
| `SQLAlchemyEventPublisher` | Nombre consistente con `SQLAlchemyUnitOfWork`, `SQLAlchemyCategoryRepository`, etc. | ✅ |
| `InMemoryEventPublisher` | Ya existe en `infrastructure.inmemory` para testing; sería confuso tener dos "InMemory" en paquetes distintos | ❌ |

**Rationale**: La implementación concreta sigue el naming de infraestructura
SQLAlchemy existente. Es in-memory por ahora pero evolucionará a Outbox.

### Decision 3: Failure policy — commit-first, never rollback on publish failure

| Condition | Action | Rationale |
|-----------|--------|-----------|
| `session.commit()` fails | `rollback()`, raise `PersistenceError` | Ya implementado en 5.4A |
| `publish_many()` fails | Raise `PersistenceError`, NO rollback | ADR-025: commit ya fue exitoso; rollback no tiene sentido |
| `publish_many()` partial | Algunos eventos publicados antes del crash | Limitación documentada — Outbox (5.5) resuelve atomicidad |

## Data Flow

```
Service.call()
  │
  ├─ uow.__enter__()           # crea Session, inicia 5 repos
  ├─ repo.save(aggregate)      # persiste cambios
  ├─ uow.register_modified(agg) # trackea root para event collection
  │
  ├─ uow.commit()
  │   ├─ session.commit()       # 1. Persiste en DB     ─── FAIL → rollback + PersistenceError
  │   ├─ _collect_events()      # 2. pull_events() de cada root modificado
  │   ├─ publisher.publish_many() # 3. Publica eventos  ─── FAIL → PersistenceError, NO rollback
  │   └─ _collected_events.clear() # 4. Limpia (solo si publish OK)
  │
  └─ uow.__exit__()             # close session
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/ingestion/infrastructure/event_publisher.py` | **Create** | `SQLAlchemyEventPublisher`: implementa `EventPublisher` Protocol, almacena eventos en `list[DomainEvent]` |
| `src/ingestion/infrastructure/persistence/unit_of_work.py` | **Modify** | Eliminar `EventPublisher` stub local; importar de `application.ports`; integrar `publish_many` en `commit()` |
| `tests/ingestion/infrastructure/persistence/test_event_publisher.py` | **Create** | Tests unitarios + integración con UoW |

## Interfaces / Contracts

### EventPublisher Protocol (existing — NO changes)

```python
# ingestion/application/ports/event_publisher.py — UNCHANGED
class EventPublisher(Protocol):
    def publish(self, event: DomainEvent) -> None: ...
    def publish_many(self, events: list[DomainEvent]) -> None: ...
```

### SQLAlchemyEventPublisher (new)

```python
# ingestion/infrastructure/event_publisher.py
class SQLAlchemyEventPublisher:
    """In-memory event publisher. Stores events for inspection.
    No external IO. Prepared for Outbox evolution (Sprint 5.5)."""

    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    def publish(self, event: DomainEvent) -> None:
        self.events.append(event)

    def publish_many(self, events: list[DomainEvent]) -> None:
        self.events.extend(events)
```

### UoW commit() integration (modified)

```python
# unit_of_work.py — commit() method
def commit(self) -> None:
    if self._session is None:
        raise PersistenceError("Cannot commit: no active session")

    try:
        self._session.commit()
    except SQLAlchemyError as exc:
        self._session.rollback()
        raise PersistenceError(f"Commit failed: {exc}") from exc

    self._collect_events()

    # NEW: Sprint 5.4B — Publish collected events
    if self._event_publisher is not None and self._collected_events:
        try:
            self._event_publisher.publish_many(self._collected_events)
        except Exception as exc:
            raise PersistenceError(
                f"Commit succeeded but event publication failed: {exc}"
            ) from exc

    self._collected_events.clear()
```

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Unit | `SQLAlchemyEventPublisher.publish()` | Crea publisher, llama `publish(e)` → `events == [e]` |
| Unit | `SQLAlchemyEventPublisher.publish_many()` | Crea publisher, llama `publish_many([e1, e2])` → `events == [e1, e2]` |
| Integration | Commit + publish flow | UoW con publisher: `register_modified` + `commit` → publisher recibe eventos |
| Integration | Commit fails → no publish | Mock `session.commit` to raise → publisher NUNCA llamado |
| Integration | Publish fails → no rollback | Mock `publish_many` to raise → commit NO revertido, `PersistenceError` |
| Integration | Second commit no-op | Commit dos veces sin cambios → `publish_many` llamado solo primera vez |
| Integration | Ordering | Eventos preservan orden de inserción en `publish_many` |
| Non-regression | 19 tests de UoW pasan | `test_unit_of_work.py` corre sin `event_publisher` (default None) |

## Migration / Rollout

No migration required. Backward compatible: tests existentes crean UoW sin
`event_publisher` (default `None`) → publicación se salta. Cero cambios
en Foundation, Domain, Application layers.

## Open Questions

Ninguno. Diseño completo y consistente con la base de código existente.

## Appendix: Key Finding

Durante la exploración se descubrió que `application/ports/event_publisher.py`
YA define el `EventPublisher` Protocol con `publish()` y `publish_many()`.
Este Protocol es el que usan `article_service`, `feed_service`, `source_service`.
El diseño reusa este Protocol en lugar de crear uno nuevo en infrastructure,
alineándose con DIP y eliminando la duplicación del stub en `unit_of_work.py`.
