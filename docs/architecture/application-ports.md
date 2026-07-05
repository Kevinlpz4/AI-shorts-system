# Application Ports Design — Ingestion Bounded Context

> **Puertos de salida de la capa de aplicación**
>
> Versión: 1.0 | Estado: **DESIGNED**
> Fecha: 2026-07-03

---

## 1. Principios de Diseño

1. **Output Ports**: La aplicación define lo que necesita. La infraestructura lo implementa.
2. **Protocols (no ABCs)**: Seguimos el patrón de `domain/ports/repositories.py` — Protocols estructurales.
3. **Sin mención de tecnología**: No hay `asyncio`, no hay `kafka`, no hay `redis`, no hay `SQLAlchemy`.
4. **Foundation ports se reutilizan**: `ClockPort` y `UUIDProvider` ya están definidos en Foundation. No se redefinen.

---

## 2. Input Ports (lo que la aplicación EXPONE)

La aplicación expone **servicios**, no buses. No implementamos CommandBus ni QueryBus — los use cases se llaman directamente.

### Decisión: Llamada Directa vs CommandBus

| Opción | Tradeoff | Decisión |
|--------|----------|----------|
| **✅ Llamada directa a servicios** | Simple, tipado, sin middleware. La presentación importa `SourceService` y llama `execute_register_source(cmd)`. | **SELECCIONADA** |
| ❌ CommandBus/QueryBus | Añade indirección, complejidad, y registro de handlers. Útil cuando hay middlewares cross-cutting (logging, validación, transacciones) pero podemos implementar eso con decoradores simples. | Descartada por YAGNI |

**Razones**: Con ~14 use cases y un solo BC, un bus añade complejidad sin beneficio. Si en el futuro agregamos BCs adicionales y necesitamos integración cross-BC via mensajes, reevaluamos. Por ahora, **inyección directa de servicios**.

---

## 3. Output Ports (lo que la aplicación NECESITA)

### 3.1 EventPublisher Protocol

```python
"""Puerto de publicación de eventos de dominio.

La aplicación registra eventos y los publica después del commit
de la transacción. El EventPublisher abstrae el mecanismo de
publicación (broker de mensajes, bus en memoria, cola, etc.).
"""
from __future__ import annotations

from typing import Protocol

from foundation.events.domain_event import DomainEvent


class EventPublisher(Protocol):
    """Publica Domain Events en el bus de eventos.

    Responsabilidad:
        Tomar uno o más DomainEvents y entregarlos a los handlers
        registrados. La entrega puede ser síncrona o asíncrona
        según la implementación.

    NO hace:
        - No sabe de aggregates ni de pull_events()
        - No persiste eventos (eso es responsabilidad del event store)
        - No maneja transacciones (eso es UnitOfWork)
    """

    def publish(self, event: DomainEvent) -> None:
        """Publica un único Domain Event.

        Args:
            event: El DomainEvent a publicar (inmutable).

        Garantiza:
            - El evento se entrega a todos los handlers registrados.
            - Si la entrega falla, la excepción se propaga.
        """
        ...

    def publish_many(self, events: list[DomainEvent]) -> None:
        """Publica múltiples Domain Events.

        Args:
            events: Lista de DomainEvents a publicar.

        Semántica:
            - Los eventos se publican en orden.
            - Si uno falla, los siguientes no se publican.
            - El caller debe decidir si reintenta o aborta.
        """
        ...
```

### 3.2 UnitOfWork Protocol

```python
"""Puerto de unidad de trabajo (transacciones).

Maneja los límites de transacción para operaciones que involucran
múltiples repositorios. Sigue el patrón Unit of Work:

1. begin() → inicia transacción (opcional, implícito en algunos ORMs)
2. commit() → persiste todos los cambios, cierra transacción
3. rollback() → descarta todos los cambios desde el último commit
"""
from __future__ import annotations

from typing import Protocol


class UnitOfWork(Protocol):
    """Frontera transaccional para operaciones de aplicación.

    Responsabilidad:
        Coordinar la persistencia de múltiples aggregates en una
        sola transacción atómica. Si cualquier operación falla,
        todos los cambios se descartan.

    NO hace:
        - No publica eventos (eso es EventPublisher)
        - No sabe qué repositorios se usan
        - No maneja concurrencia (optimistic locking es del repo)

    Flujo típico:
        1. Application Service crea UnitOfWork
        2. Repositorios registran cambios en el UoW
        3. Service ejecuta operaciones de dominio
        4. Service llama commit() → persiste todo o nada
        5. Si error → rollback() automático
    """

    def __enter__(self) -> UnitOfWork:
        """Inicia el contexto transaccional.

        Al entrar, prepara el UoW para registrar cambios.
        La implementación puede iniciar una transacción de BD
        en este punto o diferirlo al commit().
        """
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Maneja la salida del contexto.

        Si exc_type es None → commit() implícito.
        Si exc_type no es None → rollback() implícito.
        """
        ...

    def commit(self) -> None:
        """Persiste todos los cambios pendientes.

        Garantiza:
            - Todos los cambios registrados se persisten atómicamente.
            - Si hay error, se hace rollback automático.
            - Después del commit, no hay cambios pendientes.

        Raises:
            CommitError: Si la persistencia falla (infraestructura).
        """
        ...

    def rollback(self) -> None:
        """Descarta todos los cambios pendientes.

        Garantiza:
            - No hay cambios pendientes después del rollback.
            - Es seguro llamar rollback() múltiples veces.
        """
        ...
```

### 3.3 Ports de Foundation (reutilizados)

```python
# ClockPort — provee datetime actual (UTC)
from foundation.ports.clock import ClockPort

# UUIDProvider — genera UUIDs
from foundation.ports.uuid_provider import UUIDProvider
```

