"""
Provider result contract — output of a provider adapter fetch operation.

Usage::

    from runtime.contracts.provider_result import ProviderResult

    result = ProviderResult(
        source_id="techcrunch-rss",
        provider="rss",
        items=[{"title": "...", "url": "..."}],
    )
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class ProviderResult:
    """Result of a provider adapter fetch operation.

    Attributes:
        source_id: The source that was fetched.
        provider: The provider that performed the fetch.
        items: List of raw items (dicts) fetched from the source.
        fetched_at: Timestamp when the fetch was completed.
        metadata: Provider-specific metadata about the fetch.
        errors: Error messages if the fetch was partial or had issues.
    """

    source_id: str
    provider: str
    items: list[dict[str, str]] = field(default_factory=list)
    fetched_at: datetime | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
