"""Tests for SourceType enum."""

from __future__ import annotations

from ingestion.domain.value_objects.source_type import SourceType


class TestSourceType:
    def test_values(self) -> None:
        assert SourceType.RSS.value == "RSS"
        assert SourceType.API.value == "API"
        assert SourceType.SOCIAL_MEDIA.value == "SOCIAL_MEDIA"
        assert SourceType.NEWSLETTER.value == "NEWSLETTER"

    def test_members_count(self) -> None:
        assert len(SourceType) == 4

    def test_str_representation(self) -> None:
        assert str(SourceType.RSS) == "SourceType.RSS"
