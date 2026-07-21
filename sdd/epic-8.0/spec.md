# Specification: EPIC 8.0 — Operational Validation & Continuous Learning

## 1. Overview

### 1.1 Purpose

EPIC 8.0 transforms the AI_Shorts_System from a static demo into a continuous knowledge acquisition and learning platform. It proves, through real operation with accumulated experience, that the system progressively improves recommendation quality without ML, LLMs, or embeddings. The EPIC establishes measurable feedback loops, versioned datasets, and statistical validation that demonstrate genuine learning from human feedback.

### 1.2 Scope

- **IN**: Runtime orchestration (scheduler, pipeline), real PostgreSQL persistence, knowledge acquisition adapters (RSS, APIs, Reddit, GitHub, HN, Steam), human feedback interfaces (CLI + minimal web UI), statistical validation metrics, dataset versioning with train/test splits
- **OUT**: Deployment infrastructure (EPIC 9), advanced observability (EPIC 10), ML training pipelines (EPIC 11), content production (EPIC 12), LLM integration (EPIC 13), Research DDD migration (EPIC 14)

### 1.3 Out of Scope

| Item | Reason |
|------|--------|
| ML/LLM training | YAGNI — EPIC 8 prepares ground only |
| Vector embeddings | Not needed for statistical learning |
| Semantic search | Not needed for statistical learning |
| Deployment (Docker, K8s, CI/CD) | Separate future EPIC |
| Prometheus/Grafana | Separate future EPIC |
| TTS, video generation | Separate future EPIC |
| Automatic publishing | Separate future EPIC |

### 1.4 Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| Learning BC (existing) | Internal | ✅ Complete (InMemory) |
| Research BC | Internal | ✅ Complete (legacy, frozen) |
| Ingestion BC | Internal | ✅ Complete (frozen v1.0) |
| Foundation BC | Internal | ✅ Complete (frozen v1.0) |
| PostgreSQL | External | Required for Phase A |
| Python 3.12 | Runtime | ✅ Available |
| FastAPI | Framework | ✅ Available |
| SQLAlchemy | ORM | ✅ Available |
| Pydantic v2 | Validation | ✅ Available |
| pytest | Testing | ✅ Available |

## 2. Core Objective & North Star

### 2.1 Objective

"Demostrar, mediante operación continua con datos reales, que el sistema mejora progresivamente la calidad de sus recomendaciones utilizando únicamente experiencia acumulada."

**Translation**: Demonstrate, through continuous operation with real data, that the system progressively improves recommendation quality using only accumulated experience.

### 2.2 Learning Metrics Suite (North Star)

The system MUST track and expose a complete metric suite to prove continuous learning. No single metric suffices — the full suite demonstrates improvement.

| Metric | Formula | Target | Measurement Window |
|--------|---------|--------|-------------------|
| **Top-K Precision** | `count(approved_in_top_k) / k` where k=10 | ≥ 0.7 | Rolling 7d, 30d, All-time |
| **Precision** | `TP / (TP + FP)` where TP=approved correctly predicted, FP=rejected incorrectly predicted | ≥ 0.6 | Rolling 7d, 30d, All-time |
| **Recall** | `TP / (TP + FN)` where FN=approved incorrectly rejected | ≥ 0.5 | Rolling 7d, 30d, All-time |
| **Accuracy** | `(TP + TN) / (TP + TN + FP + FN)` | ≥ 0.6 | Rolling 7d, 30d, All-time |
| **Recommendation Acceptance Rate** | `accepted_recommendations / total_recommendations` | ≥ 0.5 | Rolling 7d, 30d, All-time |
| **Feedback Coverage** | `total_feedback / total_recommendations` | ≥ 0.3 | Rolling 30d, All-time |
| **Dataset Growth** | `new_samples_per_week` | ≥ 10 | Rolling 7d |
| **Signal Confidence** | `average(min(1.0, total_samples / min_sample_size))` | ≥ 0.5 | Rolling 30d |
| **Source Quality Evolution** | `stddev(source_approval_rates)` increasing over time | Positive trend | Rolling 30d vs previous 30d |

