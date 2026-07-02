# Sprint 2.3 — Foundation Result Pattern

> **Proyecto**: AI Shorts System
> **Epic**: 2 — Foundation Layer
> **Sprint**: 2.3 — Result Pattern
> **Estado**: APPROVED
> **Fecha**: 2026-07-02
> **Stack**: Python 3.12.3, stdlib-only

---

## 1. Objetivo del Sprint

Implementar el **Result Pattern** del Foundation Layer: una forma estandarizada de
modelar operaciones que pueden tener éxito o fallar de forma **esperada**, sin usar
excepciones para flujos normales.

**¿Qué problema resuelve?**

| Problema | Cómo lo resuelve este Sprint |
|----------|------------------------------|
| Cada módulo implementa su propio manejo de éxito/fracaso | `Result[T]` unifica el contrato: si una operación puede fallar, devuelve un Result |
| Las excepciones se usan para flujos esperados (no encontrado, duplicado) | `Result[T]` distingue: flujos alternativos esperados → Result, errores excepcionales → Exception |
| No hay forma de saber si una operación falló sin try/except | `result.is_success` / `result.is_failure` — inspección sin excepciones |
| El tipo del valor de éxito se pierde | `Result[T]` es genérico — `Result[TopicId]`, `Result[list[Feed]]` |
| Los errores no tienen estructura | `Error` estandariza: código machine-readable + mensaje + detalle |

---

## 2. Responsabilidades

### 2.1 Result[T]

```
Responsabilidades:
  - Encapsular éxito o fracaso de una operación
  - Proveer factory methods: success(), failure()
  - Proveer propiedades de inspección: is_success, is_failure
  - Ser genérica (T) para type safety del valor de éxito

NO hace:
  - No lanza excepciones
  - No tiene lógica de negocio
  - No sustituye excepciones para errores de programación
  - No tiene métodos de transformación (map, flat_map, bind)
```

### 2.2 Success[T]

```
Responsabilidades:
  - Representa una operación exitosa
  - Contiene el valor de tipo T
  - is_success → True, is_failure → False

NO hace:
  - No tiene error (no se puede construir con error)
```

### 2.3 Failure[T]

```
Responsabilidades:
  - Representa una operación fallida
  - Contiene el error (Error)
  - is_success → False, is_failure → True

NO hace:
  - No tiene valor de éxito (no se puede construir con valor)
```

### 2.4 Error

```
Responsabilidades:
  - Describir qué salió mal en una operación
  - code: ErrorCode — código machine-readable estandarizado
  - message: mensaje legible para el desarrollador
  - detail: información adicional (opcional)
  - __str__(): representación legible "[CODE] message"

NO hace:
  - No es una excepción (no hereda de Exception)
  - No tiene stack trace
  - No tiene lógica de logging
  - No contiene referencia a objetos de dominio
```

### 2.5 ErrorCode

```
Responsabilidades:
  - Estandarizar los códigos de error del sistema
  - Proveer al menos UNKNOWN como valor default
  - Ser extensible por cada BC (cada BC agrega sus códigos)

NO hace:
  - No contiene mensajes (son parte de Error)
  - No tiene lógica de negocio
  - No es una enumeración de errores (solo códigos)
```

---

## 3. Alcance

### 3.1 Qué pertenece al Sprint

| Componente | Descripción |
|-----------|-------------|
| **Result[T]** | Base class genérica frozen para resultados. Factory methods `success()`, `failure()`. Propiedades `is_success`, `is_failure`, `value`, `error`. |
| **Success[T]** | Subclase frozen de Result[T]. Almacena `value: T`. `is_success = True`. |
| **Failure[T]** | Subclase frozen de Result[T]. Almacena `error: Error`. `is_failure = True`. |
| **Error** | Value Object frozen con `code: ErrorCode`, `message`, `detail`. `__str__()` retorna `[CODE] message`. |
| **ErrorCode** | `str, Enum` con al menos `UNKNOWN`. Extensible por cada BC. |
| **unwrap()** | Método en Result[T] que retorna `value` en Success, lanza `RuntimeError` en Failure. |
| **result package** | `foundation/result/__init__.py` con exports públicos. |
| **API pública** | `foundation/__init__.py` actualizado para exportar Result, Success, Failure, Error, ErrorCode. |

### 3.2 Qué NO pertenece al Sprint

| Componente | Excluido porque... | Sprint asignado |
|-----------|-------------------|-----------------|
| ErrorCode con más valores que UNKNOWN | Cada BC define sus propios códigos. Foundation solo provee UNKNOWN como default. | Sprint 2.4+ o cada BC |
| map(), flat_map(), bind() | No están en el diseño. YAGNI — se agregan cuando se necesiten. | Futuro |
| Result.combine() / sequence() | No están en el diseño. | Futuro |
| Result como excepción | Result no es Exception, no hereda de Exception. | Nunca |
| FoundationError, DomainError | Error Hierarchy — son excepciones, no datos de resultado. | Sprint 2.4 |
| ApplicationError, InfrastructureError | Parte de Error Hierarchy. | Sprint 2.4 |
| DomainEvent, IntegrationEvent | Eventos de dominio. | Sprint 2.5+ |
| ClockPort, UUIDProvider | Puertos de infraestructura. | Sprint 2.6 |
| Cualquier lógica de negocio | Foundation NO tiene lógica de negocio. | Jamás |

### 3.3 Verificación contra ADR-021 (Foundation Stability Policy)

