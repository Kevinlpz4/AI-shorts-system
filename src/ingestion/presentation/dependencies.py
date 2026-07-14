"""
Dependency Injection — FastAPI native ``Depends()`` providers.

Lifetimes:
    - **Singleton**: Settings, Engine, SessionFactory (stored on ``app.state``).
    - **Scoped (generator)**: UoW per-request (yields, auto-rollback on exception).
    - **Transient**: Application Services, Clock, UUIDProvider per call.

Key design decision: Repos come from ``uow.news_sources`` etc., NOT from
separate providers. This ensures repos share the same session as the UoW.

Usage::

    @router.post("/sources")
    async def register_source(
        cmd: RegisterSourceRequest,
        service: SourceService = Depends(get_source_service),
    ):
        result = await run_sync(service.execute_register_source, cmd.to_command())
        ...
"""

from __future__ import annotations

from typing import Generator

from fastapi import Depends, Request
from sqlalchemy.orm import sessionmaker

from foundation.ports.clock import SystemClock
from foundation.ports.uuid_provider import SystemUUIDProvider
from ingestion.presentation.config import Settings
from ingestion.application.ports.event_publisher import EventPublisher
from ingestion.application.services.article_service import ArticleService
from ingestion.application.services.category_service import CategoryService
from ingestion.application.services.feed_service import FeedService
from ingestion.application.services.source_service import SourceService
from ingestion.application.services.topic_service import TopicService
from ingestion.infrastructure.event_publisher import SQLAlchemyEventPublisher
from ingestion.infrastructure.persistence.unit_of_work import (
    SQLAlchemyUnitOfWork,
)


# ══════════════════════════════════════════════════════════════════════════════
# Singleton Providers (from app.state)
# ══════════════════════════════════════════════════════════════════════════════


def get_settings(request: Request) -> Settings:
    """Retrieve Settings singleton from app.state.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The Settings instance stored on app.state.
    """
    return request.app.state.settings


def get_session_factory(request: Request) -> sessionmaker:
    """Retrieve sessionmaker from app.state.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The sessionmaker stored on app.state.
    """
    return request.app.state.session_factory


# ══════════════════════════════════════════════════════════════════════════════
# Scoped Providers (per-request)
# ══════════════════════════════════════════════════════════════════════════════


def get_event_publisher() -> EventPublisher:
    """Create a new EventPublisher per call.

    Returns:
        SQLAlchemyEventPublisher instance.
    """
    return SQLAlchemyEventPublisher()


def get_uow(
    session_factory: sessionmaker = Depends(get_session_factory),
    event_publisher: EventPublisher = Depends(get_event_publisher),
) -> Generator[SQLAlchemyUnitOfWork, None, None]:
    """Create and manage a UnitOfWork per request.

    Lifecycle:
        1. Create SQLAlchemyUnitOfWork with session_factory and event_publisher.
        2. Enter the UoW context (opens session, creates repos).
        3. Yield the UoW for use in handlers.
        4. On exit: close session. If handler raised, rollback first.

    Args:
        session_factory: SQLAlchemy sessionmaker (from app.state).
        event_publisher: EventPublisher instance.

    Yields:
        The active SQLAlchemyUnitOfWork instance.
    """
    uow = SQLAlchemyUnitOfWork(
        session_factory=session_factory,
        event_publisher=event_publisher,
    )
    with uow:
        yield uow


# ══════════════════════════════════════════════════════════════════════════════
# Transient Providers (per-call)
# ══════════════════════════════════════════════════════════════════════════════


def get_clock() -> SystemClock:
    """Create a new SystemClock per call.

    Returns:
        SystemClock instance.
    """
    return SystemClock()


def get_uuid_provider() -> SystemUUIDProvider:
    """Create a new SystemUUIDProvider per call.

    Returns:
        SystemUUIDProvider instance.
    """
    return SystemUUIDProvider()


# ══════════════════════════════════════════════════════════════════════════════
# Service Factories (per-request, depend on scoped UoW)
# ══════════════════════════════════════════════════════════════════════════════


