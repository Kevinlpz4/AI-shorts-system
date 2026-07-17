"""Tests for Learning BC Entity IDs."""
import uuid

from learning.domain.entities.ids import (
    FeedbackId,
    LearningModelId,
    LearningSignalId,
    SourceQualityId,
)
from foundation.entity_id import EntityId


class TestEntityIds:
    """All IDs must inherit EntityId, generate unique UUIDs, and be type-safe."""

    def test_all_ids_inherit_entity_id(self):
        for cls in (FeedbackId, LearningSignalId, SourceQualityId, LearningModelId):
            assert issubclass(cls, EntityId)

    def test_generate_returns_unique_ids(self):
        ids = {FeedbackId.generate() for _ in range(50)}
        assert len(ids) == 50

    def test_from_string_roundtrip(self):
        uid = uuid.uuid4()
        fid = FeedbackId.from_string(str(uid))
        assert str(fid) == str(uid)

    def test_different_id_types_not_equal(self):
        uid = uuid.uuid4()
        a = FeedbackId.from_string(str(uid))
        b = LearningSignalId.from_string(str(uid))
        assert a != b

    def test_id_str_representation(self):
        fid = FeedbackId.generate()
        assert isinstance(str(fid), str)
        assert len(str(fid)) == 36  # UUID format

    def test_id_equality_same_value(self):
        uid = uuid.uuid4()
        a = FeedbackId.from_string(str(uid))
        b = FeedbackId.from_string(str(uid))
        assert a == b