| Criterio | ¿Cumple? | Explicación |
|----------|----------|-------------|
| MULTI-BC (usado por ≥2 BCs) | ✅ Sí | TODO BC tiene operaciones que devuelven resultados |
| NO BUSINESS RULES | ✅ Sí | Result es mecánico — no hay semántica de negocio |
| ZERO DEPENDENCIES | ✅ Sí | Solo stdlib (dataclasses, typing, enum) |
| NO COUPLING | ✅ Sí | No referencia ningún BC ni concepto de dominio |
| MECHANISM, NOT POLICY | ✅ Sí | Es un patrón de manejo de resultados, no reglas de negocio |

### 3.4 Verificación contra ADR-018 (Result Pattern)

ADR-018 establece:
- Result[T] para operaciones que pueden fallar de forma esperada
- Excepciones solo para errores de programación o infraestructura
- Error como objeto de datos (no excepción)

Este sprint cumple completamente con ADR-018.

---

## 4. Archivos

### 4.1 Archivos a crear

| Ruta | Contenido | Depende de |
|------|-----------|------------|
| `src/foundation/result/__init__.py` | Re-exporta Result, Success, Failure, Error | result.py |
| `src/foundation/result/result.py` | `Result[T]`, `Success[T](Result[T])`, `Failure[T](Result[T])`, `Error` | N/A |
| `tests/foundation/test_result.py` | Tests de Result pattern | N/A |

### 4.2 Archivos a modificar

| Ruta | Cambio |
|------|--------|
| `src/foundation/__init__.py` | Agregar `Result`, `Success`, `Failure`, `Error` a los exports |

### 4.3 Archivos excluidos deliberadamente

- `src/foundation/errors/` — Error Hierarchy pertenece a Sprint 2.4
- `src/foundation/result/error_code.py` — ErrorCode va en result.py, no en archivo separado
- `src/foundation/result/_compat.py` — No se necesita (Python 3.12 tiene todo)

---

## 5. Dependencias

### 5.1 Dependencias de este Sprint

| Dependencia | Tipo | Detalle |
|------------|------|---------|
| Python 3.12 | Runtime | `@dataclass(frozen=True)`, `typing.Self`, `T` genérico (PEP 695) |
| pytest | Testing | Framework de tests |

### 5.2 Dependencias hacia este Sprint

| Componente futuro | ¿Por qué necesita este Sprint? |
|------------------|-------------------------------|
| Sprint 2.4 (Error Hierarchy) | Result usa `Error` (implementado aquí) |
| Sprint 3.x (Ingestion Domain) | Use cases devuelven `Result[T]` |
| Todos los BCs futuros | Toda operación que puede fallar devuelve `Result[T]` |

### 5.3 Árbol de dependencias

```
Sprint 2.1 (EntityId) ─→ Sprint 2.2 (Entity, AR, VO) ─→ Sprint 2.3 (Result)
                                                               │
                                                               ├──→ Sprint 2.4 (Error Hierarchy + DomainEvent)
                                                               ├──→ Sprint 3.x (Ingestion)
                                                               └──→ Research BC (refactor)
```

**Result NO depende de EntityId ni de Entity/ValueObject/AggregateRoot.** Es independiente.

---

## 6. API Pública

### 6.1 Result[T]

```python
@dataclass(frozen=True)
class Result[T]:
    """
    Resultado de una operación que puede tener éxito o fallar.
    
    T: tipo del valor en caso de éxito.
    
    Usar factory methods para construir:
        Result.success(value)  → Success[T]
        Result.failure(error)  → Failure[T]
    
    Inspección:
        result.is_success  → bool
        result.is_failure  → bool
    
    Acceso a datos:
        result.value  → T (raise si Failure)
        result.error  → Error (raise si Success)
    
    NO es una excepción. No sustituye excepciones para errores
    de programación o infraestructura.
    """
    
    @classmethod
    def success(cls, value: T) -> Result[T]:
        """Crea un resultado exitoso."""
        return Success(value=value)
    
    @classmethod
    def failure(cls, error: Error) -> Result[T]:
        """Crea un resultado fallido."""
        return Failure(error=error)
    
    @property
    def is_success(self) -> bool:
        raise NotImplementedError
    
    @property
    def is_failure(self) -> bool:
        raise NotImplementedError
    
    def unwrap(self) -> T:
        """
        Retorna el valor si es Success, lanza RuntimeError si es Failure.
        
        Útil cuando se está seguro de que el resultado es exitoso
        o cuando se quiere hacer fail-fast ante un error inesperado.
        
        Returns:
            El valor de tipo T si es Success.
        
        Raises:
            RuntimeError: Si el resultado es Failure, con el error como mensaje.
        """
        raise NotImplementedError
    
    def unwrap(self) -> T:
        """Lanza RuntimeError porque Failure no tiene valor."""
        raise RuntimeError(f"Cannot unwrap Failure: {self.error}")
    
    @property
    def value(self) -> T:
        raise RuntimeError("Cannot access value of a Failure")
```

### 6.4 ErrorCode

```python
class ErrorCode(str, Enum):
    """
    Códigos de error estandarizados.
    
    Convención: {CATEGORY}_{ERROR}
    
    Foundation provee UNKNOWN como valor default.
    Cada BC define su propio str, Enum independiente:
    
        class IngestionErrorCode(str, Enum):
            SOURCE_NOT_FOUND = "SOURCE_NOT_FOUND"
    
    NOTA: ErrorCode NO es extensible por herencia (Python 3.11+ prohíbe
    subclasear enums con miembros). Ver ADR-022 para detalle.
    
    Atributos:
        UNKNOWN: Código default cuando no hay una categoría específica.
    """
    UNKNOWN = "UNKNOWN"
```

