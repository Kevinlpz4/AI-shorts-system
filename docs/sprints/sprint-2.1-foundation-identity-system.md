# Sprint 2.1 — Foundation Identity System

> **Proyecto**: AI Shorts System
> **Epic**: 2 — Foundation Layer
> **Sprint**: 2.1 — Identity System
> **Estado**: SPECIFICATION DRAFT (v2)
> **Fecha**: 2026-07-02
> **Stack**: Python 3.12.3, stdlib-only

---

## 1. Objetivo del Sprint

Implementar el **sistema de identidad tipada** del Foundation Layer: la
capacidad de que cada entidad del sistema tenga un ID único, inmutable,
type-safe, serializable, y correctamente comportado en igualdad, hash,
JSON y colecciones.

**¿Qué problema resuelve?**

| Problema | Cómo lo resuelve este Sprint |
|----------|------------------------------|
| UUIDs crudos mezclados con strings en todo el código | `EntityId` encapsula UUID con un tipo real |
| Pasar un ID de un BC donde va otro no se detecta | `SourceId` y `FeedId` son tipos distintos — Foundation NO los conoce, cada BC define los suyos |
| Cada módulo serializa IDs a su manera | Foundation provee `FoundationEncoder` (genérico, extensible para futuros tipos) |
| IDs mutables o reasignables | `EntityId` es `@dataclass(frozen=True)` — inmutable desde la construcción |
| No hay forma estándar de generar IDs | `EntityId.new()` encapsula uuid4() — nadie fuera de Foundation necesita saber que existe uuid4() |

---

## 2. Alcance

### 2.1 Qué pertenece al Sprint

| Componente | Descripción | ¿Por qué está en este Sprint? |
|-----------|-------------|-------------------------------|
| **EntityId** | Value Object base que envuelve UUID con type safety | Es la base de TODO el sistema de identidad |
| **FoundationEncoder** | `json.JSONEncoder` que serializa EntityId (extensible para futuros tipos Foundation) | Necesario para serialización estándar desde el día 1 |
| **Igualdad tipada** | `__eq__` que compara tipo concreto Y valor | `SourceId(x) != FeedId(x)` aunque tengan el mismo UUID |
| **Hash** | `__hash__` consistente con `__eq__` | Para usar IDs en sets, dicts |
| **Serialización** | `from_string()`, `new()`, `__str__`, `__repr__` | Para persistencia, APIs, logs, debugging |
| **API pública** | `foundation/__init__.py` con exports mínimos | Para que los BCs importen correctamente |

### 2.2 Qué NO pertenece al Sprint

| Componente | Excluido porque... | Sprint asignado |
|-----------|-------------------|-----------------|
| IDs específicos (`SourceId`, `FeedId`, `TopicId`, etc.) | **Foundation NO conoce conceptos de dominio**. Cada BC define los suyos como `class SourceId(EntityId): ...` | En cada BC (Ingestion, Research, etc.) |
| Entity base class | No es parte del sistema de identidad | Sprint 2.2 |
| AggregateRoot base class | No es parte del sistema de identidad | Sprint 2.2 |
| ValueObject base class | No es parte del sistema de identidad | Sprint 2.2 |
| Result[T], Success, Failure | Es patrón de resultado, no identidad | Sprint 2.3 |
| Error, ErrorCode | Es modelo de error, no identidad | Sprint 2.3 |
| FoundationError, DomainError | Excepciones, no identidad | Sprint 2.4 |
| DomainEvent, IntegrationEvent | Eventos, no identidad | Sprint 2.5 |
| ClockPort, UUIDProvider | Puertos de infraestructura | Sprint 2.6 |
| SystemClock, FrozenClock | Implementaciones concretas | Sprint 2.6 |
| SystemUUIDProvider, SequentialUUIDProvider | Implementaciones concretas | Sprint 2.6 |
| `foundation/base/` package | Contiene Entity/AR/VO, no IDs | Sprint 2.2 |
| `foundation/result/` package | Result pattern | Sprint 2.3 |
| `foundation/errors/` package | Error hierarchy | Sprint 2.4 |
| `foundation/events/` package | Domain/Integration Events | Sprint 2.5 |
| `foundation/ports/` package | Clock/UUID ports | Sprint 2.6 |
| Cualquier lógica de negocio | Foundation NO tiene lógica de negocio | Jamás |

### 2.3 Verificación contra ADR-021 (Foundation Stability Policy)

