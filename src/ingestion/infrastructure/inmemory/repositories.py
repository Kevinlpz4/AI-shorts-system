"""
In-memory repository implementations for the Ingestion Bounded Context.

All repositories use ``dict[str, Entity]`` as their storage, keyed by
``str(entity.id)``. They implement the corresponding repository Protocols
defined in ``ingestion.domain.ports.repositories``.

These implementations are:
    - Deterministic: no external dependencies.
    - Not thread-safe: no locking or atomic operations.
    - Volatile: data is lost when the process exits.
    - LSP-compliant: they behave identically to the SQLAlchemy implementations
      in terms of exceptions, uniqueness checks, and atomicity guarantees.
"""

from __future__ import annotations

from foundation.result.result import Error, Result

from ingestion.domain.entities.category import Category
from ingestion.domain.entities.feed import Feed
from ingestion.domain.entities.ids import (
    CategoryId,
    FeedId,
    RawArticleId,
    SourceId,
    TopicId,
)
from ingestion.domain.entities.news_source import NewsSource
from ingestion.domain.entities.raw_article import RawArticle
from ingestion.domain.entities.topic import Topic
from ingestion.domain.exceptions.errors import IngestionErrorCode
from ingestion.domain.value_objects.article_url import ArticleUrl
from ingestion.infrastructure.persistence.exceptions import DuplicateEntityError


class InMemoryNewsSourceRepository:
    """In-memory store for ``NewsSource`` aggregate roots.

    Stores sources in a ``dict[str, NewsSource]`` keyed by ``str(source.id)``.
    """

    def __init__(self) -> None:
        self._sources: dict[str, NewsSource] = {}

    def save(self, source: NewsSource) -> None:
        """Persiste un NewsSource (crea o actualiza).

        Raises:
            DuplicateEntityError: Si ya existe otro source con el mismo nombre.
        """
        # LSP: validar unicidad de name (excluyéndonos en update)
        for sid, existing in self._sources.items():
            if existing.name == source.name and sid != str(source.id):
                raise DuplicateEntityError(
                    "NewsSource", "name", source.name,
                )
        self._sources[str(source.id)] = source

    def find_by_id(self, id: SourceId) -> Result[NewsSource]:
        """Busca un NewsSource por su identidad única."""
        source = self._sources.get(str(id))
        if source is None:
            return Result.failure(
                Error(
                    code=IngestionErrorCode.NEWS_SOURCE_NOT_FOUND,
                    message=f"Source '{id}' not found",
                )
            )
        return Result.success(source)

    def find_by_name(self, name: str) -> Result[NewsSource]:
        """Busca un NewsSource por su nombre único."""
        for s in self._sources.values():
            if s.name == name:
                return Result.success(s)
        return Result.failure(
            Error(
                code=IngestionErrorCode.NEWS_SOURCE_NOT_FOUND,
                message=f"Source '{name}' not found",
            )
        )

    def find_all(self) -> list[NewsSource]:
        """Retorna todos los NewsSources registrados."""
        return list(self._sources.values())

    def find_active(self) -> list[NewsSource]:
        """Retorna solo los NewsSources activos (is_active=True)."""
        return [s for s in self._sources.values() if s.is_active]

    def exists_by_name(self, name: str) -> bool:
        """Verifica si existe un NewsSource con el nombre dado."""
        return any(s.name == name for s in self._sources.values())


class InMemoryFeedRepository:
    """In-memory store for ``Feed`` aggregate roots.

    Stores feeds in a ``dict[str, Feed]`` keyed by ``str(feed.id)``.
    """

    def __init__(self) -> None:
        self._feeds: dict[str, Feed] = {}

    def save(self, feed: Feed) -> None:
        """Persiste un Feed (crea o actualiza).

        Raises:
            DuplicateEntityError: Si ya existe otro feed con el mismo
                source_id+url.
        """
        # LSP: validar unicidad de (source_id, url) — excluyéndonos en update
        for fid, existing in self._feeds.items():
            if (
                existing.source_id == feed.source_id
                and existing.url == feed.url
                and fid != str(feed.id)
            ):
                raise DuplicateEntityError(
                    "Feed", "source_id+url",
                    f"{feed.source_id}+{feed.url}",
                )
        self._feeds[str(feed.id)] = feed

    def find_by_id(self, id: FeedId) -> Result[Feed]:
        """Busca un Feed por su identidad única."""
        feed = self._feeds.get(str(id))
        if feed is None:
            return Result.failure(
                Error(
                    code=IngestionErrorCode.FEED_NOT_FOUND,
                    message=f"Feed '{id}' not found",
                )
            )
        return Result.success(feed)

    def find_by_source(self, source_id: SourceId) -> list[Feed]:
        """Retorna todos los Feeds de un NewsSource."""
        return [f for f in self._feeds.values() if f.source_id == source_id]

    def find_by_url(self, source_id: SourceId, url: ArticleUrl) -> Result[Feed]:
        """Busca un Feed por URL dentro de un NewsSource.

        Comparación por identidad de SourceId (__eq__) y valor de ArticleUrl.
        """
        for f in self._feeds.values():
            if f.source_id == source_id and f.url == url:
                return Result.success(f)
        return Result.failure(
            Error(
                code=IngestionErrorCode.FEED_NOT_FOUND,
                message="Feed not found",
            )
        )

    def find_active_by_source(self, source_id: SourceId) -> list[Feed]:
        """Retorna los Feeds activos de un NewsSource."""
        return [
            f
            for f in self._feeds.values()
            if f.source_id == source_id and f.is_active
        ]

    def exists_by_source_and_url(
        self, source_id: SourceId, url: ArticleUrl
    ) -> bool:
        """Verifica si existe un Feed con esa URL en el NewsSource."""
        return any(
            f.source_id == source_id and f.url == url
            for f in self._feeds.values()
        )

    def count_active_by_source(self, source_id: SourceId) -> int:
        """Cuenta los Feeds activos de un NewsSource."""
        return sum(
            1
            for f in self._feeds.values()
            if f.source_id == source_id and f.is_active
        )