**Improvement Criteria**: The system is "learning" when at least 3 of 5 core metrics (Top-K Precision, Precision, Accuracy, Recommendation Acceptance Rate, Signal Confidence) show positive trend over 30-day windows.

**Regression Detection**: Any core metric decreasing by ≥ 10% between consecutive 7-day windows triggers a regression alert.

## 3. Architectural Decisions

### AD-001: Runtime is NOT a Bounded Context

`src/runtime/` is a thin orchestration layer — scheduler, pipeline runner, EventBridge. **NO domain logic**. All business rules live exclusively in existing frozen BCs (Learning, Research, Ingestion, Foundation). The runtime layer ONLY coordinates; it never decides.

**Rationale**: Keeping runtime as a thin layer prevents duplication of business logic, maintains BC boundaries, and ensures the Learning BC remains the single source of truth for learning decisions.

### AD-002: All BCs remain FROZEN

No modifications to Foundation, Ingestion, Research, or Learning BC domain layers. Integration ONLY via:
- **Protocols** (cross-BC ports like `IngestionReader`, `ResearchReader`)
- **Integration Events** (event-driven communication)
- **Application Services** (coordinating cross-BC operations)

**Rationale**: BCs are battle-tested. Modifying them risks regression. New functionality extends via new modules, not modifications.

### AD-003: YAGNI — No ML/LLM/embeddings yet

EPIC 8 only prepares the ground. **Explicitly excluded**:
- No training pipelines
- No vector databases
- No semantic search
- No LLM orchestration
- No automatic model retraining

**Statistical learning only**: weighted sums, approval rates, signal strength, confidence intervals.

**Rationale**: Premature optimization. Statistical methods are sufficient to demonstrate learning. ML adds complexity without measurable value at this stage.

### AD-004: Full Data Traceability (MANDATORY)

Every piece of data consumed by the Learning BC MUST be traceable to its origin. Every recommendation, signal, dataset, or prediction MUST answer:

1. **¿De qué noticia provino?** — Source article/content ID
2. **¿Qué fuente la publicó?** — Publishing source name
3. **¿Qué features se calcularon?** — Feature snapshot (base_score, freshness, keywords, source_bonus, etc.)
4. **¿Qué feedback humano recibió?** — Human decision (APPROVE/REJECT) with reason
5. **¿Qué versión del algoritmo produjo ese resultado?** — AlgorithmVersion string

**Implementation**: Each domain entity carries provenance metadata. FeatureSnapshot, FeedbackRecord, LearningSignal, and PredictionDTO MUST include traceability fields.

### AD-005: Expanded Learning Metrics (North Star)

No single metric. Full metric suite (9 metrics defined in Section 2.2). Primary goal: recommendations must demonstrably improve over time, measured by statistical significance.

## 4. Functional Requirements

### 4.1 Phase 0 — Operational Validation

**Objective**: Prove the existing pipeline runs continuously for days with real data without crashes, data loss, or inconsistency.

#### 4.1.1 Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| P0-01 | Scheduler MUST execute pipeline runs at configurable intervals (default: 60 minutes) | MUST |
| P0-02 | Pipeline MUST complete full cycle: collect → score → recommend → log | MUST |
| P0-03 | System MUST recover gracefully from pipeline failures (no crash, log error, continue) | MUST |
| P0-04 | System MUST handle duplicate articles via deduplication (article_id check) | MUST |
| P0-05 | System MUST survive restarts without data loss (persistent state) | MUST |
| P0-06 | System MUST run continuously for ≥ 7 days without manual intervention | MUST |
| P0-07 | System MUST log pipeline execution metrics (duration, items processed, errors) | SHOULD |
| P0-08 | System MUST detect and report pipeline consistency (no orphan records) | SHOULD |

#### 4.1.2 Deliverables

- `src/runtime/scheduler.py` — Configurable scheduler (APScheduler or custom)
- `src/runtime/pipeline.py` — Pipeline orchestrator (collect → score → recommend → log)
- `src/runtime/config.py` — Runtime configuration (intervals, timeouts, retries)
- `tests/runtime/test_scheduler.py` — Scheduler unit tests
- `tests/runtime/test_pipeline.py` — Pipeline integration tests

