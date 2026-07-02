# Sprint 2.2 — Foundation Domain Building Blocks

> **Proyecto**: AI Shorts System
> **Epic**: 2 — Foundation Layer
> **Sprint**: 2.2 — Domain Building Blocks
> **Estado**: APPROVED
> **Fecha**: 2026-07-02
> **Stack**: Python 3.12.3, stdlib-only

---

## 1. Objetivo del Sprint

Implementar las **tres clases base del modelo de dominio DDD**: ValueObject, Entity
y AggregateRoot. Sobre estas clases se construirán TODAS las entidades y Value Objects
de todos los Bounded Contexts del sistema.

**¿Qué problema resuelve?**

| Problema | Cómo lo resuelve este Sprint |
|----------|------------------------------|
| Cada BC implementa su propia noción de "entidad" | Una base común `Entity` con igualdad por identidad, hash, y contrato claro |
| Value Objects mutables por accidente | `ValueObject` con `@dataclass(frozen=True)` — inmutabilidad garantizada |
| Cada Aggregate Root maneja eventos a su manera | `AggregateRoot` con `register_event()` y `pull_events()` estandarizados |
| Igualdad inconsistente entre entidades | Reglas explícitas en `Entity.__eq__` y `Entity.__hash__` |

---

## 2. Responsabilidades

### 2.1 ValueObject

```
Responsabilidades:
  - Marker class que identifica un Value Object
  - No impone implementación — cada VO concreto elige cómo construirse
  - Provee un tipo base común para type checking y polimorfismo
  - Los VOs concretos DEBEN ser inmutables (usando @dataclass(frozen=True) u otro mecanismo)

NO hace:
  - No impone @dataclass — cada VO concreto decide su implementación
  - No tiene identidad
  - No tiene eventos
  - No tiene ciclo de vida
  - No se persiste solo
  - No provee validación automática (cada VO usa __post_init__ si lo necesita)
```

### 2.2 Entity

```
Responsabilidades:
  - Identidad explícita (self.id: EntityId)
  - Igualdad por identidad (__eq__, __hash__)
  - Mutabilidad controlada (entidad con ciclo de vida)
  - Tipo exacto en igualdad (type(self) is type(other))

NO hace:
  - No tiene eventos (lo hace AggregateRoot)
  - No tiene lógica de persistencia
  - No tiene validación automática
```

### 2.3 AggregateRoot

```
Responsabilidades:
  - TODO lo de Entity (hereda)
  - Registro de Domain Events (register_event)
  - Extracción de eventos (pull_events)
  - Almacenamiento interno transitorio de eventos

NO hace:
  - No publica eventos automáticamente
  - No persiste eventos
  - No sabe de Event Bus
  - No conoce DomainEvent (usa type object transitoriamente)
```

---

## 3. Alcance

### 3.1 Qué pertenece al Sprint

| Componente | Descripción |
|-----------|-------------|
| **ValueObject** | Base class frozen para VOs. Provee inmutabilidad, `__post_init__` hook, igualdad estructural, hash. |
| **Entity** | Base class mutable con `id: EntityId`. Provee igualdad por identidad (tipo exacto + mismo ID), hash. |
| **AggregateRoot** | Extiende Entity con `_events` interno, `register_event()`, `pull_events()`. API preparada para DomainEvent (Sprint 2.4+). |
| **base package** | `foundation/base/__init__.py` con exports públicos. |
| **API pública** | `foundation/__init__.py` actualizado para exportar ValueObject, Entity, AggregateRoot. |

### 3.2 Qué NO pertenece al Sprint

| Componente | Excluido porque... | Sprint asignado |
|-----------|-------------------|-----------------|
| Result[T], Success, Failure | Patrón de resultado, no building block | Sprint 2.3 |
| Error, ErrorCode | Modelo de error | Sprint 2.3 |
| FoundationError, DomainError | Jerarquía de excepciones | Sprint 2.4 |
| DomainEvent | Evento de dominio — AggregateRoot usa type object transitoriamente | Sprint 2.4 |
| IntegrationEvent | Evento entre BCs | Sprint 2.5 |
| ClockPort, UUIDProvider | Puertos de infraestructura | Sprint 2.6 |
| Cualquier lógica de negocio | Foundation NO tiene lógica de negocio | Jamás |

### 3.3 Verificación contra ADR-021 (Foundation Stability Policy)

| Criterio | ¿Cumple? | Explicación |
|----------|----------|-------------|
| MULTI-BC (usado por ≥2 BCs) | ✅ Sí | TODO BC usa ValueObject, Entity y AggregateRoot |
| NO BUSINESS RULES | ✅ Sí | No hay semántica de negocio — son mecanismos técnicos |
| ZERO DEPENDENCIES | ✅ Sí | Solo stdlib (dataclasses, typing, uuid — ya usados en Sprint 2.1) |
| NO COUPLING | ✅ Sí | No referencia ningún BC |
| MECHANISM, NOT POLICY | ✅ Sí | Son building blocks de DDD, no reglas de negocio |