### 6.5 Error

```python
@dataclass(frozen=True)
class Error:
    """
    Error de operación (NO es una excepción).
    
    Representa qué salió mal en una operación que devolvió Failure.
    
    Atributos:
        code: ErrorCode — código machine-readable estandarizado.
              Default: ErrorCode.UNKNOWN
        message: Mensaje legible para el desarrollador
        detail: Información adicional (opcional)
    
    NO es una excepción. No hereda de Exception.
    No tiene stack trace. No tiene lógica de logging.
    
    Uso:
        Error(code=ErrorCode.UNKNOWN, message="Something went wrong")
        str(error)  # → "[UNKNOWN] Something went wrong"
    """
    code: ErrorCode = ErrorCode.UNKNOWN
    message: str = ""
    detail: str | None = None
    
    def __str__(self) -> str:
        """Retorna representación legible: [CODE] message."""
        if self.detail:
            return f"[{self.code.value}] {self.message}: {self.detail}"
        return f"[{self.code.value}] {self.message}"
```

### 6.5 foundation/__init__.py (actualizado)

```python
from foundation.base.aggregate_root import AggregateRoot
from foundation.base.entity import Entity
from foundation.base.value_object import ValueObject
from foundation.entity_id import EntityId
from foundation.json_encoder import FoundationEncoder
from foundation.result.result import Error, ErrorCode, Failure, Result, Success

__all__ = [
    "AggregateRoot",
    "Entity",
    "EntityId",
    "Error",
    "ErrorCode",
    "Failure",
    "FoundationEncoder",
    "Result",
    "Success",
    "ValueObject",
]
```

---

## 7. Decisiones de Diseño

### 7.1 Result[T] como frozen dataclass sin campos

Result[T] es `@dataclass(frozen=True)` pero **no tiene campos propios**. Solo define
factory methods y propiedades abstractas (con `NotImplementedError`).

**¿Por qué frozen?** Aunque Result base no tiene campos, frozen garantiza que
Success y Failure (sus subclases) tampoco puedan mutarse. Un resultado no cambia
después de creado.

**¿Por qué @dataclass y no abc.ABC?** Consistencia con el resto de Foundation
(F3: explicit over implicit). ABC agrega overhead de metaclase sin beneficio real.
Las propiedades lanzan NotImplementedError si alguien intenta instanciar Result
directamente.

**¿Por qué sin campos?** `Result[T]` es un tipo suma (tagged union). El campo
`value` pertenece a `Success[T]`, el campo `error` pertenece a `Failure[T]`.
Ponerlos en Result sería incorrecto semánticamente y permitiría estados inválidos.

### 7.2 Success[T] y Failure[T] como subclases de Result[T]

Se usa herencia de dataclasses con frozen=True. Python 3.12 maneja correctamente:

```python
@dataclass(frozen=True)
class Result[T]: ...

@dataclass(frozen=True)
class Success[T](Result[T]):
    value: T
```

El `__init__` generado para `Success(value=x)` llama al `__init__` de Result (sin args)
y luego asigna `value`. frozen=True no impide la asignación inicial porque dataclass
usa `object.__setattr__` internamente.

### 7.3 Error como Value Object independiente

Error NO es una subclase de ValueObject. Es una frozen dataclass independiente.

**¿Por qué?** Error no comparte el contrato de ValueObject:
- No es un Value Object de dominio (no tiene semántica de negocio)
- No necesita ser intercambiable por igualdad estructural con otros VOs de dominio
- Mantenerlo separado permite que Foundation evolucione Error sin afectar ValueObject

Si en el futuro Error necesita compatibilidad con FoundationEncoder o con la API
de ValueObject, se puede agregar sin romper nada.

### 7.4 ErrorCode como enum estandarizado

Error.code usa `ErrorCode` (un `str, Enum`), no `str` directamente. Decisiones:

| Razón | Explicación |
|-------|-------------|
| **Consistencia** | Todos los errores del sistema usan códigos del mismo tipo, no strings libres |
| **Discoverabilidad** | IDE autocomplete muestra los códigos disponibles |
| **Convención, no herencia** | Cada BC define su propio `str, Enum` independiente. No existe herencia de ErrorCode (ver ADR-022) |
| **UNKNOWN como default** | Si no se especifica código, se usa `ErrorCode.UNKNOWN` — nunca un string vacío |

**¿Por qué UNKNOWN y no REQUIRED?** Porque hay casos donde no hay un código específico (errores genéricos de dominio). UNKNOWN es explícito sobre "no sabemos exactamente qué pasó".

### Limitación conocida: ErrorCode NO es extensible por herencia

Python 3.11+ prohíbe subclasear Enums que tienen miembros definidos. Como `ErrorCode`
tiene `UNKNOWN = "UNKNOWN"`, esto NO funciona:

```python
# ❌ TypeError: cannot extend <enum 'ErrorCode'>
class IngestionError(ErrorCode):
    SOURCE_NOT_FOUND = "SOURCE_NOT_FOUND"
```

La decisión oficial (ADR-022) es:

1. **Cada BC define su propio `str, Enum`** con sus códigos de error.
2. **Foundation NO intenta ser una jerarquía de enums.** Solo define `ErrorCode.UNKNOWN`.
3. La relación es de **convención, no de herencia**: todos los enums de error siguen
   el patrón `str, Enum` y son compatibles con `Error(code=...)`.