#### 4.1.3 Acceptance Criteria

- Pipeline runs 100 times without crash
- Pipeline handles 3 consecutive failures without stopping
- Deduplication catches 100% duplicate articles
- Restart preserves all accumulated state
- 7-day continuous run completes with ≥ 95% success rate

### 4.2 Phase A — Runtime

**Objective**: Replace InMemory persistence with real PostgreSQL, add EventBridge for cross-BC communication, implement scheduler.

#### 4.2.1 Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| PA-01 | System MUST persist all Learning BC data in PostgreSQL | MUST |
| PA-02 | System MUST implement all repository ports with SQLAlchemy adapters | MUST |
| PA-03 | System MUST support UnitOfWork with real database transactions | MUST |
| PA-04 | System MUST implement EventBridge for integration events | MUST |
| PA-05 | System MUST support configurable pipeline schedule | MUST |
| PA-06 | System MUST handle concurrent access (multiple pipeline runs) | SHOULD |
| PA-07 | System MUST provide database migration scripts (Alembic) | MUST |
| PA-08 | System MUST implement connection pooling | SHOULD |

#### 4.2.2 Deliverables

- `src/learning/infrastructure/persistence/sqlalchemy/` — SQLAlchemy repository implementations
  - `feedback_repository.py`
  - `signal_repository.py`
  - `source_quality_repository.py`
  - `model_repository.py`
- `src/learning/infrastructure/persistence/sqlalchemy/unit_of_work.py` — Real UoW
- `src/learning/infrastructure/persistence/migrations/` — Alembic migrations
- `src/learning/integration/event_bridge.py` — EventBridge implementation
- `src/runtime/scheduler.py` — Scheduler with configurable intervals
- `src/runtime/pipeline.py` — Pipeline orchestrator
- `tests/learning/infrastructure/test_sqlalchemy_repos.py` — Repository tests
- `tests/runtime/test_pipeline_integration.py` — Integration tests

#### 4.2.3 Acceptance Criteria

- All 4 repositories pass integration tests against real PostgreSQL
- UnitOfWork commits/rollbacks correctly
- EventBridge publishes and subscribes events
- Scheduler runs pipeline at configured intervals
- Pipeline completes full cycle in ≤ 30 seconds
- Database handles 1000+ records without performance degradation

### 4.3 Phase B — Knowledge Acquisition

**Objective**: Expand beyond Google News RSS to multiple knowledge sources (Reddit, GitHub, HN, Steam, APIs).

#### 4.3.1 Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| PB-01 | System MUST support pluggable knowledge source adapters | MUST |
| PB-02 | System MUST implement adapter for Reddit (r/programming, r/machinelearning) | MUST |
| PB-03 | System MUST implement adapter for GitHub Trending | MUST |
| PB-04 | System MUST implement adapter for Hacker News | SHOULD |
| PB-05 | System MUST normalize all sources to common Article format | MUST |
| PB-06 | System MUST track source metadata (name, URL, type, reliability) | MUST |
| PB-07 | System MUST handle rate limits gracefully (backoff, retry) | MUST |
| PB-08 | System MUST deduplicate across sources (title similarity) | SHOULD |

#### 4.3.2 Deliverables

- `src/knowledge/adapters/` — Knowledge source adapters
  - `reddit_adapter.py`
  - `github_adapter.py`
  - `hackernews_adapter.py`
- `src/knowledge/ports/knowledge_source.py` — KnowledgeSource Protocol
- `src/knowledge/domain/article.py` — Normalized Article value object
- `tests/knowledge/adapters/` — Adapter unit tests
- `tests/knowledge/test_integration.py` — Integration tests

#### 4.3.3 Acceptance Criteria

- Each adapter fetches ≥ 10 articles per run
- All articles normalized to common format
- Rate limits handled without crashes
- Deduplication catches ≥ 90% cross-source duplicates
- Source metadata tracked for all articles

