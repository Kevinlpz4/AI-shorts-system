"""Tests for SyncPolicy value object."""

from __future__ import annotations

import pytest

from ingestion.domain.value_objects.sync_mode import SyncMode
from ingestion.domain.value_objects.sync_policy import SyncPolicy


class TestSyncPolicyValidation:
    def test_pull_with_interval(self) -> None:
        policy = SyncPolicy(mode=SyncMode.PULL, interval_minutes=30)
        assert policy.mode == SyncMode.PULL
        assert policy.interval_minutes == 30

    def test_pull_without_interval_raises(self) -> None:
        with pytest.raises(ValueError, match="PULL mode requires"):
            SyncPolicy(mode=SyncMode.PULL)

    def test_push_without_interval(self) -> None:
        policy = SyncPolicy(mode=SyncMode.PUSH)
        assert policy.interval_minutes is None

    def test_stream_without_interval(self) -> None:
        policy = SyncPolicy(mode=SyncMode.STREAM)
        assert policy.interval_minutes is None

    def test_manual_without_interval(self) -> None:
        policy = SyncPolicy(mode=SyncMode.MANUAL)
        assert policy.interval_minutes is None

    def test_default_values(self) -> None:
        policy = SyncPolicy(mode=SyncMode.PUSH)
        assert policy.max_retries == 3
        assert policy.backoff_multiplier == 2.0
        assert policy.max_backoff_minutes == 60
        assert policy.timeout_seconds == 30
        assert policy.max_items_per_run == 100

    def test_negative_max_retries_raises(self) -> None:
        with pytest.raises(ValueError, match="max_retries must be >= 0"):
            SyncPolicy(mode=SyncMode.PULL, interval_minutes=30, max_retries=-1)

    def test_zero_retries_valid(self) -> None:
        policy = SyncPolicy(mode=SyncMode.PULL, interval_minutes=30, max_retries=0)
        assert policy.max_retries == 0

    def test_zero_timeout_raises(self) -> None:
        with pytest.raises(ValueError, match="timeout_seconds must be > 0"):
            SyncPolicy(mode=SyncMode.PULL, interval_minutes=30, timeout_seconds=0)

    def test_negative_timeout_raises(self) -> None:
        with pytest.raises(ValueError, match="timeout_seconds must be > 0"):
            SyncPolicy(mode=SyncMode.PULL, interval_minutes=30, timeout_seconds=-1)

    def test_zero_max_items_raises(self) -> None:
        with pytest.raises(ValueError, match="max_items_per_run must be > 0"):
            SyncPolicy(mode=SyncMode.PULL, interval_minutes=30, max_items_per_run=0)

    def test_backoff_multiplier_one_raises(self) -> None:
        with pytest.raises(ValueError, match="backoff_multiplier must be > 1.0"):
            SyncPolicy(mode=SyncMode.PULL, interval_minutes=30, backoff_multiplier=1.0)

    def test_backoff_multiplier_less_than_one_raises(self) -> None:
        with pytest.raises(ValueError, match="backoff_multiplier must be > 1.0"):
            SyncPolicy(mode=SyncMode.PULL, interval_minutes=30, backoff_multiplier=0.5)

    def test_zero_max_backoff_raises(self) -> None:
        with pytest.raises(ValueError, match="max_backoff_minutes must be > 0"):
            SyncPolicy(mode=SyncMode.PULL, interval_minutes=30, max_backoff_minutes=0)

    def test_frozen_immutable(self) -> None:
        policy = SyncPolicy(mode=SyncMode.PULL, interval_minutes=30)
        with pytest.raises(Exception):
            policy.mode = SyncMode.PUSH

    def test_equality_by_value(self) -> None:
        p1 = SyncPolicy(mode=SyncMode.PULL, interval_minutes=30)
        p2 = SyncPolicy(mode=SyncMode.PULL, interval_minutes=30)
        assert p1 == p2

    def test_inequality(self) -> None:
        p1 = SyncPolicy(mode=SyncMode.PULL, interval_minutes=30)
        p2 = SyncPolicy(mode=SyncMode.PULL, interval_minutes=60)
        assert p1 != p2
