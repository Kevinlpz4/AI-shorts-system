"""
Repository Ports for the Ingestion Bounded Context.

All repositories are ``Protocol`` (structural typing). Any class that implements
the methods with the correct signatures is automatically a valid repository.

Principles:
  1. Protocols, not ABCs.
  2. No technology mentioned (no SQL, no Redis, no async).
  3. Methods use domain types (entity objects, VOs, IDs), not primitives.
  4. ``Result[T]`` for operations that can fail (find_by_*).
  5. ``list[T]`` for operations that may return empty (find_all, find_active).
  6. ``bool`` for existence checks (exists_by_*).
  7. Each Aggregate Root has its own repository.
  8. ``save()`` receives the full entity (no partial updates).
"""

from __future__ import annotations

from typing import Protocol

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


class NewsSourceRepository(Protocol):
    """Puerto de persistencia para NewsSource (Aggregate Root)."""

    def save(self, source: NewsSource) -> None:
        """Persiste un NewsSource (crea o actualiza)."""
        ...

    def find_by_id(self, id: SourceId) -> Result[NewsSource]:
        """Busca un NewsSource por su identidad única.

        Returns:
            Ok(NewsSource) si se encuentra.
            Error(NEWS_SOURCE_NOT_FOUND) si no existe.
        """
        ...

    def find_by_name(self, name: str) -> Result[NewsSource]:
        """Busca un NewsSource por su nombre único.

        Returns:
            Ok(NewsSource) si se encuentra.
            Error(NEWS_SOURCE_NOT_FOUND) si no existe.
        """
        ...

    def find_all(self) -> list[NewsSource]:
        """Retorna todos los NewsSources registrados."""
        ...

    def find_active(self) -> list[NewsSource]:
        """Retorna solo los NewsSources activos (is_active=True)."""
        ...

    def exists_by_name(self, name: str) -> bool:
        """Verifica si existe un NewsSource con el nombre dado."""
        ...


class FeedRepository(Protocol):
    """Puerto de persistencia para Feed (Aggregate Root)."""

    def save(self, feed: Feed) -> None:
        """Persiste un Feed (crea o actualiza)."""
        ...

    def find_by_id(self, id: FeedId) -> Result[Feed]:
        """Busca un Feed por su identidad única.

        Returns:
            Ok(Feed) si se encuentra.
            Error(FEED_NOT_FOUND) si no existe.
        """
        ...

    def find_by_source(self, source_id: SourceId) -> list[Feed]:
        """Retorna todos los Feeds de un NewsSource."""
        ...

    def find_by_url(self, source_id: SourceId, url: ArticleUrl) -> Result[Feed]:
        """Busca un Feed por URL dentro de un NewsSource.

        Returns:
            Ok(Feed) si se encuentra.
            Error(FEED_NOT_FOUND) si no existe.
        """
        ...

    def find_active_by_source(self, source_id: SourceId) -> list[Feed]:
        """Retorna los Feeds activos de un NewsSource."""
        ...

    def exists_by_source_and_url(
        self, source_id: SourceId, url: ArticleUrl
    ) -> bool:
        """Verifica si existe un Feed con esa URL en el NewsSource."""
        ...

    def count_active_by_source(self, source_id: SourceId) -> int:
        """Cuenta los Feeds activos de un NewsSource."""
        ...


class RawArticleRepository(Protocol):
    """Puerto de persistencia para RawArticle (Aggregate Root, Inmutable)."""

    def save(self, article: RawArticle) -> None:
        """Persiste un RawArticle (siempre es creación, nunca actualización).

        Puede fallar con DUPLICATE_ARTICLE si ya existe con mismo
        external_id+feed_id o content_hash+feed_id.
        """
        ...

    def save_batch(self, articles: list[RawArticle]) -> None:
        """Persiste múltiples RawArticles en una operación atómica."""
        ...

    def find_by_id(self, id: RawArticleId) -> Result[RawArticle]:
        """Busca un RawArticle por su identidad única.

        Returns:
            Ok(RawArticle) si se encuentra.
            Error(RAW_ARTICLE_NOT_FOUND) si no existe.
        """
        ...

    def find_by_feed(
        self, feed_id: FeedId, page: int = 1, size: int = 50
    ) -> list[RawArticle]:
        """Retorna RawArticles de un Feed con paginación."""
        ...

    def find_by_hash(
        self, feed_id: FeedId, content_hash: str
    ) -> Result[RawArticle]:
        """Busca un RawArticle por su content_hash dentro de un Feed.

        Returns:
            Ok(RawArticle) si se encuentra.
            Error(RAW_ARTICLE_NOT_FOUND) si no existe.
        """
        ...

    def exists_by_url(self, feed_id: FeedId, url: ArticleUrl) -> bool:
        """Verifica si existe un RawArticle con esa URL en el Feed."""
        ...

    def exists_by_hash(self, feed_id: FeedId, content_hash: str) -> bool:
        """Verifica si existe un RawArticle con ese hash en el Feed."""
        ...

    def count_by_feed(self, feed_id: FeedId) -> int:
        """Retorna la cantidad total de RawArticles de un Feed."""
        ...


class CategoryRepository(Protocol):
    """Puerto de persistencia para Category (Entity)."""

    def save(self, category: Category) -> None:
        """Persiste una Category (crea o actualiza)."""
        ...

    def find_by_id(self, id: CategoryId) -> Result[Category]:
        """Busca una Category por su identidad única.

        Returns:
            Ok(Category) si se encuentra.
            Error(CATEGORY_NOT_FOUND) si no existe.
        """
        ...

    def find_by_slug(self, slug: str) -> Result[Category]:
        """Busca una Category por su slug único.

        Returns:
            Ok(Category) si se encuentra.
            Error(CATEGORY_NOT_FOUND) si no existe.
        """
        ...

    def find_all(self) -> list[Category]:
        """Retorna todas las categorías registradas."""
        ...

    def find_active(self) -> list[Category]:
        """Retorna solo las categorías activas (is_active=True)."""
        ...

    def find_by_parent(self, parent_id: CategoryId) -> list[Category]:
        """Retorna las subcategorías directas de una categoría."""
        ...

    def exists_by_slug(self, slug: str) -> bool:
        """Verifica si existe una categoría con el slug dado."""
        ...


class TopicRepository(Protocol):
    """Puerto de persistencia para Topic (Entity)."""

    def save(self, topic: Topic) -> None:
        """Persiste un Topic (crea o actualiza)."""
        ...

    def find_by_id(self, id: TopicId) -> Result[Topic]:
        """Busca un Topic por su identidad única.

        Returns:
            Ok(Topic) si se encuentra.
            Error(TOPIC_NOT_FOUND) si no existe.
        """
        ...

    def find_by_name(self, name: str) -> Result[Topic]:
        """Busca un Topic por su nombre único.

        Returns:
            Ok(Topic) si se encuentra.
            Error(TOPIC_NOT_FOUND) si no existe.
        """
        ...

    def find_all(self) -> list[Topic]:
        """Retorna todos los topics registrados."""
        ...

    def find_active(self) -> list[Topic]:
        """Retorna solo los topics activos (is_active=True)."""
        ...

    def exists_by_name(self, name: str) -> bool:
        """Verifica si existe un Topic con el nombre dado."""
        ...