### 4.4 Phase C — Human Feedback

**Objective**: Build interfaces for humans to approve/reject content, creating real feedback history.

#### 4.4.1 Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| PC-01 | System MUST provide CLI interface for feedback (approve/reject) | MUST |
| PC-02 | System MUST provide minimal web UI for feedback | MUST |
| PC-03 | System MUST record decision + reason for rejection | MUST |
| PC-04 | System MUST update SourceQualityProfile on each decision | MUST |
| PC-05 | System MUST emit FeedbackCaptured event on each decision | MUST |
| PC-06 | System MUST support batch feedback (multiple items) | SHOULD |
| PC-07 | System MUST track feedback history with timestamps | MUST |
| PC-08 | System MUST prevent duplicate feedback on same content | MUST |

#### 4.4.2 Deliverables

- `src/cli/feedback.py` — CLI feedback interface
- `src/learning/presentation/routers/feedback.py` — Enhanced feedback API
- `src/learning/presentation/web/feedback.html` — Minimal web UI
- `tests/cli/test_feedback.py` — CLI tests
- `tests/learning/presentation/test_feedback_api.py` — API tests

#### 4.4.3 Acceptance Criteria

- CLI allows approve/reject with reason
- Web UI displays pending items and accepts decisions
- Each decision updates SourceQualityProfile
- FeedbackCaptured event emitted for all decisions
- Duplicate feedback prevented (same content_id)
- Feedback history queryable by date range

### 4.5 Phase D — Adaptive Learning

**Objective**: Implement statistical validation: metric suite, accuracy tracking, improvement reports.

#### 4.5.1 Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| PD-01 | System MUST calculate all 9 metrics defined in Section 2.2 | MUST |
| PD-02 | System MUST track metrics over rolling windows (7d, 30d, all-time) | MUST |
| PD-03 | System MUST detect improvement trends (positive slope) | MUST |
| PD-04 | System MUST detect regression (≥ 10% decrease in 7-day window) | MUST |
| PD-05 | System MUST generate weekly improvement reports | SHOULD |
| PD-06 | System MUST expose metrics via API endpoint | MUST |
| PD-07 | System MUST store metric snapshots for historical comparison | MUST |
| PD-08 | System MUST support manual weight adjustment via API | SHOULD |

#### 4.5.2 Deliverables

- `src/learning/domain/services/metrics_service.py` — Metrics calculation
- `src/learning/application/services/metrics_service.py` — Metrics orchestration
- `src/learning/presentation/routers/metrics.py` — Metrics API
- `src/learning/domain/entities/metric_snapshot.py` — MetricSnapshot entity
- `src/learning/infrastructure/persistence/metric_repository.py` — Metric persistence
- `tests/learning/domain/test_metrics.py` — Metrics calculation tests
- `tests/learning/application/test_metrics_service.py` — Service tests

#### 4.5.3 Acceptance Criteria

- All 9 metrics calculated correctly
- Metrics tracked over rolling windows
- Improvement trends detected statistically
- Regression detected within 7 days
- Metrics API returns current values and historical data
- Metric snapshots stored for ≥ 90 days

### 4.6 Phase E — Dataset Readiness

**Objective**: Versioned datasets with checksums, JSONL export, train/test splits for future ML.

#### 4.6.1 Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| PE-01 | System MUST generate versioned datasets from feedback history | MUST |
| PE-02 | System MUST include checksums for reproducibility | MUST |
| PE-03 | System MUST export in JSONL format | MUST |
| PE-04 | System MUST support train/test split (80/20 default) | MUST |
| PE-05 | System MUST track dataset metadata (version, record count, checksum, created_at) | MUST |
| PE-06 | System MUST prevent modification of versioned datasets | MUST |
| PE-07 | System MUST support dataset listing and comparison | SHOULD |
| PE-08 | System MUST include feature vectors in dataset samples | MUST |

#### 4.6.2 Deliverables

