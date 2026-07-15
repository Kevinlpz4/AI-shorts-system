# Exploration: Sprint 7.0 — Learning & Research Intelligence BC

> **Phase**: Explore (SDD)
> **Date**: 2026-07-15
> **Status**: COMPLETE
> **Change**: Sprint 7.0 — Learning BC

---

## 1. Current Domain Model Summary

### 1.1 Ingestion BC (`src/ingestion/`)

#### Aggregate Roots (3)

| AR | Identity | Inherits | Key Behavior |
|----|----------|----------|-------------|
| **NewsSource** | `SourceId` | `AggregateRoot` | Lifecycle: active/inactive. Emits `SourceEnabled`, `SourceDisabled`. References Categories & Topics by ID. |
| **Feed** | `FeedId` | `AggregateRoot` | Lifecycle: active/paused/inactive. Retry logic, auto-pause. Emits `RawArticleCollected`. |
| **RawArticle** | `RawArticleId` | `Entity` (documented as AR) | **Immutable**. No setters, no events. Volume-based AR (millions of instances). |

#### Entities (2)

| Entity | Identity | Key Behavior |
|--------|----------|-------------|
| **Category** | `CategoryId` | Hierarchical (parent_id). Slug-unique. Cascade deactivation. |
| **Topic** | `TopicId` | Simple name+description. Active/inactive lifecycle. |

#### Value Objects (8)

| VO | Frozen | Key Validation |
|----|--------|---------------|
| `SourceUrl` | ✅ | http/https, valid URL, normalized |
| `ArticleUrl` | ✅ | http/https, valid URL, `domain()` helper |
| `ArticleTitle` | ✅ | Non-empty, max 500 chars |
| `Language` | ✅ | ISO 639-1 code, 11 allowed languages |
| `SourceType` | ✅ Enum | RSS, API, SOCIAL_MEDIA, NEWSLETTER |
| `CategoryName` | ✅ | Non-empty, max 100 chars |
| `SyncPolicy` | ✅ | Mode, interval, retries, backoff, timeout |
| `SyncMode` | ✅ Enum | PULL, PUSH, STREAM, MANUAL |

#### Domain Events (3)

| Event | Publisher | Payload |
|-------|-----------|---------|
| `RawArticleCollected` | Feed | feed_id, batch_id, count, collected_at |
| `SourceEnabled` | NewsSource | source_id, enabled_at |
| `SourceDisabled` | NewsSource | source_id, reason, disabled_at |

All inherit from `foundation.events.domain_event.DomainEvent` (frozen dataclass, event_id/occurred_at/event_version). Events registered via `register_event()`, collected via `pull_events()`.

#### Repository Ports (5)

| Port | Methods | Notes |
|------|---------|-------|
| `NewsSourceRepository` | save, find_by_id, find_by_name, find_all, find_active, exists_by_name | 6 methods |
| `FeedRepository` | save, find_by_id, find_by_source, find_by_url, find_active_by_source, exists_by_source_and_url, count_active_by_source | 7 methods |
| `RawArticleRepository` | save, save_batch, find_by_id, find_by_feed, find_by_hash, exists_by_url, exists_by_hash, count_by_feed | 9 methods |
| `CategoryRepository` | save, find_by_id, find_by_slug, find_all, find_active, find_by_parent, exists_by_slug | 7 methods |
| `TopicRepository` | save, find_by_id, find_by_name, find_all, find_active, exists_by_name | 6 methods |

All are `typing.Protocol`. Use `Result[T]` for fallible operations, `list[T]` for collections.

#### Error Codes

```python
class IngestionErrorCode(str, Enum):  # 16 codes
    NEWS_SOURCE_NOT_FOUND, FEED_NOT_FOUND, RAW_ARTICLE_NOT_FOUND,
    CATEGORY_NOT_FOUND, TOPIC_NOT_FOUND, DUPLICATE_NEWS_SOURCE,
    DUPLICATE_FEED_URL, DUPLICATE_ARTICLE, INVALID_SOURCE_URL,
    INVALID_ARTICLE_URL, INVALID_LANGUAGE, NEWS_SOURCE_INACTIVE,
    FEED_INACTIVE, HAS_ACTIVE_FEEDS, CYCLE_DETECTED,
    FEED_MAX_RETRIES_EXCEEDED, FEED_ALREADY_PAUSED
```

#### Application Layer

