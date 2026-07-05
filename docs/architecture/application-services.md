# Application Services Design — Ingestion Bounded Context

> **Diseño de servicios de aplicación (use cases)**
>
> Versión: 1.0 | Estado: **DESIGNED**
> Fecha: 2026-07-03

---

## 1. Patrón de Diseño

Cada Application Service es una **clase por aggregate** (no una clase por use case). Cada método del service implementa un use case completo.

### Justificación vs Alternativas

| Patrón | Descripción | Tradeoff | Decisión |
|--------|-------------|----------|----------|
| **✅ Service por aggregate** | Una clase por aggregate (SourceService, FeedService) con métodos por use case | Cohesión alta, navegación simple, 3 clases en vez de 14. Si un service supera las 300 líneas, se refactoriza. | **SELECCIONADO** |
| ❌ Una clase por use case | RegisterSourceUseCase, etc. | 14 clases para 14 use cases. Escalable pero overhead innecesario para este tamaño de proyecto. | Descartado por YAGNI |
| ❌ Service único con TODOS los métodos | IngestionService con 20+ métodos | God object. Viola SRP. | Descartado |

### Constructor

```python
class SourceService:
    def __init__(
        self,
        source_repo: NewsSourceRepository,   # ← Domain port
        feed_repo: FeedRepository,            # ← Domain port (needed for AL-01, AL-02)
        category_repo: CategoryRepository,    # ← Domain port (needed for AssignCategory)
        topic_repo: TopicRepository,          # ← Domain port (needed for AssignTopic)
        uow: UnitOfWork,                      # ← Application port
        event_publisher: EventPublisher,      # ← Application port
        clock: ClockPort,                     # ← Foundation port
        uuid_provider: UUIDProvider,          # ← Foundation port
    ) -> None: ...
```

### Método de Use Case

```python
def execute_register_source(
    self, command: RegisterSourceCommand
) -> Result[SourceDetailDTO]: ...
```

**Siempre retorna `Result[DTO]`**. Nunca retorna `None` o la entidad de dominio directamente.

---

## 2. SourceService

### 2.1 Dependencias

- `NewsSourceRepository` — carga y persiste NewsSource
- `FeedRepository` — consulta feeds activos (AL-01, AL-02, batch feed_count)
- `CategoryRepository` — verifica existencia de categorías para AssignCategory
- `TopicRepository` — verifica existencia de topics para AssignTopic
- `UnitOfWork`
- `EventPublisher`
- `ClockPort`
- `UUIDProvider`

### 2.2 Use Cases

#### execute_register_source

| Aspecto | Especificación |
|---------|---------------|
| **Firma** | `execute_register_source(cmd: RegisterSourceCommand) -> Result[SourceDetailDTO]` |
| **AL Rules** | Ninguna directa (el dominio valida unicidad de nombre via I-02) |
| **Repos** | `NewsSourceRepository` |
| **Events** | Ninguno |
| **Transacción** | Sí (creación del source) |

**Flujo**:
1. Validar unicidad de nombre: `source_repo.exists_by_name(cmd.name)`
   - Si True → `Result.failure(Error(DUPLICATE_NEWS_SOURCE, ...))`
2. Verificar categorías existen (si cmd.categories): `category_repo.find_by_id()` para cada una
   - Si alguna no existe → `Result.failure(Error(CATEGORY_NOT_FOUND, ...))`
3. Verificar topics existen (si cmd.topics): `topic_repo.find_by_id()` para cada una
4. Construir `NewsSource` con dominio
5. `source_repo.save(source)`
6. `uow.commit()`
7. `source.pull_events()` (ninguno esperado en creación)
8. Mapear a `SourceDetailDTO`
9. Retornar `Result.success(dto)`

#### execute_update_source

| Aspecto | Especificación |
|---------|---------------|
| **Firma** | `execute_update_source(cmd: UpdateSourceCommand) -> Result[SourceDetailDTO]` |
| **AL Rules** | Ninguna directa |
| **Repos** | `NewsSourceRepository` |
| **Events** | Ninguno |
| **Transacción** | Sí |

**Flujo**:
1. Cargar source: `source_repo.find_by_id(cmd.source_id)`
   - Si `Result.failure` → propagar como `Error(NEWS_SOURCE_NOT_FOUND)`