| Criterio | ¿Cumple? | Explicación |
|----------|----------|-------------|
| MULTI-BC (usado por ≥2 BCs) | ✅ Sí | Todo BC del sistema usará EntityId |
| NO BUSINESS RULES | ✅ Sí | EntityId no sabe de fuentes, feeds, topics, scripts — solo envuelve UUID |
| ZERO DEPENDENCIES | ✅ Sí | Solo `dataclasses`, `uuid`, `json`, `typing` — todo stdlib |
| NO COUPLING | ✅ Sí | EntityId no referencia ningún BC. Foundation no conoce IDs específicos |
| MECHANISM, NOT POLICY | ✅ Sí | Es identidad: un mecanismo técnico transversal |

**Cambio respecto a v1**: Se eliminaron los IDs específicos (`SourceId`, `FeedId`, etc.)
de Foundation. La policy se cumple estrictamente: Foundation solo contiene mecanismos
técnicos, no semántica de dominio.

---

## 3. Archivos

### 3.1 Archivos a crear

| Ruta | Contenido | Depende de |
|------|-----------|------------|
| `src/foundation/__init__.py` | API pública: exporta `EntityId`, `FoundationEncoder` | N/A |
| `src/foundation/entity_id.py` | Clase `EntityId`: `@dataclass(frozen=True)` con `value: UUID`, `__str__`, `__repr__`, `__eq__` (tipado), `__hash__`, `from_string()`, `new()` | N/A |
| `src/foundation/json_encoder.py` | `FoundationEncoder(json.JSONEncoder)` — maneja EntityId, diseñado para ser extendido con futuros tipos Foundation | `entity_id.py` |
| `tests/foundation/__init__.py` | Init del paquete de tests | N/A |
| `tests/foundation/test_entity_id.py` | Tests completos de EntityId | N/A |

**Total: 5 archivos**. (se eliminó el paquete `ids/` porque es over-engineering para un solo archivo).

### 3.2 Archivos a modificar

| Ruta | Cambio |
|------|--------|
| Ninguno | Este sprint NO modifica archivos existentes. Todo el código es nuevo en `src/foundation/` y `tests/foundation/` |

### 3.3 Archivos excluidos deliberadamente

- `src/foundation/_compat.py` — No necesario. Python 3.12 tiene `typing.Self` nativo.
- `src/foundation/types/` — Los IDs específicos NO pertenecen a Foundation (ADR-021). Cada BC define los suyos.
- `src/foundation/ids/` — Un paquete completo para un solo archivo es over-engineering. `entity_id.py` va directo en `foundation/`.
- `src/foundation/ids/__init__.py` y `tests/foundation/ids/__init__.py` — Eliminados junto con el paquete `ids/`.

---

## 4. Dependencias

### 4.1 Dependencias de este Sprint

| Dependencia | Tipo | Detalle |
|------------|------|---------|
| Python 3.12 | Runtime | `typing.Self`, `@dataclass(frozen=True)`, `uuid.UUID` |
| pytest | Testing | Framework de tests existente en el proyecto |
| Ninguna librería externa | Runtime | Zero. Todo es stdlib |

### 4.2 Dependencias hacia este Sprint (quién lo necesita)

| Componente futuro | ¿Por qué necesita este Sprint? |
|------------------|-------------------------------|
| Entity (Sprint 2.2) | `Entity.id: EntityId` |
| AggregateRoot (Sprint 2.2) | Hereda de Entity, mismo `id: EntityId` |
| Result (Sprint 2.3) | Usa EntityId como tipo genérico en resultados |
| FoundationEncoder (futuro) | Se extiende con ValueObject, DomainEvent, etc. |
| Ingestion Domain (Sprint 3.x) | `SourceId(EntityId)` definido en ingestion/ |
| Research Domain (refactor) | `TopicId(EntityId)` definido en research/ |
| Todos los repositorios | CRUD operations con EntityId |

### 4.3 Árbol de dependencias

```
                    Sprint 2.1 (EntityId)
                         │
           ┌─────────────┼─────────────┐
           │             │             │
       Sprint 2.2   Sprint 3.x    Research BC
       (Entity/AR)  (Ingestion)   (TopicId)
           │
       Sprint 2.3
       (Result)
```

---

## 5. Orden de implementación

```
Paso 1  →  src/foundation/entity_id.py           (EntityId base class)
Paso 2  →  src/foundation/json_encoder.py         (FoundationEncoder)
Paso 3  →  src/foundation/__init__.py             (API pública)
Paso 4  →  tests/foundation/test_entity_id.py     (tests)
```

**Reglas del orden**:
- Cada paso se implementa y se verifica ANTES de pasar al siguiente.
- Los tests (paso 4) se implementan DESPUÉS del código, pero se ejecutan durante todo el desarrollo.
- No se avanza al paso N sin que el paso N-1 esté completo y testeado.

### Hallazgos de implementación

Durante la implementación se agregó **`__post_init__`** en EntityId para validar
que `value` sea `uuid.UUID` en runtime. Esto no estaba en el diseño original
(documentado en foundation-design.md sección 4.2), pero es necesario porque
Python no enforcea type hints en runtime.