- `src/learning/domain/entities/dataset.py` — Dataset aggregate root
- `src/learning/domain/services/dataset_versioning.py` — Versioning logic
- `src/learning/application/services/dataset_service.py` — Enhanced dataset service
- `src/learning/infrastructure/persistence/dataset_repository.py` — Dataset persistence
- `src/learning/infrastructure/export/jsonl_exporter.py` — JSONL exporter
- `tests/learning/domain/test_dataset_versioning.py` — Versioning tests
- `tests/learning/infrastructure/test_jsonl_exporter.py` — Export tests

#### 4.6.3 Acceptance Criteria

- Datasets versioned with semantic versioning
- Checksums verify dataset integrity
- JSONL export produces valid JSONL files
- Train/test split maintains class balance (±5%)
- Dataset metadata queryable
- Versioned datasets immutable after creation

## 5. Non-Functional Requirements

### 5.1 Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Pipeline cycle time | ≤ 30 seconds | End-to-end pipeline execution |
| API response time | ≤ 200ms (p95) | HTTP response time |
| Database query time | ≤ 50ms (p95) | SQL execution time |
| Metric calculation | ≤ 5 seconds | Full metric suite computation |
| Dataset generation | ≤ 60 seconds | 1000-sample dataset |

### 5.2 Reliability

| Metric | Target | Measurement |
|--------|--------|-------------|
| Pipeline success rate | ≥ 95% | Successful runs / total runs |
| Data durability | 100% | No data loss on crash |
| Recovery time | ≤ 30 seconds | Time to resume after failure |
| Uptime | ≥ 99% | Excluding planned maintenance |

### 5.3 Observability

| Capability | Requirement |
|------------|-------------|
| Logging | Structured logs (JSON) for all operations |
| Metrics | Pipeline duration, items processed, errors |
| Tracing | Correlation IDs across pipeline stages |
| Alerting | Regression detection alerts (Phase D) |

### 5.4 Security

| Requirement | Implementation |
|-------------|----------------|
| Authentication | API key or JWT for feedback API |
| Authorization | Role-based (admin, editor, viewer) |
| Data isolation | Multi-tenant ready (future) |
| Audit trail | All decisions logged with timestamp |

### 5.5 Data Integrity

| Requirement | Implementation |
|-------------|----------------|
| Immutability | FeedbackRecord, DatasetVersion immutable |
| Referential integrity | FK constraints on all tables |
| Checksums | SHA-256 for dataset versions |
| Transactions | UnitOfWork for multi-entity operations |

## 6. Traceability Requirements

### 6.1 Data Lineage

Every data point MUST carry origin metadata:

```python
@dataclass(frozen=True)
class ProvenanceMetadata:
    source_article_id: str          # Original article/content ID
    source_name: str                # Publishing source
    feature_snapshot: FeatureSnapshot  # Computed features
    algorithm_version: AlgorithmVersion  # Version that processed it
    captured_at: datetime           # When captured
    pipeline_run_id: str            # Which pipeline run produced this
```

**Applies to**: FeedbackRecord, LearningSignal, PredictionDTO, DatasetSample

### 6.2 Recommendation Provenance

Every recommendation MUST be traceable to:

1. **Source news/article**: `article_id` field in RecommendationDTO
2. **Publishing source**: `source_name` field
3. **Computed features**: `FeatureSnapshot` (base_score, freshness, keywords, source_bonus, etc.)
4. **Human feedback received**: Linked FeedbackRecord via `topic_id`
5. **Algorithm version**: `AlgorithmVersion` string in RecommendationDTO

**API Response includes**: Full provenance chain for auditability

### 6.3 Dataset Reproducibility

Every dataset version MUST include:

```python
@dataclass(frozen=True)
class DatasetMetadata:
    version: str                    # Semantic version (1.0.0)
    checksum: str                   # SHA-256 of dataset content
    record_count: int               # Number of samples
    feature_count: int              # Number of features per sample
    time_window_start: datetime     # Earliest record included
    time_window_end: datetime       # Latest record included
    algorithm_version: AlgorithmVersion  # Version used to generate features
    created_at: datetime            # Generation timestamp
    parent_version: str | None      # Previous version (for lineage)
```