---

## 4. Archivos

### 4.1 Archivos a crear

| Ruta | Contenido | Depende de |
|------|-----------|------------|
| `src/foundation/base/__init__.py` | Re-exporta ValueObject, Entity, AggregateRoot | entity.py, value_object.py, aggregate_root.py |
| `src/foundation/base/value_object.py` | `ValueObject` — `@dataclass(frozen=True)` | N/A |
| `src/foundation/base/entity.py` | `Entity` — `@dataclass` con `id: EntityId`, `__eq__`, `__hash__` | `EntityId` (Sprint 2.1) |
| `src/foundation/base/aggregate_root.py` | `AggregateRoot(Entity)` — `_events`, `register_event()`, `pull_events()` | `Entity` |
| `tests/foundation/test_value_object.py` | Tests de ValueObject | N/A |
| `tests/foundation/test_entity.py` | Tests de Entity | N/A |
| `tests/foundation/test_aggregate_root.py` | Tests de AggregateRoot | N/A |

### 4.2 Archivos a modificar

| Ruta | Cambio |
|------|--------|
| `src/foundation/__init__.py` | Agregar `ValueObject`, `Entity`, `AggregateRoot` a los exports |

### 4.3 Archivos excluidos deliberadamente

- `src/foundation/base/domain_event.py` — No pertenece a este sprint (ver Sprint 2.4)
- `src/foundation/_compat.py` — Ya se descartó en Sprint 2.1 (Python 3.12 tiene todo)
- `src/foundation/base/__init__.py` con exports individuales por clase — En su lugar se re-exporta todo desde `foundation/__init__.py`

---

## 5. Dependencias

### 5.1 Dependencias de este Sprint

| Dependencia | Tipo | Detalle |
|------------|------|---------|
| Sprint 2.1 (EntityId) | Runtime | `Entity.id: EntityId` requiere EntityId |
| Python 3.12 | Runtime | `@dataclass`, `typing.Self`, `field` |
| pytest | Testing | Framework de tests |

### 5.2 Dependencias hacia este Sprint

| Componente futuro | ¿Por qué necesita este Sprint? |
|------------------|-------------------------------|
| Sprint 2.3 (Result) | Result no depende de estos tipos, pero los usará |
| Sprint 2.4 (DomainEvent, Errors) | DomainEvent necesita ValueObject (?), AggregateRoot necesita DomainEvent |
| Sprint 3.x (Ingestion Domain) | Source(Entity), Feed(Entity), etc. heredan de Entity |
| Research BC (refactor) | ResearchTopic(Entity) hereda de Entity |
| Todos los BCs futuros | Todas las entidades y VOs del sistema |

### 5.3 Árbol de dependencias

```
Sprint 2.1 (EntityId)
    │
    └──→ Sprint 2.2 (ValueObject, Entity, AggregateRoot)
              │
              ├──→ Sprint 2.3 (Result)
              ├──→ Sprint 2.4 (DomainEvent, Errors)
              ├──→ Sprint 3.x (Ingestion)
              └──→ Research BC (refactor)
```

---

## 6. API Pública

### 6.1 ValueObject

```python
class ValueObject:
    """
    Marker class para todos los Value Objects del sistema.
    
    NO impone @dataclass(frozen=True). Cada Value Object concreto
    elige su implementación, pero DEBE ser inmutable.
    
    Los VOs típicamente se implementan con @dataclass(frozen=True),
    que provee automáticamente:
      - __init__ con todos los campos
      - __eq__ estructural
      - __hash__ basado en todos los campos
      - __repr__ automático
    
    Pero esta decisión queda en manos del VO concreto.
    """
```

### 6.2 Entity

```python
@dataclass
class Entity:
    """
    Base para todas las Entities del sistema.
    
    - Identidad explícita (self.id)
    - Igualdad por tipo concreto Y valor del ID
    - Mutable (tiene ciclo de vida)
    - __hash__ delegado al ID
    """
    id: EntityId
    
    def __eq__(self, other: object) -> bool: ...
    def __hash__(self) -> int: ...
```

### 6.3 AggregateRoot

```python
from typing import Any

@dataclass
class AggregateRoot(Entity):
    """
    Base para todos los Aggregate Roots del sistema.
    
    EXTIENDE Entity. Agrega:
      - _events: almacenamiento interno transitorio de eventos
      - register_event(event): acumula un evento
      - pull_events(): extrae, COPIA DEFENSIVAMENTE y limpia los eventos
    
    AggregateRoot SOLO almacena eventos transitoriamente.
    NO conoce publish, dispatch, commit ni infraestructura.
    """
    _events: list[Any] = field(default_factory=list, repr=False)
    
    def register_event(self, event: Any) -> None: ...
    def pull_events(self) -> list[Any]: ...
```

