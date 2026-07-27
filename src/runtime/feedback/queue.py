"""
Decision queue — manages pending items for human review.

Design principles:
    1. Queue is in-memory only (no persistence at this level).
    2. Items flow: pending → processed (approved/rejected/skipped).
    3. get_next() always returns the oldest pending item.
    4. All mutating operations return Result[T].
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid

from foundation.result.result import Error, ErrorCode, Result


@dataclass
class QueueItem:
    """An item in the decision queue."""

    id: str
    article_id: str
    provider: str
    source: str
    category: str
    topic: str
    score: float
    recommendation: str
    added_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "pending"
    metadata: Dict = field(default_factory=dict)
    # Presentation fields (optional — CLI hides when empty)
    title: Optional[str] = None
    url: Optional[str] = None
    published: Optional[str] = None
    summary: Optional[str] = None


class DecisionQueue:
    """Manages pending items for human review.

    Items are added via ``add()``, retrieved via ``get_next()``,
    and processed via ``process()``. Statistics are available via
    ``get_stats()``.
    """

    def __init__(self) -> None:
        self._items: List[QueueItem] = []
        self._processed: List[QueueItem] = []

    def add(
        self,
        article_id: str,
        provider: str,
        source: str,
        category: str,
        topic: str,
        score: float,
        recommendation: str,
        metadata: Optional[Dict] = None,
        title: Optional[str] = None,
        url: Optional[str] = None,
        published: Optional[str] = None,
        summary: Optional[str] = None,
    ) -> Result[QueueItem]:
        """Add an item to the queue."""
        item = QueueItem(
            id=str(uuid.uuid4()),
            article_id=article_id,
            provider=provider,
            source=source,
            category=category,
            topic=topic,
            score=score,
            recommendation=recommendation,
            added_at=datetime.now(timezone.utc),
            metadata=metadata or {},
            title=title,
            url=url,
            published=published,
            summary=summary,
        )
        self._items.append(item)
        return Result.success(item)

    def get_next(self) -> Result[Optional[QueueItem]]:
        """Get the next pending item (oldest first)."""
        pending = [i for i in self._items if i.status == "pending"]
        if not pending:
            return Result.success(None)
        return Result.success(pending[0])

    def process(
        self,
        item_id: str,
        decision: str,
        reason: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> Result[QueueItem]:
        """Process a decision on a queue item."""
        for item in self._items:
            if item.id == item_id:
                item.status = decision
                self._processed.append(item)
                return Result.success(item)
        return Result.failure(
            Error(code=ErrorCode.UNKNOWN, message=f"Item {item_id} not found")
        )

    def get_stats(self) -> Dict[str, int]:
        """Get queue statistics."""
        pending = len([i for i in self._items if i.status == "pending"])
        approved = len([i for i in self._processed if i.status == "approved"])
        rejected = len([i for i in self._processed if i.status == "rejected"])
        skipped = len([i for i in self._processed if i.status == "skipped"])
        return {
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "skipped": skipped,
            "total": len(self._items),
        }
