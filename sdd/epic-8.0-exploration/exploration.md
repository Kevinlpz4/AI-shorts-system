# EPIC 8.0 Exploration Report — Operational Validation & Continuous Learning

> **Date**: 2026-07-21
> **Exploration**: Exhaustive codebase audit for operational readiness
> **Project**: AI_Shorts_System

---

## 1. Current System State

### What Works (Tested & Validated)

**Foundation BC** (v1.0 STABLE — FROZEN)
- 292 test functions across 9 test files
- EntityId, ValueObject, Entity, AggregateRoot, Result, Error hierarchy, DomainEvent, ClockPort, UUIDProvider — all validated
- Zero dependencies (stdlib only)
- 7 ADRs approved, Foundation Stability Policy ratified

**Ingestion BC** (v2.0+ — COMPLETE through presentation layer)
- 1,136 test functions across 71 test files
- **Domain layer**: 230 tests (17 files) — entities (Source, Feed, Article, Topic, Category), value objects (SyncPolicy, SyncMode, Language, URLs, etc.), ports (repositories), events, errors
- **Application layer**: 228 tests (14 files) — services (Source, Feed, Article, Topic, Category), commands, queries, DTOs, mappers, error mapper
- **Infrastructure layer**: 317 tests (13 files) — InMemory repositories (validated), SQLAlchemy persistence (models, engine, config, types, decorators, exceptions), unit of work, event publisher (in-memory), repository contracts
- **Presentation layer**: 361 tests (27 files) including:
  - **119 E2E tests** (11 files) — full HTTP request cycle via httpx AsyncClient
  - Middleware stack (6 layers), health checks (liveness + readiness), OpenAPI contract, security headers, problem details, performance tests
  - Router tests for all 5 resource endpoints (sources, feeds, articles, categories, topics)
- **Fully wired FastAPI app** with factory pattern, CORS, structured JSON logging, request ID/correlation ID middleware

**Learning BC** (v1.0 — COMPLETE through presentation layer)
- 1,271 test functions across 106 test files
- **Domain layer**: 220 tests (22 files) — entities (LearningModel, LearningSignal, FeedbackRecord, KeywordStat, SourceQuality, KnowledgeArtifact), value objects (Confidence, SignalStrength, ScoreWeights, FeatureVector, FeatureSnapshot, TimeWindow, DecisionReason, DecisionType, AlgorithmVersion, SignalType), signals (handlers + registry), cross-BC ports, domain events, error hierarchy
- **Application layer**: 302 tests (15 files) — 8 services (Analytics, Dataset, Decision, Explanation, Prediction, Recommendation, Scoring, Signal), 5 query modules, 4 mappers, ports, DTOs, error mapping
- **Infrastructure layer**: 147 tests (12 files) — InMemory repositories, caches, knowledge storage, feature store, composition root, configuration, learning event publisher, unit of work, clock, dataset exporter
- **Persistence layer**: 170 tests (14 files) — 8 SQLAlchemy repositories (LearningSignal, Feedback, Dataset, FeatureStore, KnowledgeArtifact, KnowledgeTimeline, LearningModel, SourceQuality), type decorators, unit of work, migration, versioning, roundtrip, concurrency
- **Integration layer**: 227 tests (11 files) — pipeline orchestrator, event dispatcher, event context, dataset pipeline, feedback pipeline, recommendation pipeline, knowledge timeline, ingestion adapter, cross-BC ports
- **E2E layer**: 78 tests (16 files) — 12 scenario tests (complete cycle, learning volume, keyword signal, negative feedback, dataset export, timeline, feature store, coherence, full pipeline, historical, trend, reconstruction), consistency, explainability, performance, regression
- **Presentation layer**: 127 tests (16 files) — 11 API routers (analytics, artifacts, datasets, explanation, feedback, knowledge, prediction, recommendation, signals, source intelligence, timeline), health, middleware, OpenAPI, pagination, problem details
- **Fully wired FastAPI app** with factory pattern, middleware, 11 API routers

**Research BC** (Legacy — PRE-DDD but functional)
- 191 test functions across 13 test files
- **Domain**: ResearchTopic aggregate, ResearchScore, ResearchStatus VOs, DuplicateDetector, ResearchScorer services
- **Application**: AutoDiscover, ApproveTopic, RejectTopic, ManualInput, ListTopics use cases, Scheduler, SourceRegistry
- **Infrastructure**: GoogleNewsRSS (real), MockSource, PostgresRepository, PostgresSchedulerConfig
- **This is the ONLY BC that has been executed with REAL external data** (Google News RSS feeds)