- **Commands**: frozen dataclass with string IDs (RegisterFeedCommand, RecordCollectionCommand, etc.)
- **Queries**: frozen dataclass (FindFeedQuery, ListFeedsQuery, etc.)
- **Services**: SourceService, FeedService, ArticleService, CategoryService, TopicService — all return `Result[T]`
- **Ports**: `UnitOfWork` (Protocol), `EventPublisher` (Protocol)
- **DTOs**: separate Summary/Detail DTOs per entity
- **Mappers**: Entity → DTO conversion
- **Error handling**: `ApplicationErrorCode` enum, `ErrorMapper` for DomainError → Error conversion

#### Infrastructure

- **InMemory implementations**: `InMemoryRepositories`, `InMemoryUnitOfWork`, `InMemoryEventPublisher`
- **SQLAlchemy persistence**: models, repositories, UnitOfWork, event publisher, TypeDecorators
- **Composition Root**: `IngestionInfrastructure` with DI factories

#### Presentation (FastAPI)

- 37 REST endpoints under `/api/v1/`
- 2 health endpoints
- Full middleware stack: RequestID, CorrelationID, Timing, Recovery
- RFC 9457 Problem Details error responses

---

### 1.2 Research BC (`research/` — top-level, NOT under `src/`)

> ⚠️ **IMPORTANT**: Research BC uses a DIFFERENT structure from Ingestion. It lives at the project root (`research/`), not under `src/`. Its domain events DO NOT inherit from Foundation's `DomainEvent` — they define their own `DomainEvent` base class. This is a legacy pattern.

#### Aggregate Root

| AR | Identity | Key Behavior |
|----|----------|-------------|
| **ResearchTopic** | `UUID` (plain) | Lifecycle: FOUND → PENDING_REVIEW → APPROVED/REJECTED. Has `_events: list` and `pull_events()`. |

#### Value Objects

| VO | Frozen | Description |
|----|--------|-------------|
| `ResearchScore` | ✅ | relevance, popularity, recency, source_reliability (all 0-100). Weighted `total` property. |
| `ResearchSource` | ✅ | name, type (MANUAL/AUTOMATIC), reliability (0-100). Factory methods: manual(), google_news(), twitter(). |
| `ResearchStatus` | Enum | FOUND, PENDING_REVIEW, APPROVED, REJECTED |

#### Domain Events

| Event | Payload |
|-------|---------|
| `TopicDiscovered` | topic_id, title, source_name, score_total |
| `TopicApproved` | topic_id, title |
| `TopicRejected` | topic_id, title, reason |

#### Domain Services

| Service | Responsibility |
|---------|---------------|
| `ResearchScorer` | Calculates `ResearchScore` from heuristics (keywords, content length, source type, recency). Extension point: `ScorerExtension` port for AI override. |
| `DuplicateDetector` | Detects duplicate ResearchTopics |

#### Application Layer

- **Use Cases**: approve_topic, reject_topic, auto_discover, manual_input, list_topics
- **Scheduler**: topic scheduling logic
- **Source Registry**: external source management

---

### 1.3 Foundation (`src/foundation/`)

| Component | Description |
|-----------|-------------|
| `Entity` | Base with `id: EntityId` |
| `AggregateRoot` | Extends Entity with `_events`, `register_event()`, `pull_events()` |
| `ValueObject` | Marker (frozen dataclass convention) |
| `EntityId` | UUID-based, type-safe identity |
| `DomainEvent` | frozen dataclass: event_id, event_version, occurred_at, event_name (property) |
| `IntegrationEvent` | Cross-BC: source_boundary, correlation_id, causation_id |
| `Result[T]` | Success/Failure pattern |
| `Error` | code (ErrorCode enum), message, detail |
| `DomainError`, `ApplicationError`, `InfrastructureError` | Exception hierarchy |
| `ClockPort` | Time abstraction |
| `UUIDProvider` | UUID generation abstraction |

---

## 2. Scoring/Classification 现状

### What Exists Today

**ResearchScorer** (`research/domain/services/research_scorer.py`):
- Heuristic-based scoring with 4 components:
  - **Relevance** (0-100): keyword matching in title + content length + has description/URL/author
  - **Popularity** (0-100): source-based (manual=80, google-news=60, twitter=40)
  - **Recency** (0-100): time since publication (<1h=100, <6h=90, <24h=75, <48h=50, <7d=25, >7d=10)
  - **Source Reliability** (0-100): from ResearchSource.reliability

