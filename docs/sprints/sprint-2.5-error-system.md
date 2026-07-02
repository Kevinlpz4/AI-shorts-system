# Sprint 2.5: Foundation Error System

> **Status**: ARCHIVED — Completado el 2026-07-02
> **Depende de**: Sprint 2.3 (Result Pattern — Error, ErrorCode, Result[T])
> **Dependencias futuras**: Sprint 2.6 (Clock Provider), Sprint 2.7 (UUID Provider)

---

## 1. Objetivo del Sprint

Implementar la jerarquía de excepciones base del Foundation Layer — `FoundationError`, `DomainError`, `ApplicationError`, `InfrastructureError` — e integrarla con el sistema `Result` existente **sin romper backward compatibility**.

---

## 2. Responsabilidades

| Componente | Responsabilidad |
|------------|----------------|
| `FoundationError` | Base técnica de TODAS las excepciones del sistema. No es de dominio. Provee `code`, `message`, `detail`, `to_dict()`. |
| `DomainError` | Error de DOMINIO. Refleja violación de regla de negocio. Los handlers pueden traducirlo a HTTP status codes. |
| `ApplicationError` | Error de APLICACIÓN. Comando inválido, operación no permitida, recurso no encontrado. NO es lógica de negocio. |
| `InfrastructureError` | Error de INFRAESTRUCTURA. DB caída, timeout de red, servicio externo caído. Generalmente irrecuperable. |
| `Error.from_exception()` | Puente entre el mundo de excepciones y el Result Pattern. Permite convertir una excepción FoundationError en un `Error` (dataclass) para usar con `Result.failure()`. |
| `FoundationError.to_error()` | Puente inverso: una excepción puede convertirse a `Error` para propagación vía Result. |

---

## 3. Alcance

### 3.1 Qué entra

1. **Paquete `foundation/errors/`** con `__init__.py` y `base.py`
2. **`FoundationError(Exception)`** — base de todas las excepciones del sistema
   - `code: ClassVar[str]` — código machine-readable
   - `message: str` — mensaje público (opcional)
   - `detail: str` — mensaje técnico para debugging
   - `to_dict() -> dict` — serialización para APIs
3. **`DomainError(FoundationError)`** — excepción de dominio
   - `code = "DOMAIN_ERROR"` por defecto
4. **`ApplicationError(FoundationError)`** — excepción de aplicación
   - `code = "APPLICATION_ERROR"` por defecto
5. **`InfrastructureError(FoundationError)`** — excepción de infraestructura
   - `code = "INFRASTRUCTURE_ERROR"` por defecto
6. **Integración con Result** (aditiva, NO rompe compatibilidad):
   - `Error.from_exception(exception: FoundationError) -> Error` — classmethod que envuelve una excepción como Error dataclass
   - `FoundationError.to_error() -> Error` — método que convierte la excepción a Error
7. **Re-exportación desde `foundation/__init__.py`**
8. **Tests completos** para todo lo nuevo
9. **Actualización del docstring** de `foundation/__init__.py`

### 3.2 Qué NO entra

- ❌ NO se modifican las clases `Result[T]`, `Success[T]`, `Failure[T]` existentes
- ❌ NO se modifica la clase `Error` (dataclass frozen) existente
- ❌ NO se modifica `ErrorCode` (enum) existente
- ❌ NO se agregan métodos a `Result.success()` ni `Result.failure()`
- ❌ NO se agregan subclases específicas de DomainError (ResearchAlreadyReviewedError, etc.) — esas pertenecen a cada BC
- ❌ NO se implementa `ClockPort` ni `UUIDProvider` (son Sprint 2.6 y 2.7)
- ❌ NO se modifica el comportamiento de ningún BC existente

---

## 4. Archivos del Sprint

### 4.1 Nuevos

| Archivo | Propósito |
|---------|-----------|
| `src/foundation/errors/__init__.py` | Re-exports del paquete errors |
| `src/foundation/errors/base.py` | FoundationError + DomainError + ApplicationError + InfrastructureError |
| `tests/foundation/test_errors.py` | Tests de la jerarquía de errores (~25 tests) |

