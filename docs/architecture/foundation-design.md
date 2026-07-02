# 🏗️ Foundation Layer — Diseño Arquitectónico

> **Documento de diseño oficial del núcleo técnico del sistema**
>
> Todo Bounded Context (Ingestion, Research, Script, AI, etc.)
> se construye SOBRE este Foundation. No lo modifica, no lo extiende,
> solo lo usa.

---

## 1. Responsabilidades del Foundation Layer

### 1.1 Qué pertenece al Foundation

El Foundation es la **base técnica compartida**. Contiene mecanismos,
no semántica de negocio.

| Responsabilidad | ¿Por qué? |
|----------------|-----------|
| Base classes para DDD (Entity, AggregateRoot, ValueObject) | Todo BC necesita estos tipos. Definirlos una vez evita N implementaciones inconsistentes. |
| Sistema de Identidad (EntityId, typed IDs) | Cada BC necesita IDs. Sin un sistema común, terminamos con UUIDs crudos mezclados con strings. |
| Result Pattern | Sin un Result estándar, cada BC implementa su propio manejo de errores y la integración se vuelve inconsistente. |
| Jerarquía de errores (Domain, Application, Infrastructure) | Los errores CRUZAN capas. Sin una jerarquía común, el error mapping es artesanal en cada BC. |
| Domain Event base | Los eventos son el mecanismo de comunicación entre aggregates. Necesitan una base consistente. |
| Integration Event base | Los eventos entre BCs necesitan un contrato común (versionado, trazabilidad). |
| Clock abstraction | `datetime.now()` es una dependencia directa del tiempo real. Rompe testabilidad y control. |
| UUID Provider | `uuid4()` parece inocuo, pero imposibilita IDs determinísticos en tests. |
| Equality rules | Sin reglas explícitas, cada entidad implementa `__eq__` a su manera. |
| Immutability contracts | Sin un contrato, algunos VOs terminan siendo mutables por accidente. |

### 1.2 Qué NO pertenece al Foundation

| NO pertenece | ¿Por qué? |
|-------------|-----------|
| Lógica de negocio de cualquier BC | Esa va en `ingestion/`, `research/`, etc. |
| Puertos de dominio específicos (ResearchSourcePort) | Cada BC define sus propios puertos. |
| Configuración de la aplicación (.env, settings) | Esa va en `app/` o en el BC correspondiente. |
| Implementaciones concretas (PostgresRepo, RedisBus) | Son adapters de infraestructura de cada BC. |
| Wrappers de frameworks (FastAPI, aiohttp) | No es foundation, es infraestructura de presentación. |
| Casos de uso o application services | Son específicos de cada BC. |
| Domain services con lógica de negocio | Van en el dominio de cada BC. |
| ORM mappings, schemas de DB, migraciones | Van en la infraestructura de cada BC. |

### 1.3 Regla de oro

> Si un componente **tiene semántica de negocio**, no pertenece al Foundation.
>
> Si un componente **resuelve un problema técnico transversal** (identidad,
> errores, eventos, clock, resultado), **sí** pertenece al Foundation.

---

## 2. Principios Arquitectónicos

### F1. Zero External Dependencies

> Foundation depende SOLO de la librería estándar de Python.
> Nada de pydantic, attrs, o cualquier librería externa.
>
> **Justificación**: Foundation es la base del sistema. Si foundation
> depende de una librería, TODO el sistema depende de esa librería.
> Eso es acoplamiento en su peor forma.

### F2. Immutability by Default

> Todo Value Object y Evento es `@dataclass(frozen=True)`.
> Las entities son `@dataclass` puro (mutables, tienen identidad).
> La inmutabilidad se explicita: si es mutable, tiene identidad.

### F3. Explicit Over Implicit

> Sin herencia mágica. Sin metaclasses. Sin decoradores ocultos.
> Sin `__init_subclass__`. Sin `abc.ABC` forzado.
> El código foundation debe poder leerse de arriba a abajo y
> entenderse sin conocer el framework.

### F4. Composition Over Inheritance

> Las base classes son **mínimas** y contienen solo lo que es
> universal. Preferir composición (mixins, Protocols) antes que
> jerarquías profundas de herencia.

### F5. Fail Fast at Construction

> Las validaciones van en `__post_init__` (dataclass) o en el
> constructor. Un objeto inválido NO debe poder construirse.
> Esto previene estados inconsistentes en todo el sistema.

### F6. No Business Logic

> Foundation no contiene `if` relacionados con negocio.
> No conoce de "topic", "feed", "score", "aprobación".
> Si una decisión involucra una palabra del lenguaje ubicuo,
> no está en foundation.

---

## 3. Base Classes

### 3.1 ValueObject

```python
@dataclass(frozen=True)
class ValueObject:
    """
    Base para todos los Value Objects del sistema.
    
    Responsabilidades:
      - Inmutabilidad garantizada (frozen=True)
      - Igualdad estructural (automática por dataclass)
      - Validación en construcción (__post_init__)
    
    NO hace:
      - No tiene identidad
      - No tiene eventos
      - No tiene ciclo de vida
      - No se persiste solo (vive dentro de Entities)
    
    ¿Por qué frozen=True?
      - Un VO debe ser intercambiable por otro con mismos valores
      - Si un VO cambia, DEBE ser reemplazado, no mutado
      - frozen garantiza esto en tiempo de compilación
    
    ¿Por qué NO usar Protocol/ABC?
      - Un VO es un contrato de datos, no de comportamiento
      - @dataclass ya da __init__, __eq__, __hash__, __repr__ gratis
      - ABC agregaría overhead de metaclase sin beneficio
    """
    
    def __post_init__(self):
        """Hook para validación. Overridear en subclases."""
        pass
```

**Ejemplo de uso** (no implementar):

```python
@dataclass(frozen=True)
class SyncPolicy(ValueObject):
    mode: SyncMode
    interval_seconds: Optional[int] = None
    
    def __post_init__(self):
        if self.mode == SyncMode.POLLING and self.interval_seconds is None:
            raise InvalidSyncPolicyError(...)
```

### 3.2 Entity

```python
@dataclass
class Entity:
    """
    Base para todas las Entities del sistema.
    
    Responsabilidades:
      - Identidad (self.id)
      - Igualdad por identidad (__eq__, __hash__)
      - Mutabilidad permitida (el estado de una entidad cambia)
    
    NO hace:
      - No tiene eventos (ver AggregateRoot)
      - No tiene lógica de persistencia
      - No tiene validación automática (va en métodos de dominio)
    
    ¿Por qué mutable?
      - Una entidad TIENE ciclo de vida. Sus atributos cambian.
      - La mutabilidad es controlada: solo a través de métodos de dominio.
    
    ¿Por qué identidad explícita (EntityId)?
      - UUID crudo no tiene type safety
      - EntityId permite: validación, serialización, igualdad tipada
    """
    id: EntityId  # ← Tipo genérico, cada subclase concreta el suyo
    
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)
```

