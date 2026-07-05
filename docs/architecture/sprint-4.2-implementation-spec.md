# Sprint 4.2 Implementation Specification — Application Layer

> **Plan de implementación dividido en sub-sprints incrementales**
>
> Versión: 1.0 | Estado: **SPECIFIED**
> Fecha: 2026-07-03
> Basado en: ARB Report Sprint 4.1 v2.0 (APPROVED WITH SUGGESTIONS), C-01/C-02/C-03 resolved

---

## 0. Summary

| Sub-sprint | Enfoque | Archivos | Tests | Depende de |
|-----------|---------|----------|-------|------------|
| **4.2A** | Structure & Foundation Types | ~5 | Unit (error mapper, DTO constructors) | Foundation |
| **4.2B** | Commands, Queries, DTOs & Mappers | ~30 | Unit (command construction, DTO conversion) | 4.2A |
| **4.2C** | Ports & In-Memory Infrastructure | ~8 | Unit (in-memory repos, UoW) | 4.2B + domain/ports/ |
| **4.2D** | Services & Integration Tests | ~5 + tests | Integration (21 use cases, AL rules, events) | 4.2C |

**Regla**: Cada sub-sprint termina con **tests verdes**. No se avanza al siguiente sin tests pasando.

---

## 1. Sprint 4.2A — Structure & Foundation Types

### Objetivo
Crear la estructura de directorios y los tipos base que el resto de la capa de aplicación necesita. Sin lógica de negocio.

### Archivos a crear

```
src/ingestion/application/
├── __init__.py
├── exceptions/
│   ├── __init__.py
│   ├── application_error.py          ← ApplicationError base
│   ├── command_validation_error.py   ← CommandValidationError
│   └── resource_not_found_error.py   ← ResourceNotFoundError
├── common/
│   ├── __init__.py
│   ├── query_result.py              ← QueryResult[T]
│   └── paginated_dto.py             ← PaginatedDTO[T]
└── error_mapper/
    ├── __init__.py
    ├── application_error_code.py    ← ApplicationErrorCode enum
    └── error_mapper.py             ← ErrorMapper (domain, infra, validation)
```

### Especificaciones

#### ApplicationErrorCode
```python
class ApplicationErrorCode(str, Enum):
    COMMAND_INVALID = "COMMAND_INVALID"
    COMMAND_MISSING_FIELD = "COMMAND_MISSING_FIELD"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    OPERATION_FAILED = "OPERATION_FAILED"
    TRANSACTION_FAILED = "TRANSACTION_FAILED"
    CONCURRENCY_CONFLICT = "CONCURRENCY_CONFLICT"
```

#### ErrorMapper
Tres mappers estáticos (domain, infra, validation) según `application-errors.md`.

#### QueryResult[T]
```python
@dataclass(frozen=True)
class QueryResult[T]:
    data: list[T]
    total: int | None = None
    page: int | None = None
    size: int | None = None
```

### Definition of Done
- [ ] `src/ingestion/application/` con estructura de directorios
- [ ] `ApplicationErrorCode` enum definido
- [ ] `ApplicationError` + `CommandValidationError` + `ResourceNotFoundError`
- [ ] `ErrorMapper` con 3 métodos estáticos
- [ ] `QueryResult[T]` genérico
- [ ] `PaginatedDTO[T]` con property `pages`
- [ ] Tests unitarios para ErrorMapper (domain→Error, infra→Error, validation→Error)
- [ ] Tests unitarios para QueryResult y PaginatedDTO

---

## 2. Sprint 4.2B — Commands, Queries, DTOs & Mappers

### Objetivo
Implementar todos los objetos de datos (Commands, Queries, DTOs, Mappers). Son `@dataclass(frozen=True)` sin lógica de negocio. Transformaciones puras.

### Archivos a crear