class InMemoryRawArticleRepository:
    """In-memory store for ``RawArticle`` (inmutable) entities.

    Stores articles in a ``dict[str, RawArticle]`` keyed by ``str(article.id)``.

    LSP: comportamiento idéntico a SQLAlchemyRawArticleRepository:
    - ``save()`` y ``save_batch()`` lanzan ``DuplicateEntityError`` si se
      viola una constraint de unicidad.
    - ``save_batch()`` es atómico: o se guardan TODOS o NINGUNO.
    """

    def __init__(self) -> None:
        self._articles: dict[str, RawArticle] = {}

    def _check_duplicate(self, article: RawArticle) -> None:
        """Verifica si el artículo viola alguna constraint de unicidad.

        Raises:
            DuplicateEntityError: Si ya existe con mismo external_id+feed_id
                o content_hash+feed_id.
        """
        for existing in self._articles.values():
            if (
                existing.feed_id == article.feed_id
                and existing.external_id == article.external_id
            ):
                raise DuplicateEntityError(
                    "RawArticle",
                    "external_id/content_hash",
                    f"{article.external_id}/{article.content_hash}",
                )
            if (
                existing.feed_id == article.feed_id
                and existing.content_hash == article.content_hash
            ):
                raise DuplicateEntityError(
                    "RawArticle",
                    "external_id/content_hash",
                    f"{article.external_id}/{article.content_hash}",
                )

    def save(self, article: RawArticle) -> None:
        """Persiste un RawArticle (siempre es creación).

        Raises:
            DuplicateEntityError: Si ya existe un artículo con el mismo
                external_id+feed_id o content_hash+feed_id.
        """
        self._check_duplicate(article)
        self._articles[str(article.id)] = article

    def save_batch(self, articles: list[RawArticle]) -> None:
        """Persiste múltiples RawArticles atómicamente.

        LSP: O todos se guardan o ninguno. Validación previa a la inserción
        para garantizar atomicidad, análogo a SQLAlchemy que falla todo
        el batch en el primer IntegrityError durante flush().

        Raises:
            DuplicateEntityError: Si algún artículo es duplicado.
        """
        # Fase 1: validación atómica (si algo falla, nada se persiste)
        for article in articles:
            self._check_duplicate(article)
        # Fase 2: inserción (todos son válidos)
        for article in articles:
            self._articles[str(article.id)] = article

    def find_by_id(self, id: RawArticleId) -> Result[RawArticle]:
        """Busca un RawArticle por su identidad única."""
        article = self._articles.get(str(id))
        if article is None:
            return Result.failure(
                Error(
                    code=IngestionErrorCode.RAW_ARTICLE_NOT_FOUND,
                    message=f"Article '{id}' not found",
                )
            )
        return Result.success(article)

    def find_by_feed(
        self, feed_id: FeedId, page: int = 1, size: int = 50
    ) -> list[RawArticle]:
        """Retorna RawArticles de un Feed con paginación."""
        articles = [
            a for a in self._articles.values() if a.feed_id == feed_id
        ]
        start = (page - 1) * size
        return articles[start : start + size]

    def find_by_hash(
        self, feed_id: FeedId, content_hash: str
    ) -> Result[RawArticle]:
        """Busca un RawArticle por su content_hash dentro de un Feed."""
        for a in self._articles.values():
            if a.feed_id == feed_id and a.content_hash == content_hash:
                return Result.success(a)
        return Result.failure(
            Error(
                code=IngestionErrorCode.RAW_ARTICLE_NOT_FOUND,
                message="Article not found",
            )
        )

    def exists_by_url(self, feed_id: FeedId, url: ArticleUrl) -> bool:
        """Verifica si existe un RawArticle con esa URL en el Feed."""
        return any(
            a.feed_id == feed_id and a.url == url
            for a in self._articles.values()
        )

    def exists_by_hash(self, feed_id: FeedId, content_hash: str) -> bool:
        """Verifica si existe un RawArticle con ese hash en el Feed."""
        return any(
            a.feed_id == feed_id and a.content_hash == content_hash
            for a in self._articles.values()
        )

    def count_by_feed(self, feed_id: FeedId) -> int:
        """Retorna la cantidad total de RawArticles de un Feed."""
        return sum(
            1 for a in self._articles.values() if a.feed_id == feed_id
        )


