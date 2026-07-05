"""
Tests for Ingestion Domain IDs.

Covers:
  - Construction (generate, from_string)
  - Equality (type safety, value equality)
  - String representation
"""

from __future__ import annotations

from uuid import UUID

import pytest

from ingestion.domain.entities.ids import (
    CategoryId,
    FeedId,
    RawArticleId,
    SourceId,
    TopicId,
)


class TestSourceId:
    def test_generate_creates_valid_id(self) -> None:
        sid = SourceId.generate()
        assert isinstance(sid, SourceId)
        assert isinstance(sid.value, UUID)

    def test_from_string_roundtrip(self) -> None:
        sid = SourceId.generate()
        sid2 = SourceId.from_string(str(sid))
        assert sid == sid2

    def test_from_string_raises_on_invalid(self) -> None:
        with pytest.raises(ValueError):
            SourceId.from_string("not-a-uuid")

    def test_str_representation(self) -> None:
        sid = SourceId(value=UUID("12345678-1234-5678-1234-567812345678"))
        assert str(sid) == "12345678-1234-5678-1234-567812345678"

    def test_type_safety(self) -> None:
        uuid_val = UUID("12345678-1234-5678-1234-567812345678")
        sid = SourceId(value=uuid_val)
        fid = FeedId(value=uuid_val)
        assert sid != fid
        assert sid == sid
        assert fid == fid


class TestFeedId:
    def test_generate_creates_valid_id(self) -> None:
        fid = FeedId.generate()
        assert isinstance(fid, FeedId)
        assert isinstance(fid.value, UUID)

    def test_from_string_roundtrip(self) -> None:
        fid = FeedId.generate()
        fid2 = FeedId.from_string(str(fid))
        assert fid == fid2

    def test_type_safety_with_source_id(self) -> None:
        uuid_val = UUID("12345678-1234-5678-1234-567812345678")
        fid = FeedId(value=uuid_val)
        sid = SourceId(value=uuid_val)
        assert fid != sid


class TestRawArticleId:
    def test_generate_creates_valid_id(self) -> None:
        rid = RawArticleId.generate()
        assert isinstance(rid, RawArticleId)

    def test_from_string_roundtrip(self) -> None:
        rid = RawArticleId.generate()
        rid2 = RawArticleId.from_string(str(rid))
        assert rid == rid2

    def test_type_safety(self) -> None:
        uuid_val = UUID("12345678-1234-5678-1234-567812345678")
        rid = RawArticleId(value=uuid_val)
        fid = FeedId(value=uuid_val)
        assert rid != fid


class TestCategoryId:
    def test_generate_creates_valid_id(self) -> None:
        cid = CategoryId.generate()
        assert isinstance(cid, CategoryId)

    def test_from_string_roundtrip(self) -> None:
        cid = CategoryId.generate()
        cid2 = CategoryId.from_string(str(cid))
        assert cid == cid2

    def test_type_safety(self) -> None:
        uuid_val = UUID("12345678-1234-5678-1234-567812345678")
        cid = CategoryId(value=uuid_val)
        sid = SourceId(value=uuid_val)
        assert cid != sid


class TestTopicId:
    def test_generate_creates_valid_id(self) -> None:
        tid = TopicId.generate()
        assert isinstance(tid, TopicId)

    def test_from_string_roundtrip(self) -> None:
        tid = TopicId.generate()
        tid2 = TopicId.from_string(str(tid))
        assert tid == tid2

    def test_type_safety(self) -> None:
        uuid_val = UUID("12345678-1234-5678-1234-567812345678")
        tid = TopicId(value=uuid_val)
        cid = CategoryId(value=uuid_val)
        assert tid != cid