**Immutability**: Once created, dataset versions CANNOT be modified. New versions are created as new records.

### 6.4 Algorithm Versioning

Every algorithm change MUST be versioned:

```python
@dataclass(frozen=True)
class AlgorithmVersion:
    major: int    # Breaking changes (new formula)
    minor: int    # New features (additional weights)
    patch: int    # Bug fixes (corrections)
```

**Tracking**: Each PredictionDTO, RecommendationDTO, and DatasetMetadata includes `algorithm_version`. This enables:
- Comparing predictions across versions
- Rolling back to previous versions
- A/B testing different algorithms

## 7. Scenarios (Acceptance Criteria)

### 7.1 Phase 0 Scenarios

#### Scenario: Pipeline Continuous Operation

- GIVEN the scheduler is configured with 60-minute interval
- WHEN the system runs for 7 consecutive days
- THEN ≥ 160 pipeline cycles complete successfully
- AND no manual intervention is required
- AND system state is consistent at all times

#### Scenario: Pipeline Failure Recovery

- GIVEN a pipeline cycle fails due to network timeout
- WHEN the scheduler triggers the next cycle
- THEN the system resumes from where it left off
- AND the failure is logged with error details
- AND subsequent cycles complete successfully

#### Scenario: Duplicate Article Handling

- GIVEN an article with article_id "abc123" has been processed
- WHEN the same article appears in a subsequent pipeline run
- THEN the system detects the duplicate via article_id
- AND the article is skipped (not reprocessed)
- AND deduplication count is incremented

#### Scenario: System Restart Preservation

- GIVEN the system has processed 500 articles and accumulated scores
- WHEN the system is restarted (process killed and restarted)
- THEN all 500 articles and their scores are preserved
- AND the pipeline resumes from the last checkpoint
- AND no data is lost

### 7.2 Phase A Scenarios

#### Scenario: PostgreSQL Persistence

- GIVEN the system is configured with PostgreSQL connection
- WHEN a FeedbackRecord is created
- THEN the record is persisted in PostgreSQL
- AND the record can be retrieved by ID
- AND the record survives system restart

#### Scenario: UnitOfWork Transaction

- GIVEN a pipeline cycle creates multiple entities (signals, feedback, scores)
- WHEN the pipeline completes successfully
- THEN all entities are committed atomically
- AND no partial state exists in the database

#### Scenario: EventBridge Communication

- GIVEN an Ingestion event (ArticleCreated) is published
- WHEN the Learning BC receives the event
- THEN the corresponding Learning command is executed
- AND the event is acknowledged

#### Scenario: Scheduler Configuration

- GIVEN the scheduler is configured with custom interval (e.g., 30 minutes)
- WHEN the system starts
- THEN pipeline cycles execute every 30 minutes
- AND the interval can be changed without code modification

### 7.3 Phase B Scenarios

#### Scenario: Reddit Adapter

- GIVEN the Reddit adapter is configured for r/programming
- WHEN the adapter fetches articles
- THEN ≥ 10 articles are returned
- AND each article is normalized to common Article format
- AND source metadata is tracked

#### Scenario: Multi-Source Deduplication

- GIVEN the same article appears on Reddit and Hacker News
- WHEN both sources are processed
- THEN the system detects the duplicate (title similarity ≥ 0.9)
- AND the article is processed only once
- AND source attribution is preserved

#### Scenario: Rate Limit Handling

- GIVEN a knowledge source has rate limits (e.g., 60 requests/minute)
- WHEN the adapter exceeds the rate limit
- THEN the system backs off exponentially (1s, 2s, 4s, ...)
- AND retries after the backoff period
- AND does not crash or lose data

### 7.4 Phase C Scenarios

#### Scenario: CLI Feedback

- GIVEN pending content is displayed in CLI
- WHEN the user types "approve" or "reject" with reason
- THEN a FeedbackRecord is created
- AND SourceQualityProfile is updated
- AND FeedbackCaptured event is emitted

#### Scenario: Web UI Feedback

