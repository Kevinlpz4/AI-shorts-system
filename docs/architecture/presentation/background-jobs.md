# Design: Background Jobs

**Epic**: 6 — Presentation Layer & External Adapters Design
**Version**: 1.0
**Status**: Design-only — interfaces defined, not implemented

---

## 1. Purpose

Define interfaces for future background job processing. The Presentation Layer triggers jobs; the actual execution is handled by a task queue (Celery, APScheduler, or custom). This document captures the DESIGN ONLY — no implementation in Epic 6.

## 2. Job Types

| Job | Trigger | Source | Description |
|-----|---------|--------|-------------|
| RSS Fetch | Scheduler | Feed entity sync_policy | Periodic RSS/Atom feed collection |
| Webhook Delivery | Event | Domain Events | POST to external webhook URLs |
| Cleanup | Scheduler | System | Remove stale articles, expired sessions |
| Notification | Event | Domain Events | Alert on feed failures, state changes |

## 3. Task Queue Abstraction (Port)

```python
# application/ports/task_queue.py
from typing import Protocol
from dataclasses import dataclass

@dataclass(frozen=True)
class TaskResult:
    task_id: str
    status: str  # "pending", "running", "completed", "failed"
    result: dict | None = None
    error: str | None = None

class TaskQueue(Protocol):
    """Port for background task execution."""

    def enqueue(self, task_name: str, payload: dict) -> str:
        """Enqueue a task. Returns task_id."""
        ...

    def get_status(self, task_id: str) -> TaskResult:
        """Get task status by ID."""
        ...

    def cancel(self, task_id: str) -> bool:
        """Cancel a pending task."""
        ...
```

## 4. Job Status Tracking

```python
@dataclass(frozen=True)
class JobStatus:
    job_id: str
    job_type: str
    status: str  # "queued", "running", "completed", "failed"
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    retry_count: int = 0
```

## 5. RSS Collection Integration (Future)

```
Scheduler triggers every N minutes
    │
    ▼
FetchFeedJob(feed_id)
    │
    ▼
FeedService.execute_record_collection(cmd)
    │
    ▼
Result[FeedDetailDTO]
```

## 6. Adapter Implementations (Future)

| Adapter | Technology | Use Case |
|---------|-----------|----------|
| `CeleryTaskQueue` | Celery + Redis | Production task queue |
| `InMemoryTaskQueue` | Dict + threading | Testing |
| `APSchedulerTaskQueue` | APScheduler | Simple scheduler |

## 7. Integration Points

Background jobs will integrate with:
- `FeedService.execute_record_collection()` — for RSS fetch results
- `FeedService.execute_record_failure()` — for fetch failures
- Domain Events — for event-driven triggers

---

*See also: `external-adapters.md`, `presentation-design.md`*