**Legacy Core Code** (PRE-DDD, partially functional)
- `app/` — Entry point (argparse CLI), config, logger — WORKS
- `domain/` — Script, ContentIdea entities, ContentEvaluator, ports — TESTED
- `application/` — GenerateScript, GetScript, RegenerateScript use cases, DTOs — TESTED
- `infrastructure/` — OpenRouter provider (REAL AI calls), Mock provider, Postgres repositories, Mock publisher/TTS — TESTED
- `presentation/` — FastAPI routes (topics, scripts, discover, scheduler, studio) — TESTED
- `modules/` — ALL STUBS (see Section 2)
- `services/` — ALL STUBS (see Section 2)
- `agents/` — Orchestrator with ALL mock handlers
- `pipelines/` — content_pipeline, trends_pipeline

### Endpoints Hit With Real Requests

The following APIs have been tested via E2E tests (httpx AsyncClient in FastAPI test mode):

**Ingestion API** (`/api/v1/*`):
- Sources CRUD (list, create, get, update, delete)
- Feeds CRUD
- Articles CRUD
- Categories CRUD
- Topics CRUD
- Health endpoints (/health/live, /health/ready)

**Learning API** (`/api/v1/learning/*`):
- All 11 routers (prediction, explanation, recommendation, feedback, source_intelligence, knowledge, timeline, signals, datasets, artifacts, analytics)
- Health endpoints

**Legacy API** (`/api/v1/*`):
- Topics CRUD, scripts generation, discover, scheduler status/start/stop, studio endpoints

### Ingestion Pipelines That Have Processed Real Data

- **Research AutoDiscover** → Google News RSS → creates ResearchTopic entities in PostgreSQL
- **Research Scheduler** → periodic discovery with configurable queries and intervals

### Research Scoring on Real Content

- `ResearchScorer` computes relevance/popularity/recency/source_reliability scores
- `DuplicateDetector` uses hash-based deduplication (SHA-256)
- Both tested with simulated data; Google News RSS source has been tested against real feeds

---

## 2. Placeholders & Stubs

### Complete Stub Modules (100% TODO/mock)

| Module | Files | Status |
|--------|-------|--------|
| `modules/video_generator.py` | All methods return empty files or stub paths | `TODO: Implementar con MoviePy o FFmpeg` |
| `modules/voice_generator.py` | All methods are stubs | `TODO: Implementar con ElevenLabs Voice Clone API` |
| `modules/subtitles.py` | All methods are stubs | `TODO: Implementar con FFmpeg o MoviePy` |
| `modules/publisher.py` | All methods are stubs | `TODO: Implementar TikTok/Instagram API, scheduling` |
| `modules/analyzer.py` | get_video_analytics returns mock data | `TODO: Implementar con YouTube Analytics API` |
| `modules/trends.py` | get_trending_topics is a stub | `TODO: Conectar con Twitter/YouTube/Reddit API` |
| `services/youtube_service.py` | ALL methods return mock data | `TODO: Conectar con YouTube Data API v3` (6 TODOs) |
| `services/social_service.py` | ALL methods return mock data | `TODO: Conectar con Twitter/Reddit/TikTok API` (3 TODOs) |
| `services/news_service.py` | ALL methods return mock data | `TODO: Conectar con News API` (3 TODOs) |
| `services/tts_service.py` | Returns mock audio paths | Not checked in detail but likely stubs |

### Agent Orchestrator — ALL Mock

`agents/core/orchestrator.py` — 9 skill handlers, ALL return mock/dummy data:
- `_handle_get_trends` → mock trends
- `_handle_generate_idea` → mock ideas
- `_handle_write_script` → mock scripts
- `_handle_generate_hook` → mock hooks
- `_handle_generate_voice` → mock audio paths
- `_handle_generate_video` → mock video paths
- `_handle_generate_subtitles` → mock subtitle paths
- `_handle_publish` → mock publish results
- `_handle_analyze_performance` → mock metrics

### Agent Tools — ALL Stubs

- `agents/tools/video_tool.py` — `TODO: Conectar con modules/video_generator.py`
- `agents/tools/script_tool.py` — `TODO: Conectar con modules/script_generator.py`
- `agents/tools/idea_tool.py` — `TODO: Conectar con modules/idea_generator.py`
- `agents/tools/trends_tool.py` — `TODO: Conectar con modules/trends.py o services/news_service.py`

### InMemory Event Publishers