**ResearchScore** (`research/domain/value_objects/research_score.py`):
- Weighted total: relevance×0.35 + popularity×0.25 + recency×0.25 + reliability×0.15
- `is_notable`: total ≥ 70
- `__lt__` for sorting (best first)

**Extension Point**:
- `ScorerExtension` port allows AI override of heuristic scores
- Currently `_merge_with_ai_score()` just replaces with AI score (simple override)

### What Does NOT Exist

- **No learning from decisions**: The scorer doesn't improve over time based on approve/reject
- **No per-source quality tracking**: No memory of which sources produce good/bad content
- **No per-category relevance scoring**: Categories are just labels, not scored
- **No keyword learning**: High-value keywords are hardcoded frozenset
- **No article-level scoring**: Only ResearchTopic-level scoring exists
- **No feedback loop**: Approved/rejected decisions don't feed back into scoring weights

---

## 3. Human Decision Flow

### Current Flow

```
External Source → Ingestion BC → [Normalization] → Research BC → Human → Script BC
                    ↓                                      ↓
              RawArticle collected              ResearchTopic lifecycle
                    ↓                                      ↓
              Integration Event                    approve() / reject()
              (conceptual)                                 ↓
                                                   Domain Event
                                                   (TopicApproved/
                                                    TopicRejected)
```

### Detailed Steps

1. **Ingestion**: Feed.fetch() → creates RawArticles → `RawArticleCollected` event
2. **Research** (manual/auto): Creates ResearchTopic → `ResearchStatus.PENDING_REVIEW`
3. **Scoring**: ResearchScorer calculates ResearchScore heuristics
4. **Human Review**: User sees topics, decides approve/reject
5. **Decision**: `ResearchTopic.approve()` or `.reject(reason)`
6. **Events**: `TopicApproved` or `TopicRejected` emitted
7. **Downstream**: Script BC consumes `TopicApproved` to generate content

### Feedback Signals Available

| Signal | Source | Currently Used For |
|--------|--------|-------------------|
| Approve decision | ResearchTopic.approve() | Triggering content generation |
| Reject decision | ResearchTopic.reject(reason) | Audit only (reason logged) |
| Rejection reason | reject(reason) | Not analyzed |
| Score at decision time | ResearchTopic.score | Not compared to outcome |
| Source type | ResearchSource | Static weight only |
| Article keywords | Title/content | Hardcoded frozenset |
| Publication time | published_at | Recency heuristic only |

---

## 4. Boundary Analysis

### What Belongs in Ingestion BC (KEEP)

| Concept | Why Ingestion |
|---------|--------------|
| NewsSource, Feed configuration | Source setup is ingestion concern |
| Fetching, parsing, deduplication | Core ingestion pipeline |
| RawArticle storage | Audit trail of raw content |
| Category/Topic taxonomy (reference data) | Shared classification labels |
| Normalization pipeline | Content preparation |

### What Belongs in Research BC (KEEP)

| Concept | Why Research |
|---------|-------------|
| ResearchTopic lifecycle | Editorial workflow |
| Basic heuristic scoring | Initial quality estimation |
| Manual input | User-driven topic creation |
| Duplicate detection | Preventing topic duplication |

### What Should Be in Learning BC (NEW)

| Concept | Why Learning |
|---------|-------------|
| Decision history tracking | Learning requires historical data |
| Score accuracy analysis | Comparing predicted score vs actual decision |
| Source quality profiles | Learning which sources produce approved content |
| Keyword effectiveness | Learning which keywords predict approval |
| Category relevance weights | Learning which categories are most productive |
| Rejection pattern analysis | Learning why content is rejected |
| Scoring weight adjustment | Improving heuristic weights over time |
| Feature extraction | Converting articles into learning features |
| Prediction models | Predicting approval likelihood for new content |

### Clear Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION BC                                   │
│  Sources → Feeds → RawArticles → NormalizedItems                 │
│                                    │                              │
│                                    ▼ Integration Event            │
└──────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    RESEARCH BC                                    │
│  ResearchTopic → Scoring → PENDING_REVIEW → Approve/Reject       │
│       │                                  │          │             │
│       │ Decision Event                   │          │             │
│       ▼                                  │          ▼             │
└───────┼──────────────────────────────────┼──────────┼─────────────┘
        │                                  │          │
        ▼                                  ▼          ▼