Sin esta validación:
- `EntityId(value=None)` crea un ID con `value=None` silenciosamente
- `EntityId(value="string")` almacena un string, no un UUID
- La propiedad `value` ya no sería confiable como `UUID`

La validación es consistente con el principio F5 (Fail Fast at Construction).

---

## 6. Riesgos

| Riesgo | Impacto | Probabilidad | Mitigación |
|--------|---------|-------------|------------|
| **Herencia de dataclasses con defaults**: Si EntityId tiene `value: UUID = field(default_factory=uuid4)`, las subclases que agreguen fields sin defaults fallarían. Pero las subclases de EntityId (SourceId, etc.) NO están en Foundation — se definen en cada BC y tampoco agregan fields. | Bajo | Baja | Verificar con test que `class MyId(EntityId): ...` funciona. La restricción de Python aplica solo si la subclase AGREGA fields sin default. |
| **`type(self) is type(other)` en `__eq__`**: Esta comparación es estricta: `SourceId(x) != EntityId(x)` aunque tengan el mismo UUID. Si alguien tiene una colección `list[EntityId]` y espera que IDs del mismo UUID sean iguales sin importar el subtipo, fallaría. Pero tener colecciones heterogéneas de EntityId es un anti-patrón: cada BC opera con su tipo concreto. | Bajo | Baja | Documentado en edge cases. Es un trade-off deliberado para ganar type safety en runtime. |
| **from_string con UUID inválido**: `UUID("no-es-uuid")` lanza `ValueError`. No capturar silenciosamente. | Bajo | Baja | `from_string` documenta que lanza `ValueError`. Es comportamiento esperado (fail fast, principio F5). |
| **hash no determinístico entre sesiones**: `hash(UUID)` puede variar entre ejecuciones de Python (PYTHONHASHSEED). | Bajo | Baja | Comportamiento normal de cualquier tipo con `__hash__`. No persistir hashes. |
| **FoundationEncoder se queda obsoleto**: Cuando se agreguen ValueObject, DomainEvent, etc., el encoder debe actualizarse. Si se olvida, FoundationEncoder no los manejará. | Medio | Baja | El encoder está diseñado para ser extendido con `elif isinstance(...)`. Se documenta en el docstring que al agregar nuevos tipos Foundation, el encoder debe actualizarse. |
| **Exceso de ingeniería**: Tentación de agregar métodos "por si acaso" a EntityId. | Medio | Media | Aplicar YAGNI estrictamente. Solo lo documentado en el diseño original. |

---

## 7. Casos Borde

### 7.1 Igualdad entre IDs del mismo tipo y mismo valor

```python
class MyId(EntityId): ...

a = MyId(value=UUID("00000000-0000-0000-0000-000000000001"))
b = MyId(value=UUID("00000000-0000-0000-0000-000000000001"))
assert a == b             # ✅ Mismo tipo, mismo UUID → True
assert hash(a) == hash(b) # ✅ Mismo hash
```

### 7.2 Igualdad entre IDs de tipo DIFERENTE (mismo UUID)

```python
class SourceId(EntityId): ...
class FeedId(EntityId): ...

source = SourceId(value=UUID("00000000-0000-0000-0000-000000000001"))
feed = FeedId(value=UUID("00000000-0000-0000-0000-000000000001"))

assert source != feed     # ✅ False porque type(self) is not type(other)
assert hash(source) != hash(feed)  # ⚠️ hash puede coincidir por casualidad
```

**Decisión**: `__eq__` usa `type(self) is type(other)`. IDs de diferentes tipos
NUNCA son iguales, aunque tengan el mismo UUID. La seguridad de tipos en runtime
es más importante que la pureza LSP teórica.

**¿Por qué `type(self) is type(other)` y no `isinstance(other, type(self))`?**
Para evitar que una subclase de `SourceId` (si existiera) sea igual a `SourceId`.
Queremos igualdad EXACTA de tipo concreto, no herencia de tipos.

### 7.3 Comparación con no-EntityId

```python
eid = EntityId(value=UUID("00000000-0000-0000-0000-000000000001"))

assert eid != "some-string"     # ✅ NotImplemented → False
assert eid != 42                # ✅ NotImplemented → False
assert eid != 3.14              # ✅ NotImplemented → False
assert eid != [1, 2, 3]        # ✅ NotImplemented → False
assert eid != {"key": "val"}   # ✅ NotImplemented → False
assert eid != None              # ✅ NotImplemented → False
assert eid != True              # ✅ NotImplemented → False
```

### 7.4 Comparación entre EntityId base y subclase

```python
eid = EntityId(value=UUID("00000000-0000-0000-0000-000000000001"))
sub = SourceId(value=UUID("00000000-0000-0000-0000-000000000001"))

assert eid != sub    # ❌ type(EntityId) is not type(SourceId)
assert sub != eid    # ❌ type(SourceId) is not type(EntityId)
```