- `src/ingestion/infrastructure/event_publisher.py` — stores events in a Python list (no persistence, no bus)
- `src/ingestion/infrastructure/inmemory/event_publisher.py` — same pattern
- `src/learning/infrastructure/inmemory/learning_event_publisher.py` — same pattern

### Specific TODO/FIXME Locations

| File | Line | TODO |
|------|------|------|
| `modules/hooks.py` | 277 | `TODO: Usar performance_data cuando esté disponible` |
| `modules/trends.py` | 131-141 | 3 TODOs: Connect Twitter/YouTube/Reddit APIs |
| `presentation/cli/container.py` | 4 | `TODO el wiring de dependencias en UN solo lugar` |
| All `agents/tools/*.py` | ~44 | `TODO: Conectar con modules/*` |
| All `agents/core/orchestrator.py` handlers | Various | `TODO: Conectar con modules/*` |

---

## 3. Never Executed With Real Data

### Processing Pipelines That Exist Only As Code

1. **Full content pipeline** (`pipelines/content_pipeline.py`) — trends → idea → script → TTS → video → publish → analyze
2. **Trends pipeline** (`pipelines/trends_pipeline.py`) — fetch trends from multiple sources
3. **Agent orchestrator** — 9 skills, none connected to real implementations
4. **Video generation** — MoviePy/FFmpeg integration never implemented
5. **TTS generation** — ElevenLabs/Azure integration never implemented
6. **Subtitle generation** — FFmpeg integration never implemented
7. **Publishing** — YouTube/TikTok/Instagram upload never implemented
8. **Performance analysis** — YouTube Analytics integration never implemented

### Analytics/Scoring Never Called on Real Data

- `ResearchScorer` — tested with simulated data, but scores computed on real Google News topics
- `DuplicateDetector` — tested with simulated data
- **Learning BC's entire scoring/prediction/recommendation system** — all tested with in-memory data, never fed real article data

### Learning Mechanisms Never Received Real Feedback

- `FeedbackPipeline` — never received real user feedback
- `RecommendationPipeline` — never received real user recommendations
- `DatasetPipeline` — never exported real datasets
- `PredictionService` — never predicted on real content
- `ExplanationService` — never explained real decisions
- `DecisionService` — never made real decisions
- All learning signals (KEYWORD, SOURCE, CATEGORY, TOPIC, etc.) — never computed from real data

### Integrations Defined But Not Wired

- Learning BC ↔ Ingestion BC integration (adapter exists, never used with real data)
- Learning BC ↔ Research BC integration (not wired)
- Learning BC event outbound events (published to in-memory list, never consumed externally)
- Ingestion BC event publisher (in-memory only, no message broker)

---

## 4. Missing Dependencies for Continuous Operation

### Scheduler/Cron/Worker System

- **Research Scheduler** (`research/application/scheduler.py`): EXISTS and is COMPLETE — asyncio.Task-based, runs discovery every N minutes, configurable queries and intervals
- **But**: It runs in-process (asyncio Task), not as a separate worker. No Celery, no APScheduler, no systemd service, no Docker container for the worker
- **No cron jobs** defined anywhere
- **No background task queue** (no Celery, no RQ, no Huey)

### Queue/Message Broker

- **NONE** — no RabbitMQ, no Redis, no Kafka, no NATS
- Event publishers are all in-memory (Python lists)
- No message broker for cross-BC communication
- No outbox pattern implemented

### Monitoring/Alerting

- **NONE** — no Prometheus, no StatsD, no Grafana, no Datadog
- No metrics collection whatsoever (no counters, gauges, histograms)
- No alerting infrastructure
- No structured error tracking (Sentry, etc.)

### Structured Logging

- **Ingestion BC**: FULLY IMPLEMENTED — `logging_config.py` with JSON formatter, RequestContextFilter (request_id, correlation_id), configurable log level/format
- **Learning BC**: Has timing middleware, request ID middleware
- **Legacy code**: Uses basic `logging.getLogger()` without structured format
- **No log aggregation** (no ELK, no Loki, no CloudWatch)

### Health Check Infrastructure

- **Ingestion BC**: FULLY IMPLEMENTED — `/health/live` (liveness) + `/health/ready` (readiness with DB check)
- **Learning BC**: Has a health router (checked via import)
- **Legacy API**: No health checks

### Deployment Configuration

- **NO Dockerfile** anywhere
- **NO docker-compose.yml** anywhere
- **NO Makefile** anywhere
- **NO CI/CD pipeline** (no `.github/workflows/`, no `.gitlab-ci.yml/`)
- **NO Kubernetes manifests**
- **NO systemd service files**
- **NO nginx/reverse proxy config**