### 4.2 Modificados

| Archivo | Cambio |
|---------|--------|
| `src/foundation/result/result.py` | Agregar `Error.from_exception()` (classmethod) — solo aditivo |
| `src/foundation/__init__.py` | Agregar imports y exports de FoundationError, DomainError, ApplicationError, InfrastructureError |
| `docs/architecture/foundation-design.md` | Actualizar sección 13 (`__init__.py` final) para reflejar los nuevos exports |

### 4.3 Eliminados

Ninguno.

---

## 5. Dependencias

### 5.1 Con sprints anteriores

| Sprint | Dependencia | Estado |
|--------|-------------|--------|
| Sprint 2.3 | `Error` (frozen dataclass) — existe y no se modifica | ✅ |
| Sprint 2.3 | `ErrorCode` (str, Enum) — existe y no se modifica | ✅ |
| Sprint 2.3 | `Result[T]`, `Success[T]`, `Failure[T]` — existen y no se modifican | ✅ |
| Sprint 2.1 | `EntityId` — existe, no se modifica | ✅ |
| ADR-022 | ErrorCode Enum Inheritance — cada BC define su propio enum | ✅ |
| ADR-021 | Foundation Stability Policy — 5 criterios | ✅ |

### 5.2 Para sprints futuros

| Sprint | Dependencia |
|--------|-------------|
| Sprint 2.6 (Clock Provider) | La jerarquía de errores permitirá que Clock tenga sus propios errores de dominio |
| Sprint 2.7 (UUID Provider) | Igual — FoundationError como base |
| Cualquier BC | `DomainError` será la base para errores de dominio específicos (ResearchAlreadyReviewedError, etc.) |
| Cualquier BC | `InfrastructureError` será la base para errores de infraestructura (DatabaseConnectionError, etc.) |
| Application Service | Podrá capturar FoundationError y convertirlo a Error vía `Error.from_exception()` para retornar Result |

---

## 6. API Pública

### 6.1 Desde `foundation/__init__.py`

```python
from foundation import FoundationError, DomainError, ApplicationError, InfrastructureError
```

### 6.2 `foundation.errors.base`

```python
class FoundationError(Exception):
    """
    Base de TODAS las excepciones del sistema.
    
    NO es DomainError — es una base técnica.
    DomainError hereda de esta.
    
    Atributos:
        code: str — código machine-readable (ClassVar)
        message: str — mensaje público (opcional, default "")
        detail: str — mensaje técnico para debugging (default "")
    
    Métodos:
        to_error() -> Error — convierte la excepción en un Error dataclass
        to_dict() -> dict — serialización para APIs
    """

class DomainError(FoundationError):
    """Error de DOMINIO. code = "DOMAIN_ERROR"."""

class ApplicationError(FoundationError):
    """Error de APLICACIÓN. code = "APPLICATION_ERROR"."""

class InfrastructureError(FoundationError):
    """Error de INFRAESTRUCTURA. code = "INFRASTRUCTURE_ERROR"."""
```

### 6.3 Integración desde `foundation.result.result`

```python
# En Error (dataclass frozen existente) — SOLO ADITIVO:
@classmethod
def from_exception(cls, exception: FoundationError) -> Error:
    """
    Crea un Error desde una excepción FoundationError.
    
    Útil en Application Services para capturar excepciones y 
    convertirlas a Result.failure().
    
    Args:
        exception: La excepción FoundationError a envolver.
    
    Returns:
        Error con el mensaje y detalle de la excepción.
    """

# En FoundationError:
def to_error(self) -> Error:
    """
    Convierte esta excepción en un Error para Result.
    
    Permite que código que captura FoundationError lo convierta
    a Result.failure() de forma estándar.
    
    Returns:
        Error con el mensaje y detalle de esta excepción.
    """
```

---

## 7. Decisiones de Diseño

### D1. FoundationError es Exception (no dataclass)

