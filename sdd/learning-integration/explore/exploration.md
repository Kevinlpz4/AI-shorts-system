## Exploration: Cross-BC Integration for Learning BC

### Current State

The AI_Shorts_System has 2 BCs fully implemented in `src/`:
- **Ingestion BC** — Full 5-layer architecture (domain/application/infrastructure/presentation)
- **Learning BC** — Domain + Application layers only (Sprint 7.1)

**Foundation provides the integration infrastructure** but NO BC currently uses `IntegrationEvent`. The `IntegrationEvent` base class exists in `foundation/events/integration_event.py` and is fully tested (`tests/foundation/test_events.py`), but no concrete integration events have been implemented anywhere.

**Key architectural finding: There is ZERO existing integration between BCs.** The Learning BC has Protocol ports (`cross_bc.py`) for read-only access, but no concrete adapters. The Ingestion BC publishes DomainEvents internally (via `EventPublisher`) but nothing bridges them to other BCs.

### File Structure — Event-Related Code

```
src/foundation/
├── events/
│   ├── __init__.py                    # Exports DomainEvent, IntegrationEvent
│   ├── domain_event.py                # Base: event_id, event_version, occurred_at, event_name
│   ├── integration_event.py           # Base: + source_boundary, correlation_id, causation_id
│   └── _utcnow.py                     # datetime.now(timezone.utc) helper
├── base/
│   ├── aggregate_root.py              # register_event(), pull_events() — defensive copy
│   └── entity.py                      # Entity base with EntityId
├── ports/
│   ├── clock.py                       # ClockPort (Protocol), SystemClock, FrozenClock
│   └── uuid_provider.py              # UUIDProvider (Protocol), SystemUUIDProvider, SequentialUUIDProvider
├── result/
│   └── result.py                      # Result[T], Success[T], Failure[T], Error, ErrorCode
└── errors/
    └── base.py                        # FoundationError → DomainError, ApplicationError, InfrastructureError

src/ingestion/
├── domain/events/
│   └── ingestion_events.py            # RawArticleCollected, SourceEnabled, SourceDisabled
├── application/ports/
│   ├── event_publisher.py             # EventPublisher Protocol (publish/publish_many)
│   └── unit_of_work.py               # UnitOfWork Protocol
├── infrastructure/
│   ├── event_publisher.py             # SQLAlchemyEventPublisher — in-memory for testing
│   └── inmemory/
│       ├── event_publisher.py         # InMemoryEventPublisher — has clear(), has_event()
│       └── unit_of_work.py           # InMemoryUnitOfWork
│   └── persistence/
│       └── unit_of_work.py           # SQLAlchemyUnitOfWork — collects events from modified roots, publishes post-commit

src/learning/
├── domain/
│   ├── events/
│   │   ├── __init__.py               # Empty
│   │   └── learning_events.py        # FeedbackCaptured, SignalAggregated, ScoreAdjusted, DatasetGenerated, LearningModelUpdated
│   └── ports/
│       ├── cross_bc.py                # IngestionReader, ResearchReader (Protocol, read-only)
│       └── repositories.py           # 4 Repository Protocols
├── application/ports/
│   ├── event_publisher.py             # EventPublisher Protocol (generic)
│   ├── learning_event_publisher.py    # LearningEventPublisher Protocol (typed methods per event)
│   ├── unit_of_work.py               # UnitOfWork Protocol
│   └── clock.py                       # ClockPort Protocol
└── application/services/
    ├── decision_service.py            # Uses EventPublisher — pull_events() after commit
    ├── signal_service.py              # Uses EventPublisher — pull_events() after commit
    └── scoring_service.py            # Uses EventPublisher — pull_events() after commit
```

### IntegrationEvent Field Pattern

```python
@dataclass(frozen=True)
class IntegrationEvent:
    event_id: UUID = field(default_factory=uuid4)
    event_version: int = 1
    source_boundary: str = ""          # REQUIRED: which BC published
    correlation_id: str | None = None  # Chain of traceability across BCs
    causation_id: UUID | None = None   # Which DomainEvent caused this
    occurred_at: datetime = field(default_factory=_utcnow)
    
    @property
    def event_name(self) -> str:       # Computed, not a field
        return type(self).__name__
```

**Key differences from DomainEvent:**
- `source_boundary` — identifies the publishing BC (e.g., "learning", "ingestion")
- `correlation_id` — traces a chain of events across BCs
- `causation_id` — links to the specific DomainEvent that triggered this IntegrationEvent
- All payload fields MUST be serializable (no domain objects, only primitives/VOs)

### How Events Are Published and Consumed

**Current pattern (Ingestion BC — the ONLY published example):**

1. **Domain entity** calls `self.register_event(DomainEvent(...))` in constructor/method
2. **Application service** calls `self._uow.commit()` → SQLAlchemyUnitOfWork collects events from modified roots via `register_modified(root)` → `_collect_events()` → `publish_many(events)`
3. **EventPublisher** stores events in-memory (no external dispatch)

**Flow in DecisionService (Learning BC):**
```python
with self._uow:
    feedback = FeedbackRecord(...)  # register_event(FeedbackCaptured(...)) in __init__
    self._feedback_repo.save(feedback)
    self._uow.commit()
    events = feedback.pull_events()  # defensive copy
    if events:
        self._event_publisher.publish_many(events)
```