2. Si cmd.name cambia, verificar unicidad: `source_repo.exists_by_name(cmd.name)`
3. Llamar métodos de dominio: `source.change_url()`, `change_source_type()`, etc.
4. `source_repo.save(source)`
5. `uow.commit()`
6. Mapear a DTO
7. Retornar `Result.success(dto)`

#### execute_enable_source

| Aspecto | Especificación |
|---------|---------------|
| **Firma** | `execute_enable_source(cmd: EnableSourceCommand) -> Result[SourceDetailDTO]` |
| **AL Rules** | **AL-02**: source debe tener al menos un Feed activo |
| **Repos** | `NewsSourceRepository`, `FeedRepository` |
| **Events** | `SourceEnabled` |
| **Transacción** | Sí |

**Flujo**:
1. Cargar source: `source_repo.find_by_id(cmd.source_id)`
2. **AL-02**: `feed_repo.count_active_by_source(cmd.source_id)`
   - Si count == 0 → `Result.failure(Error(INVALID_STATE, "Source needs at least one active feed to be enabled"))`
3. `source.enable()` → registra `SourceEnabled` internamente
4. `source_repo.save(source)`
5. `uow.commit()`
6. `events = source.pull_events()` → contiene `SourceEnabled`
7. `event_publisher.publish_many(events)`
8. Mapear a DTO
9. Retornar `Result.success(dto)`

#### execute_disable_source

| Aspecto | Especificación |
|---------|---------------|
| **Firma** | `execute_disable_source(cmd: DisableSourceCommand) -> Result[SourceDetailDTO]` |
| **AL Rules** | **AL-01**: source no puede desactivarse si tiene Feeds activos |
| **Repos** | `NewsSourceRepository`, `FeedRepository` |
| **Events** | `SourceDisabled` |
| **Transacción** | Sí |

**Flujo**:
1. Cargar source: `source_repo.find_by_id(cmd.source_id)`
2. **AL-01**: `feed_repo.count_active_by_source(cmd.source_id)`
   - Si count > 0 → `Result.failure(Error(HAS_ACTIVE_FEEDS, "Cannot disable source with active feeds"))`
3. `source.disable(reason=cmd.reason)` → registra `SourceDisabled` internamente
4. `source_repo.save(source)`
5. `uow.commit()`
6. `events = source.pull_events()` → contiene `SourceDisabled`
7. `event_publisher.publish_many(events)`
8. Mapear a DTO
9. Retornar `Result.success(dto)`

#### execute_assign_category_to_source

| Aspecto | Especificación |
|---------|---------------|
| **Firma** | `execute_assign_category_to_source(cmd: AssignCategoryToSourceCommand) -> Result[SourceDetailDTO]` |
| **AL Rules** | Ninguna (el dominio valida la asignación) |
| **Repos** | `CategoryRepository`, `NewsSourceRepository` |
| **Events** | Ninguno |
| **Transacción** | Sí |

**Flujo**:
1. Verificar categoría existe: `category_repo.find_by_id(cmd.category_id)`
   - Si no existe → `Result.failure(Error(CATEGORY_NOT_FOUND, ...))`
2. Cargar source: `source_repo.find_by_id(cmd.source_id)`
3. `source.assign_category(cmd.category_id)` → el dominio maneja duplicados
4. `source_repo.save(source)`
5. `uow.commit()`
6. Mapear a `SourceDetailDTO`
7. Retornar `Result.success(dto)`

#### execute_assign_topic_to_source

| Aspecto | Especificación |
|---------|---------------|
| **Firma** | `execute_assign_topic_to_source(cmd: AssignTopicToSourceCommand) -> Result[SourceDetailDTO]` |
| **AL Rules** | Ninguna |
| **Repos** | `TopicRepository`, `NewsSourceRepository` |
| **Events** | Ninguno |
| **Transacción** | Sí |

**Flujo**: Análogo a assign_category_to_source, pero con topics.

---

## 3. FeedService

### 3.1 Dependencias

- `FeedRepository`
- `NewsSourceRepository` (AL-03, AL-04)
- `CategoryRepository` (asignación de categorías)
- `TopicRepository` (asignación de topics)
- `UnitOfWork`
- `EventPublisher`
- `ClockPort`
- `UUIDProvider`

