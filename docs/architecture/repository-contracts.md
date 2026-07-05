# Repository Port Contracts — Ingestion Bounded Context

> **Contratos de interfaces de repositorio del dominio de Ingestion**
>
> Versión: 1.0 | Estado: **DESIGNED**
> Fecha: 2026-07-03
> Basado en: Sprint 3.1 Design v2.0 (T-01), Aggregate Design v1.0 (T-03)
>
> **Este documento define los contratos de los 5 repositorios del BC Ingestion.**
> Son Protocols (interfaces) — NO implementaciones. No mencionan tecnologías.

---

## Tabla de Contenidos

1. [Principios de Diseño](#1-principios-de-diseño)
2. [NewsSourceRepository](#2-newssourcerepository)
3. [FeedRepository](#3-feedrepository)
4. [RawArticleRepository](#4-rawarticlerepository)
5. [CategoryRepository](#5-categoryrepository)
6. [TopicRepository](#6-topicrepository)
7. [Resumen de Métodos y Errores](#7-resumen-de-métodos-y-errores)

---

## 1. Principios de Diseño

### 1.1 Definiciones

```python
# Todos los repositorios usan estos tipos base de Foundation e Ingestion:

from foundation.value_objects import Result  # Result[T, Error]
from ingestion.domain.exceptions.errors import IngestionErrorCode
from ingestion.domain.entities.ids import (
    SourceId, FeedId, RawArticleId, CategoryId, TopicId,
)
from ingestion.domain.entities.news_source import NewsSource
from ingestion.domain.entities.feed import Feed
from ingestion.domain.entities.raw_article import RawArticle
from ingestion.domain.entities.category import Category
from ingestion.domain.entities.topic import Topic
from ingestion.domain.value_objects.article_url import ArticleUrl

# Protocol de typing
from typing import Protocol
```

### 1.2 Principios

1. **Protocols, no ABCs**: Todos los repositorios son `Protocol` (duck typing estructural). Cualquier clase que implemente los métodos con las firmas correctas es automáticamente un repositorio válido.
2. **Sin mención de tecnología**: No hay `async`, no hay `await`, no hay `Session`, no hay `Connection`, no hay `SELECT`, no hay `INSERT`. El dominio no sabe cómo se persisten los datos.
3. **Métodos en lenguaje de dominio**: Los parámetros y retornos usan tipos del dominio (entity objects, VOs, IDs), no tipos primitivos genéricos.
4. **Result[T] para operaciones que fallan**: `find_by_id`, `find_by_name`, etc. retornan `Result[T]` que puede ser `Ok(value)` o `Error(error_code, message)`. Los códigos de error son valores de `IngestionErrorCode`.
5. **list[T] para operaciones que pueden retornar vacío**: `find_all()`, `find_active()`, etc. retornan `list[T]` — si no hay resultados, lista vacía (no es error).
6. **bool para operaciones de existencia**: `exists_by_*` retorna `bool` — semánticamente claro para deduplicación y validación.
7. **Cada Aggregate Root tiene su repositorio**: NewsSource, Feed, RawArticle. También Category y Topic (Entities) porque necesitan persistencia independiente.
8. **save() recibe la entidad completa**: No hay métodos parciales como `update_retry_count()` — el repositorio persiste el estado completo de la entidad.

---

## 2. NewsSourceRepository

**Para**: `NewsSource` (Aggregate Root)
**Ubicación**: `src/ingestion/domain/ports/repositories.py`
**Métodos**: 6

```python
class NewsSourceRepository(Protocol):
    """Puerto de persistencia para NewsSource (Aggregate Root).

    Responsabilidad: Persistir y recuperar fuentes externas de información.
    Cada NewsSource tiene identidad única (SourceId) y nombre único.
    """

    def save(self, source: NewsSource) -> None:
        """Persiste un NewsSource (crea o actualiza).

        Semántica:
        - Si el NewsSource no existe (según su SourceId), se crea.
        - Si ya existe, se actualiza (reemplazo completo del estado).
        - No retorna nada — el repositorio maneja la persistencia internamente.

        Errores (no esperados en operación normal):
        - Ninguno. Si save() falla, la excepción es de infraestructura.
        """
        ...

    def find_by_id(self, id: SourceId) -> Result[NewsSource]:
        """Busca un NewsSource por su identidad única.

        Args:
            id: SourceId del NewsSource a buscar.

        Returns:
            Ok(NewsSource) si se encuentra.
            Error(NEWS_SOURCE_NOT_FOUND, mensaje) si no existe.

        Errores:
            - NEWS_SOURCE_NOT_FOUND: No existe NewsSource con ese ID.
        """
        ...

    def find_by_name(self, name: str) -> Result[NewsSource]:
        """Busca un NewsSource por su nombre único.

        Args:
            name: Nombre exacto del NewsSource.

        Returns:
            Ok(NewsSource) si se encuentra.
            Error(NEWS_SOURCE_NOT_FOUND, mensaje) si no existe.

        Errores:
            - NEWS_SOURCE_NOT_FOUND: No existe NewsSource con ese nombre.
        """
        ...

    def find_all(self) -> list[NewsSource]:
        """Retorna todos los NewsSources registrados.

        Returns:
            Lista de NewsSources (puede estar vacía).
            No retorna Error — lista vacía significa que no hay sources.
        """
        ...

    def find_active(self) -> list[NewsSource]:
        """Retorna solo los NewsSources activos (is_active = True).

        Returns:
            Lista de NewsSources activos (puede estar vacía).
        """
        ...

    def exists_by_name(self, name: str) -> bool:
        """Verifica si existe un NewsSource con el nombre dado.

        Args:
            name: Nombre a verificar.

        Returns:
            True si existe un NewsSource con ese nombre.
            False si no existe.

        Uso típico: Validación de unicidad antes de crear/renombrar.
        """
        ...
```

---

## 3. FeedRepository

**Para**: `Feed` (Aggregate Root)
**Ubicación**: `src/ingestion/domain/ports/repositories.py`
**Métodos**: 7

```python
class FeedRepository(Protocol):
    """Puerto de persistencia para Feed (Aggregate Root).

    Responsabilidad: Persistir y recuperar streams configurables de ingesta.
    Cada Feed pertenece a un NewsSource (source_id) y tiene URL única
    dentro de ese source.
    """

    def save(self, feed: Feed) -> None:
        """Persiste un Feed (crea o actualiza).

        Semántica:
        - Si el Feed no existe (según su FeedId), se crea.
        - Si ya existe, se actualiza (reemplazo completo del estado).
        """
        ...

    def find_by_id(self, id: FeedId) -> Result[Feed]:
        """Busca un Feed por su identidad única.

        Args:
            id: FeedId del Feed a buscar.

        Returns:
            Ok(Feed) si se encuentra.
            Error(FEED_NOT_FOUND, mensaje) si no existe.

        Errores:
            - FEED_NOT_FOUND: No existe Feed con ese ID.
        """
        ...

    def find_by_source(self, source_id: SourceId) -> list[Feed]:
        """Retorna todos los Feeds de un NewsSource.

        Args:
            source_id: SourceId del NewsSource.

        Returns:
            Lista de Feeds del source (puede estar vacía).
            No valida que el source exista — es responsabilidad del caller.
        """
        ...

    def find_by_url(
        self, source_id: SourceId, url: ArticleUrl
    ) -> Result[Feed]:
        """Busca un Feed por URL dentro de un NewsSource.

        Args:
            source_id: SourceId del NewsSource.
            url: ArticleUrl del Feed a buscar.

        Returns:
            Ok(Feed) si se encuentra.
            Error(FEED_NOT_FOUND, mensaje) si no existe.

        Errores:
            - FEED_NOT_FOUND: No existe Feed con esa URL en el source.

        Uso típico: Verificar unicidad de URL y obtener Feed por URL.
        """
        ...

    def find_active_by_source(self, source_id: SourceId) -> list[Feed]:
        """Retorna los Feeds activos (is_active = True) de un NewsSource.

        Args:
            source_id: SourceId del NewsSource.

        Returns:
            Lista de Feeds activos (puede estar vacía).

        Uso típico: Verificar NewsSource.can_be_disabled().
        """
        ...

    def exists_by_source_and_url(
        self, source_id: SourceId, url: ArticleUrl
    ) -> bool:
        """Verifica si existe un Feed con esa URL en el NewsSource.

        Args:
            source_id: SourceId del NewsSource.
            url: ArticleUrl a verificar.

        Returns:
            True si existe un Feed con esa URL en el source.
            False si no existe.

        Uso típico: Validación de I-06 (url única dentro del source).
        """
        ...

    def count_active_by_source(self, source_id: SourceId) -> int:
        """Cuenta los Feeds activos de un NewsSource.

        Args:
            source_id: SourceId del NewsSource.

        Returns:
            Número de Feeds activos (0 si no hay o el source no existe).

        Uso típico: Verificar NewsSource.can_be_disabled().
        Más eficiente que find_active_by_source().count() cuando
        solo se necesita el número.
        """
        ...
```

---

## 4. RawArticleRepository

**Para**: `RawArticle` (Aggregate Root, Inmutable)
**Ubicación**: `src/ingestion/domain/ports/repositories.py`
**Métodos**: 8

```python
class RawArticleRepository(Protocol):
    """Puerto de persistencia para RawArticle (Aggregate Root, Inmutable).

    Responsabilidad: Persistir y recuperar artículos crudos inmutables.
    Soporta save individual y batch. Provee métodos de deduplicación
    por hash y URL.

    Nota de inmutabilidad: Una vez creado, RawArticle nunca se actualiza.
    save() siempre es una creación, nunca una modificación.
    """

    def save(self, article: RawArticle) -> None:
        """Persiste un RawArticle (siempre es creación, nunca actualización).

        Args:
            article: RawArticle a persistir.

        Errores (esperados):
            - DUPLICATE_ARTICLE: Ya existe un RawArticle con el mismo
              external_id+feed_id o mismo content_hash+feed_id.

        Nota: El repositorio DEBE verificar las constraints de unicidad
        (I-12, I-13) y rechazar duplicados con DUPLICATE_ARTICLE.
        """
        ...

    def save_batch(self, articles: list[RawArticle]) -> None:
        """Persiste múltiples RawArticles en una operación atómica.

        Args:
            articles: Lista de RawArticles a persistir.

        Semántica:
        - Todos los artículos se persisten en la misma transacción.
        - Si alguno falla (ej: duplicado), TODOS fallan (rollback).
        - El caller debe manejar el error y reintentar uno por uno si es necesario.

        Errores:
            - DUPLICATE_ARTICLE: Algún artículo duplica external_id o hash.
        """
        ...

    def find_by_id(self, id: RawArticleId) -> Result[RawArticle]:
        """Busca un RawArticle por su identidad única.

        Args:
            id: RawArticleId del artículo a buscar.

        Returns:
            Ok(RawArticle) si se encuentra.
            Error(RAW_ARTICLE_NOT_FOUND, mensaje) si no existe.

        Errores:
            - RAW_ARTICLE_NOT_FOUND: No existe RawArticle con ese ID.
        """
        ...

    def find_by_feed(
        self, feed_id: FeedId, page: int = 1, size: int = 50
    ) -> list[RawArticle]:
        """Retorna RawArticles de un Feed con paginación.

        Args:
            feed_id: FeedId del Feed.
            page: Número de página (1-indexed, default 1).
            size: Tamaño de página (default 50, max 1000).

        Returns:
            Lista de RawArticles de ese Feed (puede estar vacía).
            Ordenados por fetched_at descendente (más recientes primero).
        """
        ...

    def find_by_hash(
        self, feed_id: FeedId, content_hash: str
    ) -> Result[RawArticle]:
        """Busca un RawArticle por su content_hash dentro de un Feed.

        Args:
            feed_id: FeedId del Feed.
            content_hash: SHA-256 hash a buscar (64 caracteres hex).

        Returns:
            Ok(RawArticle) si se encuentra.
            Error(RAW_ARTICLE_NOT_FOUND, mensaje) si no existe.

        Errores:
            - RAW_ARTICLE_NOT_FOUND: No existe RawArticle con ese hash.

        Uso típico: Deduplicación por contenido.
        """
        ...

    def exists_by_url(
        self, feed_id: FeedId, url: ArticleUrl
    ) -> bool:
        """Verifica si existe un RawArticle con esa URL en el Feed.

        Args:
            feed_id: FeedId del Feed.
            url: ArticleUrl a verificar.

        Returns:
            True si existe un RawArticle con esa URL en el Feed.
            False si no existe.

        Uso típico: Deduplicación por URL.
        """
        ...

    def exists_by_hash(
        self, feed_id: FeedId, content_hash: str
    ) -> bool:
        """Verifica si existe un RawArticle con ese hash en el Feed.

        Args:
            feed_id: FeedId del Feed.
            content_hash: SHA-256 hash a verificar.

        Returns:
            True si existe un RawArticle con ese hash en el Feed.
            False si no existe.

        Uso típico: Deduplicación por contenido (más eficiente que find_by_hash).
        """
        ...

    def count_by_feed(self, feed_id: FeedId) -> int:
        """Retorna la cantidad total de RawArticles de un Feed.

        Args:
            feed_id: FeedId del Feed.

        Returns:
            Número total de RawArticles (0 si el Feed no existe o no tiene).

        Uso típico: Estadísticas, paginación (total de páginas).
        """
        ...
```

---

## 5. CategoryRepository

**Para**: `Category` (Entity, NO Aggregate Root)
**Ubicación**: `src/ingestion/domain/ports/repositories.py`
**Métodos**: 7

```python
class CategoryRepository(Protocol):
    """Puerto de persistencia para Category (Entity).

    Responsabilidad: Persistir y recuperar la taxonomía de categorías.
    Soporta jerarquía (parent_id) y verificación de slug único.
    """

    def save(self, category: Category) -> None:
        """Persiste una Category (crea o actualiza).

        Args:
            category: Category a persistir.

        Nota: El repositorio NO valida la jerarquía (ciclos, self-parent).
        Esa validación es responsabilidad de Category.change_parent().
        """
        ...

    def find_by_id(self, id: CategoryId) -> Result[Category]:
        """Busca una Category por su identidad única.

        Args:
            id: CategoryId de la categoría a buscar.

        Returns:
            Ok(Category) si se encuentra.
            Error(CATEGORY_NOT_FOUND, mensaje) si no existe.

        Errores:
            - CATEGORY_NOT_FOUND: No existe Category con ese ID.
        """
        ...

    def find_by_slug(self, slug: str) -> Result[Category]:
        """Busca una Category por su slug único.

        Args:
            slug: Slug exacto de la categoría.

        Returns:
            Ok(Category) si se encuentra.
            Error(CATEGORY_NOT_FOUND, mensaje) si no existe.

        Errores:
            - CATEGORY_NOT_FOUND: No existe Category con ese slug.
        """
        ...

    def find_all(self) -> list[Category]:
        """Retorna todas las categorías registradas.

        Returns:
            Lista de categorías (puede estar vacía).
        """
        ...

    def find_active(self) -> list[Category]:
        """Retorna solo las categorías activas (is_active = True).

        Returns:
            Lista de categorías activas (puede estar vacía).
        """
        ...

    def find_by_parent(self, parent_id: CategoryId) -> list[Category]:
        """Retorna las subcategorías de una categoría (hijos directos).

        Args:
            parent_id: CategoryId de la categoría padre.

        Returns:
            Lista de categorías hijas directas (puede estar vacía).
            No retorna nietos ni bisnietos — solo hijos directos.

        Uso típico: Verificar I-21 (cascade de desactivación).
        """
        ...

    def exists_by_slug(self, slug: str) -> bool:
        """Verifica si existe una categoría con el slug dado.

        Args:
            slug: Slug a verificar.

        Returns:
            True si existe una categoría con ese slug.
            False si no existe.

        Uso típico: Validación de I-18 (slug único).
        """
        ...
```

---

## 6. TopicRepository

**Para**: `Topic` (Entity, NO Aggregate Root)
**Ubicación**: `src/ingestion/domain/ports/repositories.py`
**Métodos**: 6

```python
class TopicRepository(Protocol):
    """Puerto de persistencia para Topic (Entity).

    Responsabilidad: Persistir y recuperar la lista de temas/tópicos
    de interés. Soporta verificación de nombre único.
    """

    def save(self, topic: Topic) -> None:
        """Persiste un Topic (crea o actualiza).

        Args:
            topic: Topic a persistir.
        """
        ...

    def find_by_id(self, id: TopicId) -> Result[Topic]:
        """Busca un Topic por su identidad única.

        Args:
            id: TopicId del topic a buscar.

        Returns:
            Ok(Topic) si se encuentra.
            Error(TOPIC_NOT_FOUND, mensaje) si no existe.

        Errores:
            - TOPIC_NOT_FOUND: No existe Topic con ese ID.
        """
        ...

    def find_by_name(self, name: str) -> Result[Topic]:
        """Busca un Topic por su nombre único.

        Args:
            name: Nombre exacto del topic.

        Returns:
            Ok(Topic) si se encuentra.
            Error(TOPIC_NOT_FOUND, mensaje) si no existe.

        Errores:
            - TOPIC_NOT_FOUND: No existe Topic con ese nombre.
        """
        ...

    def find_all(self) -> list[Topic]:
        """Retorna todos los topics registrados.

        Returns:
            Lista de topics (puede estar vacía).
        """
        ...

    def find_active(self) -> list[Topic]:
        """Retorna solo los topics activos (is_active = True).

        Returns:
            Lista de topics activos (puede estar vacía).
        """
        ...

    def exists_by_name(self, name: str) -> bool:
        """Verifica si existe un Topic con el nombre dado.

        Args:
            name: Nombre a verificar.

        Returns:
            True si existe un Topic con ese nombre.
            False si no existe.

        Uso típico: Validación de I-23 (nombre único).
        """
        ...
```

---

## 7. Resumen de Métodos y Errores

### 7.1 Tabla Completa

| Repositorio | Método | Retorna | Error(es) |
|-------------|--------|---------|-----------|
| **NewsSourceRepository** | `save(source)` | `None` | — |
| | `find_by_id(id)` | `Result[NewsSource]` | `NEWS_SOURCE_NOT_FOUND` |
| | `find_by_name(name)` | `Result[NewsSource]` | `NEWS_SOURCE_NOT_FOUND` |
| | `find_all()` | `list[NewsSource]` | — |
| | `find_active()` | `list[NewsSource]` | — |
| | `exists_by_name(name)` | `bool` | — |
| **FeedRepository** | `save(feed)` | `None` | — |
| | `find_by_id(id)` | `Result[Feed]` | `FEED_NOT_FOUND` |
| | `find_by_source(source_id)` | `list[Feed]` | — |
| | `find_by_url(source_id, url)` | `Result[Feed]` | `FEED_NOT_FOUND` |
| | `find_active_by_source(source_id)` | `list[Feed]` | — |
| | `exists_by_source_and_url(source_id, url)` | `bool` | — |
| | `count_active_by_source(source_id)` | `int` | — |
| **RawArticleRepository** | `save(article)` | `None` | `DUPLICATE_ARTICLE` |
| | `save_batch(articles)` | `None` | `DUPLICATE_ARTICLE` |
| | `find_by_id(id)` | `Result[RawArticle]` | `RAW_ARTICLE_NOT_FOUND` |
| | `find_by_feed(feed_id, page, size)` | `list[RawArticle]` | — |
| | `find_by_hash(feed_id, hash)` | `Result[RawArticle]` | `RAW_ARTICLE_NOT_FOUND` |
| | `exists_by_url(feed_id, url)` | `bool` | — |
| | `exists_by_hash(feed_id, hash)` | `bool` | — |
| | `count_by_feed(feed_id)` | `int` | — |
| **CategoryRepository** | `save(category)` | `None` | — |
| | `find_by_id(id)` | `Result[Category]` | `CATEGORY_NOT_FOUND` |
| | `find_by_slug(slug)` | `Result[Category]` | `CATEGORY_NOT_FOUND` |
| | `find_all()` | `list[Category]` | — |
| | `find_active()` | `list[Category]` | — |
| | `find_by_parent(parent_id)` | `list[Category]` | — |
| | `exists_by_slug(slug)` | `bool` | — |
| **TopicRepository** | `save(topic)` | `None` | — |
| | `find_by_id(id)` | `Result[Topic]` | `TOPIC_NOT_FOUND` |
| | `find_by_name(name)` | `Result[Topic]` | `TOPIC_NOT_FOUND` |
| | `find_all()` | `list[Topic]` | — |
| | `find_active()` | `list[Topic]` | — |
| | `exists_by_name(name)` | `bool` | — |

### 7.2 Errores por Frecuencia de Uso

| Código | Repositorio(s) | Frecuencia esperada |
|--------|----------------|---------------------|
| `NEWS_SOURCE_NOT_FOUND` | NewsSourceRepository | Baja (configuración) |
| `FEED_NOT_FOUND` | FeedRepository | Baja (configuración) |
| `RAW_ARTICLE_NOT_FOUND` | RawArticleRepository | Media (fetch puede fallar) |
| `CATEGORY_NOT_FOUND` | CategoryRepository | Baja (configuración) |
| `TOPIC_NOT_FOUND` | TopicRepository | Baja (configuración) |
| `DUPLICATE_ARTICLE` | RawArticleRepository | Media (fetch puede incluir duplicados) |

### 7.3 Consideraciones de Implementación (futuras)

| Aspecto | Nota |
|---------|------|
| **Transaccionalidad** | `RawArticleRepository.save_batch()` debe ser atómico. Si el medio de persistencia no soporta transacciones, el repositorio debe implementar compensación o fallar completamente. |
| **Paginación** | `RawArticleRepository.find_by_feed()` con page/size. El repositorio debe soportar paginación eficiente (LIMIT/OFFSET o cursor-based). |
| **Optimistic Lock** | Todos los `save()` de ARs mutables (NewsSource, Feed, Category, Topic) deben soportar optimistic locking. RawArticle (inmutable) no lo necesita. |
| **Consistencia de unicidad** | Las constraints de unicidad (slug, nombre, url+source, external_id+feed) deben ser enforced a nivel BD, no solo en aplicación. |
