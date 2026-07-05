# DTO Design — Ingestion Bounded Context

> **Diseño de Data Transfer Objects para la capa de aplicación**
>
> Versión: 1.0 | Estado: **DESIGNED**
> Fecha: 2026-07-03
> Basado en: Application Layer Design v1.0

---

## 1. Principios de Diseño

1. **Inmutabilidad**: Todos los DTOs son `@dataclass(frozen=True)`.
2. **Sin lógica de dominio**: Los DTOs solo transportan datos. No tienen métodos de negocio.
3. **Sin referencias circulares**: Los DTOs no referencian entidades de dominio. Son representaciones planas.
4. **Mínimo exponer**: Los DTOs exponen solo lo necesario para el consumidor (API, UI). No exponen estado interno del dominio.
5. **Tres niveles**: Summary (listas), Detail (vista completa), Common (envelopes y paginación).

### ¿Por qué no InputDTO aquí?

Los InputDTOs son responsabilidad de la **capa de presentación** (API/CLI), no de la capa de aplicación. La aplicación recibe Commands y Queries ya construidos. La validación de entrada (formato de JSON, tipos primitivos, campos requeridos) pertenece a la presentación.

La aplicación define los **OutputDTOs** que la presentación necesita para responder.

---

## 2. DTOs Comunes

```python
@dataclass(frozen=True)
class PaginatedDTO[T]:
    """Envoltorio para respuestas paginadas.

    Attributes:
        data: Lista de DTOs de la página actual.
        total: Total de elementos en toda la colección.
        page: Página actual (1-indexed).
        size: Tamaño de página.
        pages: Total de páginas calculado.
    """
    data: list[T]
    total: int
    page: int
    size: int

    @property
    def pages(self) -> int:
        """Calcula el total de páginas."""
        if self.total == 0:
            return 0
        return (self.total + self.size - 1) // self.size


@dataclass(frozen=True)
class ResultDTO[T]:
    """Envoltorio estándar de respuesta para la API.

    Attributes:
        success: Indica si la operación fue exitosa.
        data: DTO de respuesta (éxito) o None.
        error: Mensaje de error (fallo) o None.
        error_code: Código machine-readable del error (fallo) o None.
    """
    success: bool
    data: T | None = None
    error: str | None = None
    error_code: str | None = None


@dataclass(frozen=True)
class ErrorDTO:
    """DTO para errores de aplicación.

    Attributes:
        code: Código machine-readable del error.
        message: Mensaje legible para el desarrollador.
        detail: Detalle técnico adicional (opcional).
    """
    code: str
    message: str
    detail: str | None = None
```

---

## 3. Source DTOs

```python
@dataclass(frozen=True)
class SourceSummaryDTO:
    """Resumen de NewsSource para listas.

    Attributes:
        id: ID del source (string para serialización).
        name: Nombre del source.
        source_type: Tipo de fuente.
        is_active: Estado de actividad.
        feed_count: Cantidad de feeds asociados.
    """
    id: str
    name: str
    source_type: str
    is_active: bool
    feed_count: int = 0
    created_at: datetime | None = None


@dataclass(frozen=True)
class SourceDetailDTO:
    """Detalle completo de NewsSource.

    Attributes:
        id: ID del source (string para serialización).
        name: Nombre del source.
        source_type: Tipo de fuente.
        source_url: URL base de la fuente.
        is_active: Estado de actividad.
        categories: Lista de categorías asignadas (summary).
        topics: Lista de topics asignados (summary).
        feeds: Lista de feeds asociados (summary, opcional).
        created_at: Fecha de creación.
        updated_at: Fecha de última actualización.
    """
    id: str
    name: str
    source_type: str
    source_url: str
    is_active: bool
    categories: list[CategorySummaryDTO] | None = None
    topics: list[TopicSummaryDTO] | None = None
    feeds: list[FeedSummaryDTO] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
```

---

## 4. Feed DTOs