### 3.2 Use Cases

#### execute_register_feed

| Aspecto | Especificación |
|---------|---------------|
| **Firma** | `execute_register_feed(cmd: RegisterFeedCommand) -> Result[FeedDetailDTO]` |
| **AL Rules** | **AL-03**: source_id referencia NewsSource existente. **AL-04**: NewsSource debe estar activo. |
| **Repos** | `FeedRepository`, `NewsSourceRepository` |
| **Events** | Ninguno |
| **Transacción** | Sí |

**Flujo**:
1. **AL-03**: `source_repo.find_by_id(cmd.source_id)`
   - Si `Result.failure` → propagar como `Error(NEWS_SOURCE_NOT_FOUND)`
2. **AL-04**: Verificar `source.is_active`
   - Si False → `Result.failure(Error(NEWS_SOURCE_INACTIVE, ...))`
3. Verificar unicidad de URL en el source: `feed_repo.exists_by_source_and_url(cmd.source_id, cmd.url)`
   - Si True → `Result.failure(Error(DUPLICATE_FEED_URL, ...))`
4. Verificar categorías existen (si cmd.categories)
5. Verificar topics existen (si cmd.topics)
6. Construir `Feed` con dominio
7. `feed_repo.save(feed)`
8. `uow.commit()`
9. Mapear a DTO
10. Retornar `Result.success(dto)`

#### execute_update_feed

| Aspecto | Especificación |
|---------|---------------|
| **Firma** | `execute_update_feed(cmd: UpdateFeedCommand) -> Result[FeedDetailDTO]` |
| **AL Rules** | Ninguna |
| **Repos** | `FeedRepository` |
| **Events** | Ninguno |
| **Transacción** | Sí |

**Flujo** simple: carga feed, actualiza campos, guarda.

#### execute_pause_feed

| Aspecto | Especificación |
|---------|---------------|
| **Firma** | `execute_pause_feed(cmd: PauseFeedCommand) -> Result[FeedDetailDTO]` |
| **AL Rules** | Ninguna (es operación manual) |
| **Repos** | `FeedRepository` |
| **Events** | Ninguno (no hay evento FeedPaused por YAGNI, es estado interno) |
| **Transacción** | Sí |

**Flujo**: carga feed, llama `feed.pause(reason)`, guarda, mapea.

#### execute_activate_feed

| Aspecto | Especificación |
|---------|---------------|
| **Firma** | `execute_activate_feed(cmd: ActivateFeedCommand) -> Result[FeedDetailDTO]` |
| **AL Rules** | Ninguna |
| **Repos** | `FeedRepository` |
| **Events** | Ninguno |
| **Transacción** | Sí |

**Flujo**: carga feed, llama `feed.activate()` (resetea retry_count), guarda, mapea.

#### execute_record_collection

| Aspecto | Especificación |
|---------|---------------|
| **Firma** | `execute_record_collection(cmd: RecordCollectionCommand) -> Result[FeedDetailDTO]` |
| **AL Rules** | Ninguna (operación interna del scheduler) |
| **Repos** | `FeedRepository`, `RawArticleRepository` (indirecto, para estadísticas) |
| **Events** | `RawArticleCollected` (si count > 0) |
| **Transacción** | Sí |

**Flujo**:
1. Cargar feed: `feed_repo.find_by_id(cmd.feed_id)`
2. `feed.record_collection(batch_id=cmd.batch_id, count=cmd.count)`
   - Si count > 0: registra `RawArticleCollected`
   - Resetea `retry_count` a 0
3. `feed_repo.save(feed)`
4. `uow.commit()`
5. `events = feed.pull_events()` → si count > 0, contiene `RawArticleCollected`
6. `event_publisher.publish_many(events)`
7. Mapear a DTO
8. Retornar `Result.success(dto)`

#### execute_record_failure

| Aspecto | Especificación |
|---------|---------------|
| **Firma** | `execute_record_failure(cmd: RecordFailureCommand) -> Result[FeedDetailDTO]` |
| **AL Rules** | Ninguna (dominio maneja auto-pause internamente) |
| **Repos** | `FeedRepository` |
| **Events** | Ninguno (no hay FeedPaused por YAGNI) |
| **Transacción** | Sí |