```
src/ingestion/application/
├── commands/
│   ├── __init__.py
│   ├── source_commands.py          ← RegisterSource, UpdateSource, EnableSource, DisableSource
│   ├── feed_commands.py            ← RegisterFeed, UpdateFeed, PauseFeed, ActivateFeed, RecordCollection, RecordFailure
│   ├── source_category_commands.py ← AssignCategoryToSource, AssignTopicToSource
│   ├── feed_category_commands.py   ← AssignCategoryToFeed, AssignTopicToFeed
│   └── article_commands.py         ← CreateRawArticleCommand
├── queries/
│   ├── __init__.py
│   ├── source_queries.py           ← FindSource, ListActiveSources
│   ├── feed_queries.py             ← FindFeed, ListFeeds
│   └── article_queries.py          ← FindArticle, ListArticles
├── dto/
│   ├── __init__.py
│   ├── source_dto.py               ← SourceSummaryDTO, SourceDetailDTO
│   ├── feed_dto.py                 ← FeedSummaryDTO, FeedDetailDTO
│   ├── article_dto.py              ← RawArticleSummaryDTO, RawArticleDetailDTO
│   ├── category_dto.py             ← CategorySummaryDTO, CategoryDetailDTO
│   └── topic_dto.py                ← TopicSummaryDTO, TopicDetailDTO
└── mappers/
    ├── __init__.py
    ├── source_mapper.py            ← SourceMapper (to_summary, to_detail)
    ├── feed_mapper.py              ← FeedMapper (to_summary, to_detail)
    ├── article_mapper.py           ← RawArticleMapper (to_summary, to_detail)
    ├── category_mapper.py          ← CategoryMapper (to_summary, to_detail)
    └── topic_mapper.py             ← TopicMapper (to_summary, to_detail)
```

### Commands (16 total)

| Archivo | Commands |
|---------|----------|
| `source_commands.py` | `RegisterSourceCommand`, `UpdateSourceCommand`, `EnableSourceCommand`, `DisableSourceCommand` |
| `source_category_commands.py` | `AssignCategoryToSourceCommand`, `AssignTopicToSourceCommand` |
| `feed_commands.py` | `RegisterFeedCommand`, `UpdateFeedCommand`, `PauseFeedCommand`, `ActivateFeedCommand`, `RecordCollectionCommand`, `RecordFailureCommand` |
| `feed_category_commands.py` | `AssignCategoryToFeedCommand`, `AssignTopicToFeedCommand` |
| `article_commands.py` | `CreateRawArticleCommand` |

### Queries (5 total)

| Archivo | Queries |
|---------|---------|
| `source_queries.py` | `FindSourceQuery`, `ListActiveSourcesQuery` |
| `feed_queries.py` | `FindFeedQuery`, `ListFeedsQuery` |
| `article_queries.py` | `FindArticleQuery`, `ListArticlesQuery` |

### DTOs (10 + 1 común)

| Archivo | DTOs |
|---------|------|
| `source_dto.py` | `SourceSummaryDTO` (sin `created_at`), `SourceDetailDTO` (sin `created_at`, `updated_at`) |
| `feed_dto.py` | `FeedSummaryDTO` (sin `last_fetched_at`), `FeedDetailDTO` (sin `created_at`, `updated_at`) |
| `article_dto.py` | `RawArticleSummaryDTO`, `RawArticleDetailDTO` |
| `category_dto.py` | `CategorySummaryDTO`, `CategoryDetailDTO` |
| `topic_dto.py` | `TopicSummaryDTO`, `TopicDetailDTO` |

> **Nota sobre timestamps**: `created_at`, `updated_at`, `last_fetched_at` se eliminan de los DTOs de aplicación para la primera iteración. Son datos de infraestructura (row timestamps) que no existen en el dominio. Si la presentación los necesita, los agrega desde la infraestructura.

### Mappers (5)

Cada mapper convierte entidades de dominio → DTOs. Son estáticos, sin estado, sin dependencias.

```python
class SourceMapper:
    @staticmethod
    def to_summary(source: NewsSource, feed_count: int = 0) -> SourceSummaryDTO: ...
    @staticmethod
    def to_detail(source: NewsSource, ...) -> SourceDetailDTO: ...
```