```python
# ✅ BIEN — Cada BC define su propio Enum
class IngestionErrorCode(str, Enum):
    SOURCE_NOT_FOUND = "SOURCE_NOT_FOUND"

# ✅ BIEN — Se usa con Error(code=...) sin problemas
Error(code=IngestionErrorCode.SOURCE_NOT_FOUND, message="Source not found")
```

### 7.5 RuntimeError en lugar de NotImplementedError

Acceder a `result.value` en un Failure lanza `RuntimeError`. Acceder a `result.error` en un Success lanza `RuntimeError`.

**¿Por qué RuntimeError y no NotImplementedError?**

| Razón | Explicación |
|-------|-------------|
| **Semántica correcta** | No es que el método "no esté implementado" — es que NO DEBE llamarse en este estado |
| **Fail Fast** | `RuntimeError` comunica "esto no debería pasar" vs "esto no está implementado aún" |
| **Claridad en debugging** | El mensaje explica exactamente qué se hizo mal |

El uso esperado NO es acceder a value/error directamente, sino usar pattern matching o `is_success` / `is_failure`:

### 7.6 unwrap() para acceso directo con fail-fast

`unwrap()` retorna el valor en Success y lanza `RuntimeError` con el error como mensaje en Failure.

**¿Por qué unwrap y no simplemente acceder a .value?**
- `.value` lanza RuntimeError en Failure (protección contra acceso incorrecto)
- `unwrap()` lanza RuntimeError INCLUYENDO el error como mensaje: `"Cannot unwrap Failure: [NOT_FOUND] Topic not found"`
- `unwrap()` es útil cuando se está seguro del éxito o en composition roots donde el error es irrecuperable

```python
# ❌ Sin unwrap — hay que checkear manualmente
if result.is_success:
    value = result.value

# ✅ Con unwrap — fail-fast, el error se propaga con contexto
value = result.unwrap()  # RuntimeError si es Failure
```

### 7.7 Error.__str__() para representación legible

`str(Error(...))` retorna `[CODE] message` (con `: detail` opcional si existe).
Esto facilita logging y debugging sin inspeccionar atributos manualmente.

### 7.6 Sin métodos map, flat_map, bind

El diseño del foundation-design.md NO incluye métodos de transformación en Result.
Se excluyen por YAGNI: se agregan cuando al menos 2 clientes del Result pattern
necesiten composición funcional.

### 7.7 Result no implementa FoundationEncoder

A diferencia de EntityId (que tiene FoundationEncoder), Result NO necesita
serialización JSON directa. El valor interno (Success.value) y el error (Failure.error)
se serializan individualmente por quien los usa.

Si se necesita en el futuro, se agrega sin romper compatibilidad.

---

## 8. Riesgos

| Riesgo | Impacto | Probabilidad | Mitigación |
|--------|---------|-------------|------------|
| **Uso incorrecto de `Result.success()` sin type parameter**: `Result.success(42)` infiere `Result[int]`, pero `Result.success()` sin valor concreto podría inferir `Result[Never]`. | Bajo | Baja | Python 3.12 infiere correctamente. Type checkers (mypy/pyright) detectan usos incorrectos. |
| **Herencia de dataclasses frozen con genéricos (PEP 695)**: Posibles edge cases con TypeVar y herencia. | Medio | Baja | Verificar con tests de tipo. Python 3.12.3 maneja PEP 695 correctamente. |
| **Result como tipo suma sin exhaustiveness checking**: Python no forcecea que se cubran Success y Failure en match/case. | Medio | Alta | Documentar que el uso correcto es con match/case. Type checkers como pyright pueden forzar exhaustiveness con `assert_never()`. |
| **Confusión Result vs Exception**: Desarrolladores podrían usar Result donde va Exception o viceversa. | Medio | Media | Documentar cuándo usar cada uno (ver §5.3 del foundation-design.md). Code review. |
| **NotImplementedError en properties**: Si alguien crea una subclase de Result sin overridear las properties, recibe NotImplementedError en runtime. | Bajo | Baja | Success y Failure son las únicas implementaciones. Result directo no debería instanciarse (aunque técnicamente puede). |

---

## 9. Casos Borde

### 9.1 Result[T]

#### 9.1.1 Construcción exitosa

```python
result = Result.success(42)
assert result.is_success is True
assert result.is_failure is False
assert result.value == 42
```

#### 9.1.2 Construcción fallida

```python
error = Error(code="NOT_FOUND", message="Topic not found")
result = Result.failure(error)
assert result.is_success is False
assert result.is_failure is True
assert result.error == error
```

#### 9.1.3 Acceder a value en Failure

```python
result: Result[int] = Result.failure(Error(code=ErrorCode.UNKNOWN, message=""))
with pytest.raises(RuntimeError, match="Cannot access value"):
    _ = result.value
```

#### 9.1.4 Acceder a error en Success

```python
result = Result.success(42)
with pytest.raises(RuntimeError, match="Cannot access error"):
    _ = result.error
```

#### 9.1.5 unwrap en Success

```python
result = Result.success(42)
assert result.unwrap() == 42
```

#### 9.1.6 unwrap en Failure

```python
result: Result[int] = Result.failure(Error(code=ErrorCode.UNKNOWN, message="fail"))
with pytest.raises(RuntimeError, match="Cannot unwrap"):
    _ = result.unwrap()
```

#### 9.1.7 Pattern Matching

