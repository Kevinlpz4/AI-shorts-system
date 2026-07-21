"""
Source definition contracts for the Runtime layer.

Defines the declarative configuration for data sources, including
retry policies, rate limits, and authentication.

Usage::

    from runtime.contracts.source_definition import SourceDefinition, RetryPolicy

    source = SourceDefinition(
        id="techcrunch-rss",
        provider="rss",
        technology="rss",
        poll_interval=timedelta(minutes=15),
    )
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta


@dataclass(frozen=True)
class RetryPolicy:
    """Retry configuration for source fetching.

    Attributes:
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay between retries.
        max_delay: Maximum delay cap (for exponential backoff).
        exponential_base: Base for exponential backoff calculation.
    """

    max_retries: int = 3
    base_delay: timedelta = timedelta(seconds=1)
    max_delay: timedelta = timedelta(seconds=60)
    exponential_base: float = 2.0


@dataclass(frozen=True)
class RateLimitConfig:
    """Rate limiting configuration for source fetching.

    Attributes:
        requests_per_minute: Maximum requests per minute.
        burst: Maximum burst size for token bucket.
    """

    requests_per_minute: int = 60
    burst: int = 10


@dataclass(frozen=True)
class AuthConfig:
    """Authentication configuration for a source.

    Attributes:
        auth_type: Authentication method (``"api_key"``, ``"bearer"``,
            ``"basic"``, ``"oauth2"``).
        credentials: Key-value pairs for authentication. The exact keys
            depend on ``auth_type``.
    """

    auth_type: str  # "api_key", "bearer", "basic", "oauth2"
    credentials: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SourceDefinition:
    """Declarative definition of a data source.

    A SourceDefinition captures everything the Runtime needs to know about
    a source to fetch data from it. Adding a new source of the same
    technology (e.g., RSS) = 1 SourceDefinition + 0 new code.

    Attributes:
        id: Unique identifier for this source.
        provider: Provider name (e.g., ``"rss"``, ``"newsapi"``).
        technology: Technology group (``"rss"``, ``"api"``, ``"graphql"``,
            ``"webhook"``).
        categories: Content categories this source covers.
        enabled: Whether this source is active.
        priority: Higher priority sources are fetched first.
        poll_interval: How often to fetch new data.
        authentication: Optional authentication configuration.
        retry_policy: Retry configuration for fetch failures.
        rate_limit: Rate limiting configuration.
        default_tags: Tags applied to all items from this source.
        metadata: Arbitrary key-value metadata.
    """

    id: str
    provider: str
    technology: str  # "rss", "api", "graphql", "webhook"
    categories: list[str] = field(default_factory=list)
    enabled: bool = True
    priority: int = 0
    poll_interval: timedelta = timedelta(minutes=30)
    authentication: AuthConfig | None = None
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    default_tags: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