```python
@dataclass(frozen=True)
class FeedSummaryDTO:
    """Resumen de Feed para listas.

    Attributes:
        id: ID del feed (string).
        label: Etiqueta legible del feed.
        source_id: ID del NewsSource padre.
        is_active: Estado de actividad.
        language: Código de idioma.
        article_count: Cantidad de artículos del feed.
        last_fetched_at: Última vez que se ejecutó fetch.
    """
    id: str
    label: str
    source_id: str
    is_active: bool
    language: str
    article_count: int = 0
    last_fetched_at: datetime | None = None


@dataclass(frozen=True)
class FeedDetailDTO:
    """Detalle completo de Feed.

    Attributes:
        id: ID del feed (string).
        source_id: ID del NewsSource padre.
        url: URL del feed.
        label: Etiqueta legible.
        language: Código de idioma.
        is_active: Estado de actividad.
        sync_policy: Configuración de sincronización.
        retry_count: Contador de reintentos actual.
        categories: Lista de categorías asignadas.
        topics: Lista de topics asignados.
        created_at: Fecha de creación.
        updated_at: Fecha de última actualización.
    """
    id: str
    source_id: str
    url: str
    label: str
    language: str
    is_active: bool
    sync_policy: dict  # SyncPolicy serializado
    retry_count: int
    categories: list[CategorySummaryDTO] | None = None
    topics: list[TopicSummaryDTO] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
```

---

## 5. RawArticle DTOs

```python
@dataclass(frozen=True)
class RawArticleSummaryDTO:
    """Resumen de RawArticle para listas.

    Attributes:
        id: ID del artículo (string).
        title: Título del artículo.
        feed_id: ID del feed de origen.
        url: URL canónica.
        author: Autor (si existe).
        language: Idioma detectado.
        published_at: Fecha de publicación original.
        fetched_at: Fecha de obtención.
    """
    id: str
    title: str
    feed_id: str
    url: str
    author: str | None = None
    language: str | None = None
    published_at: datetime | None = None
    fetched_at: datetime | None = None


@dataclass(frozen=True)
class RawArticleDetailDTO:
    """Detalle completo de RawArticle.

    Attributes:
        id: ID del artículo (string).
        feed_id: ID del feed de origen.
        external_id: ID en el sistema externo.
        content_hash: SHA-256 del contenido.
        title: Título del artículo.
        url: URL canónica.
        author: Autor (si existe).
        language: Idioma detectado.
        published_at: Fecha de publicación original.
        fetched_at: Fecha de obtención.
        content_preview: Extracto del contenido.
        metadata: Datos adicionales del proveedor.
    """
    id: str
    feed_id: str
    external_id: str
    content_hash: str
    title: str
    url: str
    author: str | None = None
    language: str | None = None
    published_at: datetime | None = None
    fetched_at: datetime
    content_preview: str | None = None
    metadata: dict | None = None
```

---

## 6. Category DTOs

```python
@dataclass(frozen=True)
class CategorySummaryDTO:
    """Resumen de Category para referencias.

    Attributes:
        id: ID de la categoría (string).
        name: Nombre de la categoría.
        slug: Slug URL-friendly.
        is_active: Estado de actividad.
    """
    id: str
    name: str
    slug: str
    is_active: bool


@dataclass(frozen=True)
class CategoryDetailDTO:
    """Detalle completo de Category.

    Attributes:
        id: ID de la categoría (string).
        name: Nombre de la categoría.
        slug: Slug URL-friendly.
        parent_id: ID de categoría padre (None si es raíz).
        is_active: Estado de actividad.
        children: Lista de subcategorías (summary).
        source_count: Cantidad de sources asociados.
        feed_count: Cantidad de feeds asociados.
    """
    id: str
    name: str
    slug: str
    parent_id: str | None = None
    is_active: bool
    children: list[CategorySummaryDTO] | None = None
    source_count: int = 0
    feed_count: int = 0
```

---

## 7. Topic DTOs

