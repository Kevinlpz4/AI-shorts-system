# Design: Composition Root

**Epic**: 6 — Presentation Layer & External Adapters Design
**Version**: 1.0
**Decisions**: D2 (Composition Root — Pythonic)

---

## 1. Overview

The Composition Root is where all concrete implementations are wired together. In Python/FastAPI, this happens through factory functions and dependency injection — NOT a monolithic IoC container.

## 2. Wiring Chain

```
Settings (pydantic-settings)
    │
    ▼
Engine (SQLAlchemy, singleton)
    │
    ▼
SessionFactory (SQLAlchemy sessionmaker, singleton)
    │
    ├──▶ SQLAlchemyNewsSourceRepository(session)
    ├──▶ SQLAlchemyFeedRepository(session)
    ├──▶ SQLAlchemyRawArticleRepository(session)
    ├──▶ SQLAlchemyCategoryRepository(session)
    └──▶ SQLAlchemyTopicRepository(session)
    │
    ▼
SQLAlchemyUnitOfWork(session_factory, event_publisher)
    │
    ├──▶ .news_sources
    ├──▶ .feeds
    ├──▶ .raw_articles
    ├──▶ .categories
    └──▶ .topics
    │
    ▼
SourceService(source_repo, feed_repo, category_repo, topic_repo, uow, event_publisher, clock, uuid_provider)
FeedService(feed_repo, source_repo, category_repo, topic_repo, uow, event_publisher, clock, uuid_provider)
ArticleService(raw_article_repo, feed_repo, uow, event_publisher, clock, uuid_provider)
    │
    ▼
FastAPI Routers (via Depends())
```

## 3. Files

| File | Role | Content |
|------|------|---------|
| `main.py` | App factory | `create_app()` → FastAPI instance |
| `lifespan.py` | Lifecycle | Engine + SessionFactory creation/disposal |
| `dependencies.py` | DI functions | `get_uow()`, `get_source_repo()`, etc. |
| `providers.py` | Factories | `create_source_service()`, etc. |

## 4. main.py

```python
# main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager

from .lifespan import lifespan
from .routers import sources, feeds, articles, categories, topics, system
from .exceptions.handlers import register_exception_handlers
from .middleware import RequestIDMiddleware, CorrelationIDMiddleware, TimingMiddleware

def create_app() -> FastAPI:
    """Application factory. Creates configured FastAPI instance."""
    app = FastAPI(
        title="AI Shorts System — Ingestion API",
        description="News ingestion bounded context API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── API v1 ──
    api_v1 = APIRouter(prefix="/api/v1")
    api_v1.include_router(sources.router)
    api_v1.include_router(feeds.router)       # flat: /feeds/*
    api_v1.include_router(articles.router)
    api_v1.include_router(categories.router)
    api_v1.include_router(topics.router)
    api_v1.include_router(system.info_router)
    app.include_router(api_v1)

    # ── Health (outside /api/v1) ──
    app.include_router(system.health_router)

    # ── Middleware ──
    app.add_middleware(TimingMiddleware)
    app.add_middleware(CorrelationIDMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # ── Exception handlers ──
    register_exception_handlers(app)

    return app
```

## 5. UoW Lifecycle in DI

The critical insight: UoW is a context manager. In FastAPI DI, we use a generator dependency:

```python
# dependencies.py
from typing import Generator

def get_uow(request: Request) -> Generator[SQLAlchemyUnitOfWork, None, None]:
    """Creates UoW for the request lifetime.

    The `with uow:` block is entered in __enter__ and exited in __exit__.
    If the handler raises, __exit__ does rollback automatically.
    """
    sf = request.app.state.session_factory
    uow = SQLAlchemyUnitOfWork(session_factory=sf)
    with uow:
        yield uow
    # __exit__ handles rollback on exception + session close
```

This means:
- Session is created at `__enter__` (start of request)
- Session is closed at `__exit__` (end of request, regardless of outcome)
- Rollback happens automatically if exception occurred

## 6. Service Construction

Services are NOT singletons. They're created per handler call (transient). This is fine because they're lightweight — just holding references.

```python
# providers.py
def create_source_service(
    source_repo: NewsSourceRepository,
    feed_repo: FeedRepository,
    category_repo: CategoryRepository,
    topic_repo: TopicRepository,
    uow: UnitOfWork,
    event_publisher: EventPublisher,
    clock: ClockPort,
    uuid_provider: UUIDProvider,
) -> SourceService:
    """Factory: creates SourceService with all dependencies."""
    return SourceService(
        source_repo=source_repo,
        feed_repo=feed_repo,
        category_repo=category_repo,
        topic_repo=topic_repo,
        uow=uow,
        event_publisher=event_publisher,
        clock=clock,
        uuid_provider=uuid_provider,
    )
```

## 7. No Modifications to Frozen Layers

The Composition Root wires existing components together. It does NOT:
- Modify any Application Service
- Modify any Repository
- Modify any Domain Entity
- Modify the UnitOfWork Protocol or implementation

It ONLY:
- Creates instances
- Passes them as constructor arguments
- Manages lifetimes via FastAPI DI

---

*See also: `dependency-injection.md`, `lifespan.py` design in `dependency-injection.md`*