class InMemoryCategoryRepository:
    """In-memory store for ``Category`` entities.

    Stores categories in a ``dict[str, Category]`` keyed by
    ``str(category.id)``.
    """

    def __init__(self) -> None:
        self._categories: dict[str, Category] = {}

    def save(self, category: Category) -> None:
        """Persiste una Category (crea o actualiza).

        Raises:
            DuplicateEntityError: Si ya existe otra categoría con el mismo slug.
        """
        # LSP: validar unicidad de slug (excluyéndonos en update)
        for cid, existing in self._categories.items():
            if existing.slug == category.slug and cid != str(category.id):
                raise DuplicateEntityError(
                    "Category", "slug", category.slug or "",
                )
        self._categories[str(category.id)] = category

    def find_by_id(self, id: CategoryId) -> Result[Category]:
        """Busca una Category por su identidad única."""
        cat = self._categories.get(str(id))
        if cat is None:
            return Result.failure(
                Error(
                    code=IngestionErrorCode.CATEGORY_NOT_FOUND,
                    message=f"Category '{id}' not found",
                )
            )
        return Result.success(cat)

    def find_by_slug(self, slug: str) -> Result[Category]:
        """Busca una Category por su slug único."""
        for cat in self._categories.values():
            if cat.slug == slug:
                return Result.success(cat)
        return Result.failure(
            Error(
                code=IngestionErrorCode.CATEGORY_NOT_FOUND,
                message=f"Category with slug '{slug}' not found",
            )
        )

    def find_all(self) -> list[Category]:
        """Retorna todas las categorías registradas."""
        return list(self._categories.values())

    def find_active(self) -> list[Category]:
        """Retorna solo las categorías activas (is_active=True)."""
        return [
            cat for cat in self._categories.values() if cat.is_active
        ]

    def find_by_parent(self, parent_id: CategoryId) -> list[Category]:
        """Retorna las subcategorías directas de una categoría."""
        return [
            cat
            for cat in self._categories.values()
            if cat.parent_id == parent_id
        ]

    def exists_by_slug(self, slug: str) -> bool:
        """Verifica si existe una categoría con el slug dado."""
        return any(cat.slug == slug for cat in self._categories.values())


class InMemoryTopicRepository:
    """In-memory store for ``Topic`` entities.

    Stores topics in a ``dict[str, Topic]`` keyed by ``str(topic.id)``.
    """

    def __init__(self) -> None:
        self._topics: dict[str, Topic] = {}

    def save(self, topic: Topic) -> None:
        """Persiste un Topic (crea o actualiza).

        Raises:
            DuplicateEntityError: Si ya existe otro topic con el mismo nombre.
        """
        # LSP: validar unicidad de name (excluyéndonos en update)
        for tid, existing in self._topics.items():
            if existing.name == topic.name and tid != str(topic.id):
                raise DuplicateEntityError(
                    "Topic", "name", topic.name,
                )
        self._topics[str(topic.id)] = topic

    def find_by_id(self, id: TopicId) -> Result[Topic]:
        """Busca un Topic por su identidad única."""
        topic = self._topics.get(str(id))
        if topic is None:
            return Result.failure(
                Error(
                    code=IngestionErrorCode.TOPIC_NOT_FOUND,
                    message=f"Topic '{id}' not found",
                )
            )
        return Result.success(topic)

    def find_by_name(self, name: str) -> Result[Topic]:
        """Busca un Topic por su nombre único."""
        for topic in self._topics.values():
            if topic.name == name:
                return Result.success(topic)
        return Result.failure(
            Error(
                code=IngestionErrorCode.TOPIC_NOT_FOUND,
                message=f"Topic '{name}' not found",
            )
        )

    def find_all(self) -> list[Topic]:
        """Retorna todos los topics registrados."""
        return list(self._topics.values())

    def find_active(self) -> list[Topic]:
        """Retorna solo los topics activos (is_active=True)."""
        return [
            topic for topic in self._topics.values() if topic.is_active
        ]

    def exists_by_name(self, name: str) -> bool:
        """Verifica si existe un Topic con el nombre dado."""
        return any(
            topic.name == name for topic in self._topics.values()
        )