| Aspecto | Decisión |
|---------|----------|
| **Decisión** | `FoundationError` hereda de `Exception`, NO es `@dataclass`. |
| **Justificación** | Las excepciones en Python NO deben ser dataclasses frozen. `Exception` ya maneja args, traceback, y causa chain. Hacer una exception frozen rompe el protocolo de excepciones de Python. |
| **Alternativa** | `@dataclass(frozen=True)` — descartado porque `Exception.__init__` espera mutabilidad. |
| **ADR** | ADR-020 (Tres capas de error) |
| **Principios** | F3 (explicit over implicit) |

### D2. code como ClassVar[str] (no enum)

| Aspecto | Decisión |
|---------|----------|
| **Decisión** | `code` es `ClassVar[str]` con valor default por clase. Cada subclase especializada (e.g., `ResearchAlreadyReviewedError`) define su propio `code`. |
| **Justificación** | Los códigos de las excepciones son strings planos, NO enums. Son categorías de error. Los enums son para `ErrorCode` en el Result Pattern (que ya existe). Son conceptos diferentes. |
| **Alternativa** | Usar `ErrorCode` enum — descartado porque mezcla excepciones (excepcionales) con Result (esperado). |
| **Principios** | F4 (composition over inheritance) |

### D3. FoundationError.to_error() preserva el código en el mensaje

| Aspecto | Decisión |
|---------|----------|
| **Decisión** | `FoundationError.to_error()` usa `ErrorCode.UNKNOWN` para el campo `code` (porque los tipos son diferentes: `str` vs `ErrorCode`), pero **preserva el código de la excepción como prefijo en el mensaje**: `f"[{self.code}] {self.message}"`. |
| **Justificación** | El código de excepción ("DOMAIN_ERROR") tiene valor semántico — perderlo sería una degradación innecesaria. Al prefijarlo en el `message` se mantiene visible y es consistente con el formato `[CODE] message` que ya usa `Error.__str__()`. |
| **Alternativa** | Forzar que cada excepción tenga un ErrorCode — descartado porque crearía acoplamiento entre dos sistemas de error diferentes. |
| **Principios** | F3 (explicit over implicit) |

### D4. Integración aditiva (no rompe nada)

| Aspecto | Decisión |
|---------|----------|
| **Decisión** | Todo cambio es ADITIVO. No se modifica ninguna clase, método, o firma existente. Solo se AGREGAn `Error.from_exception()` y `FoundationError.to_error()`. |
| **Justificación** | Garantizar que los 221 tests existentes sigan pasando SIN modificaciones. Cero regresiones. |
| **Principios** | ADR-021 (Stability Policy) |

### D5. Los tres subtipos son clases simples sin comportamiento extra

| Aspecto | Decisión |
|---------|----------|
| **Decisión** | `DomainError`, `ApplicationError`, `InfrastructureError` solo cambian el `code` default. No agregan métodos ni atributos. |
| **Justificación** | YAGNI. El comportamiento específico de cada capa va en subclases de cada BC (e.g., `ResearchAlreadyReviewedError(DomainError)`). Estas tres son solo separación por capa. |
| **Principios** | F1 (zero dependencies), F6 (no business logic) |

---

## 8. Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Romper tests existentes de Result | Baja | Alto | Todos los cambios son aditivos. No se modifican firmas existentes. Los 221 tests deben pasar sin cambios. |
| Confundir Error (dataclass) con FoundationError (exception) | Media | Medio | Nomenclatura clara: "Error" es el dataclass de Result, "FoundationError" es la excepción base. Documentado en docstrings. |
| Crear acoplamiento entre FoundationError y Error | Baja | Medio | `from_exception()` usa `ErrorCode.UNKNOWN` con código preservado en el mensaje. El acoplamiento es mínimo y controlado. |
| Subclases de FoundationError sin `code` definido | Baja | Bajo | `code` tiene default por nivel. Si una subclase no lo define, usa el de su padre. |
| Mezcla de conceptos Result/Exception en los BCs | Media | Bajo | La documentación deja claro: Result para flujos esperados, Exception para lo excepcional. Ver sección 5.3 del foundation-design.md. |

---

## 9. Criterios de Aceptación