```python
result = Result.success(42)
match result:
    case Success(value=v):
        assert v == 42
    case Failure(error=e):
        pytest.fail("Should not be failure")
```

### 9.2 Success[T]

#### 9.2.1 Inmutabilidad

```python
s = Success(value=42)
with pytest.raises(FrozenInstanceError):
    s.value = 99  # type: ignore[misc]
```

#### 9.2.2 Igualdad estructural

```python
a = Success(value=42)
b = Success(value=42)
c = Success(value=99)

assert a == b   # ✅ Mismos valores
assert a != c   # ✅ Diferentes valores
assert hash(a) == hash(b)  # ✅ Mismo hash
```

#### 9.2.3 Success con tipos no comparables

```python
s1 = Success(value=[1, 2, 3])  # ✅ list, dict, etc. como value
s2 = Success(value=[1, 2, 3])
assert s1 == s2  # ✅ Igualdad estructural funciona
```

#### 9.2.4 Success con None

```python
s = Success(value=None)
assert s.is_success is True
assert s.value is None
# Success(None) != Failure — son tipos diferentes
```

### 9.3 Failure[T]

#### 9.3.1 Inmutabilidad

```python
f = Failure(error=Error(code="ERR", message=""))
with pytest.raises(FrozenInstanceError):
    f.error = Error(code="NEW", message="")  # type: ignore[misc]
```

#### 9.3.2 Igualdad estructural

```python
err = Error(code="NOT_FOUND", message="x")
a = Failure(error=err)
b = Failure(error=err)
c = Failure(error=Error(code="DUPLICATE", message="y"))

assert a == b   # ✅ Mismo error
assert a != c   # ✅ Diferente error
```

#### 9.3.3 Failure con diferentes tipos genéricos

```python
int_failure: Result[int] = Result.failure(Error(code="ERR", message=""))
str_failure: Result[str] = Result.failure(Error(code="ERR", message=""))

# Son tipos diferentes en tiempo de compilación
# En runtime, la igualdad es estructural
assert int_failure == str_failure  # Ambos Failure con mismo Error
```

### 9.4 Error

#### 9.4.1 Error mínimo

```python
err = Error(code=ErrorCode.UNKNOWN, message="Topic not found")
assert err.code is ErrorCode.UNKNOWN
assert err.message == "Topic not found"
assert err.detail is None
```

#### 9.4.2 Error con detail y __str__

```python
err = Error(code=ErrorCode.UNKNOWN, message="Invalid data", detail="Field 'name' is required")
assert err.detail == "Field 'name' is required"
assert str(err) == "[UNKNOWN] Invalid data: Field 'name' is required"
```

#### 9.4.3 Error no es excepción

```python
err = Error(code=ErrorCode.UNKNOWN, message="")
assert not isinstance(err, Exception)
assert not isinstance(err, BaseException)
```

#### 9.4.4 Error inmutable

```python
err = Error(code=ErrorCode.UNKNOWN, message="Y")
with pytest.raises(FrozenInstanceError):
    err.code = ErrorCode.UNKNOWN  # type: ignore[misc]
```

#### 9.4.5 Error con default UNKNOWN

```python
err = Error(message="something")
assert err.code is ErrorCode.UNKNOWN
```

#### 9.4.6 __str__ sin detail

```python
err = Error(code=ErrorCode.UNKNOWN, message="Something went wrong")
assert str(err) == "[UNKNOWN] Something went wrong"
```

#### 9.4.7 __str__ con message vacío

```python
err = Error(code=ErrorCode.UNKNOWN)
assert str(err) == "[UNKNOWN] "
```

### 9.5 Edge cases cross-component

#### 9.5.1 Success vs Failure (nunca iguales)

```python
s = Result.success(42)
f: Result[int] = Result.failure(Error(code="ERR", message=""))
assert s != f  # ✅ Success != Failure
```

#### 9.5.2 Result con tipos complejos

```python
result = Result.success({"key": [1, 2, 3]})
assert result.is_success is True
assert result.value == {"key": [1, 2, 3]}
```

#### 9.5.3 Result de Result (anidado)

```python
inner = Result.success(42)
outer = Result.success(inner)
assert outer.is_success is True
assert outer.value == inner
assert outer.value.is_success is True
```

---

## 10. Estrategia de Testing

### 10.1 Estructura de tests

```
tests/foundation/
├── test_entity_id.py       ← Sprint 2.1 (existente)
├── test_value_object.py    ← Sprint 2.2 (existente)
├── test_entity.py          ← Sprint 2.2 (existente)
├── test_aggregate_root.py  ← Sprint 2.2 (existente)
└── test_result.py          ← NUEVO
```

### 10.2 Test Result (~55 tests)

#### Grupo 1: Construcción (~6 tests)

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 1.1 | `test_success_creation` | `Result.success(42)` | `Success` instance | Válido |
| 1.2 | `test_failure_creation` | `Result.failure(Error(...))` | `Failure` instance | Válido |
| 1.3 | `test_success_type_retained` | `Result.success("hello")` | `isinstance(Success[str])` | Válido |
| 1.4 | `test_success_with_none` | `Result.success(None)` | `Success[None]` instance | Edge case |
| 1.5 | `test_success_with_false` | `Result.success(False)` | `value is False` | Edge case |
| 1.6 | `test_success_with_zero` | `Result.success(0)` | `value == 0` | Edge case |