┌──────────────────────────────────────────────────────────────────┐
│                    LEARNING BC (NEW)                              │
│  DecisionHistory ← ResearchTopic decisions                       │
│  SourceQuality ← Approved/rejected per source                    │
│  KeywordEffectiveness ← Title keywords vs approval rate          │
│  ScoreCalibration ← Predicted score vs actual decision           │
│  ScoringWeights → Improved heuristic weights                     │
│  PredictionModel → Approval likelihood for new content           │
│                                                                  │
│  Consumes: TopicApproved, TopicRejected (from Research)          │
│  Produces: ScoringWeights (to Research), Predictions (to UI)     │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5. Integration Points

### 5.1 Where Learning Hooks Into Existing Code

| Hook Point | Layer | Mechanism | What Learning Does |
|------------|-------|-----------|-------------------|
| `TopicApproved` event | Research Domain | Integration Event | Records decision, updates source quality, adjusts weights |
| `TopicRejected` event | Research Domain | Integration Event | Records decision + reason, updates source quality, learns rejection patterns |
| `ResearchScore` at decision time | Research VO | Read-only reference | Compares predicted score vs actual outcome for calibration |
| `ResearchSource` | Research VO | Read-only reference | Identifies source for quality tracking |
| `RawArticle` metadata | Ingestion Domain | Read-only reference | Extracts features (title keywords, language, content preview) |
| `NewsSource`/`Feed` config | Ingestion Domain | Read-only reference | Maps articles back to source config for quality profiling |
| `Category`/`Topic` taxonomy | Ingestion Domain | Read-only reference | Learns category relevance from approval patterns |

### 5.2 Event Flow (Proposed)

```
Research BC                          Learning BC
     │                                    │
     ├── TopicApproved ──────────────────►│ RecordDecisionCommand
     │   (topic_id, title, score)         │   → DecisionHistory
     │                                    │   → SourceQuality.update()
     │                                    │   → ScoreCalibration.record()
     │                                    │
     ├── TopicRejected ──────────────────►│ RecordDecisionCommand
     │   (topic_id, title, reason)        │   → DecisionHistory
     │                                    │   → SourceQuality.update()
     │                                    │   → RejectionPattern.record()
     │                                    │
     │                                    │── ScoringWeightsUpdated ──► Research
     │                                    │   (adjusted weights)
```

### 5.3 Reading Existing Data (Cross-BC References)

Learning BC needs READ access to:
- `RawArticleRepository` — for feature extraction (via Application Layer port)
- `NewsSourceRepository` — for source quality profiling
- `FeedRepository` — for feed quality profiling
- `CategoryRepository` / `TopicRepository` — for taxonomy mapping
- Research data (ResearchTopic scores, decisions) — via Research BC ports

---

## 6. Data Available for Learning

### 6.1 Raw Signals (from Ingestion)

| Signal | Type | Source | Learning Value |
|--------|------|--------|---------------|
| Article title | `str` | RawArticle | Keyword extraction, topic classification |
| Article URL/domain | `str` | RawArticle | Source domain quality |
| Article author | `str \| None` | RawArticle | Author reputation tracking |
| Article language | `Language` | RawArticle | Language-based filtering |
| Article published_at | `datetime \| None` | RawArticle | Recency patterns |
| Article content_preview | `str \| None` | RawArticle | Content quality signals |
| Article metadata | `dict` | RawArticle | Provider-specific signals |
| Content hash | `str` | RawArticle | Deduplication patterns |
| Source name | `str` | NewsSource | Source identity |
| Source type | `SourceType` | NewsSource | Source category (RSS/API/SOCIAL) |
| Source URL | `SourceUrl` | NewsSource | Source domain |
| Source categories | `list[CategoryId]` | NewsSource | Category assignment patterns |
| Source topics | `list[TopicId]` | NewsSource | Topic assignment patterns |
| Feed language | `Language` | Feed | Language quality |
| Feed categories | `list[CategoryId]` | Feed | Feed-level category patterns |
| Feed topics | `list[TopicId]` | Feed | Feed-level topic patterns |

### 6.2 Decision Signals (from Research)

| Signal | Type | Source | Learning Value |
|--------|------|--------|---------------|
| Approval decision | `bool` | ResearchTopic.approve() | Binary classification target |
| Rejection reason | `str` | ResearchTopic.reject() | Multi-class rejection taxonomy |
| Score at decision | `ResearchScore` | ResearchTopic.score | Score calibration data |
| Score components | `relevance/popularity/recency/reliability` | ResearchScore | Component-level calibration |
| Source name | `str` | ResearchSource | Source quality correlation |
| Source type | `SourceType` | ResearchSource | Source type quality |
| Source reliability | `int` | ResearchSource | Reliability calibration |
| Decision timestamp | `datetime` | reviewed_at | Temporal patterns |