1. ✅ `FoundationError(Exception)` existe con `code`, `message`, `detail`, `to_dict()`, `to_error()`
2. ✅ `DomainError(FoundationError)` existe con `code = "DOMAIN_ERROR"` default
3. ✅ `ApplicationError(FoundationError)` existe con `code = "APPLICATION_ERROR"` default
4. ✅ `InfrastructureError(FoundationError)` existe con `code = "INFRASTRUCTURE_ERROR"` default
5. ✅ `Error.from_exception(FoundationError)` retorna un `Error` válido
6. ✅ `FoundationError.to_error()` retorna un `Error` válido
7. ✅ Todos los tipos se exportan desde `foundation.__init__`
8. ✅ 221 tests existentes pasan SIN modificaciones
9. ✅ Tests nuevos para toda la funcionalidad nueva
10. ✅ Zero dependencias externas (stdlib-only)
11. ✅ Foundation NO conoce el dominio — no hay referencias a conceptos de BCs

---

## 10. Estrategia de Testing

### 10.1 Tests nuevos: `tests/foundation/test_errors.py` (~25 tests)

| Grupo | Tests | Cubre |
|-------|-------|-------|
| **TestFoundationError** | 5 | Construcción, code default, message, detail, to_dict |
| **TestDomainError** | 3 | Construcción, code default, isinstance de FoundationError |
| **TestApplicationError** | 3 | Construcción, code default, isinstance |
| **TestInfrastructureError** | 3 | Construcción, code default, isinstance |
| **TestJerarquia** | 3 | isinstance checks cruzados, no confunde capas |
| **TestToError** | 4 | FoundationError.to_error(), DomainError.to_error(), mensajes preservados |
| **TestFromException** | 4 | Error.from_exception(), preserva message y detail |
| **TestNoRegresion** | 3 | Confirmar que Error, ErrorCode, Result NO se modificaron |

### 10.2 Tests existentes que deben seguir pasando

| Archivo | Tests |
|---------|-------|
| `tests/foundation/test_result.py` | 60 tests — SIN MODIFICACIONES |
| `tests/foundation/test_entity_id.py` | 65 tests |
| `tests/foundation/test_entity.py` | 23 tests |
| `tests/foundation/test_aggregate_root.py` | 24 tests |
| `tests/foundation/test_value_object.py` | 13 tests |
| `tests/foundation/test_events.py` | 25 tests |
| **Total** | **221 tests — deben pasar SIN cambios** |

---

## 11. Casos Borde (Edge Cases)

| Caso | Comportamiento esperado |
|------|------------------------|
| FoundationError con message vacío | `message` default `""`. `to_dict()` incluye `"message": ""` |
| FoundationError con detail vacío | `detail` default `""`. `to_dict()` incluye `"detail": ""` |
| DomainError() sin args | `code = "DOMAIN_ERROR"`, `message = ""`, `detail = ""` |
| isinstance(DomainError(), Exception) | `True` (hereda de Exception vía FoundationError) |
| isinstance(DomainError(), BaseException) | `True` |
| isinstance(InfrastructureError(), DomainError) | `False` (son siblings) |
| isinstance(ApplicationError(), FoundationError) | `True` (hereda) |
| Error.from_exception() con exception que tiene code custom | message incluye `"[CUSTOM_CODE] message"` — el código se preserva como prefijo |
| FoundationError con subclase anónima | `code` usa ClassVar del padre si la subclase no lo redefine |
| Exception + raise nativo | FoundationError se puede lanzar con `raise` normal, capturar con `except FoundationError` |
| FoundationError con causa | `raise FoundationError(...) from cause` funciona (Exception nativo) |

---

## 12. Compatibilidad con la Arquitectura Existente

### 12.1 ADR Compliance

| ADR | Compliance |
|-----|-----------|
| ADR-021 (Foundation Stability) | ✅ Cumple MULTI-BC (todos los BCs usan errores), NO BUSINESS RULES (no tiene lógica de negocio), ZERO DEPENDENCIES (stdlib-only), NO COUPLING (no acopla BCs), MECHANISM (es base técnica). |
| ADR-022 (ErrorCode Inheritance) | ✅ No toca ErrorCode. No intenta herencia entre enums. |
| ADR-020 (Tres Capas de Error) | ✅ Implementa exactamente lo descrito: FoundationError → DomainError / ApplicationError / InfrastructureError. |