### Definition of Done
- [ ] 16 Commands implementados como `@dataclass(frozen=True)` con type hints del dominio
- [ ] 5 Queries implementadas como `@dataclass(frozen=True)`
- [ ] 10 DTOs implementados como `@dataclass(frozen=True)`
- [ ] 5 Mappers implementados con métodos estáticos
- [ ] Tests: cada Command/Query se construye correctamente
- [ ] Tests: cada Mapper convierte entity → DTO correctamente
- [ ] Tests: casos borde (entity con None, listas vacías)
- [ ] 230 tests de dominio siguen pasando

---

## 3. Sprint 4.2C — Ports & In-Memory Infrastructure

### Objetivo
Implementar los puertos de aplicación (EventPublisher, UnitOfWork) y la infraestructura en memoria para testing. También extender los Protocols de dominio con los batch methods.

### Archivos a modificar/crear

```
src/ingestion/domain/ports/
├── repositories.py                  ← +count_active_by_sources(), +count_by_feeds()  (MODIFICAR)

src/ingestion/application/
├── ports/
│   ├── __init__.py
│   ├── event_publisher.py          ← EventPublisher Protocol
│   └── unit_of_work.py             ← UnitOfWork Protocol

tests/ingestion/application/
├── __init__.py
├── support/
│   ├── __init__.py
│   ├── in_memory_source_repo.py    ← InMemoryNewsSourceRepository
│   ├── in_memory_feed_repo.py      ← InMemoryFeedRepository [+ batch methods]
│   ├── in_memory_article_repo.py   ← InMemoryRawArticleRepository [+ batch methods]
│   ├── in_memory_category_repo.py  ← InMemoryCategoryRepository
│   ├── in_memory_topic_repo.py     ← InMemoryTopicRepository
│   ├── in_memory_uow.py            ← InMemoryUnitOfWork
│   └── in_memory_event_publisher.py ← InMemoryEventPublisher
```

### Batch Methods (Domain Protocol Extension)

Agregar a `FeedRepository`:
```python
def count_active_by_sources(self, source_ids: list[SourceId]) -> dict[SourceId, int]: ...
```

Agregar a `RawArticleRepository`:
```python
def count_by_feeds(self, feed_ids: list[FeedId]) -> dict[FeedId, int]: ...
```

> **Excepción controlada al Domain Freeze**: Solo métodos de query. No modifican entidades, VOs, eventos, ni invariantes. Documentado en AD-CRITICAL-02.

### Application Ports

#### EventPublisher
```python
class EventPublisher(Protocol):
    def publish(self, event: DomainEvent) -> None: ...
    def publish_many(self, events: list[DomainEvent]) -> None: ...
```

#### UnitOfWork
```python
class UnitOfWork(Protocol):
    def __enter__(self) -> UnitOfWork: ...
    def __exit__(self, ...) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
```

### In-Memory Implementations

Cada in-memory repo:
- Almacena en `dict[UUID, Entity]`
- Implementa todos los métodos del Protocol (incluyendo batch)
- Retorna `Result.success` o `Result.failure` según el caso
- Soporta `save()` como upsert

### Definition of Done
- [ ] `count_active_by_sources()` agregado a `FeedRepository` Protocol
- [ ] `count_by_feeds()` agregado a `RawArticleRepository` Protocol
- [ ] `EventPublisher` Protocol definido en application/ports/
- [ ] `UnitOfWork` Protocol definido en application/ports/
- [ ] 5 InMemory repositories implementan todos los métodos
- [ ] `InMemoryUnitOfWork` implementa context manager + commit/rollback
- [ ] `InMemoryEventPublisher` captura eventos publicados para assertions
- [ ] Tests: cada in-memory repo pasa pruebas de comportamiento
- [ ] Tests: UoW commit/rollback funciona correctamente
- [ ] Tests: EventPublisher captura eventos correctamente
- [ ] 230 tests de dominio siguen pasando