### 3.3 AggregateRoot

```python
@dataclass
class AggregateRoot(Entity):
    """
    Base para todos los Aggregate Roots.
    
    EXTIENDE Entity. Agrega:
      - Capacidad de emitir Domain Events
      - pull_events() para que el Application Service los publique
    
    NO hace:
      - No publica eventos automáticamente
      - No persiste eventos
      - No sabe de Event Bus
    
    ¿Por qué separado de Entity?
      - No toda Entity es Aggregate Root
      - Solo el AR necesita emitir eventos
      - Separar evita que entidades internas emitan eventos sin control
    
    ¿Por qué pull_events() y no publish directo?
      - SRP: el AR genera eventos, quien los maneja es otra capa
      - Testabilidad: los events se inspeccionan sin publicar
      - Consistencia: se publican DESPUÉS de persistir el AR
    """
    _events: list[DomainEvent] = field(default_factory=list, repr=False)
    
    def register_event(self, event: DomainEvent) -> None:
        """Acumula un evento para publicación posterior."""
        self._events.append(event)
    
    def pull_events(self) -> list[DomainEvent]:
        """
        Extrae y limpia los eventos acumulados.
        
        Quien llama (Application Service) es responsable de:
          1. Persistir el Aggregate
          2. Publicar los eventos
        """
        events = self._events
        self._events = []
        return events
```

### 3.4 DomainEvent

```python
@dataclass(frozen=True)
class DomainEvent:
    """
    Base para TODOS los Domain Events.
    
    Responsabilidades:
      - Identidad única (event_id)
      - Timestamp de ocurrencia (occurred_at)
      - Trazabilidad (event_name, event_version)
      - Inmutabilidad total
    
    NO hace:
      - No tiene lógica de negocio
      - No se persiste (opcionalmente sí, en event sourcing)
      - No se publica a sí mismo
    
    ¿Por qué frozen=True?
      - Un evento es un hecho consumado. No se puede modificar el pasado.
      - Inmutabilidad garantiza que los handlers ven datos consistentes.
    
    ¿Por qué event_id UUID?
      - Permite idempotencia en handlers
      - Permite trazabilidad (correlación entre eventos)
    
    ¿Por qué event_version?
      - Los eventos evolucionan. El versionado permite cambios controlados.
      - Ver ADR-015 del Epic 1.
    """
    event_id: UUID = field(default_factory=uuid4)
    event_name: str = ""
    event_version: int = 1
    occurred_at: datetime = field(default_factory=_utcnow)
    
    def __post_init__(self):
        """Auto-asigna event_name si no se proveyó."""
        if not self.event_name:
            # Usamos object.__setattr__ porque frozen=True
            object.__setattr__(self, "event_name", type(self).__name__)
```

**Importante**: El problema de herencia de dataclasses en Python es real. Para evitarlo, se usa una convención:

```python
# ❌ NO hacer: defaults mezclados en herencia
@dataclass(frozen=True)
class DomainEvent:
    event_id: UUID = field(default_factory=uuid4)

@dataclass(frozen=True)
class TopicDiscovered(DomainEvent):
    topic_id: UUID  # ← Esto falla si DomainEvent tiene defaults
    title: str

# ✅ HACER: DomainEvent sin defaults problemáticos
# DomainEvent define event_id, occurred_at, event_version en __init__
# Los valores default se asignan en __post_init__
```

**Solución**: `field(default_factory=...)` en la base y `__post_init__` para auto-asignación. Funciona porque `default_factory` no interfiere con la herencia de la misma manera que `default`.

### 3.5 IntegrationEvent

```python
@dataclass(frozen=True)
class IntegrationEvent:
    """
    Base para Integration Events (cruzan Bounded Contexts).
    
    DIFIERE de DomainEvent en:
      - Tiene event_version OBLIGATORIO (cambios incompatibles = breaking)
      - Tiene source_boundary (qué BC lo publicó)
      - Tiene correlation_id para trazabilidad cross-BC
      - NO contiene objetos de dominio (solo datos serializables)
    
    NO hace:
      - No contiene objetos de dominio (no ResearchTopic, no Feed)
      - No asume formato de serialización
      - No tiene lógica de enrutamiento
    """
    event_id: UUID = field(default_factory=uuid4)
    event_name: str = ""
    event_version: int = 1
    source_boundary: str = ""      # "ingestion", "research", etc.
    correlation_id: Optional[str] = None  # para trazabilidad cross-BC
    causation_id: Optional[UUID] = None    # qué Domain Event originó esto
    occurred_at: datetime = field(default_factory=_utcnow)
    
    def __post_init__(self):
        if not self.event_name:
            object.__setattr__(self, "event_name", type(self).__name__)
        if not self.event_version:
            raise ValueError("IntegrationEvent requiere event_version > 0")
```

---

## 4. Sistema de IDs

### 4.1 ¿Por qué no UUID crudo?

Problemas de usar `uuid.UUID` directamente:

```python
def get_topic(topic_id: UUID) -> ResearchTopic: ...
def get_feed(feed_id: UUID) -> Feed: ...

# ❌ Peligro: se pueden intercambiar! Python no lo detecta
topic = get_topic(feed_id)  # Compila, corre, da error raro
```

Con IDs tipados:

```python
class TopicId(EntityId): ...
class FeedId(EntityId): ...

def get_topic(topic_id: TopicId) -> ResearchTopic: ...
def get_feed(feed_id: FeedId) -> Feed: ...

# ✅ Error en tiempo de compilación (type checker)
topic = get_topic(feed_id)  # ❌ FeedId != TopicId
```

### 4.2 EntityId

