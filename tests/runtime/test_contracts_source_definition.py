"""
Tests for SourceDefinition, RetryPolicy, RateLimitConfig, AuthConfig.

Covers:
- RetryPolicy default and custom construction
- RateLimitConfig default and custom construction
- AuthConfig construction
- SourceDefinition default and custom construction
- Immutability (frozen)
"""
from __future__ import annotations

from datetime import timedelta

import pytest

from runtime.contracts.source_definition import (
    AuthConfig,
    RateLimitConfig,
    RetryPolicy,
    SourceDefinition,
)


class TestRetryPolicy:
    """Tests for RetryPolicy frozen dataclass."""

    def test_default_construction(self) -> None:
        """RetryPolicy has sensible defaults."""
        policy = RetryPolicy()

        assert policy.max_retries == 3
        assert policy.base_delay == timedelta(seconds=1)
        assert policy.max_delay == timedelta(seconds=60)
        assert policy.exponential_base == 2.0

    def test_custom_construction(self) -> None:
        """RetryPolicy accepts custom values."""
        policy = RetryPolicy(
            max_retries=5,
            base_delay=timedelta(seconds=2),
            max_delay=timedelta(seconds=120),
            exponential_base=3.0,
        )

        assert policy.max_retries == 5
        assert policy.base_delay == timedelta(seconds=2)
        assert policy.max_delay == timedelta(seconds=120)
        assert policy.exponential_base == 3.0

    def test_frozen_immutability(self) -> None:
        """RetryPolicy is frozen."""
        policy = RetryPolicy()

        with pytest.raises(AttributeError):
            policy.max_retries = 10  # type: ignore[misc]


class TestRateLimitConfig:
    """Tests for RateLimitConfig frozen dataclass."""

    def test_default_construction(self) -> None:
        """RateLimitConfig has sensible defaults."""
        config = RateLimitConfig()

        assert config.requests_per_minute == 60
        assert config.burst == 10

    def test_custom_construction(self) -> None:
        """RateLimitConfig accepts custom values."""
        config = RateLimitConfig(requests_per_minute=120, burst=20)

        assert config.requests_per_minute == 120
        assert config.burst == 20

    def test_frozen_immutability(self) -> None:
        """RateLimitConfig is frozen."""
        config = RateLimitConfig()

        with pytest.raises(AttributeError):
            config.burst = 50  # type: ignore[misc]


class TestAuthConfig:
    """Tests for AuthConfig frozen dataclass."""

    def test_construction(self) -> None:
        """AuthConfig accepts type and credentials."""
        auth = AuthConfig(
            auth_type="api_key",
            credentials={"key": "abc123"},
        )

        assert auth.auth_type == "api_key"
        assert auth.credentials == {"key": "abc123"}

    def test_default_credentials(self) -> None:
        """AuthConfig defaults to empty credentials dict."""
        auth = AuthConfig(auth_type="bearer")

        assert auth.auth_type == "bearer"
        assert auth.credentials == {}

    def test_frozen_immutability(self) -> None:
        """AuthConfig is frozen."""
        auth = AuthConfig(auth_type="basic")

        with pytest.raises(AttributeError):
            auth.auth_type = "oauth2"  # type: ignore[misc]


class TestSourceDefinition:
    """Tests for SourceDefinition frozen dataclass."""

    def test_minimal_construction(self) -> None:
        """SourceDefinition requires id, provider, and technology."""
        source = SourceDefinition(
            id="src-1",
            provider="rss",
            technology="rss",
        )

        assert source.id == "src-1"
        assert source.provider == "rss"
        assert source.technology == "rss"
        assert source.categories == []
        assert source.enabled is True
        assert source.priority == 0
        assert source.poll_interval == timedelta(minutes=30)
        assert source.authentication is None
        assert source.retry_policy == RetryPolicy()
        assert source.rate_limit == RateLimitConfig()
        assert source.default_tags == []
        assert source.metadata == {}

    def test_full_construction(self) -> None:
        """SourceDefinition accepts all fields."""
        source = SourceDefinition(
            id="src-2",
            provider="newsapi",
            technology="api",
            categories=["tech", "science"],
            enabled=False,
            priority=5,
            poll_interval=timedelta(minutes=15),
            authentication=AuthConfig(
                auth_type="api_key",
                credentials={"key": "xyz"},
            ),
            retry_policy=RetryPolicy(max_retries=5),
            rate_limit=RateLimitConfig(requests_per_minute=30),
            default_tags=["ai", "ml"],
            metadata={"region": "us-east-1"},
        )

        assert source.id == "src-2"
        assert source.provider == "newsapi"
        assert source.technology == "api"
        assert source.categories == ["tech", "science"]
        assert source.enabled is False
        assert source.priority == 5
        assert source.poll_interval == timedelta(minutes=15)
        assert source.authentication is not None
        assert source.authentication.auth_type == "api_key"
        assert source.retry_policy.max_retries == 5
        assert source.rate_limit.requests_per_minute == 30
        assert source.default_tags == ["ai", "ml"]
        assert source.metadata == {"region": "us-east-1"}

    def test_frozen_immutability(self) -> None:
        """SourceDefinition is frozen."""
        source = SourceDefinition(
            id="src-1",
            provider="rss",
            technology="rss",
        )

        with pytest.raises(AttributeError):
            source.enabled = False  # type: ignore[misc]