### 6.4 foundation/__init__.py (actualizado)

```python
from foundation.entity_id import EntityId
from foundation.json_encoder import FoundationEncoder
from foundation.base.value_object import ValueObject
from foundation.base.entity import Entity
from foundation.base.aggregate_root import AggregateRoot

__all__ = [
    "EntityId",
    "FoundationEncoder",
    "ValueObject",
    "Entity",
    "AggregateRoot",
]
```

---

## 7. Decisiones de Diseño

### 7.1 Entity.__eq__ usa type strict, no isinstance

El diseño original (foundation-design.md §3.2) muestra `isinstance(other, type(self))`.
Sin embargo, la sección §11.1 dice textualmente: *"dos entities son iguales si tienen
el MISMO ID y son del MISMO TIPO"*.

La implementación usa **`type(self) is type(other)`** por tres razones:

1. **Consistencia con EntityId**: Sprint 2.1 estableció que `type(self) is type(other)`
   es el patrón correcto para igualdad en Foundation. Entity no debería ser diferente.

2. **Simetría**: `isinstance(other, type(self))` rompe simetría cuando se comparan
   Entity con AggregateRoot: `Entity(x) == AggregateRoot(x)` da True pero
   `AggregateRoot(x) == Entity(x)` da NotImplemented (Python lo resuelve vía
   reflexión, pero la semántica es confusa).

3. **Precisión semántica**: En DDD, dos entidades de diferentes tipos NO son la
   misma entidad aunque tengan el mismo ID. Un `User` y un `AdminUser` (si AdminUser
   extiende User) deberían compararse exactamente.

### 7.2 AggregateRoot._events usa list[Any] transitoriamente

El diseño final especifica `_events: list[DomainEvent]` y `register_event(event: DomainEvent)`.
Sin embargo, DomainEvent pertenece al Sprint 2.4.

Para no bloquear este sprint, se usa **`list[Any]`** como tipo interno temporal.
`Any` es explícitamente temporal y deja clara la intención de migración futura.

La API pública es idéntica: `register_event(event)` acepta cualquier tipo,
`pull_events()` devuelve una lista.

Cuando el Sprint 2.4 implemente DomainEvent, el único cambio será:
- `_events: list[Any]` → `_events: list[DomainEvent]`
- `register_event(event: Any)` → `register_event(event: DomainEvent)`
- `pull_events() -> list[Any]` → `pull_events() -> list[DomainEvent]`

**Esto NO rompe compatibilidad hacia atrás** porque el tipo se estrecha (de general
a específico — `Any` → `DomainEvent`), no se ensancha.

`Any` se elige sobre `object` porque:
- `Any` es el tipo más permisivo — acepta literalmente cualquier valor
- `object` forzaría type narrowing en el usuario
- `Any` comunica explícitamente "placeholder temporal, será reemplazado"

`pull_events()` realiza COPIA DEFENSIVA (`list(self._events)`) antes de limpiar
la colección interna. Esto asegura que quien recibe los eventos no pueda mutar
la colección interna del AggregateRoot.

### 7.3 ValueObject es Marker Class — no impone implementación

ValueObject es intencionalmente una **marker class** (clase marcadora). NO impone
`@dataclass(frozen=True)` ni ningún otro mecanismo de implementación.

**¿Por qué marker class y no `@dataclass(frozen=True)`?**

| Razón | Explicación |
|-------|-------------|
| **Flexibilidad** | No todos los VOs necesitan `@dataclass`. Algunos podrían usar `namedtuple`, `attrs`, o un `__init__` manual con lógica específica. |
| **Responsabilidad única** | Foundation define QUÉ es un Value Object (el contrato). Cada VO define CÓMO se implementa. |
| **Menos acoplamiento** | Si Foundation impusiera `@dataclass`, cambiarlo después rompería todos los VOs. Como marker class, Foundation no se acopla a la implementación. |
| **YAGNI** | No necesitamos métodos en ValueObject todavía. Cuando los necesitemos (al menos 2 VOs compartiendo un patrón), los agregamos. |

**Inmutabilidad**: Aunque Foundation no la impone, TODO Value Object DEBE ser inmutable.
Es una invariante del concepto DDD de Value Object. La verificación es responsabilidad
de code review + tests del VO concreto.

**Validación**: Cada VO concreto implementa `__post_init__` si necesita validación.
Foundation no provee un hook automático porque no impone `@dataclass`.

### 7.4 Entity.id no tiene valor por defecto

```python
id: EntityId  # ← sin default, sin default_factory
```