- GIVEN pending content is displayed in web UI
- WHEN the user clicks "Approve" or "Reject" button
- THEN a FeedbackRecord is created via API
- AND the UI updates to show next pending item
- AND feedback count is incremented

#### Scenario: Duplicate Feedback Prevention

- GIVEN a FeedbackRecord exists for content_id "xyz789"
- WHEN the user attempts to submit feedback for the same content_id
- THEN the system rejects the duplicate
- AND returns an error message
- AND the existing record is not modified

### 7.5 Phase D Scenarios

#### Scenario: Metric Calculation

- GIVEN 100 feedback records exist with 60 approved and 40 rejected
- WHEN the metrics service calculates Precision
- THEN Precision = 0.6 (60 / (60 + 0)) assuming no false positives
- AND the metric is stored with timestamp

#### Scenario: Improvement Detection

- GIVEN metrics for the last 30 days show Top-K Precision at 0.65
- WHEN metrics for the previous 30 days show Top-K Precision at 0.55
- THEN the system detects a positive trend (+0.10)
- AND improvement is flagged in the report

#### Scenario: Regression Detection

- GIVEN metrics for the last 7 days show Accuracy at 0.70
- WHEN metrics for the previous 7 days show Accuracy at 0.80
- THEN the system detects a regression (-12.5%)
- AND a regression alert is triggered
- AND the alert includes affected metrics and time window

### 7.6 Phase E Scenarios

#### Scenario: Dataset Generation

- GIVEN 500 FeedbackRecords exist with feature snapshots
- WHEN a dataset is generated for the last 30 days
- THEN a new DatasetVersion is created with version "1.0.0"
- AND the dataset contains 500 samples
- AND each sample includes all feature vectors
- AND a SHA-256 checksum is computed

#### Scenario: Dataset Versioning

- GIVEN DatasetVersion "1.0.0" exists
- WHEN a new dataset is generated
- THEN DatasetVersion "1.1.0" is created
- AND "1.0.0" remains unchanged (immutable)
- AND metadata includes parent_version = "1.0.0"

#### Scenario: Train/Test Split

- GIVEN a dataset with 1000 samples (600 approved, 400 rejected)
- WHEN a train/test split is generated (80/20)
- THEN training set contains 800 samples
- AND test set contains 200 samples
- AND class balance is maintained (±5%: 480/320 train, 120/80 test)

#### Scenario: JSONL Export

- GIVEN a DatasetVersion exists
- WHEN JSONL export is triggered
- THEN a valid JSONL file is produced
- AND each line is valid JSON
- AND the file can be loaded by standard JSONL readers

## 8. Validation Metrics & Measurement

### 8.1 Metric Definitions

| Metric | Calculation Method | Data Sources |
|--------|-------------------|--------------|
| Top-K Precision | Sort recommendations by probability, take top K, count approved / K | PredictionDTO, FeedbackRecord |
| Precision | TP / (TP + FP) from confusion matrix | PredictionDTO, FeedbackRecord |
| Recall | TP / (TP + FN) from confusion matrix | PredictionDTO, FeedbackRecord |
| Accuracy | (TP + TN) / (TP + TN + FP + FN) | PredictionDTO, FeedbackRecord |
| Recommendation Acceptance Rate | Count accepted / total recommendations | RecommendationDTO, FeedbackRecord |
| Feedback Coverage | Total feedback / total recommendations | FeedbackRecord, RecommendationDTO |
| Dataset Growth | New samples per week | DatasetMetadata |
| Signal Confidence | Average of min(1.0, total_samples / min_sample_size) | LearningSignal |
| Source Quality Evolution | StdDev of source_approval_rates | SourceQualityProfile |

### 8.2 Measurement Windows

| Window | Duration | Use Case |
|--------|----------|----------|
| Rolling 7d | Last 7 days | Short-term trends, regression detection |
| Rolling 30d | Last 30 days | Medium-term trends, improvement detection |
| All-time | Since system start | Long-term baseline, overall performance |

### 8.3 Improvement Criteria

The system is "learning" when:

