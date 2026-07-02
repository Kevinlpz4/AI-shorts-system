# Sprint 2.6: Foundation Infrastructure Abstractions

> **Status**: DRAFT — Pendiente de aprobación
> **Depende de**: Sprint 2.3 (Result Pattern), Sprint 2.5 (Error System)
> **Dependencias futuras**: Sprint 2.7 (UUID Provider avanzado — opcional)

---

## 1. Objetivo del Sprint

Implementar los puertos de infraestructura del Foundation Layer — `ClockPort`, `UUIDProvider` — y sus implementaciones concretas (`SystemClock`, `FrozenClock`, `SystemUUIDProvider`, `SequentialUUIDProvider`), abstrayendo la obtención de tiempo y UUIDs para garantizar **pruebas determinísticas** y **desacoplamiento de infraestructura**.

Al finalizar este sprint, el Foundation Layer alcanza la versión **Foundation v1.0 STABLE**.

---

## 2. Responsabilidades

| Componente | Responsabilidad |
|------------|----------------|
| `ClockPort` | Puerto (Protocol) que abstrae la obtención del tiempo actual. |
| `SystemClock` | Implementación real — usa `datetime.now(timezone.utc)`. Para producción. |
| `FrozenClock` | Implementación congelada — siempre devuelve el mismo datetime. Para tests. |
| `UUIDProvider` | Puerto (Protocol) que abstrae la generación de UUIDs. |
| `SystemUUIDProvider` | Implementación real — usa `uuid4()`. Para producción. |
| `SequentialUUIDProvider` | Implementación secuencial — UUIDs determinísticos. Para tests. |

---

## 3. Alcance

### 3.1 Qué entra

1. **Puerto `ClockPort`** — Protocol con `now()` y `utc_today()`
2. **`SystemClock`** — implementación real de producción
3. **`FrozenClock`** — implementación congelada para tests
4. **Puerto `UUIDProvider`** — Protocol con `generate()`
5. **`SystemUUIDProvider`** — implementación real de producción
6. **`SequentialUUIDProvider`** — implementación secuencial para tests
7. **Tests completos** para todos los componentes
8. **Re-exportación desde `foundation/__init__.py`** (y desde `foundation/ports/` si existe)

### 3.2 Qué NO entra

- ❌ NO se modifica ninguna clase existente (Entity, EntityId, Result, Error, etc.)
- ❌ NO se modifica el AggregateRoot para usar Clock (eso es responsabilidad de cada BC)
- ❌ NO se agrega `utc_today()` a ningún domain object
- ❌ NO se implementa `types/__init__.py` (IDs específicos del sistema)
- ❌ NO se agrega `_compat.py` (solo si es necesario y se detecta en implementación)
- ❌ NO se modifica `FoundationEncoder` para soportar FoundationError (fuera de alcance)
- ❌ NO se agregan injecciones de dependencia automáticas (IoC container)
- ❌ NO se implementa `ClockPort` en AggregateRoot por defecto (cada BC decide)

---

## 4. Archivos del Sprint

### 4.1 Nuevos

| Archivo | Propósito |
|---------|-----------|
| `src/foundation/ports/__init__.py` | Re-exports del paquete ports |
| `src/foundation/ports/clock.py` | ClockPort (Protocol) + SystemClock + FrozenClock |
| `src/foundation/ports/uuid_provider.py` | UUIDProvider (Protocol) + SystemUUIDProvider + SequentialUUIDProvider |
| `tests/foundation/test_clock.py` | Tests de ClockPort, SystemClock, FrozenClock (~15 tests) |
| `tests/foundation/test_uuid_provider.py` | Tests de UUIDProvider, SystemUUIDProvider, SequentialUUIDProvider (~15 tests) |

### 4.2 Modificados

| Archivo | Cambio |
|---------|--------|
| `src/foundation/__init__.py` | Agregar imports y exports de ClockPort, SystemClock, FrozenClock, UUIDProvider, SystemUUIDProvider, SequentialUUIDProvider |

### 4.3 Eliminados

Ninguno.

---

## 5. Dependencias

### 5.1 Con sprints anteriores