```python
@dataclass(frozen=True)
class TopicSummaryDTO:
    """Resumen de Topic para referencias.

    Attributes:
        id: ID del topic (string).
        name: Nombre del topic.
        is_active: Estado de actividad.
    """
    id: str
    name: str
    is_active: bool


@dataclass(frozen=True)
class TopicDetailDTO:
    """Detalle completo de Topic.

    Attributes:
        id: ID del topic (string).
        name: Nombre del topic.
        description: Descripción del topic.
        is_active: Estado de actividad.
        source_count: Cantidad de sources asociados.
        feed_count: Cantidad de feeds asociados.
    """
    id: str
    name: str
    description: str | None = None
    is_active: bool
    source_count: int = 0
    feed_count: int = 0
```

---

## 8. Cuándo Usar Cada DTO

| Escenario | DTO de entrada | DTO de salida |
|-----------|---------------|---------------|
| Crear source | Primitive input → RegisterSourceCommand | SourceDetailDTO (con datos completos) |
| Listar sources | ListActiveSourcesQuery | PaginatedDTO[SourceSummaryDTO] |
| Ver source detalle | FindSourceQuery | SourceDetailDTO |
| Deshabilitar source | DisableSourceCommand | SourceSummaryDTO (confirmación) |
| Crear feed | Primitive input → RegisterFeedCommand | FeedDetailDTO |
| Listar feeds de source | ListFeedsQuery | PaginatedDTO[FeedSummaryDTO] |
| Ver feed detalle | FindFeedQuery | FeedDetailDTO |
| Pausar feed | PauseFeedCommand | FeedSummaryDTO (confirmación) |
| Crear artículo | Primitive input → CreateRawArticleCommand | RawArticleDetailDTO |
| Listar artículos | ListArticlesQuery | PaginatedDTO[RawArticleSummaryDTO] |
| Buscar artículos | ListArticlesQuery (con feed_id) | PaginatedDTO[RawArticleSummaryDTO] |
| Error de operación | — | ResultDTO[ErrorDTO] (con success=False) |

**Regla general**:
- **Commands** (mutaciones) → retornan **DetailDTO** del aggregate afectado (para feedback inmediato)
- **Create/Register** → retornan **DetailDTO** con el ID generado
- **Enable/Disable/Pause/Activate** → retornan **SummaryDTO** del aggregate (confirmación ligera)
- **RecordCollection/RecordFailure** → retornan **SummaryDTO** del feed (estado actualizado)
- **Queries de lista** → retornan **PaginatedDTO[SummaryDTO]**
- **Queries de detalle** → retornan **DetailDTO**
- **Errores** → retornan **ResultDTO[ErrorDTO]**

---

## 9. Decisiones de Diseño

### 9.1 IDs como strings en DTOs

Los DTOs exponen IDs como `str` (no `SourceId`, `UUID`, etc.) porque:
- Serialización a JSON: UUID no es serializable nativamente
- Consumo por API: los clientes trabajan con strings
- Separación de concerns: la representación interna (EntityId) no debe filtrarse

El mapper convierte `EntityId` → `str(self.id.value)` para los DTOs.

### 9.2 ¿Por qué no exponer directamente las entidades de dominio?

**Clean Architecture**: La capa de presentación NO debe conocer las entidades de dominio. Si expusiéramos entidades directamente:
- Cambios en el dominio (renombrar atributos) impactarían la API
- Estado interno (retry_count, _events) se filtraría
- No podríamos controlar qué campos son públicos

### 9.3 SummaryDTO vs DetailDTO

**SummaryDTO** es para listas y referencias cruzadas (cuando un aggregate aparece como campo de otro). Contiene los campos mínimos para identificar y mostrar el elemento.

**DetailDTO** es para vistas detalladas (pantalla de detalle, respuesta de creación). Contiene todos los campos públicos del aggregate.

### 9.4 ¿Por qué no DTOs de creación separados?

Podríamos tener `CreateSourceDTO`, `CreateFeedDTO`, etc., pero YAGNI. Los Commands ya cumplen ese rol. Los DTOs son exclusivamente para salida. La entrada se maneja con InputDTOs en la presentación o directamente con Commands desde tests/CLI.