### 12.2 Baseline v1.0

No rompe la baseline. Architecture Baseline v1.0 está FROZEN y no se modifica.

### 12.3 Foundation Principles

| Principio | Compliance |
|-----------|-----------|
| F1 — Zero External Dependencies | ✅ Solo usa `typing` (ClassVar) de stdlib |
| F2 — Immutability by Default | ✅ N/A (exceptions no son inmutables por diseño) |
| F3 — Explicit Over Implicit | ✅ Sin metaclasses, sin decoradores ocultos |
| F4 — Composition Over Inheritance | ✅ Jerarquía plana de 3 niveles máximo |
| F5 — Fail Fast at Construction | ✅ FoundationError valida en `__init__` |
| F6 — No Business Logic | ✅ Sin palabras del lenguaje ubicuo |

---

## 13. Diseño Detallado

### 13.1 `foundation/errors/base.py`

```python
"""
Jerarquía de excepciones base del Foundation Layer.

Arquitectura:
    FoundationError (Exception)
    ├── DomainError         — violación de regla de negocio
    ├── ApplicationError    — error de aplicación (comando inválido, no encontrado)
    └── InfrastructureError — error de infraestructura (DB caída, timeout)

Uso en BCs:
    class ResearchAlreadyReviewedError(DomainError):
        code = "RESEARCH_ALREADY_REVIEWED"
    
    class DatabaseConnectionError(InfrastructureError):
        code = "DB_CONNECTION_ERROR"
"""

from typing import ClassVar

from foundation.result.result import Error  # solo para type hints en to_error


class FoundationError(Exception):
    """Base de TODAS las excepciones del sistema."""
    
    code: ClassVar[str] = "FOUNDATION_ERROR"
    
    def __init__(self, message: str = "", detail: str = ""):
        self.message = message
        self.detail = detail
        super().__init__(self.detail)
    
    def to_dict(self) -> dict:
        return {
            "error": self.code,
            "message": self.message,
            "detail": self.detail,
        }
    
    def to_error(self) -> Error:
        """Convierte esta excepción en un Error dataclass para Result.
        
        Preserva el código de excepción como prefijo en el mensaje
        para mantener la trazabilidad semántica.
        """
        return Error(
            code=ErrorCode.UNKNOWN,
            message=f"[{self.code}] {self.message}".strip(),
            detail=self.detail,
        )


class DomainError(FoundationError):
    """Error de DOMINIO — violación de regla de negocio."""
    code: ClassVar[str] = "DOMAIN_ERROR"


class ApplicationError(FoundationError):
    """Error de APLICACIÓN — comando inválido, operación no permitida."""
    code: ClassVar[str] = "APPLICATION_ERROR"


class InfrastructureError(FoundationError):
    """Error de INFRAESTRUCTURA — DB caída, timeout, red."""
    code: ClassVar[str] = "INFRASTRUCTURE_ERROR"
```

### 13.2 Modificación en `result.py` (solo aditivo)

```python
# Agregar al final de la clase Error:
@classmethod
def from_exception(cls, exception: FoundationError) -> Error:
    """Crea un Error desde una excepción FoundationError.
    
    Preserva el código de la excepción como prefijo en el mensaje
    para no perder información semántica.
    
    Args:
        exception: La excepción a envolver (FoundationError o subclase).
    
    Returns:
        Error con code=UNKNOWN (por diferencia de tipos), 
        message con prefijo "[EXCEPTION_CODE] original message",
        detail de la excepción.
    """
    return cls(
        code=ErrorCode.UNKNOWN,
        message=f"[{exception.code}] {exception.message}".strip(),
        detail=exception.detail,
    )
```

### 13.3 Modificación en `foundation/__init__.py`

Se agregan imports y exports de FoundationError, DomainError, ApplicationError, InfrastructureError.

---

*Esta especificación sigue los lineamientos de ADR-021 (Foundation Stability Policy),
ADR-022 (ErrorCode Enum Inheritance), ADR-020 (Tres Capas de Error), y el diseño
arquitectónico definido en foundation-design.md.*