**Nota**: Esto significa que si una función acepta `EntityId` como parámetro y
compara con otro `EntityId`, una subclase NO será igual a la base aunque tenga
el mismo UUID. Es la consecuencia deliberada de la decisión 7.2.

### 7.5 from_string con UUID válido

```python
hex_str = "12345678-1234-5678-1234-567812345678"
eid = EntityId.from_string(hex_str)
assert eid.value == UUID(hex_str)
assert str(eid) == hex_str
```

### 7.6 from_string con formatos que UUID acepta

```python
EntityId.from_string("12345678-1234-5678-1234-567812345678")     # ✅ estándar
EntityId.from_string("{12345678-1234-5678-1234-567812345678}")   # ✅ con llaves
EntityId.from_string("12345678123456781234567812345678")         # ✅ sin guiones
EntityId.from_string("urn:uuid:12345678-1234-5678-1234-567812345678")  # ✅ con URN
```

El constructor de `UUID()` de Python acepta todos estos formatos. EntityId hereda
ese comportamiento sin modificaciones.

### 7.7 from_string con UUID inválido

```python
with pytest.raises(ValueError):
    EntityId.from_string("no-soy-uuid")
with pytest.raises(ValueError):
    EntityId.from_string("")
with pytest.raises(ValueError):
    EntityId.from_string("123")
with pytest.raises(ValueError):
    EntityId.from_string("gggggggg-gggg-gggg-gggg-gggggggggggg")
```

TODOS deben lanzar `ValueError`. `UUID()` de Python lanza `ValueError` para
cualquier string que no sea un UUID válido.

### 7.8 Constructor con valor inválido

```python
with pytest.raises(TypeError):
    EntityId(value=None)           # TypeError: UUID() expects ... 

with pytest.raises(TypeError):
    EntityId(value=123)            # TypeError: UUID() expects ...

with pytest.raises(TypeError):
    EntityId(value=3.14)           # TypeError: UUID() expects ...
```

### 7.9 Serialización roundtrip

```python
original = EntityId(value=UUID("12345678-1234-5678-1234-567812345678"))
as_str = str(original)
restored = EntityId.from_string(as_str)
assert original == restored             # ✅ Roundtrip exitoso
assert type(restored) is EntityId       # ✅ Tipo preservado
```

### 7.10 __str__ vs __repr__

```python
eid = EntityId(value=UUID("12345678-1234-5678-1234-567812345678"))

assert str(eid) == "12345678-1234-5678-1234-567812345678"
# __str__ es solo el UUID, sin adornos — útil para logs, APIs, DB

assert repr(eid) == "EntityId(value=UUID('12345678-1234-5678-1234-567812345678'))"
# __repr__ incluye el tipo y el constructor — útil para debugging
# (es el default de @dataclass, no necesita override)
```

### 7.11 Hash consistency

```python
u = UUID("00000000-0000-0000-0000-000000000001")
id1 = EntityId(value=u)
id2 = EntityId(value=u)
assert hash(id1) == hash(id2)  # ✅ Misma sesión → mismo hash
```

### 7.12 UUIDs en sets

```python
u1 = UUID("00000000-0000-0000-0000-000000000001")
u2 = UUID("00000000-0000-0000-0000-000000000002")

s = {EntityId(value=u1), EntityId(value=u2)}
assert len(s) == 2            # ✅ Dos UUIDs diferentes → dos elementos

# Mismo UUID:
s.add(EntityId(value=u1))
assert len(s) == 2            # ✅ Misma clave → no se duplica
```

### 7.13 EntityId como clave de dict

```python
u1 = UUID("00000000-0000-0000-0000-000000000001")
d = {EntityId(value=u1): "item1"}
d[EntityId(value=u1)] = "item2"
assert len(d) == 1            # ✅ Misma clave → sobrescribe
assert d[EntityId(value=u1)] == "item2"
```

### 7.14 Pickle

```python
import pickle
eid = EntityId(value=UUID("00000000-0000-0000-0000-000000000001"))
data = pickle.dumps(eid)
restored = pickle.loads(data)
assert eid == restored              # ✅ Igualdad preservada
assert type(restored) is EntityId   # ✅ Tipo preservado
assert restored.value == eid.value  # ✅ Valor preservado
```

Los `@dataclass(frozen=True)` son picklables por defecto. El valor UUID también
es picklable nativamente.

### 7.15 copy.copy y copy.deepcopy