| Sprint | Dependencia | Estado |
|--------|-------------|--------|
| Sprint 2.5 | `FoundationError(Exception)` — base para posibles errores de clock/UUID | ✅ |
| Sprint 2.3 | `ErrorCode` — para errores estándar si los puertos los necesitan | ✅ |
| ADR-021 | Foundation Stability Policy — los puertos cumplen los 5 criterios | ✅ |
| ADR-019 | ClockPort y UUIDProvider como Puertos — decisión ya tomada | ✅ |

### 5.2 Para sprints futuros

| Sprint | Dependencia |
|--------|-------------|
| Cualquier BC | `ClockPort` se inyectará en entities que necesiten tiempo |
| Cualquier BC | `UUIDProvider` se inyectará en entities/factories que generen IDs |
| Sprint 2.7+ | `types/__init__.py` para IDs específicos (SourceId, FeedId, etc.) |

---

## 6. API Pública

### 6.1 `foundation.ports.clock`

```python
from datetime import date, datetime
from typing import Protocol


class ClockPort(Protocol):
    """
    Puerto: provee el tiempo actual.
    
    Responsabilidades:
      - Devolver datetime actual en UTC (timezone-aware)
      - Devolver fechas consistentes dentro de una operación
    
    NO hace:
      - No formatea fechas
      - No convierte timezones
      - No sabe de dominio
    """
    
    def now(self) -> datetime:
        """Devuelve el datetime actual en UTC (timezone-aware)."""
        ...
    
    def utc_today(self) -> date:
        """Devuelve la fecha actual en UTC."""
        ...


class SystemClock:
    """Clock real — usa datetime.now(timezone.utc). Para producción."""
    
    def now(self) -> datetime:
        return datetime.now(timezone.utc)
    
    def utc_today(self) -> date:
        return self.now().date()


class FrozenClock:
    """Clock congelado — siempre devuelve la misma hora. Para tests."""
    
    def __init__(self, now: datetime | None = None):
        self._frozen = now if now is not None else datetime(2026, 1, 1, tzinfo=timezone.utc)
    
    def now(self) -> datetime:
        return self._frozen
    
    def utc_today(self) -> date:
        return self._frozen.date()
```

### 6.2 `foundation.ports.uuid_provider`

```python
from uuid import UUID, uuid4, uuid5

# Namespace fijo para UUIDs determinísticos de SequentialUUIDProvider
UUID_NAMESPACE = UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c4")


class UUIDProvider(Protocol):
    """
    Puerto: genera UUIDs.
    
    Responsabilidades:
      - Generar UUIDs únicos
      - (Opcional) Generar UUIDs determinísticos para tests
    
    NO hace:
      - No valida UUIDs (eso es de EntityId)
      - No formatea UUIDs
    """
    
    def generate(self) -> UUID:
        """Genera un nuevo UUID."""
        ...


class SystemUUIDProvider:
    """UUID real — usa uuid4(). Para producción."""
    
    def generate(self) -> UUID:
        return uuid4()


class SequentialUUIDProvider:
    """UUID secuencial — para tests determinísticos."""
    
    def __init__(self, start: int = 1):
        self._counter = start
    
    def generate(self) -> UUID:
        result = uuid5(UUID_NAMESPACE, str(self._counter))
        self._counter += 1
        return result
```

### 6.3 Desde `foundation/__init__.py`

```python
from foundation import ClockPort, SystemClock, FrozenClock
from foundation import UUIDProvider, SystemUUIDProvider, SequentialUUIDProvider
```

---

## 7. Decisiones de Diseño

### D1. Protocol vs ABC

| Aspecto | Decisión |
|---------|----------|
| **Decisión** | `ClockPort` y `UUIDProvider` son `Protocol` (no `ABC`). |
| **Justificación** | Protocol permite duck typing estructural. No requiere herencia explícita — cualquier objeto con `now()` y `utc_today()` es un `ClockPort`. Esto facilita mocks en tests y reduce acoplamiento. |
| **Alternativa** | `ABC` con `@abstractmethod` — descartado porque fuerza herencia explícita y crea acoplamiento de tipo. |
| **Principios** | F3 (explicit over implicit), F4 (composition over inheritance) |

### D2. FrozenClock default

| Aspecto | Decisión |
|---------|----------|
| **Decisión** | `FrozenClock` usa `datetime(2026, 1, 1, tzinfo=timezone.utc)` si no se provee `now`. |
| **Justificación** | Un default razonable que no requiere configuración extra para tests simples. Es una fecha fácil de reconocer como "congelada". |
| **Principios** | F3 (explicit over implicit) |

