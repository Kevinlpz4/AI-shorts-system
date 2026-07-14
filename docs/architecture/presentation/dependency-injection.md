# Design: Dependency Injection

**Epic**: 6 — Presentation Layer & External Adapters Design
**Version**: 1.0
**Decisions**: D2 (Composition Root — Pythonic DI)

---

## 1. Approach

FastAPI's native dependency injection system (`Depends()`). NO external IoC container. Factory functions for all components. Each dependency is a generator (for UoW lifecycle management).

## 2. Files

| File | Responsibility |
|------|---------------|
| `dependencies.py` | Request-scoped dependency generators |
| `providers.py` | Factory functions creating service instances |
| `lifespan.py` | Startup/shutdown — Engine, SessionFactory creation |

## 3. Dependency Graph

```
┌─────────────────────────────────────────────────────┐
│                    Lifespan (Singleton)              │
│                                                     │
│  Settings ──▶ Engine ──▶ SessionFactory             │
│                                                     │
└─────────────────────────────────────────────────────┘
                        │
          ┌─────────────┼─────────────────────┐
          ▼             ▼                     ▼
  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
  │ dependencies  │ │ dependencies │ │  dependencies     │
  │ .py           │ │ .py          │ │  .py              │
  │               │ │              │ │                   │
  │ get_uow()     │ │ get_source_ │ │  get_event_       │
  │ (generator)   │ │ repo()       │ │  publisher()      │
  │               │ │ (scoped)     │ │  (scoped)         │
  └──────┬───────┘ └──────┬──────┘ └────────┬──────────┘
         │                │                  │
         └────────────────┼──────────────────┘
                          ▼
              ┌──────────────────────┐
              │     providers.py      │
              │                      │
              │  create_source_      │
              │  service(uow, repos) │
              │                      │
              │  create_feed_        │
              │  service(uow, repos) │
              │                      │
              │  create_article_     │
              │  service(uow, repos) │
              └──────────┬───────────┘
                         ▼
              ┌──────────────────────┐
              │     Router handlers   │
              │  (use Depends(get_*)) │
              └──────────────────────┘
```

## 4. Lifespan (Singletons)

```python
# lifespan.py
from contextlib import asynccontextmanager
from sqlalchemy.orm import sessionmaker

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create engine + session factory. Shutdown: dispose."""
    # Startup
    settings = get_settings()
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)

    # Store on app state for dependency access
    app.state.engine = engine
    app.state.session_factory = session_factory

    yield

    # Shutdown
    engine.dispose()
```

## 5. Dependencies (Request-scoped)

```python
# dependencies.py
from fastapi import Request

def get_session_factory(request: Request) -> sessionmaker:
    """Get session factory from app state (singleton)."""
    return request.app.state.session_factory

def get_uow(request: Request) -> Generator[SQLAlchemyUnitOfWork, None, None]:
    """Create UoW per request. Auto-rollback on exception."""
    sf = get_session_factory(request)
    uow = SQLAlchemyUnitOfWork(session_factory=sf)
    with uow:
        yield uow

def get_event_publisher(request: Request) -> EventPublisher:
    """Get event publisher (scoped to request)."""
    return InMemoryEventPublisher()  # or SQLAlchemyEventPublisher

def get_clock() -> ClockPort:
    return SystemClock()

def get_uuid_provider() -> UUIDProvider:
    return UUID4Provider()

# ── Repo access (scoped via UoW) ──

def get_source_repo(uow: SQLAlchemyUnitOfWork = Depends(get_uow)):
    return uow.news_sources

def get_feed_repo(uow: SQLAlchemyUnitOfWork = Depends(get_uow)):
    return uow.feeds

def get_article_repo(uow: SQLAlchemyUnitOfWork = Depends(get_uow)):
    return uow.raw_articles

def get_category_repo(uow: SQLAlchemyUnitOfWork = Depends(get_uow)):
    return uow.categories

def get_topic_repo(uow: SQLAlchemyUnitOfWork = Depends(get_uow)):
    return uow.topics
```

## 6. Providers (Factory Functions)

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

# Same pattern for FeedService, ArticleService
```

## 7. Router Usage

```python
# routers/sources.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/sources", tags=["Sources"])

@router.post("/", status_code=201)
async def register_source(
    body: CreateSourceRequest,
    source_service: SourceService = Depends(get_source_service),
):
    cmd = RegisterSourceCommand(
        name=body.name,
        source_type=body.source_type,
        source_url=body.source_url,
    )
    result = source_service.execute_register_source(cmd)
    return result  # FastAPI handles Result→Response mapping
```

## 8. Lifetime Management

| Component | Lifetime | Scope | Notes |
|-----------|----------|-------|-------|
| Settings | Singleton | App | Created once at startup |
| Engine | Singleton | App | Created once, reused |
| SessionFactory | Singleton | App | Created once, reused |
| UoW | Scoped | Request | Created per request, closed at end |
| Repos | Scoped | Request | Owned by UoW, same Session |
| EventPublisher | Scoped | Request | Per request |
| Clock | Transient | Handler | Created each time (cheap) |
| UUIDProvider | Transient | Handler | Created each time (cheap) |
| Application Services | Transient | Handler | Created per handler call |

## 9. Testing Overrides

```python
# tests/ingestion/presentation/conftest.py
from fastapi.testclient import TestClient
from ingestion.infrastructure.inmemory.unit_of_work import InMemoryUnitOfWork

def get_test_uow():
    return InMemoryUnitOfWork()

def get_test_client():
    app = create_app()
    app.dependency_overrides[get_uow] = get_test_uow
    app.dependency_overrides[get_event_publisher] = InMemoryEventPublisher
    return TestClient(app)
```

---

*See also: `composition-root.md`, `presentation-design.md`*