### Database Migrations

- **Learning BC**: Has Alembic-style migration (`src/learning/persistence/migrations/`)
- **Ingestion BC**: Uses SQLAlchemy `create_all()` (no Alembic)
- **Legacy**: Migration script (`scripts/migrate_to_postgres.py`) for SQLite → PostgreSQL

---

## 5. Production Risks for 24/7 Operation

### Hardcoded Values

| File | Value | Risk |
|------|-------|------|
| `app/config.py:140` | `postgresql+psycopg2://kevin:1234@localhost:5432/system_shorts` | Default DB URL with hardcoded credentials |
| `app/config.py:106` | `TTS_VOICE_ID: "21m00Tcm4TlvDq8ikWAM"` | Hardcoded ElevenLabs voice ID |
| `app/config.py:114` | `VIDEO_CODEC: str = "h264"` | May need to change per deployment |
| `app/config.py:115` | `VIDEO_BITRATE: str = "4M"` | May need to change per deployment |
| `services/youtube_service.py:115` | `video_id = "dQw4w9WgXcQ"` | Rick Roll as mock video ID |
| `src/ingestion/presentation/config.py:87` | `SECRET_KEY: str = "change-me-in-production"` | Default insecure secret key |
| `src/ingestion/presentation/config.py:77` | `DATABASE_URL: str = "sqlite:///./ai_shorts.db"` | Default SQLite URL |

### Resource Leaks

- **DB connections**: Ingestion BC has proper pool configuration (`pool_size`, `max_overflow`, `pool_pre_ping`, `pool_recycle=3600`) in `src/ingestion/infrastructure/persistence/config.py` ✅
- **Legacy code**: `infrastructure/persistence/database.py` uses `pool_pre_ping=True, pool_size=5, max_overflow=10` — adequate
- **InMemory event publishers**: Events stored in Python lists that grow unboundedly — potential memory leak over time
- **No HTTP session management**: No `aiohttp.ClientSession` lifecycle management visible in research sources

### Error Handling Gaps

- **Legacy orchestrator**: Only catches `Exception` generically, no specific error types
- **Legacy services**: Return empty dicts/lists on error, no error propagation
- **Learning BC**: Properly uses Result[T] pattern with DomainError hierarchy ✅
- **Ingestion BC**: Properly uses Result[T] pattern with error mapper ✅

### Race Conditions

- **Research Scheduler**: Uses `asyncio.create_task` — runs in same event loop, no concurrent access issues (single-threaded asyncio)
- **Ingestion Unit of Work**: Has concurrency tests (`tests/ingestion/infrastructure/test_concurrency.py`)
- **Learning Unit of Work**: Has concurrency tests (`tests/learning/persistence/test_concurrency.py`)
- **No distributed locking** mechanism (no Redis locks, no DB advisory locks)

### Graceful Shutdown

- **Ingestion BC**: `lifespan` context manager calls `engine.dispose()` on shutdown ✅
- **Research Scheduler**: Has `stop()` method that cancels the asyncio task gracefully ✅
- **Legacy API**: No explicit shutdown handling beyond uvicorn defaults
- **No SIGTERM/SIGINT handlers** registered anywhere (relies on uvicorn defaults)

### Timeout Configurations

- **Ingestion SyncPolicy**: Has `timeout_seconds` field (default: 30s) with validation ✅
- **Database connections**: `pool_recycle=3600` (1 hour) ✅
- **No HTTP request timeouts** configured for external API calls (OpenRouter, Google News)
- **No global request timeout** middleware

---

## 6. Test Coverage Overview

### Tests Per Bounded Context

| BC | Test Functions | Test Files | Layers |
|----|---------------|------------|--------|
| **Foundation** | 292 | 9 | Domain (9 files) |
| **Ingestion** | 1,136 | 71 | Domain (230), Application (228), Infrastructure (317), Presentation (361, incl. 119 E2E) |
| **Learning** | 1,271 | 106 | Domain (220), Application (302), Infrastructure (147), Persistence (170), Integration (227), E2E (78), Presentation (127) |
| **Research** (legacy) | 191 | 13 | Domain, Application, Infrastructure |
| **Legacy Core** | 328 | 19 | Domain (127), Application (73), Infrastructure (60), Presentation (36), Root (32) |
| **TOTAL** | **~3,218** | **~218** | |

### Test Categories