**NO dispatcher pattern exists.** Events are published but NOT consumed by any handler/subscriber in the current codebase. The `SignalRegistry` handles signal computation, not event dispatch.

### Existing Adapter/Dispatcher Patterns

| Pattern | Exists? | Details |
|---------|---------|---------|
| IntegrationEvent base class | ✅ | Foundation — fully implemented and tested |
| Concrete IntegrationEvent subclasses | ❌ | None implemented anywhere |
| EventDispatcher / EventBus | ❌ | No dispatch mechanism exists |
| Event Subscriber / Handler | ❌ | No subscription pattern |
| Outbox Pattern | ❌ | Mentioned in comments but not implemented |
| Cross-BC Adapters | ❌ | Protocol ports exist (cross_bc.py) but no implementations |
| Event Store / Persistence | ❌ | Events are transient (not persisted) |

### Learning Domain Events — Current Fields

| Event | Fields | Inheritance |
|-------|--------|-------------|
| FeedbackCaptured | feedback_id, topic_id, decision, source_name, captured_at | DomainEvent |
| SignalAggregated | signal_id, signal_type, dimension, strength_value, window | DomainEvent |
| ScoreAdjusted | model_id, old_weights, new_weights, reason, adjusted_at | DomainEvent |
| DatasetGenerated | dataset_id, version, record_count, format, generated_at | DomainEvent |
| LearningModelUpdated | model_id, old_version, new_version, updated_at | DomainEvent |

All use the MISSING sentinel pattern for required fields in frozen dataclass inheritance.

### Cross-BC Ports — Current State

```python
# src/learning/domain/ports/cross_bc.py
class IngestionReader(Protocol):
    def get_article_features(self, article_id: str) -> Result[dict]: ...
    def get_source_config(self, source_name: str) -> Result[dict]: ...

class ResearchReader(Protocol):
    def get_topic_score(self, topic_id: str) -> Result[dict]: ...
    def get_topic_details(self, topic_id: str) -> Result[dict]: ...
```

These are READ-ONLY ports. No write-side integration exists. No concrete implementations exist.

### Affected Areas

- `src/learning/domain/events/` — New integration events (concrete subclasses of IntegrationEvent)
- `src/learning/domain/ports/cross_bc.py` — Add IntegrationEventPort for publishing integration events
- `src/learning/application/ports/` — New IntegrationEventPublisher port
- `src/learning/application/services/` — Services need to produce integration events from domain events
- `src/learning/infrastructure/` — NEW directory needed for concrete adapters and integration implementations
- `src/ingestion/infrastructure/` — May need adapter to expose data for Learning BC's IngestionReader

### Approaches

1. **Outbox Pattern (Domain Events → Integration Events)**
   - Domain entities emit DomainEvents as today
   - Application services map DomainEvents → IntegrationEvents via a translator
   - IntegrationEvents are published through an IntegrationEventPublisher
   - Adapters in infrastructure implement cross-BC read ports
   - Pros: Clean separation, follows existing patterns, testable
   - Cons: Requires new infrastructure layer for Learning BC
   - Effort: Medium

2. **Event Sourcing / Event Bus**
   - Central event bus dispatches events to subscribers
   - Each BC subscribes to events from other BCs
   - Pros: Loose coupling, scalable
   - Cons: Over-engineering for current system size, no existing bus infrastructure
   - Effort: High

3. **Direct Adapter (Synchronous Cross-BC Calls)**
   - Learning BC calls Ingestion/Research BCs directly via adapters
   - No integration events, just Protocol implementations
   - Pros: Simple, no new infrastructure
   - Cons: Tight coupling, no event traceability, no async capability
   - Effort: Low

### Recommendation

**Approach 1 — Outbox Pattern with Domain → Integration Event Mapping.**

Reasons:
- Foundation already provides `IntegrationEvent` with all needed fields (correlation_id, causation_id, source_boundary)
- The Learning BC already has `EventPublisher` ports — extend with `IntegrationEventPublisher`
- The MISSING sentinel pattern and frozen dataclass inheritance are established
- The service layer already follows the `commit → pull_events → publish` pattern
- This is the natural evolution — not a new pattern, just completing the existing one

Architecture:
```
Learning Domain → DomainEvent (internal) → Application Service maps → IntegrationEvent (cross-BC)
                                                                    ↓
                                                          IntegrationEventPublisher (Port)
                                                                    ↓
                                                          InMemoryIntegrationPublisher (Adapter)
                                                                    ↓
                                                          EventDispatcher (routes to subscribers)
```

### Risks

- **No EventDispatcher exists** — the dispatch/subscription mechanism needs to be built from scratch. This is the biggest gap.
- **No Research BC in `src/`** — `ResearchReader` port has no implementation target. Need to create a stub adapter.
- **Learning BC has no infrastructure layer** — needs `src/learning/infrastructure/` with adapters, publishers, and potentially an event store.
- **IntegrationEvent has no serialization** — `IntegrationEvent` explicitly says "no assumed serialization format." Need to decide on JSON serialization for the publisher.

### Ready for Proposal

Yes. The exploration reveals a clear path:
1. Create integration events in `src/learning/domain/events/integration_events.py`
2. Add `IntegrationEventPublisher` port in `src/learning/application/ports/`
3. Create `src/learning/infrastructure/` with concrete adapters
4. Build a simple in-memory EventDispatcher for cross-BC routing
5. Map DomainEvents → IntegrationEvents in application services
6. Implement concrete adapters for IngestionReader and ResearchReader