```python
import copy
eid = EntityId(value=UUID("00000000-0000-0000-0000-000000000001"))

shallow = copy.copy(eid)
assert eid == shallow       # ✅ Igualdad preservada

deep = copy.deepcopy(eid)
assert eid == deep          # ✅ Igualdad preservada
# Nota: Para objetos frozen, copy.copy() puede devolver la misma referencia.
# Eso es aceptable porque el objeto es inmutable — no hay estado que clonar.
```

### 7.16 Inmutabilidad

```python
eid = EntityId(value=UUID("00000000-0000-0000-0000-000000000001"))
with pytest.raises(FrozenInstanceError):
    eid.value = UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
```

### 7.17 EntityId.new()

```python
a = EntityId.new()
b = EntityId.new()
assert isinstance(a, EntityId)   # ✅ Tipo correcto
assert isinstance(a.value, UUID)  # ✅ UUID válido
assert a != b                     # ✅ Diferentes
```

`new()` encapsula `uuid4()`. Ningún código fuera de Foundation necesita saber que `uuid4()` existe.

### 7.18 Múltiples formas de crear un EntityId

```python
# Todas equivalentes en tipo, diferentes en origen del UUID:
auto = EntityId()                      # auto-generado (default_factory)
new = EntityId.new()                   # explícito via factory method
specific = EntityId(value=UUID(...))   # UUID específico
restored = EntityId.from_string("...") # desde string
```

### 7.18 Múltiples formas de crear un EntityId

```python
# Todas equivalentes en tipo, diferentes en origen del UUID:
auto = EntityId()                           # auto-generado
new = EntityId.new()                        # explícito via factory method
specific = EntityId(value=UUID("..."))      # UUID específico
restored = EntityId.from_string("...")      # desde string
```

### 7.19 FoundationEncoder con tipos no-Foundation

```python
encoder = FoundationEncoder()
assert json.dumps({"x": 1}, cls=FoundationEncoder) == '{"x": 1}'
assert json.dumps([1, "a", True], cls=FoundationEncoder) == '[1, "a", true]'
# Tipos nativos deben seguir funcionando
```

### 7.20 FoundationEncoder sin encoder (error esperado)

```python
eid = EntityId(value=UUID("12345678-1234-5678-1234-567812345678"))
with pytest.raises(TypeError):
    json.dumps({"id": eid})  # ❌ No es serializable sin encoder
```

---

## 8. Estrategia de Testing

### 8.1 Estructura de tests

```
tests/foundation/test_entity_id.py   ← Único archivo de tests
```

No hay `tests/foundation/types/` porque Foundation no contiene IDs específicos.

### 8.2 test_entity_id.py — Plan de tests

#### Grupo 1: Construcción (Construction)

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 1.1 | `test_create_with_default_generates_uuid` | `EntityId()` | `isinstance(value, UUID)` | Válido |
| 1.2 | `test_create_with_specific_uuid` | `EntityId(value=u)` | `value == u` | Válido |
| 1.3 | `test_value_is_uuid_not_string` | `EntityId(value=u)` | `type(value) is UUID` | Válido |
| 1.4 | `test_new_factory_method` | `EntityId.new()` | `isinstance(value, UUID)` | Válido |
| 1.5 | `test_new_returns_unique_values` | 2x `EntityId.new()` | `a != b` | Válido |
| 1.6 | `test_create_with_none_raises_type_error` | `EntityId(value=None)` | `TypeError` | Inválido |
| 1.7 | `test_create_with_int_raises_type_error` | `EntityId(value=123)` | `TypeError` | Inválido |
| 1.8 | `test_create_with_float_raises_type_error` | `EntityId(value=3.14)` | `TypeError` | Inválido |
| 1.9 | `test_create_with_string_raises_type_error` | `EntityId(value="...")` | `TypeError` | Inválido |

**Nota 1.9**: Se agregó `__post_init__` que valida que `value` sea `uuid.UUID` en
runtime. Strings pasados al constructor lanzan `TypeError`. Para crear desde
string, usar `EntityId.from_string()`. Esto es consistente con el principio
F5 (Fail Fast at Construction).