Cada Entity DEBE recibir un ID explícito en su constructor. No existe una Entity
sin identidad. Esto es deliberado:
- Obliga a quien crea la entidad a decidir qué ID usar
- Evita IDs generados automáticamente que pueden no ser lo que se necesita
- Consistente con DDD: la identidad se asigna en el momento de creación

### 7.5 AggregateRoot._events usa field(default_factory=list)

Usar `default_factory=list` (no `= []`) evita el problema clásico de Python
donde el valor por defecto mutable es compartido entre todas las instancias.

`repr=False` evita que los eventos aparezcan en `__repr__` (serían ruidosos y
potencialmente grandes). `compare=False` es innecesario porque `Entity.__eq__`
override el generado por `@dataclass`.

**Defensive copy en pull_events()**: `pull_events()` usa `list(self._events)` para
crear una NUEVA lista antes de limpiar `self._events.clear()`. Esto asegura que
quien recibe los eventos no pueda mutar la colección interna del AggregateRoot.

---

## 8. Riesgos

| Riesgo | Impacto | Probabilidad | Mitigación |
|--------|---------|-------------|------------|
| **Entity con id mutable**: Si alguien reasigna `entity.id`, la entidad cambia de identidad. `@dataclass` no protege contra esto. | Medio | Baja | Documentar que reasignar `id` rompe invariantes. El type checker no lo previene, pero es una mala práctica evidente en code review. Además, `EntityId` en sí es frozen. |
| **Herencia de dataclasses con fields**: Si una subclase de Entity agrega fields sin default, y Entity tiene `id: EntityId` sin default, no hay conflicto. Pero si Entity tuviera un field con default DESPUÉS de `id`, Python lanzaría error. | Bajo | Baja | Entity solo tiene `id: EntityId` (sin default). Cualquier subclase que agregue fields con defaults no tendrá conflicto. Verificar con tests. |
| **AggregateRoot._events pierde eventos en pull vacío**: Si se llama `pull_events()` cuando no hay eventos, debe devolver lista vacía, no None. | Bajo | Baja | `list(self._events)` sobre lista vacía devuelve `[]`. Test incluido. |
| **ValueObject con campos mutables internos**: `@dataclass(frozen=True)` impide reasignar atributos, pero NO impide mutar objetos internos (ej: `list` dentro de un VO). Un VO con `tags: list[str]` permitiría `vo.tags.append("nuevo")` aunque frozen. | Medio | Alta | Documentar que los VOs NO deben contener tipos mutables. Los tests de aceptación verifican que frozen impide reasignación. La mutación interna es responsabilidad del desarrollador. |
| **Entity.__hash__ cambia si id cambia**: Si se reasigna `entity.id`, el hash cambia y la entidad se pierde en sets/dicts. | Medio | Baja | `id` es un field de dataclass sin protección especial contra reasignación. Mitigado documentando que reasignar `id` es una violación de invariante. |

---

## 9. Casos Borde

### 9.1 ValueObject

#### 9.1.1 Marker class — ValueObject sin atributos ni implementación

```python
class Empty(ValueObject): ...
a = Empty()
b = Empty()
# ValueObject es marker class: no impone __eq__ ni __hash__
# Cada subclass decide su implementación
```

#### 9.1.2 Igualdad estructural (con @dataclass(frozen=True))

```python
@dataclass(frozen=True)
class Address(ValueObject):
    street: str
    city: str

a = Address(street="Main", city="NYC")
b = Address(street="Main", city="NYC")
c = Address(street="Other", city="NYC")

assert a == b    # ✅ Mismos valores (por @dataclass, no por ValueObject)
assert a != c    # ✅ Diferentes valores
assert hash(a) == hash(b)  # ✅ Mismo hash
```

#### 9.1.3 Inmutabilidad (con @dataclass(frozen=True))

```python
@dataclass(frozen=True)
class Address(ValueObject):
    street: str
    city: str

addr = Address(street="Main", city="NYC")
addr.street = "Other"  # ❌ FrozenInstanceError
```

#### 9.1.4 Validación en __post_init__ (con @dataclass(frozen=True))

```python
@dataclass(frozen=True)
class PositiveInt(ValueObject):
    value: int
    
    def __post_init__(self):
        if self.value <= 0:
            raise ValueError("value must be positive")

PositiveInt(value=5)    # ✅
PositiveInt(value=-1)   # ❌ ValueError
```

#### 9.1.5 ValueObject sin @dataclass (implementación manual)

```python
class ManualVO(ValueObject):
    """VO con implementación manual — válido pero NO recomendado."""
    def __init__(self, value: str) -> None:
        self._value = value
    
    @property
    def value(self) -> str:
        return self._value

vo = ManualVO("test")
# NO tiene igualdad estructural automática
# NO es inmutable (a menos que se implemente manualmente)
```

#### 9.1.6 isinstance check polimórfico

