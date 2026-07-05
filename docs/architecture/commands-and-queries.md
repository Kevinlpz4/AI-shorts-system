# Commands & Queries Design — Ingestion Bounded Context

> **Diseño de objetos Command y Query para la capa de aplicación**
>
> Versión: 1.0 | Estado: **DESIGNED**
> Fecha: 2026-07-03
> Basado en: CQRS decision (unified, no separate buses), Application Layer Design v1.0

---

## 1. Principios de Diseño

1. **Inmutabilidad total**: Todos los Command y Query son `@dataclass(frozen=True)`. Una vez creados, no se modifican.
2. **Pure data carriers**: Sin métodos, sin lógica, sin validación de dominio. Solo transportan datos.
3. **Minimal validation**: Solo validación de tipos (Python type hints). NO validación de dominio (no-chequeo de existencia, no-chequeo de unicidad).
4. **Command vs Query**: Command = muta estado. Query = solo lectura.
5. **IDs como objetos tipados**: Los IDs de dominio (SourceId, FeedId, etc.) se reciben como strings en el input y se convierten a objetos tipados en el service. Pero en el Command/Query, usamos el tipo del dominio para mantener type safety interno.
   - **Decisión**: Usar tipos del dominio (SourceId, FeedId, etc.) en los Commands/Queries. La conversión de primitivas a IDs ocurre en el **InputDTO** o en la capa de presentación.
6. **QueryResult[T]**: Envoltorio genérico para resultados de consultas con metadata de paginación.

---

## 2. QueryResult[T]

```python
@dataclass(frozen=True)
class QueryResult[T]:
    """Resultado de una consulta con metadata de paginación.

    Attributes:
        data: Lista de resultados (tipo T).
        total: Total de resultados disponibles (para paginación).
        page: Página actual (1-indexed).
        size: Tamaño de página solicitado.
    """

    data: list[T]
    total: int | None = None
    page: int | None = None
    size: int | None = None
```

---

## 3. Commands

### 3.1 Source Commands

```python
@dataclass(frozen=True)
class RegisterSourceCommand:
    """Crea un nuevo NewsSource.

    Attributes:
        name: Nombre único del source (validado por dominio).
        source_type: Tipo de fuente (RSS, API, SOCIAL_MEDIA, NEWSLETTER).
        source_url: URL base de la fuente.
        categories: Lista opcional de CategoryIds a asignar.
        topics: Lista opcional de TopicIds a asignar.
    """
    name: str
    source_type: SourceType
    source_url: SourceUrl
    categories: list[CategoryId] | None = None
    topics: list[TopicId] | None = None


@dataclass(frozen=True)
class UpdateSourceCommand:
    """Actualiza la configuración de un NewsSource existente.

    Attributes:
        source_id: ID del source a actualizar.
        name: Nuevo nombre (None = no cambiar).
        source_type: Nuevo tipo (None = no cambiar).
        source_url: Nueva URL (None = no cambiar).
    """
    source_id: SourceId
    name: str | None = None
    source_type: SourceType | None = None
    source_url: SourceUrl | None = None


@dataclass(frozen=True)
class EnableSourceCommand:
    """Activa un NewsSource.

    Attributes:
        source_id: ID del source a activar.
    """
    source_id: SourceId


@dataclass(frozen=True)
class DisableSourceCommand:
    """Desactiva un NewsSource.

    Attributes:
        source_id: ID del source a desactivar.
        reason: Razón de la desactivación.
    """
    source_id: SourceId
    reason: str
```

### 3.2 Feed Commands