#### Grupo 2: Igualdad (Equality)

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 2.1 | `test_same_type_same_value_are_equal` | `EntityId(u), EntityId(u)` | `== True` | Válido |
| 2.2 | `test_same_type_different_value_not_equal` | `EntityId(u1), EntityId(u2)` | `== False` | Válido |
| 2.3 | `test_equal_ids_have_same_hash` | `EntityId(u), EntityId(u)` | `hash()` iguales | Válido |
| 2.4 | `test_different_type_same_value_not_equal` | `class A(EntityId), class B(EntityId)` con mismo uuid | `A(u) != B(u)` | Edge case |
| 2.5 | `test_entity_id_base_vs_subclass_not_equal` | `EntityId(u) vs A(u)` | `!= True` | Edge case |
| 2.6 | `test_equals_string_returns_false` | `EntityId(u) == "..."` | `False` | Edge case |
| 2.7 | `test_equals_int_returns_false` | `EntityId(u) == 42` | `False` | Edge case |
| 2.8 | `test_equals_float_returns_false` | `EntityId(u) == 3.14` | `False` | Edge case |
| 2.9 | `test_equals_list_returns_false` | `EntityId(u) == [1,2,3]` | `False` | Edge case |
| 2.10 | `test_equals_dict_returns_false` | `EntityId(u) == {"a": 1}` | `False` | Edge case |
| 2.11 | `test_equals_bool_returns_false` | `EntityId(u) == True` | `False` | Edge case |
| 2.12 | `test_equals_none_returns_false` | `EntityId(u) == None` | `False` | Edge case |
| 2.13 | `test_not_equal_different_value` | `EntityId(u1) != EntityId(u2)` | `True` | Válido |
| 2.14 | `test_not_equal_different_type` | `A(u) != B(u)` | `True` | Edge case |

#### Grupo 3: Serialización (Serialization)

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 3.1 | `test_str_returns_uuid_string` | `EntityId(value=u)` | `str == str(u)` | Válido |
| 3.2 | `test_str_no_extra_wrapping` | `EntityId(value=u)` | `str` no contiene `EntityId()` | Válido |
| 3.3 | `test_repr_includes_type_and_value` | `EntityId(value=u)` | `repr` contiene `EntityId` y el UUID | Válido |
| 3.4 | `test_roundtrip_from_string` | `EntityId.from_string(str(eid))` | igual a original | Válido |
| 3.5 | `test_from_string_standard_format` | `from_string("1234-...")` | UUID válido | Válido |
| 3.6 | `test_from_string_with_braces` | `from_string("{uuid}")` | UUID válido | Edge case |
| 3.7 | `test_from_string_without_hyphens` | `from_string("1234...32chars")` | UUID válido | Edge case |
| 3.8 | `test_from_string_with_urn` | `from_string("urn:uuid:...")` | UUID válido | Edge case |
| 3.9 | `test_from_string_invalid_format` | `from_string("not-a-uuid")` | `ValueError` | Inválido |
| 3.10 | `test_from_string_empty_string` | `from_string("")` | `ValueError` | Inválido |
| 3.11 | `test_from_string_too_short` | `from_string("123")` | `ValueError` | Inválido |
| 3.12 | `test_from_string_invalid_hex` | `from_string("gggggggg-...")` | `ValueError` | Inválido |

#### Grupo 4: JSON Serialization

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 4.1 | `test_encoder_serializes_entity_id` | `json.dumps(eid, cls=FoundationEncoder)` | `'"uuid-string"'` | Válido |
| 4.2 | `test_encoder_in_dict` | `json.dumps({"id": eid}, cls=FoundationEncoder)` | `'{"id": "uuid"}'` | Válido |
| 4.3 | `test_encoder_with_list` | `json.dumps([eid1, eid2], cls=FoundationEncoder)` | `'["u1", "u2"]'` | Válido |
| 4.4 | `test_encoder_with_native_types` | `json.dumps({"x": 1, "y": "a"}, cls=FoundationEncoder)` | `'{"x":1,"y":"a"}'` | Válido |
| 4.5 | `test_encoder_with_none` | `json.dumps({"x": None}, cls=FoundationEncoder)` | `'{"x":null}'` | Válido |
| 4.6 | `test_json_without_encoder_fails` | `json.dumps({"id": eid})` | `TypeError` | Inválido |
| 4.7 | `test_encoder_with_unknown_type_fails` | `json.dumps({"x": object()}, cls=FoundationEncoder)` | `TypeError` | Inválido |

#### Grupo 5: Colecciones (Collections)

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 5.1 | `test_can_be_used_in_set` | `{EntityId(u1), EntityId(u2)}` | `len == 2` | Válido |
| 5.2 | `test_set_deduplicates_same_value` | `{EntityId(u), EntityId(u)}` | `len == 1` | Válido |
| 5.3 | `test_can_be_used_as_dict_key` | `d = {EntityId(u): "val"}` | `d[EntityId(u)] == "val"` | Válido |
| 5.4 | `test_dict_key_overwrite` | `d[EntityId(u)] = "v2"` | `len(d) == 1` | Válido |
| 5.5 | `test_dict_with_multiple_keys` | `d = {EntityId(u1): "a", EntityId(u2): "b"}` | `len == 2` | Válido |

#### Grupo 6: Pickle

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 6.1 | `test_pickle_roundtrip` | `pickle.loads(pickle.dumps(eid))` | `== eid` | Válido |
| 6.2 | `test_pickle_preserves_type` | `pickle.loads(pickle.dumps(eid))` | `type is EntityId` | Válido |
| 6.3 | `test_pickle_preserves_value` | `pickle.loads(pickle.dumps(eid))` | `.value == eid.value` | Válido |