#### Grupo 2: Inspección (~8 tests)

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 2.1 | `test_is_success_on_success` | `Result.success(42)` | `is_success == True` | Válido |
| 2.2 | `test_is_success_on_failure` | `Result.failure(Error(...))` | `is_success == False` | Válido |
| 2.3 | `test_is_failure_on_success` | `Result.success(42)` | `is_failure == False` | Válido |
| 2.4 | `test_is_failure_on_failure` | `Result.failure(Error(...))` | `is_failure == True` | Válido |
| 2.5 | `test_success_value_access` | `Result.success(42)` | `value == 42` | Válido |
| 2.6 | `test_failure_error_access` | `Result.failure(err)` | `error == err` | Válido |
| 2.7 | `test_success_error_raises` | `Result.success(42).error` | `RuntimeError` | Inválido |
| 2.8 | `test_failure_value_raises` | `Result.failure(err).value` | `RuntimeError` | Inválido |

#### Grupo 3: Igualdad (~6 tests)

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 3.1 | `test_equal_success` | `Success(42)`, `Success(42)` | `== True` | Válido |
| 3.2 | `test_unequal_success` | `Success(42)`, `Success(99)` | `!= True` | Válido |
| 3.3 | `test_equal_failure` | `Failure(e)`, `Failure(e)` | `== True` | Válido |
| 3.4 | `test_unequal_failure` | `Failure(e1)`, `Failure(e2)` | `!= True` | Válido |
| 3.5 | `test_success_not_equal_failure` | `Success(42)` vs `Failure(err)` | `!= True` | Edge case |
| 3.6 | `test_success_same_hash` | `Success(42)`, `Success(42)` | `hash()` igual | Válido |

#### Grupo 4: Hash (~3 tests)

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 4.1 | `test_hash_equal_success` | `Success(42)`, `Success(42)` | `hash()` igual | Válido |
| 4.2 | `test_hash_different_success` | `Success(42)`, `Success(99)` | `hash()` diferente | Válido |
| 4.3 | `test_hash_success_and_failure` | `Success(42)` vs `Failure(err)` | `hash()` diferente | Válido |

#### Grupo 6: unwrap (~4 tests)

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 6.1 | `test_unwrap_success` | `Result.success(42).unwrap()` | `42` | Válido |
| 6.2 | `test_unwrap_failure_raises` | `Result.failure(err).unwrap()` | `RuntimeError` | Inválido |
| 6.3 | `test_unwrap_with_none` | `Result.success(None).unwrap()` | `None` | Edge case |
| 6.4 | `test_unwrap_error_message` | `RuntimeError message` | Incluye `str(error)` | Inválido |

#### Grupo 7: ErrorCode + Error (~11 tests)

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 7.1 | `test_errorcode_unknown_default` | `ErrorCode` | `ErrorCode.UNKNOWN == "UNKNOWN"` | Válido |
| 7.2 | `test_error_creation` | `Error(ErrorCode.UNKNOWN, "msg")` | `code is ErrorCode.UNKNOWN` | Válido |
| 7.3 | `test_error_default_code` | `Error(message="msg")` | `code is ErrorCode.UNKNOWN` | Válido |
| 7.4 | `test_error_with_detail` | `Error(ErrorCode.UNKNOWN, "msg", detail="x")` | `detail == "x"` | Válido |
| 7.5 | `test_error_detail_defaults_none` | `Error(code=ErrorCode.UNKNOWN, message="y")` | `detail is None` | Válido |
| 7.6 | `test_error_str_no_detail` | `str(Error(ErrorCode.UNKNOWN, "Something"))` | `"[UNKNOWN] Something"` | Válido |
| 7.7 | `test_error_str_with_detail` | `str(Error(ErrorCode.UNKNOWN, "Inv", detail="Field"))` | `"[UNKNOWN] Inv: Field"` | Válido |
| 7.8 | `test_error_not_exception` | `isinstance(err, BaseException)` | `False` | Edge case |
| 7.9 | `test_error_structural_equality` | Mismo code + message + detail | `== True` | Válido |
| 7.10 | `test_error_str_empty_message` | `Error(code=ErrorCode.UNKNOWN)` | `str(err) == "[UNKNOWN] "` | Edge case |
| 7.11 | `test_error_frozen` | Mutación de `error.code` | `FrozenInstanceError` | Inválido |

#### Grupo 8: Pattern Matching (~3 tests)

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 8.1 | `test_match_success` | `match Result.success(42)` | Coincide `Success(value=42)` | Válido |
| 8.2 | `test_match_failure` | `match Result.failure(err)` | Coincide `Failure(error=err)` | Válido |
| 8.3 | `test_match_exhaustive` | Ambos casos cubiertos | No hay `TypeError` | Edge case |

#### Grupo 9: Serialización (~4 tests)

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 9.1 | `test_deepcopy_success` | `copy.deepcopy(Result.success([1,2,3]))` | Copia independiente | Edge case |
| 9.2 | `test_deepcopy_failure` | `copy.deepcopy(Result.failure(err))` | Copia independiente | Edge case |
| 9.3 | `test_pickle_success` | `pickle.loads(pickle.dumps(Result.success(42)))` | `value == 42` | Edge case |
| 9.4 | `test_pickle_failure` | `pickle.loads(pickle.dumps(Result.failure(err)))` | `error == err` | Edge case |