```python
@dataclass(frozen=True)
class RegisterFeedCommand:
    """Crea un nuevo Feed bajo un NewsSource.

    Attributes:
        source_id: ID del NewsSource padre.
        url: URL del feed.
        label: Etiqueta legible del feed.
        language: Código de idioma ISO 639-1.
        sync_policy: Política de sincronización.
        categories: Lista opcional de CategoryIds.
        topics: Lista opcional de TopicIds.
    """
    source_id: SourceId
    url: ArticleUrl
    label: ArticleTitle
    language: Language
    sync_policy: SyncPolicy
    categories: list[CategoryId] | None = None
    topics: list[TopicId] | None = None


@dataclass(frozen=True)
class UpdateFeedCommand:
    """Actualiza la configuración de un Feed existente.

    Attributes:
        feed_id: ID del feed a actualizar.
        label: Nuevo label (None = no cambiar).
        language: Nuevo idioma (None = no cambiar).
        sync_policy: Nueva política (None = no cambiar).
    """
    feed_id: FeedId
    label: ArticleTitle | None = None
    language: Language | None = None
    sync_policy: SyncPolicy | None = None


@dataclass(frozen=True)
class PauseFeedCommand:
    """Pausa manualmente un Feed.

    Attributes:
        feed_id: ID del feed a pausar.
        reason: Razón de la pausa.
    """
    feed_id: FeedId
    reason: str


@dataclass(frozen=True)
class ActivateFeedCommand:
    """Reactivar un Feed pausado o inactivo.

    Attributes:
        feed_id: ID del feed a reactivar.
    """
    feed_id: FeedId


@dataclass(frozen=True)
class RecordCollectionCommand:
    """Registra una ejecución de fetch exitosa para un Feed.

    Emitido por el scheduler después de un fetch exitoso.
    Puede disparar el evento RawArticleCollected.

    Attributes:
        feed_id: ID del feed que se recolectó.
        batch_id: UUID único del batch de recolección.
        count: Cantidad de artículos nuevos (post-dedup).
        collected_at: Momento exacto de la recolección.
    """
    feed_id: FeedId
    batch_id: UUID
    count: int
    collected_at: datetime


@dataclass(frozen=True)
class RecordFailureCommand:
    """Registra una falla de fetch para un Feed.

    Puede disparar auto-pause si se excede max_retries.

    Attributes:
        feed_id: ID del feed que falló.
        error: Descripción del error.
        failed_at: Momento exacto de la falla.
    """
    feed_id: FeedId
    error: str
    failed_at: datetime
```

### 3.3 Article Commands

```python
@dataclass(frozen=True)
class CreateRawArticleCommand:
    """Crea un nuevo RawArticle (inmutable).

    Attributes:
        feed_id: ID del feed del que se obtuvo.
        external_id: ID único en el sistema externo.
        content_hash: SHA-256 del contenido (64 hex chars).
        title: Título del artículo.
        url: URL canónica del artículo.
        author: Autor (opcional).
        language: Idioma detectado (opcional).
        published_at: Fecha de publicación original (opcional).
        fetched_at: Momento de obtención.
        content_preview: Extracto o resumen (opcional).
        metadata: Datos adicionales específicos del proveedor.
    """
    feed_id: FeedId
    external_id: str
    content_hash: str
    title: ArticleTitle
    url: ArticleUrl
    author: str | None = None
    language: Language | None = None
    published_at: datetime | None = None
    fetched_at: datetime
    content_preview: str | None = None
    metadata: dict | None = None
```

### 3.4 Category & Topic Commands

**Decisión de diseño**: Commands específicos por aggregate en vez de un solo comando genérico con `target_type`. Esto evita ambigüedad en qué Service procesa cada comando y elimina la dependencia cross-service. Cada comando tiene un único Service responsable.

```python
@dataclass(frozen=True)
class AssignCategoryToSourceCommand:
    """Asigna una categoría a un NewsSource.

    Attributes:
        category_id: ID de la categoría a asignar.
        source_id: ID del NewsSource target.
    """
    category_id: CategoryId
    source_id: SourceId


@dataclass(frozen=True)
class AssignCategoryToFeedCommand:
    """Asigna una categoría a un Feed.

    Attributes:
        category_id: ID de la categoría a asignar.
        feed_id: ID del Feed target.
    """
    category_id: CategoryId
    feed_id: FeedId


@dataclass(frozen=True)
class AssignTopicToSourceCommand:
    """Asigna un topic a un NewsSource.

    Attributes:
        topic_id: ID del topic a asignar.
        source_id: ID del NewsSource target.
    """
    topic_id: TopicId
    source_id: SourceId


@dataclass(frozen=True)
class AssignTopicToFeedCommand:
    """Asigna un topic a un Feed.

    Attributes:
        topic_id: ID del topic a asignar.
        feed_id: ID del Feed target.
    """
    topic_id: TopicId
    feed_id: FeedId
```

---

## 4. Queries

### 4.1 Source Queries

```python
@dataclass(frozen=True)
class FindSourceQuery:
    """Obtiene un NewsSource por su ID.

    Attributes:
        source_id: ID del source a buscar.
    """
    source_id: SourceId


@dataclass(frozen=True)
class ListActiveSourcesQuery:
    """Lista todos los NewsSources activos.

    Sin parámetros — retorna todos los sources con is_active=True.
    """
    pass
```

### 4.2 Feed Queries

```python
@dataclass(frozen=True)
class FindFeedQuery:
    """Obtiene un Feed por su ID.

    Attributes:
        feed_id: ID del feed a buscar.
    """
    feed_id: FeedId


@dataclass(frozen=True)
class ListFeedsQuery:
    """Lista los Feeds de un NewsSource.

    Attributes:
        source_id: ID del NewsSource.
        include_inactive: Si incluir feeds inactivos (default: False).
    """
    source_id: SourceId
    include_inactive: bool = False
```