```python
@dataclass(frozen=True)
class EntityId:
    """
    Value Object base para todos los IDs del sistema.
    
    Es un VO (no una Entity): no tiene identidad propia,
    igualdad por valor, inmutable.
    
    Responsabilidades:
      - Envolver un UUID con type safety
      - Garantizar que siempre es un UUID válido
      - Serialización a string y desde string
      - Igualdad y hash correctos
    
    ¿Por qué NO heredar de UUID?
      - UUID es una clase C-extendida de Python.
      - Heredar de tipos nativos de Python tiene edge cases.
      - Composición > herencia.
    
    ¿Por qué frozen=True?
      - Un ID no cambia. Nunca. Si cambia, es otra entidad.
    """
    value: UUID = field(default_factory=uuid4)
    
    def __str__(self) -> str:
        return str(self.value)
    
    def __eq__(self, other):
        if not isinstance(other, EntityId):
            return NotImplemented
        return self.value == other.value
    
    def __hash__(self):
        return hash(self.value)
    
    @classmethod
    def from_string(cls, raw: str) -> Self:
        """Crea un ID desde string. Lanza ValueError si inválido."""
        return cls(value=UUID(raw))
    
    @classmethod
    def generate(cls) -> Self:
        """Crea un ID con nuevo UUID."""
        return cls()
```

### 4.3 IDs específicos (por BC)

Cada BC define sus propios IDs por composición:

```python
# En foundation/types/__init__.py — SOLO este archivo

class SourceId(EntityId): ...
class FeedId(EntityId): ...
class FeedGroupId(EntityId): ...
class RawItemId(EntityId): ...
class CategoryId(EntityId): ...
class TopicId(EntityId): ...
class ScriptId(EntityId): ...
class BatchId(EntityId): ...
```

**¿Por qué clases vacías?** Porque el type safety viene del **tipo**, no del comportamiento. `SourceId` y `FeedId` no necesitan métodos diferentes — el sistema los trata como tipos distintos por nombre.

### 4.4 Serialización

```python
# EntityId se serializa como string UUID
# Para JSON:
import json

class EntityIdEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, EntityId):
            return str(obj)
        return super().default(obj)

# Para Pydantic/schemas (si se usa en API):
# Se agrega un método to_dict() o se usa el str() implícito
```

---

## 5. Result Pattern

### 5.1 ¿Por qué Result y no excepciones?

Las excepciones deben representar **situaciones excepcionales** (error de infraestructura, bug, violación de invariante irrecuperable).

Los **flujos alternativos esperados** (no encontrado, duplicado, validación) deben modelarse con Result.

```python
# ❌ Excepción como flujo normal
try:
    topic = await repo.find(id)
except TopicNotFoundError:
    return Response(status=404)

# ✅ Result como flujo normal
result = await use_case.execute(command)
if result.is_failure:
    return Response(status=result.error.status_code, ...)
```

### 5.2 Result[T]

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
    def success(cls, value: T) -> Result[T]:
        """Crea un resultado exitoso."""
        return Success(value=value)
    
    @classmethod
    def failure(cls, error: Error) -> Result[T]:
        """Crea un resultado fallido."""
        return Failure(error=error)
    
    @property
    def is_success(self) -> bool: ...
    @property
    def is_failure(self) -> bool: ...
    @property
    def value(self) -> T: ...
    @property
    def error(self) -> Error: ...


@dataclass(frozen=True)
class Success[T](Result[T]):
    value: T
    
    @property
    def is_success(self) -> bool:
        return True
    
    @property
    def is_failure(self) -> bool:
        return False


@dataclass(frozen=True)
class Failure[T](Result[T]):
    error: Error
    
    @property
    def is_success(self) -> bool:
        return False
    
    @property
    def is_failure(self) -> bool:
        return True
```

### 5.3 Cuándo usar Result vs Excepciones

| Escenario | Usar |
|-----------|------|
| No encontrado | ✅ Result.failure(NotFoundError) |
| Validación de negocio (duplicado, estado inválido) | ✅ Result.failure(ValidationError) |
| Violación de invariante (programación incorrecta) | ❌ Exception |
| Error de infraestructura (DB caída, timeout) | ❌ Exception |
| Error de programación (None donde se esperaba str) | ❌ Exception |
| Operación esperada que puede fallar (buscar, crear) | ✅ Result |
| Operación que NO debe fallar (sumar, concatenar) | ❌ Exception |

**Regla**: Si el error es **esperable** en operación normal → Result.
Si es **inesperado** (bug, infraestructura) → Exception.

### 5.4 Error

```python
@dataclass(frozen=True)
class Error:
    """
    Error del Result Pattern.
    
    No es una excepción. Es un objeto de datos que describe
    qué salió mal en una operación.
    
    Atributos:
      - code: Código machine-readable (ErrorCode — default UNKNOWN)
      - message: Mensaje legible para el desarrollador
      - detail: Información adicional opcional (default None)
    
    NO hace:
      - No tiene stack trace
      - No es una excepción (no hereda de Exception)
      - No tiene lógica de logging
    
    El código de excepción es de tipo ``ErrorCode`` (enum),
    NO es ``str``. Cada BC define su propio ``str, Enum``
    independiente. Ver ADR-022.
    """
    code: ErrorCode = ErrorCode.UNKNOWN
    message: str = ""
    detail: str | None = None

    @classmethod
    def from_exception(cls, exception: Exception) -> Error:
        """
        Crea un ``Error`` desde una excepción ``FoundationError``.
        
        Preserva el código de la excepción como prefijo en el mensaje
        para no perder información semántica::
        
            err = Error.from_exception(DomainError("Topic already reviewed"))
            str(err)  # "[UNKNOWN] [DOMAIN_ERROR] Topic already reviewed"
        
        Si la excepción NO es ``FoundationError``, se usa ``str(exception)``
        como mensaje.
        
        NOTA: El campo ``code`` del Error SIEMPRE es ``ErrorCode.UNKNOWN``.
        La diferencia de tipos (``FoundationError.code`` es ``ClassVar[str]``,
        ``Error.code`` es ``ErrorCode``) impide un mapeo directo. El código
        de excepción se preserva como prefijo en el mensaje.
        
        Este degradation es DELIBERADO — mantiene desacoplados ambos
        sistemas de códigos. Cualquier mapeo más específico es
        responsabilidad de los BCs o del Composition Root.
        """
        from foundation.errors.base import FoundationError as _FoundationError
        
        if isinstance(exception, _FoundationError):
            return cls(
                code=ErrorCode.UNKNOWN,
                message=f"[{exception.code}] {exception.message}".strip(),
                detail=exception.detail,
            )
        return cls(
            code=ErrorCode.UNKNOWN,
            message=str(exception),
        )