#### Grupo 7: Copy

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 7.1 | `test_shallow_copy_preserves_equality` | `copy.copy(eid)` | `== eid` | Válido |
| 7.2 | `test_deep_copy_preserves_equality` | `copy.deepcopy(eid)` | `== eid` | Válido |
| 7.3 | `test_deep_copy_preserves_value` | `copy.deepcopy(eid)` | `.value == eid.value` | Válido |

#### Grupo 8: Inmutabilidad

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 8.1 | `test_frozen_cannot_modify_value` | `eid.value = new_uuid` | `FrozenInstanceError` | Inválido |
| 8.2 | `test_frozen_cannot_delete_value` | `del eid.value` | `FrozenInstanceError` | Inválido |
| 8.3 | `test_frozen_cannot_set_new_attr` | `eid.new_attr = "x"` | `FrozenInstanceError` | Inválido |

### 8.3 Convenciones de tests

```python
# Naming: test_{escenario}_expected_result
# Assertions: assert nativas (sin librerías externas)
# Fixtures: solo pytest, sin conftest.py nuevo
# Datos: UUIDs fijos para determinismo

from uuid import UUID
from dataclasses import FrozenInstanceError
import json, pickle, copy
import pytest

from foundation import EntityId, FoundationEncoder

SAMPLE_UUID = UUID("12345678-1234-5678-1234-567812345678")
ANOTHER_UUID = UUID("87654321-4321-8765-4321-876543210987")


class TestEntityIdConstruction:
    def test_create_with_default_generates_uuid(self):
        eid = EntityId()
        assert isinstance(eid.value, UUID)

    def test_create_with_specific_uuid(self):
        eid = EntityId(value=SAMPLE_UUID)
        assert eid.value == SAMPLE_UUID

    def test_create_with_none_raises_type_error(self):
        with pytest.raises(TypeError):
            EntityId(value=None)
```

---

## 9. Criterios de Aceptación

### 9.1 Todos los tests pasan

```bash
pytest tests/foundation/ -v
```

✅ Todos los tests del grupo `tests/foundation/` pasan sin errores ni warnings.
✅ No hay tests saltados (`skipped`) ni pendientes.
✅ No se rompen tests existentes del proyecto.
✅ Cobertura del 100% de código de EntityId y FoundationEncoder.

### 9.2 EntityId

- [ ] Se puede crear con UUID aleatorio (default).
- [ ] Se puede crear con UUID específico.
- [ ] Se puede crear con string UUID (auto-conversión).
- [ ] `EntityId.new()` crea UUID único sin exponer `uuid4()`.
- [ ] `value` es siempre `uuid.UUID`, no string.

### 9.3 Igualdad

- [ ] Mismo tipo + mismo UUID → `== True`.
- [ ] Mismo tipo + diferente UUID → `== False`.
- [ ] Diferente tipo + mismo UUID → `!= True` (type safety).
- [ ] EntityId base != subclase aunque tengan el mismo UUID.
- [ ] EntityId != cualquier tipo no-EntityId (string, int, None, etc.).
- [ ] Hash consistente con equality.

### 9.4 Serialización

- [ ] `str(eid)` devuelve solo el UUID string (sin wrapping).
- [ ] `repr(eid)` incluye `EntityId(value=UUID('...'))`.
- [ ] `from_string(str(eid))` recrea el mismo ID.
- [ ] `from_string()` acepta todos los formatos que UUID() acepta.
- [ ] `from_string()` lanza `ValueError` para strings inválidos.

### 9.5 FoundationEncoder

- [ ] Serializa EntityId a string UUID en JSON.
- [ ] Funciona dentro de dicts y listas JSON.
- [ ] No rompe serialización de tipos nativos.
- [ ] Sin encoder, EntityId lanza `TypeError` en `json.dumps`.

### 9.6 Colecciones

- [ ] EntityId funciona como key de dict.
- [ ] EntityId funciona en sets.
- [ ] Deduplicación correcta (mismo UUID → misma clave).

### 9.7 Pickle y Copy

- [ ] Pickle roundtrip preserva igualdad, tipo y valor.
- [ ] `copy.copy` preserva igualdad.
- [ ] `copy.deepcopy` preserva igualdad y valor.

### 9.8 Inmutabilidad

- [ ] Modificar `value` lanza `FrozenInstanceError`.
- [ ] Eliminar `value` lanza `FrozenInstanceError`.
- [ ] Agregar nuevos atributos lanza `FrozenInstanceError`.

### 9.9 Zero dependencias externas

- [ ] `src/foundation/` solo importa de stdlib.
- [ ] No se agregaron dependencias a `requirements.txt`.
- [ ] `pip freeze` no muestra librerías nuevas.