#### Grupo 10: Edge Cases (~8 tests)

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 10.1 | `test_success_with_list_value` | `Result.success([1, 2, 3])` | `value == [1, 2, 3]` | Edge case |
| 10.2 | `test_success_with_empty_list` | `Result.success([])` | `value == []` | Edge case |
| 10.3 | `test_success_with_dict_value` | `Result.success({"a": 1})` | `value == {"a": 1}` | Edge case |
| 10.4 | `test_success_with_empty_dict` | `Result.success({})` | `value == {}` | Edge case |
| 10.5 | `test_failure_generic_type_int` | `Result.failure(err)` | `isinstance(Failure[int])` | Válido |
| 10.6 | `test_failure_generic_type_str` | `Result.failure(err)` | `isinstance(Failure[str])` | Válido |
| 10.7 | `test_result_in_set` | Set con resultados | Size correcto | Edge case |
| 10.8 | `test_result_in_dict` | Dict con keys de resultado | Lookup funciona | Edge case |

#### Grupo 11: Inmutabilidad (~3 tests)

| # | Test | Input | Expected | Categoría |
|---|------|-------|----------|-----------|
| 11.1 | `test_success_frozen` | `s.value = 99` | `FrozenInstanceError` | Inválido |
| 11.2 | `test_failure_frozen` | `f.error = new_err` | `FrozenInstanceError` | Inválido |
| 11.3 | `test_success_and_failure_are_types` | `type(Success(42)) is not type(Failure(err))` | Son clases distintas | Edge case |

### 10.3 Convenciones de tests

```python
from dataclasses import FrozenInstanceError
import pytest

from foundation import Error, ErrorCode, Failure, Result, Success


class TestConstruction:
    def test_success_creation(self):
        result = Result.success(42)
        assert isinstance(result, Success)
        assert result.value == 42

    def test_failure_creation(self):
        error = Error(code=ErrorCode.UNKNOWN, message="Not found")
        result: Result[int] = Result.failure(error)
        assert isinstance(result, Failure)
        assert result.error == error

    def test_unwrap_success_returns_value(self):
        result = Result.success(42)
        assert result.unwrap() == 42

    def test_unwrap_failure_raises(self):
        error = Error(code=ErrorCode.UNKNOWN, message="fail")
        result: Result[int] = Result.failure(error)
        with pytest.raises(RuntimeError, match="Cannot unwrap"):
            result.unwrap()
```

---

## 11. Criterios de Aceptación

### 11.1 Tests

```bash
pytest tests/foundation/ -v
```

- [ ] Todos los tests de `tests/foundation/` pasan (136 existentes + ~60 nuevos)
- [ ] No hay tests saltados ni pendientes
- [ ] No se rompen tests existentes del proyecto

### 11.2 Result[T]

- [ ] `Result.success(value)` construye un `Success[T]`
- [ ] `Result.failure(error)` construye un `Failure[T]`
- [ ] `is_success` es True para Success, False para Failure
- [ ] `is_failure` es True para Failure, False para Success
- [ ] `value` retorna el valor en Success, lanza `RuntimeError` en Failure
- [ ] `error` retorna el error en Failure, lanza `RuntimeError` en Success
- [ ] `unwrap()` retorna el valor en Success, lanza `RuntimeError` en Failure
- [ ] Success y Failure son frozen (inmutables)
- [ ] Pattern matching funciona: `match result: case Success(...): case Failure(...):`

### 11.3 ErrorCode

- [ ] `ErrorCode.UNKNOWN == "UNKNOWN"`
- [ ] Cada BC define su propio `str, Enum` para códigos de error (no hereda de ErrorCode — ver ADR-022)

### 11.4 Error

- [ ] `Error(code=ErrorCode.UNKNOWN, message="...")` construye correctamente
- [ ] `Error(message="...")` usa `ErrorCode.UNKNOWN` como default
- [ ] `Error.__str__()` retorna `[CODE] message` (con `: detail` opcional)
- [ ] `detail` default es `None`
- [ ] Error NO es instancia de `Exception` ni `BaseException`
- [ ] Error es frozen (inmutable)
- [ ] Error tiene igualdad estructural

### 11.5 Integración

- [ ] `from foundation import Error, ErrorCode, Failure, Result, Success` funciona
- [ ] `foundation/__init__.py` exporta las 5 clases
- [ ] No hay imports rotos de sprints anteriores
- [ ] FoundationEncoder no se modifica
- [ ] EntityId, Entity, ValueObject, AggregateRoot no se modifican

### 11.6 Zero dependencias

- [ ] `src/foundation/` solo importa de stdlib
- [ ] No se agregaron dependencias a requirements.txt

### 11.7 Validación contra ADR-018

- [ ] Result no es Exception
- [ ] Error no es Exception
- [ ] Result no lanza excepciones internamente
- [ ] Result no sustituye excepciones para errores de infraestructura

---

## 12. Compatibilidad con la Arquitectura Existente

### 12.1 No rompe sprints anteriores

- Sprint 2.1 (EntityId, FoundationEncoder): Sin cambios
- Sprint 2.2 (ValueObject, Entity, AggregateRoot): Sin cambios

### 12.2 Consistencia con patrones existentes

- `@dataclass(frozen=True)` — mismo patrón que EntityId
- Genéricos (PEP 695) — mismo estilo que el diseño de foundation-design.md
- Zero dependencias — mismo principio que todo Foundation

### 12.3 Foundation permanece independiente del dominio

Result[T] no referencia:
- EntityId (no lo necesita)
- ValueObject, Entity, AggregateRoot
- Ningún concepto de dominio

---

## Apéndice A: Diseño de Referencia

Extraído de foundation-design.md §5 con ajustes por marker class y decisiones de diseño:

### A.1 Result[T]