**Flujo**:
1. Cargar feed: `feed_repo.find_by_id(cmd.feed_id)`
2. `result = feed.record_failure(error=cmd.error)`
   - Incrementa retry_count
   - Si `not can_retry()`: auto-pause (marca `is_active = False`)
3. `feed_repo.save(feed)`
4. `uow.commit()`
5. Mapear a DTO (incluyendo estado de pause si aplica)
6. Retornar `Result.success(dto)`

#### execute_assign_category_to_feed

| Aspecto | Especificación |
|---------|---------------|
| **Firma** | `execute_assign_category_to_feed(cmd: AssignCategoryToFeedCommand) -> Result[FeedDetailDTO]` |
| **AL Rules** | Ninguna |
| **Repos** | `CategoryRepository`, `FeedRepository` |
| **Events** | Ninguno |
| **Transacción** | Sí |

**Flujo**:
1. Verificar categoría existe: `category_repo.find_by_id(cmd.category_id)`
2. Cargar feed: `feed_repo.find_by_id(cmd.feed_id)`
3. `feed.assign_category(cmd.category_id)`
4. `feed_repo.save(feed)`
5. `uow.commit()`
6. Mapear a `FeedDetailDTO`
7. Retornar `Result.success(dto)`

#### execute_assign_topic_to_feed

| Aspecto | Especificación |
|---------|---------------|
| **Firma** | `execute_assign_topic_to_feed(cmd: AssignTopicToFeedCommand) -> Result[FeedDetailDTO]` |
| **AL Rules** | Ninguna |
| **Repos** | `TopicRepository`, `FeedRepository` |
| **Events** | Ninguno |
| **Transacción** | Sí |

**Flujo**: Análogo a assign_category_to_feed, pero con topics.

---

## 4. ArticleService

### 4.1 Dependencias

- `RawArticleRepository`
- `FeedRepository` (AL-05)
- `UnitOfWork`
- `EventPublisher`
- `ClockPort`
- `UUIDProvider`

### 4.2 Use Cases

#### execute_create_article

| Aspecto | Especificación |
|---------|---------------|
| **Firma** | `execute_create_article(cmd: CreateRawArticleCommand) -> Result[RawArticleDetailDTO]` |
| **AL Rules** | **AL-05**: feed_id referencia un Feed existente |
| **Repos** | `RawArticleRepository`, `FeedRepository` |
| **Events** | Ninguno (el RawArticle no emite eventos — es inmutable) |
| **Transacción** | Sí |

**Flujo**:
1. **AL-05**: `feed_repo.find_by_id(cmd.feed_id)`
   - Si `Result.failure` → propagar como `Error(FEED_NOT_FOUND)`
2. Verificar duplicados pre-save:
   - `raw_article_repo.exists_by_url(cmd.feed_id, cmd.url)`
   - Si True → `Result.failure(Error(DUPLICATE_ARTICLE, "URL already exists in this feed"))`
   - `raw_article_repo.exists_by_hash(cmd.feed_id, cmd.content_hash)`
   - Si True → `Result.failure(Error(DUPLICATE_ARTICLE, "Content hash already exists in this feed"))`
3. Construir `RawArticle` (dominio valida invariantes I-11 a I-17)
4. `raw_article_repo.save(article)`
5. `uow.commit()`
6. Mapear a DTO
7. Retornar `Result.success(dto)`

#### execute_find_article

| Aspecto | Especificación |
|---------|---------------|
| **Firma** | `execute_find_article(cmd: FindArticleQuery) -> Result[RawArticleDetailDTO]` |
| **AL Rules** | Ninguna |
| **Repos** | `RawArticleRepository` |
| **Transacción** | No (solo lectura) |

**Flujo**:
1. `raw_article_repo.find_by_id(cmd.article_id)`
   - Si `Result.failure` → propagar como `Error(RAW_ARTICLE_NOT_FOUND)`
2. Mapear a `RawArticleDetailDTO`
3. Retornar `Result.success(dto)`

#### execute_list_articles

| Aspecto | Especificación |
|---------|---------------|
| **Firma** | `execute_list_articles(cmd: ListArticlesQuery) -> Result[QueryResult[RawArticleSummaryDTO]]` |
| **AL Rules** | Ninguna |
| **Repos** | `RawArticleRepository` |
| **Transacción** | No (solo lectura) |