```python
@dataclass(frozen=True)
class Address(ValueObject):
    street: str

addr = Address(street="Main")
assert isinstance(addr, ValueObject)  # ✅ Polimorfismo funciona
```

### 9.2 Entity

#### 9.2.1 Igualdad por identidad

```python
id = EntityId.new()
a = Entity(id=id)
b = Entity(id=id)
c = Entity(id=EntityId.new())

assert a == b       # ✅ Mismo ID
assert a != c       # ✅ Diferente ID
assert hash(a) == hash(b)  # ✅ Mismo hash
```

#### 9.2.2 Igualdad por tipo exacto

```python
class Person(Entity): ...
class Company(Entity): ...

same_id = EntityId.new()
person = Person(id=same_id)
company = Company(id=same_id)

assert person != company  # ✅ Diferentes tipos
```

#### 9.2.3 Entity sin ID (error de construcción)

```python
Entity()  # ❌ TypeError: missing argument 'id'
```

#### 9.2.4 Mismas entidades con diferentes atributos

```python
id = EntityId.new()
a = Entity(id=id)
# Dataclass @dataclass en Entity solo tiene id,
# pero en subclase con más atributos:

class Person(Entity):
    name: str

p1 = Person(id=id, name="Alice")
p2 = Person(id=id, name="Bob")
assert p1 == p2  # ✅ Misma identidad, diferentes atributos
```

#### 9.2.5 Entity en sets y dicts

```python
id1 = EntityId.new()
id2 = EntityId.new()

s = {Entity(id=id1), Entity(id=id2)}
assert len(s) == 2

s.add(Entity(id=id1))
assert len(s) == 1  # ✅ Deduplicación por identidad
```

#### 9.2.6 Compare con no-Entity

```python
e = Entity(id=EntityId.new())
assert (e == "string") is False
assert (e == 42) is False
assert (e == None) is False  # noqa: E711
```

### 9.3 AggregateRoot

#### 9.3.1 Registro y extracción de eventos

```python
ar = MyAggregate(id=EntityId.new())
assert ar.pull_events() == []  # ✅ Sin eventos

ar.register_event({"type": "something_happened"})
ar.register_event({"type": "another_event"})
events = ar.pull_events()
assert len(events) == 2   # ✅ Dos eventos registrados
assert ar.pull_events() == []  # ✅ Limpiado después de pull
```

#### 9.3.2 Eventos no afectan igualdad

```python
ar1 = MyAggregate(id=some_id)
ar2 = MyAggregate(id=some_id)

ar1.register_event("event1")
assert ar1 == ar2  # ✅ Iguales aunque ar1 tenga eventos
```

#### 9.3.3 Eventos no aparecen en repr

```python
ar = MyAggregate(id=some_id)
ar.register_event("secret")
assert "_events" not in repr(ar) or "secret" not in repr(ar)
```

#### 9.3.4 Múltiples ciclos register + pull

```python
ar = MyAggregate(id=some_id)
ar.register_event("e1")
assert len(ar.pull_events()) == 1

ar.register_event("e2")
ar.register_event("e3")
assert len(ar.pull_events()) == 2  # ✅ Nuevos eventos
assert len(ar.pull_events()) == 0  # ✅ Vacío
```

#### 9.3.5 Subclase de AggregateRoot

```python
class Order(AggregateRoot):
    total: float

order = Order(id=EntityId.new(), total=99.99)
order.register_event({"type": "order_created"})
assert len(order.pull_events()) == 1
assert order.total == 99.99  # ✅ Atributos de subclase preservados
```

---

## 10. Estrategia de Testing

### 10.1 Estructura de tests

```
tests/foundation/
├── test_entity_id.py       ← Sprint 2.1 (existente)
├── test_value_object.py    ← Nuevo
├── test_entity.py          ← Nuevo
└── test_aggregate_root.py  ← Nuevo
```

### 10.2 Test ValueObject (~18 tests)

ValueObject es marker class, por lo tanto los tests se realizan sobre
**concrete subclasses** con `@dataclass(frozen=True)`.

#### Grupo 1: Marker class

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 1.1 | `test_is_marker_class` | `ValueObject()` | Instancia válida | Válido |
| 1.2 | `test_can_subclass_with_dataclass` | `Address(st="M", c="C")` | Instancia válida | Válido |
| 1.3 | `test_can_subclass_without_dataclass` | `CustomVO()` | Instancia válida | Válido |
| 1.4 | `test_isinstance_check` | `isinstance(addr, ValueObject)` | `True` | Válido |