---

## 4. Sprint 4.2D — Application Services & Integration Tests

### Objetivo
Implementar los 3 Application Services con los 21 use cases completos, incluyendo AL-01 a AL-05, event publishing, batch counts, y error mapping. Pruebas de integración end-to-end con infraestructura en memoria.

### Archivos a crear

```
src/ingestion/application/
├── services/
│   ├── __init__.py
│   ├── source_service.py           ← SourceService (8 use cases)
│   ├── feed_service.py             ← FeedService (10 use cases)
│   └── article_service.py          ← ArticleService (3 use cases)

tests/ingestion/application/
├── test_source_service.py          ← Tests para SourceService
├── test_feed_service.py            ← Tests para FeedService
├── test_article_service.py         ← Tests para ArticleService
└── test_integration.py             ← Flows cross-service + AL rules
```

### Service: SourceService (8 use cases)

| Método | Use Case | AL Rule | Eventos |
|--------|----------|---------|---------|
| `execute_register_source` | RegisterSource | — | — |
| `execute_update_source` | UpdateSource | — | — |
| `execute_enable_source` | EnableSource | AL-02 | SourceEnabled |
| `execute_disable_source` | DisableSource | AL-01 | SourceDisabled |
| `execute_assign_category_to_source` | AssignCategoryToSource | — | — |
| `execute_assign_topic_to_source` | AssignTopicToSource | — | — |
| `execute_find_source` | FindSource | — | — |
| `execute_list_active_sources` | ListActiveSources | — | — (usa batch count) |

### Service: FeedService (10 use cases)

| Método | Use Case | AL Rule | Eventos |
|--------|----------|---------|---------|
| `execute_register_feed` | RegisterFeed | AL-03, AL-04 | — |
| `execute_update_feed` | UpdateFeed | — | — |
| `execute_pause_feed` | PauseFeed | — | — |
| `execute_activate_feed` | ActivateFeed | — | — |
| `execute_record_collection` | RecordCollection | — | RawArticleCollected |
| `execute_record_failure` | RecordFailure | — | — |
| `execute_assign_category_to_feed` | AssignCategoryToFeed | — | — |
| `execute_assign_topic_to_feed` | AssignTopicToFeed | — | — |
| `execute_find_feed` | FindFeed | — | — |
| `execute_list_feeds` | ListFeeds | — | — (usa batch count) |

### Service: ArticleService (3 use cases)

| Método | Use Case | AL Rule | Eventos |
|--------|----------|---------|---------|
| `execute_create_article` | CreateRawArticle | AL-05 | — |
| `execute_find_article` | FindArticle | — | — |
| `execute_list_articles` | ListArticles | — | — |

### Patrón de cada método

```python
def execute_<use_case>(self, cmd: <Command>) -> Result[DTO]:
    try:
        # 1. AL rules (verificaciones cross-AR antes de dominio)
        # 2. Cargar aggregates del repositorio
        # 3. Llamar métodos de dominio
        # 4. Persistir con UoW
        # 5. Pull y publicar eventos
        # 6. Mapear a DTO y retornar Result.success
    except DomainError as e:
        uow.rollback()
        return Result.failure(mapper.map_domain_error(e))
    except InfrastructureError as e:
        uow.rollback()
        return Result.failure(mapper.map_infra_error(e))
    except Exception as e:
        uow.rollback()
        return Result.failure(Error(UNKNOWN, ...))
```