```

### 5.5 ErrorCode

```python
class ErrorCode(str, Enum):
    """
    Códigos de error estandarizados.
    
    Foundation provee ``UNKNOWN`` como valor default.
    Cada Bounded Context define su propio ``str, Enum`` independiente::
    
        class IngestionErrorCode(str, Enum):
            SOURCE_NOT_FOUND = "SOURCE_NOT_FOUND"
    
    NOTA: ``ErrorCode`` NO es extensible por herencia. Python 3.11+ prohíbe
    subclasear Enums que tienen miembros definidos ([PEP 663]).
    Ver ADR-022 para detalle y justificación.
    """
    UNKNOWN = "UNKNOWN"
```

---

## 6. Jerarquía de Errores

### 6.1 Principios

1. **Tres capas**: Domain, Application, Infrastructure.
2. **Todas heredan de FoundationError** (base técnica).
3. **DomainError es la más importante** — refleja el lenguaje ubicuo.
4. **Las excepciones son para lo EXCEPCIONAL**. Los errores esperados van en Result.

### 6.2 FoundationError (base)

```python
class FoundationError(Exception):
    """
    Base de TODAS las excepciones del sistema.
    
    No es un DomainError — es una base técnica.
    DomainError hereda de esta.
    
    Atributos:
      - code: ClassVar[str] — código machine-readable (por nivel)
      - message: str — mensaje público (opcional, default "")
      - detail: str — mensaje técnico para debugging (opcional, default "")
    
    NOTA: ``code`` es ``ClassVar[str]`` (no ``ErrorCode``). Son dominios
    diferentes: ``FoundationError.code`` es un string de categorización,
    ``Error.code`` es un ``ErrorCode`` enum para el Result Pattern.
    """
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
        """
        Convierte esta excepción en un ``Error`` dataclass para Result.
        
        Preserva el código de excepción como prefijo en el mensaje::
        
            error = FoundationError("fail").to_error()
            str(error)  # "[FOUNDATION_ERROR] fail"
        
        NOTA arquitectónica:
        ``Error.code`` SIEMPRE es ``ErrorCode.UNKNOWN``. La conversión
        deliberadamente degrada el código de excepción (``ClassVar[str]``)
        porque los sistemas de códigos son diferentes y deben permanecer
        desacoplados. Cualquier mapeo más específico (e.g., cierto
        ``DomainError`` a un ``ErrorCode`` concreto del BC) es
        responsabilidad del BC que captura la excepción o del
        Composition Root.
        """
        return Error(
            code=ErrorCode.UNKNOWN,
            message=f"[{self.code}] {self.message}".strip(),
            detail=self.detail,
        )
```

### 6.3 Domain Error

```python
class DomainError(FoundationError):
    """
    Error de DOMINIO. Representa una violación de regla de negocio.
    
    Características:
      - El mensaje usa lenguaje ubicuo
      - Tiene semántica de negocio
      - Los handlers pueden traducirlo a HTTP status codes
    
    Ejemplos:
      - ResearchAlreadyReviewedError
      - CannotRemoveLastFeedError
      - DuplicateTopicError
    """
    code: ClassVar[str] = "DOMAIN_ERROR"
```

### 6.4 Application Error

```python
class ApplicationError(FoundationError):
    """
    Error de APLICACIÓN. Comando inválido, operación no permitida.
    
    Características:
      - No es lógica de negocio (no viola reglas del dominio)
      - Es un error de uso del sistema
    
    Ejemplos:
      - CommandValidationError (payload inválido)
      - ResourceNotFoundError (en aplicación, no en dominio)
      - PermissionDeniedError
    """
    code: ClassVar[str] = "APPLICATION_ERROR"
```

### 6.5 Infrastructure Error

```python
class InfrastructureError(FoundationError):
    """
    Error de INFRAESTRUCTURA. DB caída, timeout, red.
    
    Características:
      - No refleja lógica de negocio
      - Generalmente irrecuperable en el momento
      - El sistema debe degradar gracefulmente
    
    Ejemplos:
      - DatabaseConnectionError
      - ExternalServiceTimeoutError
      - SerializationError
    """
    code: ClassVar[str] = "INFRASTRUCTURE_ERROR"
```

### 6.6 Jerarquía completa

```
FoundationError
├── DomainError
│   ├── ResearchAlreadyReviewedError
│   ├── InvalidSyncPolicyError
│   ├── CannotRemoveLastFeedError
│   └── ...
├── ApplicationError
│   ├── CommandValidationError
│   ├── ResourceNotFoundError
│   └── ...
└── InfrastructureError
    ├── DatabaseConnectionError
    ├── ExternalServiceError
    ├── SerializationError
    └── ...
```

---

## 7. Domain Events

### 7.1 Diseño

Ver sección 3.4 para la base class. Aquí las decisiones adicionales.

### 7.2 Identidad

Cada DomainEvent tiene `event_id: UUID`. Esto permite:
- **Idempotencia**: si un handler recibe el mismo event_id dos veces, lo ignora.
- **Trazabilidad**: se puede seguir la cadena de eventos.
- **Correlación**: `causation_id` vincula un evento con su causa.

### 7.3 Timestamp

`occurred_at: datetime` es **SIEMPRE UTC**. Siempre con timezone.

```python
# ✅ Correcto
occurred_at: datetime = field(default_factory=_utcnow)

# ❌ Incorrecto (naive datetime)
occurred_at: datetime = field(default_factory=datetime.now)

# ❌ Incorrecto (local time)
occurred_at: datetime = field(default_factory=datetime.now)
```

### 7.4 Metadata

Los eventos pueden incluir metadata adicional (opcional, para trazabilidad):

```python
@dataclass(frozen=True)
class DomainEvent:
    event_id: UUID = field(default_factory=uuid4)
    event_name: str = ""
    event_version: int = 1
    occurred_at: datetime = field(default_factory=_utcnow)
    metadata: dict = field(default_factory=dict)  # opcional
```

### 7.5 Correlación y Causalidad

```python
# Causation: qué evento causó este evento
# Correlation: cadena completa de eventos relacionados

@dataclass(frozen=True)
class DomainEvent:
    event_id: UUID = field(default_factory=uuid4)
    causation_id: Optional[UUID] = None  # evento que causó este
    correlation_id: Optional[str] = None  # cadena de trazabilidad
    occurred_at: datetime = field(default_factory=_utcnow)