#### Grupo 2: Igualdad estructural (sobre subclase @dataclass(frozen=True))

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 2.1 | `test_same_values_are_equal` | `Address(st="M", c="C")` ×2 | `== True` | Válido |
| 2.2 | `test_different_values_not_equal` | `Address(st="M", c="C")` vs `Address(st="O", c="C")` | `== False` | Válido |
| 2.3 | `test_equal_vos_have_same_hash` | Mismos valores | `hash()` igual | Válido |
| 2.4 | `test_compare_with_non_vo` | `vo == "string"` | `False` | Edge case |
| 2.5 | `test_vos_with_different_types_not_equal` | `Address(...) == PersonName(...)` | `False` | Edge case |

#### Grupo 3: Inmutabilidad (sobre subclase @dataclass(frozen=True))

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 3.1 | `test_cannot_modify_field` | `vo.field = new_val` | `FrozenInstanceError` | Inválido |
| 3.2 | `test_cannot_add_new_field` | `vo.new_attr = val` | `FrozenInstanceError` | Inválido |
| 3.3 | `test_vo_contains_only_immutable_types` | VO con `list` interno | Documentar riesgo (frozen solo protege reasignación) | Advertencia |

#### Grupo 4: Validación en __post_init__ (sobre subclase @dataclass(frozen=True))

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 4.1 | `test_post_init_validates` | `PositiveInt(value=5)` | Instancia válida | Válido |
| 4.2 | `test_post_init_rejects_invalid` | `PositiveInt(value=-1)` | `ValueError` | Inválido |

#### Grupo 5: Serialización (básica)

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 5.1 | `test_repr_includes_fields` | `Address(st="M", c="C")` | `"Address(st='M', c='C')"` | Válido |
| 5.2 | `test_str_defaults_to_repr` | `Address(st="M", c="C")` | `str == repr` | Válido |

### 10.3 Test Entity (~25 tests)

#### Grupo 1: Construcción

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 1.1 | `test_create_with_id` | `Entity(id=EntityId.new())` | Instancia válida | Válido |
| 1.2 | `test_create_without_id_raises` | `Entity()` | `TypeError` | Inválido |
| 1.3 | `test_create_subclass` | `Person(id=eid, name="A")` | Instancia válida | Válido |
| 1.4 | `test_entity_id_is_entity_id` | `Entity(id=eid)` | `type(e.id) is EntityId` | Válido |

#### Grupo 2: Igualdad por identidad

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 2.1 | `test_same_id_are_equal` | `Entity(id)`, `Entity(id)` | `== True` | Válido |
| 2.2 | `test_different_id_not_equal` | `Entity(id1)`, `Entity(id2)` | `== False` | Válido |
| 2.3 | `test_equal_with_different_attributes` | `Person(id, "A")`, `Person(id, "B")` | `== True` | Válido |
| 2.4 | `test_symmetric_equality` | `a == b` y `b == a` | Ambos True | Válido |
| 2.5 | `test_reflexive_equality` | `e == e` | `True` | Válido |

#### Grupo 3: Igualdad por tipo estricto

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 3.1 | `test_different_type_same_id_not_equal` | `Person(id)`, `Company(id)` | `!= True` | Válido |
| 3.2 | `test_different_type_not_equal` | `Person(id1)`, `Company(id2)` | `!= True` | Válido |
| 3.3 | `test_entity_vs_aggregate_root_not_equal` | `Entity(id)`, `AggregateRoot(id)` | `!= True` | Edge case |
| 3.4 | `test_compare_with_non_entity` | `e == "string"`, `e == 42` | `False` | Edge case |
| 3.5 | `test_compare_with_none` | `e == None` | `False` | Edge case |

#### Grupo 4: Hash

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 4.1 | `test_equal_ids_same_hash` | `Entity(id)`, `Entity(id)` | `hash()` igual | Válido |
| 4.2 | `test_hash_depends_only_on_id` | `Person(id, "A")`, `Person(id, "B")` | `hash()` igual (mismo ID) | Válido |
| 4.3 | `test_different_id_different_hash` | `Entity(id1)`, `Entity(id2)` | `hash()` diferente (colisión improbable) | Válido |
| 4.4 | `test_hash_is_entity_id_hash` | `e = Entity(id)` | `hash(e) == hash(e.id)` | Válido |

#### Grupo 5: Mutabilidad

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 5.1 | `test_can_modify_non_id_field` | `person.name = "new"` | Cambio aceptado | Válido |
| 5.2 | `test_cannot_modify_id_value` | `entity.id.value = new_uuid` | `FrozenInstanceError` (EntityId es frozen) | Inválido |

#### Grupo 6: Colecciones

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 6.1 | `test_entity_in_set` | Set con entities | Size correcto | Válido |
| 6.2 | `test_entity_as_dict_key` | Dict con entity keys | Lookup funciona | Válido |
| 6.3 | `test_set_deduplicates_by_id` | Misma entidad agregada 2x | `len == 1` | Válido |
| 6.4 | `test_dict_key_retrieval_by_id` | Entidad como key, lookup por misma ID | `dict[e] == value` | Válido |

