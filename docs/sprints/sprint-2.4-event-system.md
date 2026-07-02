# Sprint 2.4: Foundation Event System

> **Status**: COMPLETED  
> **Implementation verification**: 221 tests passing  

## Change Scope

Introducir el modelo base de eventos del Foundation Layer: `DomainEvent` (intra-BC) e `IntegrationEvent` (cross-BC), y actualizar `AggregateRoot` para tipar `_events` como `list[DomainEvent]`.

## Requirements

### REQ-01: DomainEvent base class

- **Type**: `@dataclass(frozen=True)`
- **Fields**:
  - `event_id: UUID` — auto-generado via `field(default_factory=uuid4)`
  - `event_version: int` — default `1`
  - `occurred_at: datetime` — auto-generado via `field(default_factory=_utcnow)` (timezone-aware UTC)
- **event_name**: `@property` computada que retorna `type(self).__name__` — NO es un campo de dataclass
- **Frozen**: No se puede mutar ninguna propiedad (FrozenInstanceError)
- **No es Exception**: `not isinstance(event, Exception)`
- **Hashable/Equality**: La igualdad es estructural (todos los campos) — funciona en sets y como key de dict
- **Herencia**: Subclases con `@dataclass(frozen=True)` heredan todos los campos y comportamiento

#### Scenarios

1. **Default construction**: `DomainEvent()` crea instancia con UUID válido, event_version=1, occurred_at no-None
2. **Custom event_id**: `DomainEvent(event_id=uuid)` usa el UUID provisto
3. **Custom event_version**: `DomainEvent(event_version=2)` usa el version provisto
4. **event_name property**: `DomainEvent().event_name == "DomainEvent"`
5. **event_name in subclass**: Subclase `TopicDiscovered(DomainEvent)` → `event_name == "TopicDiscovered"`
6. **event_name is NOT a field**: `event.event_name = "x"` → `AttributeError`
7. **Frozen**: `event.event_id = new_uuid` → `FrozenInstanceError`
8. **Equality**: Dos eventos con mismos fields (incluyendo occurred_at) son `==` y mismo `hash()`
9. **Inequality**: Eventos con distinto `event_id` NO son `==`
10. **Not Exception**: `not isinstance(DomainEvent(), Exception)`
11. **Hashable in set**: `{DomainEvent(...), DomainEvent(...)}` deduplica por igualdad
12. **Subclass with extra fields**: Subclase puede agregar campos con defaults

### REQ-02: IntegrationEvent base class

- **Type**: `@dataclass(frozen=True)` — NO hereda de DomainEvent (son siblings, el foundation NO conoce dominio)
- **Fields**:
  - `event_id: UUID` — auto-generado
  - `event_version: int` — default `1`
  - `source_boundary: str` — default `""` (subclases DEBEN setearlo)
  - `correlation_id: str | None` — default `None`
  - `causation_id: UUID | None` — default `None`
  - `occurred_at: datetime` — auto-generado UTC
- **event_name**: `@property` computada — mismo patrón que DomainEvent
- **Frozen**: Mismas restricciones
- **No es Exception**
- **Hashable/Equality**: Igualdad estructural

#### Scenarios

1. **Default construction**: `IntegrationEvent()` con UUID, event_version=1, source_boundary="", correlation_id=None, causation_id=None
2. **event_name property**: `IntegrationEvent().event_name == "IntegrationEvent"`
3. **source_boundary**: `IntegrationEvent(source_boundary="research")`
4. **correlation_id**: `IntegrationEvent(correlation_id="corr-123")`
5. **causation_id**: `IntegrationEvent(causation_id=uuid)`
6. **event_name in subclass**: Subclase `TopicPublished(IntegrationEvent)` → `event_name == "TopicPublished"`
7. **event_name is NOT a field**: `event.event_name = "x"` → `AttributeError`
8. **Frozen**: `event.event_id = new_uuid` → `FrozenInstanceError`
9. **Equality**: Dos eventos con mismos fields son `==` y mismo `hash()`
10. **Inequality**: Eventos con distinto event_id NO son `==`
11. **Not Exception**
12. **Hashable in dict**: Funciona como key de dict

### REQ-03: AggregateRoot type narrowing

- `_events` cambia de `list[Any]` a `list[DomainEvent]`
- `register_event(event: DomainEvent)` — valida tipo, `TypeError` si no es DomainEvent
- `pull_events()` — devuelve `list[DomainEvent]` (defensive copy)
- Eventos NO afectan igualdad ni hash del AggregateRoot
- `repr` NO incluye `_events`

#### Scenarios

1. **register_event**: `register_event(DomainEvent())` almacena sin error
2. **register_multiple**: Múltiples eventos se acumulan
3. **register_rejects_non_domain_event**: `register_event("string")` → `TypeError`
4. **pull_events**: Devuelve lista con eventos registrados
5. **pull_events clears**: Después de pull, la lista interna está vacía
6. **pull_without_register**: `pull_events()` sin eventos → `[]`
7. **Defensive copy**: Mutar la lista devuelta no afecta el interno
8. **Events not in equality**: Dos ARs con diferentes eventos pero mismo ID son iguales
9. **Events not in hash**: El hash depende solo del EntityId
10. **repr**: `repr(ar)` no contiene "_events" ni nombres de eventos

### REQ-04: Foundation re-exports

- `DomainEvent` e `IntegrationEvent` exportados desde `foundation.__init__`

#### Scenarios

1. `from foundation import DomainEvent` funciona
2. `from foundation import IntegrationEvent` funciona

## Design Constraints

1. **Zero external dependencies**: stdlib-only (dataclasses, uuid, datetime)
2. **DomainEvent e IntegrationEvent son siblings**: No hay herencia entre ellos. Ambos son `@dataclass(frozen=True)` independientes. Esto porque Foundation NO conoce el dominio — no puede modelar "IntegrationEvent extends DomainEvent" como relación de dominio.
3. **event_name como @property (no campo)**: Evita `__post_init__`, evita mutación en objetos frozen, evita problemas de herencia de dataclasses con defaults. El nombre SIEMPRE coincide con la clase.
4. **IntegrationEvent NO tiene source_boundary requerido en constructor**: Tiene default `""`. La validación de que una subclase lo setee es por convención, no por enforcement en Foundation (porque Foundation no conoce los BCs).
5. **AggregateRoot usa list[DomainEvent] solamente**: No almacena IntegrationEvents. Los IntegrationEvents son responsabilidad del Application Service / Message Bus.
6. **Architecture Baseline v1.0 FROZEN**: Cualquier cambio que rompa baseline requiere ADR.

## Files

### New

| File | Purpose |
|------|---------|
| `src/foundation/events/_utcnow.py` | Helper UTC timestamp |
| `src/foundation/events/domain_event.py` | DomainEvent class |
| `src/foundation/events/integration_event.py` | IntegrationEvent class |
| `src/foundation/events/__init__.py` | Event system package re-exports |
| `tests/foundation/test_events.py` | ~25 tests for DomainEvent + IntegrationEvent |

### Modified

| File | Change |
|------|--------|
| `src/foundation/__init__.py` | Added DomainEvent, IntegrationEvent exports |
| `src/foundation/base/aggregate_root.py` | `_events: list[DomainEvent]`, register_event type validation |
| `tests/foundation/test_aggregate_root.py` | Updated to use DomainEvent in register_event |

## ADRs Referenced

- **ADR-021**: Foundation Stability Policy — Foundation no se modifica sin ADR + 5 criterios
- **ADR-022**: ErrorCode Enum Inheritance — Documenta que Python 3.11+ no permite subclassing enums con miembros