- **Unit tests**: ~2,500+ (default, run with `pytest`)
- **Integration tests**: ~400+ (marked with `@pytest.mark.integration`, SKIPPED by default in `pytest.ini: addopts = -m "not integration"`)
- **E2E tests**: 197 (Ingestion 119 + Learning 78)
- **Performance tests**: Present in both Ingestion and Learning E2E

### Test Configuration

```ini
# pytest.ini
asyncio_mode = auto
addopts = -m "not integration"  # Integration tests skipped by default
pythonpath = src
markers:
    integration: Tests that hit real external APIs
    unit: Pure unit tests
    performance: Performance tests with p95 measurements
```

### Coverage Gaps

- **No integration tests with REAL external services** (no actual OpenRouter calls, no real Google News fetch)
- **No load/stress tests** beyond basic performance measurements
- **No mutation testing**
- **No contract testing** between BCs (e.g., Learning consuming Ingestion events)
- **Legacy modules/ directory**: ZERO tests for video_generator, voice_generator, subtitles, publisher, analyzer, trends
- **Legacy services/ directory**: ZERO tests for youtube_service, social_service, news_service
- **Legacy agents/ directory**: ZERO tests

---

## 7. Architecture Constraints

### What's Frozen (DO NOT CHANGE)

1. **Foundation v1.0 STABLE** — API public is locked. Changes require ADR + ARB approval + 5 criteria compliance. Bug fixes OK.
2. **Repository structure** — `src/{bc}/{domain,application,infrastructure,presentation}` pattern is established
3. **Design principles** — DDD, Hexagonal, SOLID are non-negotiable
4. **Testing strategy** — Strict TDD, Result[T] pattern for fallible operations, frozen dataclasses for VOs

### What Can Change

1. **Infrastructure adapters** — Can add new implementations of ports (e.g., replace InMemory event publisher with RabbitMQ)
2. **New BCs** — Can be added following existing patterns
3. **Legacy code** — `app/`, `domain/`, `application/`, `infrastructure/`, `modules/`, `services/`, `agents/` are NOT part of the DDD architecture and can be refactored/migrated
4. **Deployment** — No deployment config exists yet

### Two Parallel Codebases

The project has TWO codebases that coexist:

1. **Legacy code** (`app/`, `domain/`, `application/`, `infrastructure/`, `modules/`, `services/`, `agents/`, `pipelines/`, `presentation/`) — Pre-DDD, monolithic, with the main entry point
2. **DDD BCs** (`src/foundation/`, `src/ingestion/`, `src/learning/`) — Clean Architecture, with their own entry points

The legacy `app/main.py` is the PRIMARY entry point. The DDD BCs have their own FastAPI apps but are not yet the primary entry point.

### Key Architectural Decision for EPIC 8.0

The system needs to decide:
- **Which codebase is the operational one?** The legacy `app/main.py` or the DDD BCs?
- **How do the 4 BCs communicate?** Currently all in-memory. Need message broker for production.
- **What's the deployment model?** Monolith (single uvicorn)? Multiple services? Containerized?

---

## Summary: Operational Readiness Assessment

| Capability | Status | Gap |
|------------|--------|-----|
| Domain logic | ✅ Complete (Foundation, Ingestion, Learning) | Research needs DDD migration |
| Application services | ✅ Complete (Ingestion, Learning) | Research has basic use cases |
| API endpoints | ✅ Complete (Ingestion, Learning, Legacy) | All tested |
| Persistence | ✅ PostgreSQL (InMemory + SQLAlchemy) | No migrations in Ingestion |
| AI integration | ✅ OpenRouter works | Only integration that actually works with real API |
| News ingestion | ✅ Google News RSS works | Only BC with real data flow |
| Video generation | ❌ Stub only | Not implemented |
| TTS generation | ❌ Stub only | Not implemented |
| Subtitle generation | ❌ Stub only | Not implemented |
| Publishing | ❌ Stub only | Not implemented |
| Scheduling | ⚠️ In-process asyncio only | No separate worker, no cron |
| Event bus | ❌ In-memory only | No message broker |
| Monitoring | ❌ None | No metrics, no alerting |
| Logging | ✅ Structured JSON (Ingestion) | Legacy code uses basic logging |
| Health checks | ✅ Liveness + readiness (Ingestion) | Legacy API has none |
| Deployment | ❌ None | No Docker, no CI/CD |
| Graceful shutdown | ⚠️ Partial (engine disposal only) | No SIGTERM handling |
| Error handling | ✅ Domain errors (Ingestion, Learning) | Legacy uses generic Exception |
