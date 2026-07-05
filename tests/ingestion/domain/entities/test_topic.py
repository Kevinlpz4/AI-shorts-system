"""
Tests for Topic entity.

Covers:
  - Construction (valid/invalid)
  - Invariants (I-22, I-23)
  - Behavior (rename, update_description, activate, deactivate)
  - Equality and hash
"""

from __future__ import annotations

import pytest

from foundation.base.entity import Entity

from ingestion.domain.entities.ids import TopicId
from ingestion.domain.entities.topic import Topic


class TestTopicCreation:
    def test_create_valid_topic(self, topic_id: TopicId) -> None:
        topic = Topic(
            id=topic_id,
            name="Artificial Intelligence",
            description="AI and ML related content",
        )
        assert topic.id == topic_id
        assert topic.name == "Artificial Intelligence"
        assert topic.description == "AI and ML related content"
        assert topic.is_active is True

    def test_create_without_description(self, topic_id: TopicId) -> None:
        topic = Topic(id=topic_id, name="Climate Change")
        assert topic.description is None

    def test_empty_name_raises(self, topic_id: TopicId) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            Topic(id=topic_id, name="")

    def test_whitespace_name_raises(self, topic_id: TopicId) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            Topic(id=topic_id, name="   ")

    def test_inherits_entity(self, topic: Topic) -> None:
        assert isinstance(topic, Entity)

    def test_equality_by_id(self, topic_id: TopicId) -> None:
        topic1 = Topic(id=topic_id, name="AI")
        topic2 = Topic(id=topic_id, name="Different")
        assert topic1 == topic2

    def test_inequality(self, topic_id: TopicId) -> None:
        topic1 = Topic(id=topic_id, name="AI")
        topic2 = Topic(id=TopicId.generate(), name="AI")
        assert topic1 != topic2


class TestTopicBehavior:
    def test_rename(self, topic: Topic) -> None:
        topic.rename("Machine Learning")
        assert topic.name == "Machine Learning"

    def test_rename_empty_raises(self, topic: Topic) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            topic.rename("")

    def test_rename_whitespace_raises(self, topic: Topic) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            topic.rename("   ")

    def test_update_description(self, topic: Topic) -> None:
        topic.update_description("Updated description")
        assert topic.description == "Updated description"

    def test_update_description_to_none(self, topic: Topic) -> None:
        topic.update_description(None)
        assert topic.description is None

    def test_activate(self, topic: Topic) -> None:
        topic.is_active = False
        topic.activate()
        assert topic.is_active is True

    def test_deactivate(self, topic: Topic) -> None:
        topic.deactivate()
        assert topic.is_active is False

    def test_rename_trims_whitespace(self, topic: Topic) -> None:
        topic.rename("  New Name  ")
        assert topic.name == "New Name"