### 10.4 Test AggregateRoot (~20 tests)

#### Grupo 1: Construcción y herencia

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 1.1 | `test_create_with_id` | `AggregateRoot(id)` | Instancia válida | Válido |
| 1.2 | `test_is_instance_of_entity` | `isinstance(ar, Entity)` | `True` | Válido |
| 1.3 | `test_inherits_entity_equality` | ARs con mismo ID | `== True` | Válido |
| 1.4 | `test_create_subclass` | `Order(id, total=99.9)` | Instancia válida | Válido |
| 1.5 | `test_not_equal_to_entity_same_id` | `AR(id) != Entity(id)` | `True` | Edge case |

#### Grupo 2: Registro de eventos

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 2.1 | `test_register_event` | `ar.register_event(e)` | Evento almacenado | Válido |
| 2.2 | `test_register_multiple_events` | 3 eventos, pull | `len == 3` | Válido |
| 2.3 | `test_register_any_type` | string, dict, int | Todos aceptados | Válido |

#### Grupo 3: Extracción y limpieza de eventos

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 3.1 | `test_pull_events_returns_events` | Registrar 2, pull | Lista de 2 eventos | Válido |
| 3.2 | `test_pull_events_clears_list` | pull → pull | Segundo pull = `[]` | Válido |
| 3.3 | `test_pull_events_without_register` | `ar.pull_events()` | `[]` | Válido |
| 3.4 | `test_multiple_register_and_pull_cycles` | reg, pull, reg, pull | Cada pull solo lo nuevo | Válido |
| 3.5 | `test_pull_events_empties_collection` | registrar 1, pull, verificar len interno | `len(ar._events) == 0` | Válido |

#### Grupo 4: Copia defensiva de eventos

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 4.1 | `test_pull_returns_new_list` | `pulled = ar.pull_events()` | `pulled is not ar._events` | Válido |
| 4.2 | `test_mutating_pulled_events_does_not_affect_internal` | Mutar lista devuelta | `ar._events` no cambia | Válido |

#### Grupo 5: Eventos no afectan igualdad

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 5.1 | `test_events_not_in_equality` | Mismo ID, diferentes eventos | `== True` | Válido |
| 5.2 | `test_events_not_in_hash` | Mismo ID, diferentes eventos | `hash()` igual | Válido |

#### Grupo 6: Representación

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 6.1 | `test_repr_does_not_include_events` | `repr(ar with events)` | No contiene eventos | Válido |

### 10.5 Convenciones de tests

```python
from uuid import UUID
from dataclasses import dataclass, FrozenInstanceError
from typing import Self
import pytest

from foundation import EntityId, ValueObject, Entity, AggregateRoot


SAMPLE_UUID = UUID("12345678-1234-5678-1234-567812345678")


# Helpers para testing
@dataclass(frozen=True)
class Address(ValueObject):
    street: str
    city: str


class Person(Entity):
    name: str


class MyAggregate(AggregateRoot):
    pass
```

---

## 11. Criterios de Aceptación

### 11.1 Tests

```bash
pytest tests/foundation/ -v
```

- [ ] Todos los tests de `tests/foundation/` pasan (65 existentes + ~50 nuevos)
- [ ] No hay tests saltados ni pendientes
- [ ] No se rompen tests existentes del proyecto

### 11.2 ValueObject

- [ ] `ValueObject` es marker class — se puede instanciar directamente `ValueObject()`
- [ ] Se puede subclass con `@dataclass(frozen=True)` — `Address(st="M", c="C")`
- [ ] Se puede subclass sin `@dataclass` — implementación manual
- [ ] `isinstance(subclass_instance, ValueObject)` devuelve `True`
- [ ] Los VOs concretos con `@dataclass(frozen=True)` son inmutables — no se puede reasignar fields
- [ ] Los VOs concretos con `@dataclass(frozen=True)` tienen igualdad estructural
- [ ] Los VOs concretos con `@dataclass(frozen=True)` tienen `__post_init__` funcional
- [ ] Foundation NO impone implementación — cada VO elige cómo construirse

### 11.3 Entity

- [ ] `Entity(id=...)` construye correctamente
- [ ] `Entity()` sin ID lanza `TypeError`
- [ ] Dos entities con mismo ID y mismo tipo → iguales
- [ ] Dos entities con mismo ID pero diferente tipo → NO iguales
- [ ] Entity != AggregateRoot aunque tengan mismo ID
- [ ] Entity != tipos no-Entity (string, int, None)
- [ ] Hash consistente con igualdad
- [ ] Entity funciona como key de dict y elemento de set
- [ ] Atributos no-ID mutables

### 11.4 AggregateRoot