### 9.10 Integridad del repositorio

- [ ] `git status` — solo archivos nuevos en `src/foundation/` y `tests/foundation/`.
- [ ] No se modificó ningún archivo existente.
- [ ] El código existente (`research/`, `app/`, `presentation/`, etc.) no se tocó.

---

## Apéndice A: Diseño de Referencia

### A.1 EntityId (diseño actualizado)

```python
@dataclass(frozen=True)
class EntityId:
    """
    Value Object base para todos los IDs del sistema.
    
    Responsabilidades:
      - Envolver un UUID con type safety
      - Garantizar que siempre es un UUID válido
      - Serialización a string y desde string
      - Igualdad por tipo concreto Y valor
      - Hash consistente con igualdad
    
    ¿Por qué frozen=True?
      - Un ID no cambia. Nunca. Si cambia, es otra entidad.
    
    ¿Por qué type(self) is type(other) en __eq__?
      - SourceId(x) NO debe ser igual a FeedId(x)
      - El type safety debe funcionar en runtime, no solo en type checker
      - Ver ADR-017 y Sprint Specification 2.1 sección 7.2
    """
    value: UUID = field(default_factory=uuid4)
    
    def __str__(self) -> str:
        return str(self.value)
    
    def __eq__(self, other):
        if type(self) is not type(other):
            return NotImplemented
        return self.value == other.value
    
    def __hash__(self):
        return hash(self.value)
    
    @classmethod
    def from_string(cls, raw: str) -> Self:
        """Crea un ID desde string. Lanza ValueError si inválido."""
        return cls(value=UUID(raw))
    
    @classmethod
    def new(cls) -> Self:
        """Crea un ID con nuevo UUID aleatorio.
        
        Es la forma PREFERIDA de crear IDs nuevos. Encapsula uuid4()
        para que el resto del sistema no dependa de la implementación.
        """
        return cls()
```

### A.2 FoundationEncoder

```python
class FoundationEncoder(json.JSONEncoder):
    """
    JSONEncoder genérico para tipos Foundation.
    
    Actualmente maneja:
      - EntityId         → serializa como string UUID
    
    Cuando se agreguen nuevos tipos Foundation (ValueObject, DomainEvent,
    Result, etc.), agregar su serialización AQUÍ, no crear encoders
    separados.
    
    Uso:
        json.dumps({"id": some_entity_id}, cls=FoundationEncoder)
    
    Nota: Si un tipo Foundation no tiene serialización registrada,
    FoundationEncoder delega al default de JSONEncoder, que lanza
    TypeError para tipos no serializables.
    """
    
    def default(self, obj):
        if isinstance(obj, EntityId):
            return str(obj)
        return super().default(obj)
```

### A.3 IDs específicos (NO en Foundation)

Cada BC define sus propios IDs por herencia:

```python
# En ingestion/domain/ids.py
class SourceId(EntityId): ...
class FeedId(EntityId): ...
class FeedGroupId(EntityId): ...
class RawItemId(EntityId): ...
class BatchId(EntityId): ...

# En research/domain/ids.py
class TopicId(EntityId): ...

# En script_generation/domain/ids.py (futuro)
class ScriptId(EntityId): ...

# En shared/domain/ids.py
class CategoryId(EntityId): ...
```

Foundation NO sabe de ninguno de estos tipos. Solo provee `EntityId` como
mecanismo.

---

## Apéndice B: Estructura de Archivos Resultante

```
src/foundation/
├── __init__.py              ← API pública: EntityId, FoundationEncoder
├── entity_id.py             ← EntityId (sin subpaquetes)
└── json_encoder.py          ← FoundationEncoder

tests/foundation/
├── __init__.py
└── test_entity_id.py        ← Todos los tests (~55 tests)
```

**Nota**: Se eliminó el paquete `ids/` porque `entity_id.py` es el único archivo.
Si en el futuro Foundation crece y justifica subpaquetes, se crean en ese momento.
YAGNI.

---

## Apéndice C: Mapa de Decisiones v1 → v2

| Aspecto | v1 (original) | v2 (revisado) | ¿Por qué? |
|---------|--------------|---------------|-----------|
| `__eq__` compara | Solo `.value` | `type(self) is type(other)` AND `.value` | Type safety real en runtime |
| IDs específicos | En Foundation (`types/`) | En cada BC | ADR-021: Foundation no conoce dominio |
| Encoder | `EntityIdEncoder` (solo IDs) | `FoundationEncoder` (genérico) | Extensible para futuros tipos Foundation |
| `types/` package | Sí (8 IDs) | No | Afuera de Foundation |
| Archivos a crear | 11 | 7 | Eliminados types/ y sus tests |
| Tests totales | ~30 | ~55 | Expandidos por nuevas categorías |