```python
@dataclass(frozen=True)
class Result[T]:
    """
    Result Pattern: encapsula éxito o fracaso de una operación.
    
    T: tipo del valor en caso de éxito.
    
    NO hacer:
      - No lanza excepciones internamente
      - No tiene lógica de negocio
      - No sustituye excepciones para errores de programación
    
    ¿Por qué frozen?
      - Un resultado no cambia después de creado.
    
    ¿Por qué genérico (T)?
      - Type safety: Result[TopicId] vs Result[str]
    """
    
    @classmethod
    def success(cls, value: T) -> "Result[T]":
        """Crea un resultado exitoso."""
        return Success(value=value)
    
    @classmethod
    def failure(cls, error: "Error") -> "Result[T]":
        """Crea un resultado fallido."""
        return Failure(error=error)
    
    @property
    def is_success(self) -> bool:
        """True si el resultado es exitoso."""
        raise NotImplementedError
    
    @property
    def is_failure(self) -> bool:
        """True si el resultado es fallido."""
        raise NotImplementedError
    
    def unwrap(self) -> T:
        """Retorna el valor o lanza RuntimeError si es Failure."""
        raise NotImplementedError
    
    @property
    def value(self) -> T:
        """Valor de éxito. Lanza RuntimeError si es Failure."""
        raise RuntimeError("Cannot access value of a Failure")
    
    @property
    def error(self) -> "Error":
        """Error. Lanza RuntimeError si es Success."""
        raise RuntimeError("Cannot access error of a Success")


@dataclass(frozen=True)
class Success[T](Result[T]):
    value: T
    
    @property
    def is_success(self) -> bool:
        return True
    
    @property
    def is_failure(self) -> bool:
        return False
    
    def unwrap(self) -> T:
        """Retorna el valor directamente."""
        return self.value
    
    @property
    def error(self) -> "Error":
        raise RuntimeError("Cannot access error of a Success")


@dataclass(frozen=True)
class Failure[T](Result[T]):
    error: Error
    
    @property
    def is_success(self) -> bool:
        return False
    
    @property
    def is_failure(self) -> bool:
        return True
    
    def unwrap(self) -> T:
        """Lanza RuntimeError porque Failure no tiene valor."""
        raise RuntimeError(f"Cannot unwrap Failure: {self.error}")
    
    @property
    def value(self) -> T:
        raise RuntimeError("Cannot access value of a Failure")


class ErrorCode(str, Enum):
    """Códigos de error estandarizados. Foundation provee UNKNOWN."""
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Error:
    """
    Error del Result Pattern.
    
    No es una excepción. Es un objeto de datos que describe
    qué salió mal en una operación.
    
    Atributos:
      - code: ErrorCode (default: ErrorCode.UNKNOWN)
      - message: Mensaje legible para el desarrollador
      - detail: Información adicional (opcional)
    
    NO hace:
      - No tiene stack trace
      - No es una excepción (no hereda de Exception)
      - No tiene lógica de logging
    """
    code: ErrorCode = ErrorCode.UNKNOWN
    message: str = ""
    detail: str | None = None
    
    def __str__(self) -> str:
        """[CODE] message o [CODE] message: detail."""
        if self.detail:
            return f"[{self.code.value}] {self.message}: {self.detail}"
        return f"[{self.code.value}] {self.message}"
```

---

## Apéndice B: Estructura de Archivos Resultante

```
src/foundation/
├── __init__.py              ← API pública (EntityId, FoundationEncoder,
│                                ValueObject, Entity, AggregateRoot,
│                                Result, Success, Failure, Error)
├── entity_id.py             ← Sprint 2.1
├── json_encoder.py          ← Sprint 2.1
├── base/                    ← Sprint 2.2
│   ├── __init__.py
│   ├── value_object.py
│   ├── entity.py
│   └── aggregate_root.py
└── result/                  ← NUEVO (Sprint 2.3)
    ├── __init__.py          ← Re-exporta Result, Success, Failure, Error, ErrorCode
    └── result.py            ← Result[T], Success[T], Failure[T], Error, ErrorCode

tests/foundation/
├── __init__.py
├── conftest.py              ← Sprint 2.1
├── test_entity_id.py        ← Sprint 2.1 (65 tests)
├── test_value_object.py     ← Sprint 2.2 (18 tests)
├── test_entity.py           ← Sprint 2.2 (29 tests)
├── test_aggregate_root.py   ← Sprint 2.2 (24 tests)
└── test_result.py           ← NUEVO (~60 tests)
```

---

## Apéndice C: Ejemplos de Uso (no implementar)

```python
# Domain service que usa Result
from foundation import Error, ErrorCode, Failure, Result, Success

def calculate_score(article: Article) -> Result[float]:
    if not article.content:
        return Result.failure(
            Error(code=ErrorCode.UNKNOWN, message="Article has no content")
        )
    
    score = _compute_score(article.content)
    return Result.success(score)


# Application service que usa Result
class EvaluateTopicUseCase:
    async def execute(self, command: EvaluateTopicCommand) -> Result[TopicEvaluation]:
        # Pattern matching — forma preferida
        topic = await self.topic_repo.find_by_id(command.topic_id)
        
        match topic:
            case Success(value=t):
                evaluation = self.evaluator.evaluate(t)
                return Result.success(evaluation)
            case Failure(error=e):
                return Result.failure(e)


# Composition root — unwrap para fail-fast
def main() -> None:
    result = calculate_score(article)
    score = result.unwrap()  # RuntimeError si falla
    print(f"Score: {score}")
```