1. **At least 3 of 5 core metrics** show positive trend over 30-day window
2. **Core metrics**: Top-K Precision, Precision, Accuracy, Recommendation Acceptance Rate, Signal Confidence
3. **Positive trend**: Current 30d value > Previous 30d value by ≥ 0.02 (2 percentage points)
4. **Statistical significance**: Trend is consistent (not due to random variation)

### 8.4 Regression Detection

Regression is detected when:

1. **Any core metric** decreases by ≥ 10% between consecutive 7-day windows
2. **Example**: Accuracy drops from 0.80 to 0.72 (-10%)
3. **Alert triggered**: System logs warning and flags for investigation
4. **No automatic rollback**: Human review required before action

## 9. Definition of Done

### Phase 0 Complete When:
- [ ] Pipeline runs 100 cycles without crash
- [ ] System recovers from 3 consecutive failures
- [ ] Deduplication catches 100% duplicates
- [ ] Restart preserves all state
- [ ] 7-day continuous run completes (≥ 95% success)

### Phase A Complete When:
- [ ] All 4 repositories pass PostgreSQL integration tests
- [ ] UnitOfWork commits/rollbacks correctly
- [ ] EventBridge publishes/subscribes events
- [ ] Scheduler runs at configured intervals
- [ ] Pipeline completes in ≤ 30 seconds
- [ ] Database handles 1000+ records

### Phase B Complete When:
- [ ] ≥ 3 knowledge source adapters implemented
- [ ] All articles normalized to common format
- [ ] Rate limits handled gracefully
- [ ] Cross-source deduplication works (≥ 90%)
- [ ] Source metadata tracked

### Phase C Complete When:
- [ ] CLI interface functional
- [ ] Web UI functional
- [ ] Feedback recorded with reason
- [ ] SourceQualityProfile updated
- [ ] FeedbackCaptured events emitted
- [ ] Duplicate feedback prevented

### Phase D Complete When:
- [ ] All 9 metrics calculated correctly
- [ ] Metrics tracked over rolling windows
- [ ] Improvement trends detected
- [ ] Regression detected (≥ 10% decrease)
- [ ] Metrics API functional
- [ ] Metric snapshots stored (≥ 90 days)

### Phase E Complete When:
- [ ] Datasets versioned (semantic versioning)
- [ ] Checksums computed (SHA-256)
- [ ] JSONL export functional
- [ ] Train/test splits maintain balance
- [ ] Dataset metadata queryable
- [ ] Versioned datasets immutable

## 10. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| PostgreSQL migration breaks existing tests | High | High | Run full test suite after each migration step. Keep InMemory for unit tests. |
| Scheduler introduces race conditions | Medium | High | Use database locks for concurrent access. Implement idempotent operations. |
| Knowledge source APIs change | Medium | Medium | Abstract behind Protocol ports. Implement adapter pattern with fallback. |
| Metric calculation performance degrades | Low | Medium | Index frequently queried columns. Cache metric snapshots. |
| Dataset generation blocks pipeline | Medium | Medium | Run dataset generation in background task. Use async operations. |
| Feedback volume exceeds capacity | Low | Low | Implement pagination. Add rate limiting on feedback API. |
| Algorithm versioning complexity | Medium | Low | Start with simple major.minor.patch. Extend only when needed. |

## 11. Future EPICs (Explicitly Out of Scope)

| EPIC | Description | Dependency |
|------|-------------|------------|
| EPIC 9 | Deployment infrastructure (Docker, K8s, CI/CD) | None |
| EPIC 10 | Advanced observability (Prometheus, Grafana) | None |
| EPIC 11 | ML training pipelines | EPIC 8 (datasets ready) |
| EPIC 12 | Content production (TTS, video) | EPIC 8 (recommendations) |
| EPIC 13 | LLM integration | EPIC 8 (feedback loop) |
| EPIC 14 | Research DDD migration | None |

---

**Document Version**: 1.0
**Created**: 2026-07-21
**Author**: SDD Spec Phase
**Status**: Complete — Ready for Design Phase