def get_source_service(
    uow: SQLAlchemyUnitOfWork = Depends(get_uow),
    clock: SystemClock = Depends(get_clock),
    uuid_provider: SystemUUIDProvider = Depends(get_uuid_provider),
) -> SourceService:
    """Create SourceService with repos from UoW.

    Repos come from ``uow.news_sources`` etc., ensuring they share
    the same session as the UoW.

    Args:
        uow: The active SQLAlchemyUnitOfWork.
        clock: ClockPort implementation.
        uuid_provider: UUIDProvider implementation.

    Returns:
        Configured SourceService instance.
    """
    # Access _event_publisher from the concrete UoW
    event_publisher = uow._event_publisher
    return SourceService(
        source_repo=uow.news_sources,
        feed_repo=uow.feeds,
        category_repo=uow.categories,
        topic_repo=uow.topics,
        uow=uow,
        event_publisher=event_publisher,
        clock=clock,
        uuid_provider=uuid_provider,
    )


def get_feed_service(
    uow: SQLAlchemyUnitOfWork = Depends(get_uow),
    clock: SystemClock = Depends(get_clock),
    uuid_provider: SystemUUIDProvider = Depends(get_uuid_provider),
) -> FeedService:
    """Create FeedService with repos from UoW.

    Args:
        uow: The active SQLAlchemyUnitOfWork.
        clock: ClockPort implementation.
        uuid_provider: UUIDProvider implementation.

    Returns:
        Configured FeedService instance.
    """
    event_publisher = uow._event_publisher
    return FeedService(
        feed_repo=uow.feeds,
        source_repo=uow.news_sources,
        category_repo=uow.categories,
        topic_repo=uow.topics,
        uow=uow,
        event_publisher=event_publisher,
        clock=clock,
        uuid_provider=uuid_provider,
    )


def get_article_service(
    uow: SQLAlchemyUnitOfWork = Depends(get_uow),
    clock: SystemClock = Depends(get_clock),
    uuid_provider: SystemUUIDProvider = Depends(get_uuid_provider),
) -> ArticleService:
    """Create ArticleService with repos from UoW.

    Args:
        uow: The active SQLAlchemyUnitOfWork.
        clock: ClockPort implementation.
        uuid_provider: UUIDProvider implementation.

    Returns:
        Configured ArticleService instance.
    """
    event_publisher = uow._event_publisher
    return ArticleService(
        raw_article_repo=uow.raw_articles,
        feed_repo=uow.feeds,
        uow=uow,
        event_publisher=event_publisher,
        clock=clock,
        uuid_provider=uuid_provider,
    )


def get_category_service(
    uow: SQLAlchemyUnitOfWork = Depends(get_uow),
    clock: SystemClock = Depends(get_clock),
    uuid_provider: SystemUUIDProvider = Depends(get_uuid_provider),
) -> CategoryService:
    """Create CategoryService with repos from UoW.

    Args:
        uow: The active SQLAlchemyUnitOfWork.
        clock: ClockPort implementation.
        uuid_provider: UUIDProvider implementation.

    Returns:
        Configured CategoryService instance.
    """
    event_publisher = uow._event_publisher
    return CategoryService(
        category_repo=uow.categories,
        uow=uow,
        event_publisher=event_publisher,
        clock=clock,
        uuid_provider=uuid_provider,
    )


def get_topic_service(
    uow: SQLAlchemyUnitOfWork = Depends(get_uow),
    clock: SystemClock = Depends(get_clock),
    uuid_provider: SystemUUIDProvider = Depends(get_uuid_provider),
) -> TopicService:
    """Create TopicService with repos from UoW.

    Args:
        uow: The active SQLAlchemyUnitOfWork.
        clock: ClockPort implementation.
        uuid_provider: UUIDProvider implementation.

    Returns:
        Configured TopicService instance.
    """
    event_publisher = uow._event_publisher
    return TopicService(
        topic_repo=uow.topics,
        uow=uow,
        event_publisher=event_publisher,
        clock=clock,
        uuid_provider=uuid_provider,
    )