### 6.3 Derived Features (Learning Computes)

| Feature | Computation | Purpose |
|---------|-------------|---------|
| Source approval rate | approved / (approved + rejected) per source | Source quality score |
| Category approval rate | approved / (approved + rejected) per category | Category relevance |
| Keyword effectiveness | approval rate per keyword | Keyword scoring |
| Time-of-day patterns | approval rate by hour/day | Temporal optimization |
| Score calibration error | predicted_total - actual_outcome | Scoring accuracy |
| Rejection cluster analysis | common themes in rejection reasons | Rejection pattern detection |

---

## 7. Architecture Patterns to Follow

### 7.1 Patterns from Ingestion BC (MUST Replicate)

| Pattern | Implementation | Learning BC Equivalent |
|---------|---------------|----------------------|
| **DDD Aggregate Root** | `AggregateRoot` from Foundation | `DecisionHistory`, `SourceQualityProfile` as ARs |
| **DDD Entity** | `Entity` from Foundation | `KeywordEffectiveness` as Entity |
| **Value Object** | `@dataclass(frozen=True)` | `ApprovalRate`, `WeightAdjustment` as VOs |
| **Domain Event** | Inherits `DomainEvent` from Foundation | `ScoringWeightsUpdated`, `SourceQualityChanged` |
| **Repository Protocol** | `typing.Protocol` | `DecisionHistoryRepository`, `SourceQualityRepository` |
| **ErrorCode Enum** | `str, Enum` (ADR-022) | `LearningErrorCode` independent enum |
| **Entity IDs** | Inherit `EntityId` from Foundation | `DecisionId`, `SourceQualityId` in Learning BC |
| **Command/Query** | `@dataclass(frozen=True)` | `RecordDecisionCommand`, `GetSourceQualityQuery` |
| **Service Pattern** | Injected deps, `Result[T]` returns | `LearningService` with repo + UoW injection |
| **UnitOfWork** | `Protocol` with context manager | Reuse Foundation's UnitOfWork |
| **EventPublisher** | `Protocol` post-commit | Reuse Foundation's EventPublisher |
| **DTO/Mapper** | Summary + Detail DTOs, mapper classes | `DecisionSummaryDTO`, `SourceQualityMapper` |
| **Error Hierarchy** | `DomainError` subclasses + ErrorCode | `LearningDomainError` subclasses |
| **InMemory implementations** | For testing | `InMemoryDecisionHistoryRepository` |

### 7.2 Patterns to AVOID

| Anti-Pattern | Why | Learning BC |
|-------------|-----|-------------|
| Top-level BC directory | Legacy pattern (Research) | Use `src/learning/` |
| Custom DomainEvent base | Foundation already provides one | Inherit from `foundation.events.domain_event.DomainEvent` |
| Plain UUID identity | Not type-safe | Use `EntityId` subclasses |
| Mutable events | Events are facts, immutable | Use `@dataclass(frozen=True)` |
| God entities | SRP violation | Split into focused ARs |

### 7.3 Testing Patterns

| Pattern | Implementation |
|---------|---------------|
| `conftest.py` per directory | Fixtures scoped to layer |
| InMemory repos | For unit tests |
| Service tests | Mock repos + InMemory UoW |
| `pytest.mark.integration` | DB-dependent tests |
| `asyncio_mode=auto` | pytest-asyncio configured |

---

## 8. Risks and Constraints

### 8.1 Frozen Layers — DO NOT TOUCH

| Layer | Version | Status | Impact on Learning |
|-------|---------|--------|-------------------|
| **Foundation** | v1.0 | FROZEN | Learning consumes Foundation's base classes. No additions needed. |
| **Domain** | v2.0 | FROZEN | Learning does NOT modify Ingestion domain. Cross-BC references by ID only. |
| **Application** | v1.1 | FROZEN | Learning does NOT modify Ingestion application. |
| **Persistence** | v1.0 | FROZEN | Learning gets its OWN persistence layer. |
| **Presentation** | v1.0 | FROZEN | Learning gets its OWN presentation layer. |