### 4.3 Article Queries

```python
@dataclass(frozen=True)
class FindArticleQuery:
    """Obtiene un RawArticle por su ID.

    Attributes:
        article_id: ID del artículo a buscar.
    """
    article_id: RawArticleId


@dataclass(frozen=True)
class ListArticlesQuery:
    """Lista los RawArticles de un Feed con paginación.

    Attributes:
        feed_id: ID del Feed.
        page: Número de página (1-indexed).
        size: Tamaño de página.
    """
    feed_id: FeedId
    page: int = 1
    size: int = 50

```

---

## 5. Tabla Resumen

| Nombre | Tipo | Service Responsable | Mutación | Parámetros requeridos |
|--------|------|--------------------|----------|----------------------|
| RegisterSourceCommand | Command | SourceService | Sí | name, source_type, source_url |
| UpdateSourceCommand | Command | SourceService | Sí | source_id |
| EnableSourceCommand | Command | SourceService | Sí | source_id |
| DisableSourceCommand | Command | SourceService | Sí | source_id, reason |
| AssignCategoryToSourceCommand | Command | SourceService | Sí | category_id, source_id |
| AssignTopicToSourceCommand | Command | SourceService | Sí | topic_id, source_id |
| RegisterFeedCommand | Command | FeedService | Sí | source_id, url, label, language, sync_policy |
| UpdateFeedCommand | Command | FeedService | Sí | feed_id |
| PauseFeedCommand | Command | FeedService | Sí | feed_id, reason |
| ActivateFeedCommand | Command | FeedService | Sí | feed_id |
| RecordCollectionCommand | Command | FeedService | Sí | feed_id, batch_id, count, collected_at |
| RecordFailureCommand | Command | FeedService | Sí | feed_id, error, failed_at |
| AssignCategoryToFeedCommand | Command | FeedService | Sí | category_id, feed_id |
| AssignTopicToFeedCommand | Command | FeedService | Sí | topic_id, feed_id |
| CreateRawArticleCommand | Command | ArticleService | Sí | feed_id, external_id, content_hash, title, url, fetched_at |
| FindSourceQuery | Query | SourceService | No | source_id |
| ListActiveSourcesQuery | Query | SourceService | No | — |
| FindFeedQuery | Query | FeedService | No | feed_id |
| ListFeedsQuery | Query | FeedService | No | source_id |
| FindArticleQuery | Query | ArticleService | No | article_id |
| ListArticlesQuery | Query | ArticleService | No | feed_id, page, size |

---

## 6. Decisiones de Diseño

### 6.1 ¿Por qué usar tipos del dominio en Commands/Queries?

Los Command y Query objetos se construyen **dentro del Application Service** o desde la **capa de presentación** (después de convertir input). Usar tipos del dominio (SourceId, FeedId, ArticleUrl, etc.) en lugar de primitivos (str, UUID) mantiene type safety y evita errores de tipo en tiempo de compilación.

**Flujo**: Input (HTTP/json) → InputDTO (validación) → Command (tipos del dominio) → Service.execute(command)

### 6.2 ¿Por qué NO hay validación en Commands/Queries?

La validación de dominio pertenece al dominio (invariantes) o al Application Service (reglas cross-AR). Un Command que contiene un `ArticleTitle` vacío será rechazado por el VO en el dominio. Un Command que referencia un source inexistente será rechazado por el AL rule en el service. Los Commands son solo transporte de datos.

### 6.3 ¿Por qué commands específicos en vez de uno genérico con target_type?

Inicialmente se diseñó `AssignCategoryCommand` con `target_type: str` para manejar SOURCE, FEED, y ARTICLE desde un solo comando. Sin embargo, esto creaba ambigüedad sobre qué Service procesaba cada comando y requería lógica condicional en el receptor. Se optó por 4 commands específicos (`AssignCategoryToSourceCommand`, `AssignCategoryToFeedCommand`, `AssignTopicToSourceCommand`, `AssignTopicToFeedCommand`) para:
- Eliminar ambigüedad de responsabilidad (cada comando tiene un Service único)
- Evitar dependencias cross-service
- Type safety: cada comando recibe el tipo de ID correcto (SourceId vs FeedId)
- Facilitar testeabilidad (cada comando se prueba en aislamiento)

### 6.4 ¿Por qué QueryResult[T] en vez de paginación inline?

`QueryResult[T]` es un genérico reutilizable que encapsula la metadata de paginación. Esto evita repetir `total`, `page`, `size` en cada DTO de lista y permite que la capa de presentación maneje la paginación de forma consistente.
