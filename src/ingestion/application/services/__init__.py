"""
Application Services — Casos de uso del BC Ingestion.

Contiene los 3 servicios que orquestan toda la lógica de aplicación:
    - SourceService: CRUD y estado de NewsSource.
    - FeedService: CRUD, estado y fetch de Feed.
    - ArticleService: Creación y consulta de RawArticle.

Cada servicio recibe sus dependencias (repositorios, puertos) por inyección
en el constructor. NO instancian nada directamente (DIP).

Uso::

    from ingestion.application.services import SourceService

    service = SourceService(
        source_repo=my_source_repo,
        feed_repo=my_feed_repo,
        category_repo=my_category_repo,
        topic_repo=my_topic_repo,
        uow=my_uow,
        event_publisher=my_publisher,
        clock=my_clock,
        uuid_provider=my_uuid_provider,
    )
    result = service.execute_register_source(cmd)
"""

from __future__ import annotations

from ingestion.application.services.article_service import ArticleService
from ingestion.application.services.feed_service import FeedService
from ingestion.application.services.source_service import SourceService

__all__ = [
    "ArticleService",
    "FeedService",
    "SourceService",
]