**No se redefinen.** Se inyectan directamente desde Foundation.

---

## 4. Repository Ports (desde domain/ports/)

Los 5 repositorios ya están definidos en `domain/ports/repositories.py`:

| Puerto | Define |
|--------|--------|
| `NewsSourceRepository` | save(), find_by_id(), find_by_name(), find_all(), find_active(), exists_by_name() |
| `FeedRepository` | save(), find_by_id(), find_by_source(), find_by_url(), find_active_by_source(), exists_by_source_and_url(), count_active_by_source(), **count_active_by_sources()** |
| `RawArticleRepository` | save(), save_batch(), find_by_id(), find_by_feed(), find_by_hash(), exists_by_url(), exists_by_hash(), count_by_feed(), **count_by_feeds()** |
| `CategoryRepository` | save(), find_by_id(), find_by_slug(), find_all(), find_active(), find_by_parent(), exists_by_slug() |
| `TopicRepository` | save(), find_by_id(), find_by_name(), find_all(), find_active(), exists_by_name() |

La aplicación los consume directamente. No se redefinen.

> **Nota — Batch methods**: `FeedRepository.count_active_by_sources(source_ids: list[SourceId]) -> dict[SourceId, int]` y `RawArticleRepository.count_by_feeds(feed_ids: list[FeedId]) -> dict[FeedId, int]` son métodos agregados para resolver el anti-patrón N+1 al poblar `SourceSummaryDTO.feed_count` y `FeedSummaryDTO.article_count`. Estos métodos son extensiones de query (no mutan el modelo de dominio) y se agregan como excepción controlada al Domain Freeze — el modelo de dominio (entidades, VOs, eventos, invariantes) permanece intacto.

---

## 5. Mapa Completo de Puertos

```
┌─────────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                                │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  INPUT PORTS (expuestos a presentación)                       │   │
│  │                                                               │   │
│  │  SourceService:                                                │   │
│  │    execute_register_source(RegisterSourceCommand) → Result    │   │
│  │    execute_update_source(UpdateSourceCommand) → Result        │   │
│  │    execute_enable_source(EnableSourceCommand) → Result        │   │
│  │    execute_disable_source(DisableSourceCommand) → Result      │   │
│  │    execute_find_source(FindSourceQuery) → Result              │   │
│  │    execute_list_active_sources(ListActiveSourcesQuery)→Result │   │
│  │                                                               │   │
│  │  FeedService:                                                  │   │
│  │    execute_register_feed(RegisterFeedCommand) → Result        │   │
│  │    execute_update_feed(UpdateFeedCommand) → Result            │   │
│  │    execute_pause_feed(PauseFeedCommand) → Result              │   │
│  │    execute_activate_feed(ActivateFeedCommand) → Result        │   │
│  │    execute_record_collection(RecordCollectionCommand)→Result  │   │
│  │    execute_record_failure(RecordFailureCommand) → Result      │   │
│  │    execute_find_feed(FindFeedQuery) → Result                  │   │
│  │    execute_list_feeds(ListFeedsQuery) → Result                │   │
│  │                                                               │   │
│  │  ArticleService:                                               │   │
│  │    execute_create_article(CreateRawArticleCommand) → Result   │   │
│  │    execute_find_article(FindArticleQuery) → Result            │   │
│  │    execute_list_articles(ListArticlesQuery) → Result          │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  OUTPUT PORTS (dependencias inyectadas)                       │   │
│  │                                                               │   │
│  │  ┌─────────────────┐  ┌──────────────────┐  ┌────────────┐   │   │
│  │  │ NewsSourceRepo   │  │ FeedRepository   │  │ RawArticle │   │   │
│  │  │ (domain/ports)   │  │ (domain/ports)   │  │ Repository │   │   │
│  │  └─────────────────┘  └──────────────────┘  └────────────┘   │   │
│  │  ┌─────────────────┐  ┌──────────────────┐                    │   │
│  │  │ CategoryRepo     │  │ TopicRepository  │                    │   │
│  │  │ (domain/ports)   │  │ (domain/ports)   │                    │   │
│  │  └─────────────────┘  └──────────────────┘                    │   │
│  │                                                               │   │
│  │  ┌─────────────────┐  ┌──────────────────┐  ┌────────────┐   │   │
│  │  │ EventPublisher   │  │ UnitOfWork       │  │ ClockPort  │   │   │
│  │  │ (application)    │  │ (application)    │  │(Foundation) │   │   │
│  │  └─────────────────┘  └──────────────────┘  └────────────┘   │   │
│  │  ┌─────────────────┐                                          │   │
│  │  │ UUIDProvider     │                                          │   │
│  │  │ (Foundation)     │                                          │   │
│  │  └─────────────────┘                                          │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Decisiones de Diseño

### 6.1 ¿Por qué UnitOfWork como Protocol separado?

El patrón Unit of Work desacopla la lógica transaccional de los repositorios:
- Los repositorios individuales pueden operar sin transacción (lecturas)
- El Application Service controla explícitamente cuándo se hace commit
- Las implementaciones concretas pueden usar transacciones SQL, MongoDB sessions, o cualquier mecanismo

### 6.2 ¿Por qué EventPublisher no incluye store?

EventPublisher solo **publica**. Si necesitamos event sourcing o event store en el futuro, se agrega otro port. SRP: una responsabilidad por port.

### 6.3 ¿Por qué no un IntegrationEventPublisher?

Los Integration Events (cross-BC) se publican **después** de los Domain Events, como un paso adicional en el Application Service. Por YAGNI, no se define un port separado aún. Cuando el primer Integration Event sea necesario, se agrega `IntegrationEventPublisher` en este mismo archivo.