```

---

## 8. Integration Events

### 8.1 Diferencias con Domain Events

| Característica | Domain Event | Integration Event |
|---------------|-------------|-------------------|
| **Alcance** | Mismo BC | Entre BCs |
| **Versionado** | Opcional (mismo BC) | Obligatorio (ADRs) |
| **Payload** | Puede contener objetos de dominio | Solo tipos serializables |
| **Source** | Aggregate Root | Application Service |
| **Bus** | In-process | Externo (pub/sub, cola) |
| **Idempotencia** | Deseable | REQUERIDA |
| **Evolución** | Flexible | Versionado estricto |
| **Trazabilidad** | correlation_id | correlation_id + source_boundary |

### 8.2 Reglas de diseño

1. **Todo Integration Event debe ser serializable a JSON** sin pérdida.
2. **Todo Integration Event tiene `event_version`** que se incrementa solo en cambios incompatibles.
3. **El payload solo contiene tipos planos**: str, int, float, bool, list, dict, UUID, datetime.
4. **No contiene objetos de dominio, no contiene EntityId** (son internos de cada BC). Usar `str(entity_id)` en su lugar.

---

## 9. Clock Provider

### 9.1 ¿Por qué abstraer datetime.now()?

**Razón #1: Testabilidad.**

```python
# ❌ Sin Clock: el test depende del tiempo real
def test_expired_topic(self):
    topic = create_topic(created_at=datetime.now(timezone.utc))
    # Este test falla si la entidad compara con datetime.now internamente
    # y hay mínimas diferencias de timing
    assert topic.is_expired  # ¿True? Depende de cuándo se ejecute