**Flujo**:
1. `articles = raw_article_repo.find_by_feed(cmd.feed_id, cmd.page, cmd.size)`
2. `total = raw_article_repo.count_by_feed(cmd.feed_id)`
3. Mapear cada artículo a `RawArticleSummaryDTO`
4. Retornar `Result.success(QueryResult(data=dtos, total=total, page=cmd.page, size=cmd.size))`

---



## 5. Mapper Pattern

Cada `*Mapper` es una clase estática (o clase con métodos de clase) que convierte entre entidades de dominio y DTOs:

```python
class SourceMapper:
    @staticmethod
    def to_summary(source: NewsSource, feed_count: int = 0) -> SourceSummaryDTO:
        return SourceSummaryDTO(
            id=str(source.id),
            name=source.name,
            source_type=source.source_type.value,
            is_active=source.is_active,
            feed_count=feed_count,
        )

    @staticmethod
    def to_detail(
        source: NewsSource,
        categories: list[CategorySummaryDTO] | None = None,
        topics: list[TopicSummaryDTO] | None = None,
        feeds: list[FeedSummaryDTO] | None = None,
    ) -> SourceDetailDTO:
        return SourceDetailDTO(
            id=str(source.id),
            name=source.name,
            source_type=source.source_type.value,
            source_url=str(source.source_url),
            is_active=source.is_active,
            categories=categories,
            topics=topics,
            feeds=feeds,
        )
```

**Los mappers no tienen estado. No inyectan dependencias. Son transformaciones puras.**

### Batch Count Pattern (anti N+1)

Para poblar `SourceSummaryDTO.feed_count` en listas sin N+1:

1. El service carga todos los sources activos: `source_repo.find_active()`
2. Extrae los IDs: `source_ids = [s.id for s in sources]`
3. Batch query: `feed_repo.count_active_by_sources(source_ids) → dict[SourceId, int]`
4. Mappea cada source con su count: `SourceMapper.to_summary(source, feed_counts.get(source.id, 0))`

Análogamente para `FeedSummaryDTO.article_count`:
1. Carga los feeds de un source: `feed_repo.find_by_source(source_id)`
2. Extrae los IDs: `feed_ids = [f.id for f in feeds]`
3. Batch query: `raw_article_repo.count_by_feeds(feed_ids) → dict[FeedId, int]`
4. Mappea cada feed con su count

Este patrón requiere 2 queries (sources + batch counts) en vez de N+1. Los métodos `count_active_by_sources()` y `count_by_feeds()` se agregan a los Protocols de repositorio en `domain/ports/` como extensión de query (sin modificar el modelo de dominio).

---

## 6. Resumen de Use Cases

| # | Use Case | Service | AL Rules | Events | Transacción |
|--|----------|---------|----------|--------|-------------|
| 1 | RegisterSource | SourceService | — | — | Sí |
| 2 | UpdateSource | SourceService | — | — | Sí |
| 3 | EnableSource | SourceService | AL-02 | SourceEnabled | Sí |
| 4 | DisableSource | SourceService | AL-01 | SourceDisabled | Sí |
| 5 | AssignCategoryToSource | SourceService | — | — | Sí |
| 6 | AssignTopicToSource | SourceService | — | — | Sí |
| 7 | RegisterFeed | FeedService | AL-03, AL-04 | — | Sí |
| 8 | UpdateFeed | FeedService | — | — | Sí |
| 9 | PauseFeed | FeedService | — | — | Sí |
| 10 | ActivateFeed | FeedService | — | — | Sí |
| 11 | RecordCollection | FeedService | — | RawArticleCollected | Sí |
| 12 | RecordFailure | FeedService | — | — | Sí |
| 13 | AssignCategoryToFeed | FeedService | — | — | Sí |
| 14 | AssignTopicToFeed | FeedService | — | — | Sí |
| 15 | CreateRawArticle | ArticleService | AL-05 | — | Sí |
| 16 | FindSource | SourceService | — | — | No |
| 17 | FindFeed | FeedService | — | — | No |
| 18 | FindArticle | ArticleService | — | — | No |
| 19 | ListActiveSources | SourceService | — | — | No |
| 20 | ListFeeds | FeedService | — | — | No |
| 21 | ListArticles | ArticleService | — | — | No |