### 8.2 Architectural Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Learning reads Ingestion data → coupling | Medium | Use Repository Ports (read-only). Learning defines its own ports that reference Ingestion IDs. |
| Learning emits events that Research consumes → reverse coupling | Medium | Learning events are Integration Events (cross-BC). Research subscribes optionally. |
| Research BC is at top-level, not under src/ | Low | Learning follows src/ pattern. Don't replicate Research's legacy structure. |
| Score weight changes affect existing scoring | High | Weight changes are gradual, not sudden. A/B testing possible. |
| Decision history grows unbounded | Low | Implement TTL or archiving strategy. |

### 8.3 Data Consistency Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Learning reads stale data | Low | Acceptable — learning doesn't need real-time consistency |
| Decision event lost | Medium | EventPublisher with retry/logging. Learning can reprocess from decision history. |
| Weight adjustment breaks scoring | High | Gradual adjustment with bounds (min/max weights). Rollback capability. |

### 8.4 What We Must NOT Break

1. **Foundation's 5 criteria**: Learning adds nothing to Foundation
2. **Ingestion's Domain Events**: Learning consumes but doesn't produce Ingestion events
3. **Research's domain model**: Learning consumes Research events, doesn't modify Research entities
4. **Existing API endpoints**: No changes to `/api/v1/*` routes
5. **Existing tests**: Zero regressions in 1838+ existing tests
6. **Clean Architecture layering**: Learning must follow the same layer ordering

---

## 9. Recommended Learning BC Structure

```
src/learning/
├── __init__.py
├── domain/
│   ├── entities/
│   │   ├── decision_history.py      # AR: records approve/reject decisions
│   │   ├── source_quality.py        # AR: per-source quality profile
│   │   ├── keyword_effectiveness.py  # Entity: per-keyword approval stats
│   │   └── ids.py                   # DecisionId, SourceQualityId, etc.
│   ├── value_objects/
│   │   ├── approval_rate.py         # VO: approved/total ratio
│   │   ├── weight_adjustment.py     # VO: scoring weight deltas
│   │   ├── rejection_category.py    # VO: classified rejection reason
│   │   └── feature_vector.py        # VO: extracted article features
│   ├── events/
│   │   ├── learning_events.py       # ScoringWeightsUpdated, SourceQualityChanged
│   │   └── integration_events.py    # Cross-BC events
│   ├── ports/
│   │   ├── repositories.py          # DecisionHistoryRepo, SourceQualityRepo
│   │   └── scoring_reader.py        # Read-only access to Ingestion/Research data
│   └── exceptions/
│       └── errors.py                # LearningErrorCode enum
├── application/
│   ├── commands/
│   │   ├── decision_commands.py     # RecordDecisionCommand
│   │   └── weight_commands.py       # AdjustScoringWeightsCommand
│   ├── queries/
│   │   ├── quality_queries.py       # GetSourceQualityQuery
│   │   └── prediction_queries.py    # PredictApprovalQuery
│   ├── services/
│   │   ├── learning_service.py      # Main service
│   │   └── feature_extractor.py     # Extract features from articles
│   ├── dto/
│   │   ├── decision_dto.py
│   │   └── quality_dto.py
│   ├── mappers/
│   │   └── learning_mapper.py
│   ├── ports/
│   │   ├── unit_of_work.py          # Reuse Foundation's
│   │   └── event_publisher.py       # Reuse Foundation's
│   └── errors/
│       └── error_mapper.py
├── infrastructure/
│   ├── persistence/
│   │   ├── models/
│   │   ├── repositories/
│   │   └── types.py
│   └── inmemory/
│       └── repositories.py
└── presentation/
    ├── routers/
    │   ├── decisions.py
    │   └── quality.py
    └── schemas/
```

---

## 10. Ready for Proposal

**Status**: ✅ Ready

**What the orchestrator should tell the user**:
- Exploration complete. The Learning BC is a NEW bounded context that consumes decision signals from Research and feature data from Ingestion.
- It follows the exact same DDD/Clean Architecture patterns as Ingestion BC.
- It has its own domain, application, persistence, and presentation layers.
- All frozen layers remain untouched.
- The key architectural decision is HOW Learning communicates with Research/Ingestion: via Integration Events (preferred) or direct repository reads (simpler but more coupled).

**Key design decisions needed for Proposal phase**:
1. Should Learning use Integration Events or read directly from other BCs' repositories?
2. What is the granularity of the decision history? Per-Topic or per-RawArticle?
3. How do scoring weight adjustments flow back to Research? Event? Direct port call?
4. Should Learning have its own database or share Ingestion's?
5. What is the initial set of features (MVP vs full learning pipeline)?
