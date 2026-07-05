"""Tests for SyncMode enum."""

from __future__ import annotations

from ingestion.domain.value_objects.sync_mode import SyncMode


class TestSyncMode:
    def test_values(self) -> None:
        assert SyncMode.PULL.value == "PULL"
        assert SyncMode.PUSH.value == "PUSH"
        assert SyncMode.STREAM.value == "STREAM"
        assert SyncMode.MANUAL.value == "MANUAL"

    def test_members_count(self) -> None:
        assert len(SyncMode) == 4