### D3. SequentialUUIDProvider vs MockUUIDProvider

| Aspecto | Decisión |
|---------|----------|
| **Decisión** | `SequentialUUIDProvider` usa `uuid5()` con namespace fijo + contador incremental. |
| **Justificación** | Los UUIDs generados son válidos (RFC 4122), determinísticos, y únicos dentro del test. A diferencia de un mock que devuelve siempre el mismo UUID, `SequentialUUIDProvider` permite múltiples llamadas sin colisiones. |
| **Alternativa** | `MockUUIDProvider` que devuelve siempre el mismo UUID — descartado porque dos entities no pueden tener el mismo ID. Guardar una lista de UUIDs predefinidos — descartado (demasiado verbose en tests). |
| **Principios** | F3 (explicit over implicit), F5 (fail fast) |

### D4. Sin inyección automática

| Aspecto | Decisión |
|---------|----------|
| **Decisión** | NO se implementa inyección automática de dependencias (no IoC container). Clock y UUID se inyectan manualmente donde se necesiten. |
| **Justificación** | YAGNI. El Foundation es stdlib-only y no debe tener un contenedor IoC. La inyección manual es explícita y suficiente. Si surge la necesidad, se agrega en el Composition Root de la aplicación (fuera de Foundation). |
| **Principios** | F1 (zero dependencies), F6 (no business logic) |

### D5. Foundation v1.0 STABLE

| Aspecto | Decisión |
|---------|----------|
| **Decisión** | Al completar este sprint, Foundation se declara **v1.0 STABLE**. A partir de entonces: la API pública no se modifica sin ADR, solo se agregan componentes que cumplan ADR-021, y todo BC depende de esta API estable. |
| **Justificación** | Con Identity, Building Blocks, Result, Events, Errors, Clock y UUID completos, Foundation cubre todas las necesidades técnicas transversales del sistema. No hay razón para seguir modificando la API base. |
| **Principios** | ADR-021 (Foundation Stability Policy) |

---

## 8. Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Romper tests existentes al modificar `__init__.py` | Baja | Alto | Todos los cambios son aditivos. No se modifican firmas existentes. Los 249 tests deben pasar sin cambios. |
| SequentialUUIDProvider genere UUIDs no únicos | Baja | Medio | `uuid5()` con namespace fijo + contador garantiza unicidad. El contador arranca en 1 y es independiente por instancia. |
| FrozenClock sin timezone | Baja | Alto | El default `FrozenClock` usa `tzinfo=timezone.utc` explícitamente. Se verifica en tests. |
| Dependencia circular en imports | Baja | Medio | `ports/` no importa de `errors/` ni de `events/` ni de `result/`. `ports/` solo usa stdlib. |

---

## 9. Criterios de Aceptación

1. ✅ `ClockPort` existe como Protocol con `now()` y `utc_today()`
2. ✅ `SystemClock` implementa `ClockPort` usando `datetime.now(timezone.utc)`
3. ✅ `FrozenClock` implementa `ClockPort` con datetime congelado (default o custom)
4. ✅ `UUIDProvider` existe como Protocol con `generate()`
5. ✅ `SystemUUIDProvider` implementa `UUIDProvider` usando `uuid4()`
6. ✅ `SequentialUUIDProvider` implementa `UUIDProvider` usando `uuid5()` secuencial
7. ✅ Todos los tipos se exportan desde `foundation.__init__`
8. ✅ 249 tests existentes pasan SIN modificaciones
9. ✅ Tests nuevos para toda la funcionalidad nueva (~30 tests)
10. ✅ Zero dependencias externas (stdlib-only)
11. ✅ Foundation NO conoce el dominio
12. ✅ Foundation v1.0 STABLE declarado en la documentación

---

## 10. Estrategia de Testing

### 10.1 Tests nuevos

| Archivo | Tests | Cubre |
|---------|-------|-------|
| `tests/foundation/test_clock.py` | ~15 | ClockPort structural check, SystemClock.now() es UTC, SystemClock.utc_today(), FrozenClock.now() fijo, FrozenClock.utc_today(), FrozenClock default, FrozenClock custom datetime, FrozenClock idempotente |
| `tests/foundation/test_uuid_provider.py` | ~15 | UUIDProvider structural check, SystemUUIDProvider.generate() retorna UUID, SystemUUIDProvider genera únicos, SequentialUUIDProvider.generate() retorna UUID, SequentialUUIDProvider secuencial, SequentialUUIDProvider.start custom, SequentialUUIDProvider no colisiona |