# ✅ Con Clock: el tiempo es controlable
def test_expired_topic(self):
    clock = MockClock(now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    topic = create_topic(created_at=datetime(2025, 12, 1, tzinfo=timezone.utc), clock=clock)
    assert topic.is_expired  # ✅ Determinístico
```

**Razón #2: Consistencia.**

```python
# ❌ Múltiples datetime.now() en un flujo pueden dar diferentes valores
created_at = datetime.now(timezone.utc)
# ... 3ms después ...
updated_at = datetime.now(timezone.utc)  # Diferente!

# ✅ Clock centralizado
clock = SystemClock()
created_at = clock.now()
# ... siempre mismo "now" si se inyecta el mismo clock
updated_at = clock.now()  # Mismo valor si es un clock congelado
```

### 9.2 ClockPort

```python
class ClockPort(Protocol):
    """
    Puerto: provee el tiempo actual.
    
    Responsabilidades:
      - Devolver datetime actual en UTC
      - Devolver fechas consistentes dentro de una operación
    
    No hace:
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
```

### 9.3 Implementaciones

```python
class SystemClock:
    """Clock real — usa datetime.now(timezone.utc). Para producción."""
    
    def now(self) -> datetime:
        return datetime.now(timezone.utc)
    
    def utc_today(self) -> date:
        return self.now().date()


class FrozenClock:
    """Clock congelado — siempre devuelve la misma hora. Para tests."""
    
    def __init__(self, now: Optional[datetime] = None):
        self._frozen = now or datetime(2026, 1, 1, tzinfo=timezone.utc)
    
    def now(self) -> datetime:
        return self._frozen
    
    def utc_today(self) -> date:
        return self._frozen.date()
```

### 9.4 Decisión

| Aspecto | Veredicto |
|---------|-----------|
| **¿Clock en Foundation?** | ✅ Sí. Como puerto (Protocol). |
| **¿Obligatorio en todas las entities?** | ⚠️ Opcional. Se inyecta solo donde se necesita. La entidad puede tener un default SystemClock. |
| **Implementación default** | `SystemClock` (usa datetime.now real). |
| **Para tests** | `FrozenClock` (determinístico). |

---

## 10. UUID Provider

### 10.1 ¿Por qué abstraer uuid4()?

Misma razón que Clock: **testabilidad**.

```python
# ❌ Sin UUID Provider
class ResearchTopic:
    id: UUID = field(default_factory=uuid4)

# En un test:
topic1 = create_topic()
topic2 = create_topic()
# No podemos predecir los IDs!

# ✅ Con UUID Provider
class ResearchTopic:
    id: UUID = field(default_factory=_uuid_provider.generate)

# En un test:
provider = SequentialUUIDProvider()
topic1 = create_topic(uuid_provider=provider)
topic2 = create_topic(uuid_provider=provider)
# Los IDs son predecibles!
```

### 10.2 UUIDProvider

```python
class UUIDProvider(Protocol):
    """
    Puerto: genera UUIDs.
    
    Responsabilidades:
      - Generar UUIDs únicos
      - (Opcional) Generar UUIDs determinísticos para tests
    
    No hace:
      - No validar UUIDs (eso es de EntityId)
      - No formatear UUIDs
    """
    
    def generate(self) -> UUID:
        """Genera un nuevo UUID."""
        ...
```

### 10.3 Implementaciones

```python
class SystemUUIDProvider:
    """UUID real — usa uuid4(). Para producción."""
    
    def generate(self) -> UUID:
        return uuid4()


class SequentialUUIDProvider:
    """UUID secuencial — para tests determinísticos."""
    
    def __init__(self, start: int = 1):
        self._counter = start
    
    def generate(self) -> UUID:
        # Usar un namespace fijo + secuencia para que los UUIDs
        # sean únicos dentro del test y predecibles
        result = uuid5(UUID_NAMESPACE, str(self._counter))
        self._counter += 1
        return result
```

### 10.4 Decisión

| Aspecto | Veredicto |
|---------|-----------|
| **¿UUIDProvider en Foundation?** | ✅ Sí. Como puerto. |
| **¿Obligatorio?** | ⚠️ Opcional. Se usa donde el test necesita IDs predecibles. |
| **¿Costo?** | Mínimo. Un Protocol de 1 método. |
| **Alternativa** | Usar `monkeypatch` en tests — descartado (muta estado global). |

---

## 11. Reglas de Igualdad

### 11.1 Entities

```python
class Entity:
    """
    Regla: dos entities son iguales si tienen el MISMO ID y son
    del MISMO TIPO.
    
    NO importa si los atributos difieren — la identidad es la
    identidad. Si el ID es el mismo, es la misma entidad en
    diferentes puntos de su ciclo de vida.
    """
    id: EntityId
    
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)
```

**¿Y si una Entity tiene ID nulo?** No existe. Toda Entity nace con un ID.

### 11.2 Value Objects

```python
@dataclass(frozen=True)
class ValueObject:
    """
    Regla: dos VOs son iguales si TODOS sus atributos son iguales.
    
    La igualdad estructural es AUTOMÁTICA por @dataclass.
    No se necesita implementar __eq__ a menos que haya attributes
    que deban excluirse (ej: metadata transitoria).
    """
    pass
```

### 11.3 Aggregate Roots

```python
class AggregateRoot(Entity):
    """
    Regla: misma que Entity (igualdad por identidad).
    
    Los _events NO participan en la igualdad (repr=False, y no
    se incluyen en __eq__ de dataclass por ser field(compare=False)).
    """
    pass
```

### 11.4 Domain Events

```python
@dataclass(frozen=True)
class DomainEvent:
    """
    Regla: dos eventos son iguales si TODOS sus atributos son iguales.
    
    Esto incluye event_id. Dos eventos con el mismo event_id son
    el MISMO evento (útil para idempotencia).
    
    Para comparación semántica (mismo tipo de evento, mismo
    topic_id, etc.), el handler debe comparar explícitamente.
    """
    pass
```

---

## 12. Inmutabilidad

### 12.1 Reglas

| Tipo | Decorador | ¿Por qué? |
|------|-----------|-----------|
| **ValueObject** | `@dataclass(frozen=True)` | Identidad por valor. Si cambia, es otro. |
| **Entity** | `@dataclass` | Tiene ciclo de vida. Cambia controladamente. |
| **AggregateRoot** | `@dataclass` | Es una Entity. Los eventos internos cambian. |
| **DomainEvent** | `@dataclass(frozen=True)` | Es un hecho consumado. Inmutable. |
| **IntegrationEvent** | `@dataclass(frozen=True)` | Misma razón. |
| **Result** | `@dataclass(frozen=True)` | Un resultado no cambia. |
| **Error** | `@dataclass(frozen=True)` | Idem. |
| **DTOs de aplicación** | `@dataclass(frozen=True)` | Solo transportan datos. |

### 12.2 Excepciones controladas

Si un VO necesita un campo que se computa perezosamente (lazy):

```python
@dataclass(frozen=True)
class MyVO(ValueObject):
    _cached_computed: Optional[float] = field(default=None, repr=False, compare=False)
    
    def __post_init__(self):
        """Frozen impide modificar. Usamos object.__setattr__ para init."""
        pass
    
    @property
    def computed(self) -> float:
        if self._cached_computed is None:
            # ⚠️ Excepción controlada y documentada
            value = self._compute_expensive()
            object.__setattr__(self, "_cached_computed", value)
        return self._cached_computed
```

**Regla**: la excepción se documenta con un comentario y solo se usa cuando el cómputo es realmente costoso. Para el 99% de los casos, precomputar en `__post_init__`.

---

## 13. Convenciones

### 13.1 Nombres

| Elemento | Convención | Ejemplo |
|----------|-----------|---------|
| Clases | PascalCase | `AggregateRoot`, `EntityId`, `Result` |
| Métodos | snake_case | `pull_events()`, `register_event()` |
| Funciones | snake_case | `_utcnow()` |
| Variables | snake_case | `event_id`, `occurred_at` |
| Constantes | UPPER_SNAKE | `UUID_NAMESPACE` |
| Módulos | snake_case | `value_objects.py`, `base_classes.py` |
| Paquetes | snake_case | `foundation/`, `domain/` |
| Privado (within module) | `_prefijo` | `_events`, `_utcnow` |
| Privado (within class) | `__prefijo` | solo para evitar colisiones en herencia |
| Type vars | T, U, V | `Result[T]` |
| Protocols | Sufijo `Port` o nada | `ClockPort`, `RepositoryPort` |

### 13.2 Módulos y Paquetes

```
foundation/
├── __init__.py            ← Exporta solo lo público de foundation
├── base/
│   ├── __init__.py        ← Entity, AggregateRoot, ValueObject
│   ├── entity.py
│   ├── aggregate_root.py
│   └── value_object.py
├── entity_id.py           ← EntityId (en raíz, no en ids/)
├── json_encoder.py        ← FoundationEncoder (JSON serialization)
├── result/
│   ├── __init__.py        ← Result, Success, Failure, Error
│   └── result.py          ← También contiene ErrorCode
├── errors/
│   ├── __init__.py        ← FoundationError, DomainError, etc.
│   └── base.py            ← Jerarquía de errores (sin codes.py)
├── events/
│   ├── __init__.py        ← DomainEvent, IntegrationEvent
│   ├── domain_event.py
│   ├── integration_event.py
│   └── _utcnow.py         ← helper compartido
├── ports/                 ← Sprint 2.6 (futuro)
│   ├── __init__.py
│   ├── clock.py           ← ClockPort
│   └── uuid_provider.py   ← UUIDProvider
├── types/                 ← IDs específicos del sistema (futuro)
│   └── __init__.py
└── _compat.py             ← Polyfill para typing.Self (si necesario)
```

> **Nota:** `ports/`, `types/` y `_compat.py` existen en el diseño pero
> se implementarán en sprints posteriores (Sprint 2.6 en adelante).

### 13.3 Imports

```python
# ❌ Import disperso (usa paths internos)
from foundation.base.entity import Entity
from foundation.entity_id import EntityId

# ✅ Import desde el paquete raíz (si __init__.py exporta)
from foundation import Entity, EntityId

# ❌ Import de módulos internos de foundation
from foundation.result.result import Result  # ❌ Evitar
# ✅ Import desde foundation
from foundation import Result  # ✅ API pública
```

**Regla de imports**: un BC importa de `foundation` como **unidad**. Nunca importa de sub-módulos internos que no estén en `__init__.py`. Si `foundation/__init__.py` no exporta algo, ese algo no es público y no debe usarse desde fuera.

### 13.4 Organización de __init__.py

```python
# foundation/__init__.py (implementado — Sprint 2.5)
"""Foundation Layer — Base técnica compartida del sistema."""

from foundation.base.aggregate_root import AggregateRoot
from foundation.base.entity import Entity
from foundation.base.value_object import ValueObject
from foundation.entity_id import EntityId
from foundation.errors import ApplicationError, DomainError, FoundationError, InfrastructureError
from foundation.events.domain_event import DomainEvent
from foundation.events.integration_event import IntegrationEvent
from foundation.json_encoder import FoundationEncoder
from foundation.result.result import Error, ErrorCode, Failure, Result, Success

__all__ = [
    "AggregateRoot",
    "ApplicationError",
    "DomainError",
    "DomainEvent",
    "Entity",
    "EntityId",
    "Error",
    "ErrorCode",
    "Failure",
    "FoundationEncoder",
    "FoundationError",
    "InfrastructureError",
    "IntegrationEvent",
    "Result",
    "Success",
    "ValueObject",
]
```

> **Nota:** Los puertos `ClockPort` y `UUIDProvider` se agregarán en Sprint 2.6.
```

---

## 14. Dependencias Externas

### 14.1 Política

```yaml
foundation:
  dependencies: "ZERO EXTERNAL"
  allowed_stdlib:
    - dataclasses
    - datetime
    - uuid
    - typing
    - enum
    - abc          # Solo si necesario (preferir Protocol)
    - json         # Solo para serialización base
    - functools    # Solo si necesario
  forbidden:
    - pydantic     # Foundation no valida schemas de API
    - attrs        # @dataclass ya hace el trabajo
    - numpy        # Sin sentido en foundation
    - any third-party
```

### 14.2 Justificación

Cada dependencia externa en foundation es una dependencia que TODO el sistema hereda.

Si `foundation` usa `pydantic`, entonces `ingestion/domain/`, `research/domain/`, etc. **todos** dependen de pydantic. El dominio ya no es puro.

La única excepción posible: `typing_extensions` para `Self` en Python < 3.11. Y eso se maneja en `_compat.py` con un try/except condicional.

---

## 15. Estructura de Carpetas Definitiva

```
foundation/
├── __init__.py                   ← API pública: exporta todo lo usable
│
├── base/
│   ├── __init__.py
│   ├── entity.py                 ← Entity base class
│   ├── aggregate_root.py         ← AggregateRoot (hereda Entity)
│   └── value_object.py           ← ValueObject base
│
├── entity_id.py                  ← EntityId con type safety (en raíz)
├── json_encoder.py               ← FoundationEncoder (JSON)
│
├── result/
│   ├── __init__.py
│   └── result.py                 ← Result[T], Success, Failure, Error, ErrorCode
│
├── errors/
│   ├── __init__.py
│   └── base.py                   ← FoundationError, DomainError, etc.
│
├── events/
│   ├── __init__.py
│   ├── domain_event.py           ← DomainEvent base
│   ├── integration_event.py      ← IntegrationEvent base
│   └── _utcnow.py                ← Helper UTC timestamp
│
├── ports/                        ← Sprint 2.6+
│   ├── __init__.py
│   ├── clock.py                  ← ClockPort Protocol
│   └── uuid_provider.py          ← UUIDProvider Protocol
│
├── types/                        ← IDs específicos (Sprint 2.6+)
│   └── __init__.py               ← SourceId, FeedId, TopicId, etc.
│
└── _compat.py                    ← Polyfills (si necesarios)
```

### ¿Por qué entity_id.py en raíz y no en ids/?

`EntityId` es un módulo único que define el mecanismo de IDs tipados. No hay suficientes archivos que justifiquen un sub-paquete `ids/`. Tenerlo en raíz simplifica los imports y refleja que es un componente fundamental al mismo nivel que `result/`, `errors/`, etc.

`types/` (futuro — Sprint 2.6+) contendrá las definiciones de IDs específicos del sistema (`SourceId`, `TopicId`, `FeedId`, etc.) y se implementará cuando haya BCs que los necesiten.

---

## 16. ADRs

### ADR-016: Foundation Layer como Base Técnica Compartida

| Campo | Valor |
|-------|-------|
| **Estado** | APPROVED |
| **Contexto** | Cada BC necesitaba base classes, IDs, errores, eventos. Sin un foundation común, cada BC implementaría los mismos patrones de forma inconsistente. |
| **Decisión** | Crear `foundation/` con: Entity, AggregateRoot, ValueObject, EntityId, Result, jerarquía de errores, DomainEvent, IntegrationEvent, ClockPort, UUIDProvider. Dependencia stdlib-only. |
| **Alternativas** | shared_kernel (descartado — sugiere datos compartidos, no base técnica). Cada BC con su propia base (descartado — duplicación). |
| **Principios** | F1 (zero dependencies), F2 (immutability by default), F3 (explicit over implicit), F6 (no business logic). |

### ADR-017: EntityId como Value Object con Type Safety

| Campo | Valor |
|-------|-------|
| **Estado** | APPROVED |
| **Contexto** | Los IDs crudos (UUID, str, int) permiten mezclar tipos accidentalmente. Una función que espera `FeedId` puede recibir `TopicId` sin error de compilación. |
| **Decisión** | EntityId es un Value Object frozen que encapsula UUID. Cada tipo de ID es una subclase (SourceId(EntityId), FeedId(EntityId), etc.). La igualdad y hash se delegan al UUID interno. |
| **Alternativas** | UUID crudo (descartado — sin type safety). Type alias (descartado — Python no enforcea type aliases en runtime). NewType (descartado — solo es útil para type checkers, no para runtime). |
| **Principios** | F3 (explicit over implicit), F2 (immutability by default). |

### ADR-018: Result Pattern para Flujos Esperados

| Campo | Valor |
|-------|-------|
| **Estado** | APPROVED |
| **Contexto** | Las excepciones se usaban para flujos normales (no encontrado, duplicado). Esto complicaba el manejo de errores y mezclaba casos esperados con excepcionales. |
| **Decisión** | Result[T] para operaciones que pueden fallar de forma esperada. Excepciones solo para errores de programación o infraestructura. Error como objeto de datos (no excepción). |
| **Alternativas** | Solo excepciones (descartado — difícil de rastrear flujos alternativos). Maybe/Option pattern (descartado — no porta información de error). |
| **Principios** | F3 (explicit over implicit), F5 (fail fast at construction). |

### ADR-019: ClockPort y UUIDProvider como Puertos

| Campo | Valor |
|-------|-------|
| **Estado** | APPROVED |
| **Contexto** | datetime.now() y uuid4() son dependencias directas del tiempo real y el azar. Rompen testabilidad y determinismo. |
| **Decisión** | ClockPort y UUIDProvider como Protocols en foundation/ports/. Implementaciones default (SystemClock, SystemUUIDProvider) para producción. FrozenClock y SequentialUUIDProvider para tests. |
| **Alternativas** | No abstraer (descartado — tests no determinísticos). Monkeypatch en tests (descartado — muta estado global, frágil). |
| **Principios** | P2 (Port-Driven Boundaries), F1 (zero external dependencies). |

### ADR-020: Tres Capas de Error (Domain, Application, Infrastructure)

| Campo | Valor |
|-------|-------|
| **Estado** | APPROVED |
| **Contexto** | Sin una jerarquía clara, los errores se mezclaban. Un error de DB se trataba igual que una violación de regla de negocio. |
| **Decisión** | FoundationError → DomainError / ApplicationError / InfrastructureError. DomainError contiene semántica de negocio. InfrastructureError indica fallo técnico. |
| **Alternativas** | Jerarquía plana (descartado — no diferencia responsabilidades). Single base class (descartado — pierde semántica de capa). |
| **Principios** | P1 (Domain Isolation), P6 (Explicit Integration Boundaries). |

### ADR-022: ErrorCode Enum Inheritance Policy

| Campo | Valor |
|-------|-------|
| **Estado** | APPROVED |
| **Contexto** | Python 3.11+ prohíbe subclasear Enums con miembros. No se puede heredar de `ErrorCode` porque tiene `UNKNOWN`. |
| **Decisión** | Foundation define solo `ErrorCode` con su miembro `UNKNOWN`. Cada BC define su propio `str, Enum` independiente. La relación es por convención, no por herencia. |
| **Alternativas** | Sacar UNKNOWN del enum (complejidad innecesaria, YAGNI). Usar API privada `enum._simple_enum` (inestable). |
| **Principios** | F3 (explicit over implicit), ADR-021 (Foundation Stability). |

---

## Resumen de Componentes del Foundation

| Componente | ¿Qué es? | Inmutable | Stdlib-only | Sprint |
|-----------|---------|-----------|-------------|-------|
| Entity | Base class para entities | ❌ | ✅ | 2.2 ✅ |
| AggregateRoot | Entity con eventos | ❌ | ✅ | 2.2 ✅ |
| ValueObject | Base class para VOs | ✅ frozen | ✅ | 2.2 ✅ |
| EntityId | ID tipado con UUID | ✅ frozen | ✅ | 2.1 ✅ |
| FoundationEncoder | JSONEncoder para tipos Foundation | ✅ | ✅ | 2.1 ✅ |
| Result[T] | Result pattern genérico | ✅ frozen | ✅ | 2.3 ✅ |
| Error | Error de datos (no excepción) | ✅ frozen | ✅ | 2.3 ✅ |
| FoundationError | Base exception del sistema | ❌ | ✅ | 2.5 ✅ |
| DomainError | Excepción de dominio | ❌ | ✅ | 2.5 ✅ |
| ApplicationError | Excepción de aplicación | ❌ | ✅ | 2.5 ✅ |
| InfrastructureError | Excepción de infraestructura | ❌ | ✅ | 2.5 ✅ |
| ErrorCode | Enum de códigos (solo UNKNOWN) | ✅ | ✅ | 2.3 ✅ |
| DomainEvent | Evento intra-BC | ✅ frozen | ✅ | 2.4 ✅ |
| IntegrationEvent | Evento entre BCs | ✅ frozen | ✅ | 2.4 ✅ |
| ClockPort | Protocol de tiempo | N/A | ✅ | 2.6 ⏳ |
| UUIDProvider | Protocol de UUIDs | N/A | ✅ | 2.6 ⏳ |
| SystemClock | Clock real (producción) | N/A | ✅ | 2.6 ⏳ |
| FrozenClock | Clock congelado (tests) | N/A | ✅ | 2.6 ⏳ |
| SystemUUIDProvider | UUID real (producción) | N/A | ✅ | 2.6 ⏳ |
| SequentialUUIDProvider | UUID secuencial (tests) | N/A | ✅ | 2.6 ⏳ |

**Todo esto sin una sola dependencia externa.** Foundation es Python puro.

---

## Foundation Stability Policy

[ADR-021](adr/adr-021-foundation-stability-policy.md) define qué se puede agregar
al Foundation Layer y bajo qué condiciones.

**Los 5 criterios obligatorios** (resumen):

1. **MULTI-BC**: Usado por al menos 2 Bounded Contexts
2. **NO BUSINESS RULES**: Sin reglas de negocio de ningún BC
3. **ZERO DEPENDENCIES**: Sin dependencias externas
4. **NO COUPLING**: No incrementa acoplamiento entre BCs
5. **MECHANISM, NOT POLICY**: Resuelve un problema técnico transversal

> Si una funcionalidad solo la utiliza un BC, NO pertenece a Foundation.

---

## Repository Structure

La estructura definitiva del repositorio está definida en
[repository-structure.md](repository-structure.md).

```
src/
├── foundation/         ← Base técnica (stdlib only)
├── ai/                 ← AI capabilities compartidas
├── ingestion/          ← Ingestion BC
├── research/           ← Research BC
├── script_generation/  ← Script BC (futuro)
├── shared/             ← Dominio compartido entre BCs
└── presentation/       ← Entry points (CLI, API, config)
```

### Regla de oro

```
foundation/  ← nada (stdlib only)
     ↑
todos los BCs importan de foundation
ningún BC importa de otro BC
shared/ y ai/ pueden ser importados por varios BCs
presentation/ importa de todos (Composition Root)
```

---

## Próximo paso

Con la Baseline Architecture v1.0 del Epic 1 y el diseño del Foundation Layer completos:

### Documentos finalizados

| Documento | Estado |
|-----------|--------|
| `baseline-v1.md` (Epic 1) | ✅ FROZEN |
| `foundation-design.md` (Epic 2) | ✅ COMPLETO (actualizado Sprint 2.5) |
| `adr/adr-021.md` (Foundation Stability Policy) | ✅ APROBADO |
| `adr/adr-022.md` (ErrorCode Enum Inheritance) | ✅ APROBADO |
| `repository-structure.md` | ✅ APROBADO |

### ADRs totales: 22

| Grupo | ADRs | Estado |
|-------|------|--------|
| Epic 1 — Arquitectura (ADR-001 al 015) | 15 | Aprobados y FROZEN |
| Foundation (ADR-016 al 022) | 7 | Aprobados |

### Estado de implementación

```
Sprint 2.1 ─→ 2.2 ─→ 2.3 ─→ 2.4 ─→ 2.5 ─→ 2.6 ─→ 2.7 ─→ ...
 Identity    BLocks  Result  Events  Errors  Clock    UUID      ──→ Foundation v1.0 STABLE
                                                                       (al completar Sprint 2.6)
```

### Foundation v1.0 — Estabilidad

Al completar el Sprint 2.6 (Infrastructure Abstractions), el Foundation Layer
alcanzará la versión **Foundation v1.0 STABLE**, momento a partir del cual:

- La API pública NO podrá modificarse sin ADR y breaking change controlado.
- Solo se agregarán componentes que cumplan los 5 criterios de ADR-021.
- Todo BC existente dependerá de esta API estable.

El plan posterior es:

```
1. Foundation v1.0 ──→  2. Ingestion Domain Core  ──→  3. Ingestion Infra  ──→  4. Wiring

  (base técnica)         (entities, VOs, ports)      (adapters, repos)      (composition root)
```