### Definition of Done
- [ ] `SourceService` con 8 métodos implementados
- [ ] `FeedService` con 10 métodos implementados
- [ ] `ArticleService` con 3 métodos implementados
- [ ] AL-01: Verifica feeds activos antes de disable → `Error(HAS_ACTIVE_FEEDS)`
- [ ] AL-02: Verifica ≥1 feed activo antes de enable → `Error(INVALID_STATE)`
- [ ] AL-03: Verifica source existe antes de crear feed → `Error(NEWS_SOURCE_NOT_FOUND)`
- [ ] AL-04: Verifica source activo antes de crear feed → `Error(NEWS_SOURCE_INACTIVE)`
- [ ] AL-05: Verifica feed existe antes de crear artículo → `Error(FEED_NOT_FOUND)`
- [ ] Eventos se publican DESPUÉS del commit (no antes)
- [ ] Batch count pattern: `ListActiveSources` usa `count_active_by_sources()`
- [ ] Batch count pattern: `ListFeeds` usa `count_by_feeds()`
- [ ] `execute_record_collection` publica `RawArticleCollected` si count > 0
- [ ] `execute_record_failure` auto-pausa feed si `max_retries` excedido
- [ ] Errores de dominio se mapean a `Result.failure` con código correcto
- [ ] Errores de infraestructura se mapean a `Result.failure(OPERATION_FAILED)`
- [ ] Todos los tests de aplicación pasan
- [ ] 230 tests de dominio siguen pasando

---

## 5. Orden de Implementación dentro de cada Sub-sprint

### 4.2A — Structure & Foundation Types
1. `exceptions/application_error.py` + `command_validation_error.py` + `resource_not_found_error.py`
2. `error_mapper/application_error_code.py`
3. `error_mapper/error_mapper.py`
4. `common/query_result.py`
5. `common/paginated_dto.py`
6. Tests

### 4.2B — Commands, Queries, DTOs & Mappers
1. Commands (source → feed → article → category/topic)
2. Queries (source → feed → article)
3. DTOs (source → feed → article → category → topic)
4. Mappers (source → feed → article → category → topic)
5. Tests

### 4.2C — Ports & In-Memory Infrastructure
1. Extend domain repo Protocols (batch methods)
2. Application ports (EventPublisher, UnitOfWork)
3. InMemory repositories (source → feed → article → category → topic)
4. InMemoryUnitOfWork
5. InMemoryEventPublisher
6. Tests

### 4.2D — Application Services & Integration Tests
1. SourceService
2. FeedService
3. ArticleService
4. Integration tests per service
5. Cross-service integration tests (AL rules, event flows)

---

## 6. Riesgos y Mitigaciones

| # | Riesgo | Sub-sprint | Severidad | Mitigación |
|---|--------|------------|-----------|------------|
| **R-I01** | **Domain Freeze violation**: batch methods en repos Protocols sentan precedente | 4.2C | 🟡 Media | Documentar cada excepción en ARB. Solo métodos de query, sin mutación. |
| **R-I02** | **Heavy DI**: Services con 8-11 dependencias | 4.2D | 🟡 Media | Composition Root documentado en `tests/support/` como factory. Sin DI container en primera iteración. |
| **R-I03** | **Service >300 líneas**: SourceService o FeedService pueden crecer | 4.2D | 🔶 Baja | Refactorizar a use case classes si supera 300 líneas. Code review obligatorio. |
| **R-I04** | **In-memory repos no cubren edge cases**: batch methods con listas vacías, sources sin feeds | 4.2C | 🔶 Baja | Tests específicos para bordes: lista vacía, source sin feeds, feed sin artículos. |

---

## 7. Definition of Done (Sprint 4.2 Completo)

- [ ] 21 use cases implementados y testeables (8 Source + 10 Feed + 3 Article)
- [ ] AL-01 a AL-05 verificados en tests de integración
- [ ] Batch count pattern verificado (N+1 eliminado)
- [ ] Eventos AFTER commit verificados
- [ ] Errores de dominio mapean correctamente a `Result.failure`
- [ ] Errores de infraestructura mapean a `OPERATION_FAILED`
- [ ] C-01 resuelto: 4 commands específicos, sin cross-service calls
- [ ] C-02 resuelto: SearchRawArticles eliminado, solo ListArticles
- [ ] C-03 resuelto: batch methods evitan N+1
- [ ] 230+ tests de dominio pasan sin regresiones
- [ ] Documentación actualizada (ARB report, design docs)