### 10.2 Tests existentes que deben seguir pasando

| Archivo | Tests |
|---------|-------|
| `tests/foundation/test_result.py` | 60 tests — SIN MODIFICACIONES |
| `tests/foundation/test_entity_id.py` | 65 tests |
| `tests/foundation/test_entity.py` | 23 tests |
| `tests/foundation/test_aggregate_root.py` | 24 tests |
| `tests/foundation/test_value_object.py` | 13 tests |
| `tests/foundation/test_events.py` | 25 tests |
| `tests/foundation/test_errors.py` | 28 tests |
| **Total** | **249 tests — deben pasar SIN cambios** |

---

## 11. Casos Borde (Edge Cases)

| Caso | Comportamiento esperado |
|------|------------------------|
| SystemClock.now() sin timezone | Siempre retorna timezone-aware (UTC) |
| SystemClock.now() llamado 2 veces | Pueden diferir (es tiempo real) |
| FrozenClock() sin args | Usa default datetime(2026, 1, 1, tzinfo=timezone.utc) |
| FrozenClock.now() llamado 2 veces | MISMO valor (es congelado) |
| FrozenClock con datetime no-UTC | Se preserva el datetime tal cual se provee |
| SequentialUUIDProvider start=0 | Primer UUID con counter 0 |
| SequentialUUIDProvider.generate() * N | Cada UUID es único y mayor al anterior (uuid5 es determinístico por counter) |
| SequentialUUIDProvider con start muy alto | Funciona igual, counter arranca en ese valor |
| SystemUUIDProvider.generate() | Nunca retorna None ni excepción |
| Protocol structural check | Cualquier objeto con `now()` y `utc_today()` cumple ClockPort — no necesita herencia explícita |

---

## 12. Compatibilidad con la Arquitectura Existente

### 12.1 ADR Compliance

| ADR | Compliance |
|-----|-----------|
| ADR-021 (Foundation Stability) | ✅ Cumple MULTI-BC (todos los BCs usan tiempo/UUIDs), NO BUSINESS RULES, ZERO DEPENDENCIES (stdlib-only), NO COUPLING, MECHANISM. |
| ADR-019 (ClockPort y UUIDProvider como Puertos) | ✅ Implementa exactamente lo descrito. |
| ADR-020 (Tres Capas de Error) | ✅ FoundationError está disponible pero los puertos no lanzan errores propios. |

### 12.2 Baseline v1.0

No rompe la baseline. Architecture Baseline v1.0 está FROZEN y no se modifica.

### 12.3 Foundation Principles

| Principio | Compliance |
|-----------|-----------|
| F1 — Zero External Dependencies | ✅ Solo `datetime`, `uuid`, `typing` de stdlib |
| F2 — Immutability by Default | ✅ Los puertos son stateless. Los providers mutan contador interno (deliberado). |
| F3 — Explicit Over Implicit | ✅ Protocols explícitos, sin metaclases |
| F4 — Composition Over Inheritance | ✅ Protocols, no herencia de clases abstractas |
| F5 — Fail Fast at Construction | ✅ FrozenClock sin args usa default válido |
| F6 — No Business Logic | ✅ Sin palabras del lenguaje ubicuo |

---

## 13. Diseño Detallado

### 13.1 `foundation/ports/clock.py`

```python
"""
Clock Port — Abstracción del tiempo para testabilidad.

Arquitectura:
    ClockPort (Protocol)
    ├── SystemClock     — producción: datetime.now(timezone.utc)
    └── FrozenClock     — tests: datetime congelado

Uso en BCs::
    class ResearchTopic:
        def __init__(self, ..., clock: ClockPort | None = None):
            self._clock = clock or SystemClock()
        
        def is_expired(self) -> bool:
            return self._expires_at < self._clock.now()
"""

from datetime import date, datetime, timezone
from typing import Protocol


class ClockPort(Protocol):
    """Puerto: provee el tiempo actual."""

    def now(self) -> datetime:
        """Devuelve el datetime actual en UTC (timezone-aware)."""
        ...

    def utc_today(self) -> date:
        """Devuelve la fecha actual en UTC."""
        ...


class SystemClock:
    """Clock real — datetime.now(timezone.utc). Producción."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    def utc_today(self) -> date:
        return self.now().date()


class FrozenClock:
    """Clock congelado — mismo datetime siempre. Tests."""

    _DEFAULT_FROZEN = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def __init__(self, now: datetime | None = None):
        self._frozen = now if now is not None else self._DEFAULT_FROZEN

    def now(self) -> datetime:
        return self._frozen

    def utc_today(self) -> date:
        return self._frozen.date()
```