- [ ] Hereda de Entity (misma igualdad, mismo hash, misma construcción)
- [ ] `register_event(event)` acumula eventos internamente
- [ ] `register_event()` acepta cualquier tipo (`Any` — placeholder hasta Sprint 2.4)
- [ ] `pull_events()` devuelve lista con COPIA DEFENSIVA de los eventos acumulados
- [ ] `pull_events()` limpia la colección interna inmediatamente después de copiar
- [ ] `pull_events()` sin eventos devuelve `[]`
- [ ] Mutar la lista devuelta por `pull_events()` NO afecta la colección interna
- [ ] La lista devuelta por `pull_events()` NO es la misma referencia que `_events`
- [ ] Eventos no afectan igualdad ni hash
- [ ] Eventos no aparecen en `repr()`
- [ ] Múltiples ciclos register/pull funcionan
- [ ] AggregateRoot NO conoce publish, dispatch, commit ni infraestructura
- [ ] AggregateRoot != Entity aunque tengan el mismo ID

### 11.5 API pública

- [ ] `from foundation import ValueObject, Entity, AggregateRoot` funciona
- [ ] `foundation/__init__.py` exporta las tres clases
- [ ] No hay imports rotos de Sprint 2.1

### 11.6 Zero dependencias

- [ ] `src/foundation/` solo importa de stdlib
- [ ] No se agregaron dependencias a requirements.txt

---

## Apéndice A: Diseño de Referencia

### A.1 ValueObject

Extraído de foundation-design.md §3.1 — ajustado a marker class:

```python
class ValueObject:
    """
    Marker class para todos los Value Objects del sistema.
    
    NO impone @dataclass(frozen=True). Cada Value Object concreto
    elige su implementación, pero DEBE ser inmutable.
    
    Responsabilidades:
      - Tipo base común para polimorfismo
      - Tagging de Value Objects en el sistema
    
    NO hace:
      - No tiene identidad
      - No tiene eventos
      - No tiene ciclo de vida
      - No impone implementación
      - No provee __eq__, __hash__, __init__, __repr__
    """
```

### A.2 Entity

Extraído de foundation-design.md §3.2 con ajuste `type(self) is type(other)` (ver §7.1):

```python
@dataclass
class Entity:
    """
    Base para todas las Entities del sistema.
    
    Responsabilidades:
      - Identidad (self.id)
      - Igualdad por identidad (__eq__, __hash__)
      - Mutabilidad permitida
    """
    id: EntityId
    
    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        return self.id == other.id  # type: ignore[union-attr]
    
    def __hash__(self) -> int:
        return hash(self.id)
```

### A.3 AggregateRoot

Extraído de foundation-design.md §3.3 con `Any` como placeholder temporal:

```python
from typing import Any

@dataclass
class AggregateRoot(Entity):
    """
    Base para todos los Aggregate Roots.
    
    EXTIENDE Entity. Agrega:
      - Capacidad de emitir Domain Events
      - pull_events() para que el Application Service los publique
    
    AggregateRoot SOLO almacena eventos. NO conoce publish, dispatch,
    commit ni ninguna infraestructura.
    """
    _events: list[Any] = field(default_factory=list, repr=False)
    
    def register_event(self, event: Any) -> None:
        """Acumula un evento para publicación posterior."""
        self._events.append(event)
    
    def pull_events(self) -> list[Any]:
        """
        Extrae los eventos con COPIA DEFENSIVA y limpia la colección.
        
        Quien llama (Application Service) es responsable de:
          1. Persistir el Aggregate
          2. Publicar los eventos
        
        Copia defensiva: se crea una nueva lista para que quien recibe
        los eventos no pueda mutar la colección interna del AggregateRoot.
        
        NOTA: Cuando DomainEvent (Sprint 2.4) esté implementado,
        el tipo _events se estrechará de list[Any] a list[DomainEvent].
        """
        events = list(self._events)
        self._events.clear()
        return events
```

---

## Apéndice B: Estructura de Archivos Resultante

```
src/foundation/
├── __init__.py              ← API pública (EntityId, FoundationEncoder,
│                                ValueObject, Entity, AggregateRoot)
├── entity_id.py             ← Sprint 2.1
├── json_encoder.py          ← Sprint 2.1
└── base/                    ← NUEVO
    ├── __init__.py          ← Re-exporta las 3 clases
    ├── value_object.py      ← ValueObject
    ├── entity.py            ← Entity
    └── aggregate_root.py    ← AggregateRoot

tests/foundation/
├── __init__.py
├── conftest.py              ← Sprint 2.1
├── test_entity_id.py        ← Sprint 2.1 (65 tests)
├── test_value_object.py     ← NUEVO (~15 tests)
├── test_entity.py           ← NUEVO (~20 tests)
└── test_aggregate_root.py   ← NUEVO (~15 tests)
```