### 13.2 `foundation/ports/uuid_provider.py`

```python
"""
UUID Provider — Abstracción de generación de UUIDs para testabilidad.

Arquitectura:
    UUIDProvider (Protocol)
    ├── SystemUUIDProvider         — producción: uuid4()
    └── SequentialUUIDProvider     — tests: uuid5() secuencial

Uso en BCs::
    class ResearchTopic:
        def __init__(self, ..., uuid_provider: UUIDProvider | None = None):
            self._uuid_provider = uuid_provider or SystemUUIDProvider()
        
        @classmethod
        def create(cls, title: str, ...) -> ResearchTopic:
            return cls(id=TopicId(self._uuid_provider.generate()), ...)
"""

from uuid import UUID, uuid4, uuid5

UUID_NAMESPACE = UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c4")


class UUIDProvider(Protocol):
    """Puerto: genera UUIDs."""

    def generate(self) -> UUID:
        """Genera un nuevo UUID."""
        ...


class SystemUUIDProvider:
    """UUID real — uuid4(). Producción."""

    def generate(self) -> UUID:
        return uuid4()


class SequentialUUIDProvider:
    """UUID secuencial — uuid5() determinístico. Tests."""

    def __init__(self, start: int = 1):
        self._counter = start

    def generate(self) -> UUID:
        result = uuid5(UUID_NAMESPACE, str(self._counter))
        self._counter += 1
        return result
```

### 13.3 Modificación en `foundation/__init__.py`

Se agregan imports y exports de:

```python
from foundation.ports.clock import ClockPort, FrozenClock, SystemClock
from foundation.ports.uuid_provider import (
    UUIDProvider,
    SequentialUUIDProvider,
    SystemUUIDProvider,
)
```

---

## 14. Foundation v1.0 — Declaración de Estabilidad

Al completar este sprint, el Foundation Layer se declara **Foundation v1.0 STABLE**.

### 14.1 Implica

- La **API pública** (`foundation/__init__.py`) NO puede modificarse sin ADR y breaking change controlado.
- Solo se agregan nuevos componentes que cumplan **TODOS** los 5 criterios de ADR-021.
- Todo BC existente y futuro depende de esta API estable.
- Las implementaciones internas pueden cambiar (refactor) siempre que la API pública permanezca igual.

### 14.2 No implica

- No implica que Foundation esté "terminado" — pueden agregarse componentes si cumplen ADR-021.
- No implica que no pueda haber bug fixes — los bugs se corrigen con pruebas y sin cambiar la API.
- No implica que los BCs deban comenzar — el orden lo define el roadmap del producto.

### 14.3 Check-list de estabilidad

- [ ] Identity System → EntityId, FoundationEncoder (Sprint 2.1)
- [ ] Domain Building Blocks → ValueObject, Entity, AggregateRoot (Sprint 2.2)
- [ ] Result Pattern → Result[T], Success, Failure, Error, ErrorCode (Sprint 2.3)
- [ ] Event System → DomainEvent, IntegrationEvent (Sprint 2.4)
- [ ] Error System → FoundationError, DomainError, ApplicationError, InfrastructureError (Sprint 2.5)
- [ ] Infrastructure Abstractions → ClockPort, SystemClock, FrozenClock, UUIDProvider, SystemUUIDProvider, SequentialUUIDProvider (Sprint 2.6)
- [x] Zero external dependencies (stdlib-only)
- [x] Sin lógica de negocio
- [x] Sin dependencias ocultas entre BCs
- [x] Test suite completa y pasando

---

*Esta especificación sigue los lineamientos de ADR-019 (ClockPort y UUIDProvider),
ADR-021 (Foundation Stability Policy), y el diseño arquitectónico definido en
foundation-design.md (Secciones 9 y 10).*
