"""
Tests for decision queue.
"""
from __future__ import annotations


from runtime.feedback.queue import DecisionQueue, QueueItem


class TestQueueItem:
    """Tests for QueueItem dataclass."""

    def test_creation(self):
        item = QueueItem(
            id="item-001",
            article_id="art-001",
            provider="google_news_ai",
            source="https://example.com",
            category="ai",
            topic="llm",
            score=0.85,
            recommendation="Test rec",
        )
        assert item.status == "pending"
        assert item.metadata == {}
        assert item.added_at is not None

    def test_creation_with_metadata(self):
        item = QueueItem(
            id="item-001",
            article_id="art-001",
            provider="google_news_ai",
            source="https://example.com",
            category="ai",
            topic="llm",
            score=0.85,
            recommendation="Test rec",
            metadata={"key": "value"},
        )
        assert item.metadata == {"key": "value"}


class TestDecisionQueue:
    """Tests for DecisionQueue."""

    def test_empty_queue(self):
        queue = DecisionQueue()
        result = queue.get_next()
        assert result.is_success
        assert result.value is None

    def test_add_item(self):
        queue = DecisionQueue()
        result = queue.add(
            article_id="art-001",
            provider="google_news_ai",
            source="https://example.com",
            category="ai",
            topic="llm",
            score=0.85,
            recommendation="Test rec",
        )
        assert result.is_success
        item = result.value
        assert item.article_id == "art-001"
        assert item.status == "pending"

    def test_add_multiple_items(self):
        queue = DecisionQueue()
        for i in range(3):
            queue.add(
                article_id=f"art-{i}",
                provider="test",
                source="https://example.com",
                category="ai",
                topic="llm",
                score=0.8,
                recommendation=f"Rec {i}",
            )
        stats = queue.get_stats()
        assert stats["pending"] == 3
        assert stats["total"] == 3

    def test_get_next_returns_first_pending(self):
        queue = DecisionQueue()
        r1 = queue.add(
            article_id="art-001",
            provider="test",
            source="https://example.com",
            category="ai",
            topic="llm",
            score=0.9,
            recommendation="First",
        )
        queue.add(
            article_id="art-002",
            provider="test",
            source="https://example.com",
            category="ai",
            topic="llm",
            score=0.8,
            recommendation="Second",
        )
        next_item = queue.get_next()
        assert next_item.is_success
        assert next_item.value.id == r1.value.id

    def test_process_approve(self):
        queue = DecisionQueue()
        result = queue.add(
            article_id="art-001",
            provider="test",
            source="https://example.com",
            category="ai",
            topic="llm",
            score=0.85,
            recommendation="Test",
        )
        item_id = result.value.id
        process_result = queue.process(item_id, decision="approved")
        assert process_result.is_success
        assert process_result.value.status == "approved"

    def test_process_reject(self):
        queue = DecisionQueue()
        result = queue.add(
            article_id="art-001",
            provider="test",
            source="https://example.com",
            category="ai",
            topic="llm",
            score=0.85,
            recommendation="Test",
        )
        item_id = result.value.id
        process_result = queue.process(item_id, decision="rejected")
        assert process_result.is_success
        assert process_result.value.status == "rejected"

    def test_process_skip(self):
        queue = DecisionQueue()
        result = queue.add(
            article_id="art-001",
            provider="test",
            source="https://example.com",
            category="ai",
            topic="llm",
            score=0.85,
            recommendation="Test",
        )
        item_id = result.value.id
        process_result = queue.process(item_id, decision="skipped")
        assert process_result.is_success
        assert process_result.value.status == "skipped"

    def test_process_nonexistent_item(self):
        queue = DecisionQueue()
        result = queue.process("nonexistent-id", decision="approved")
        assert result.is_failure
        assert "not found" in result.error.message.lower()

    def test_get_next_skips_processed(self):
        queue = DecisionQueue()
        r1 = queue.add(
            article_id="art-001",
            provider="test",
            source="https://example.com",
            category="ai",
            topic="llm",
            score=0.9,
            recommendation="First",
        )
        r2 = queue.add(
            article_id="art-002",
            provider="test",
            source="https://example.com",
            category="ai",
            topic="llm",
            score=0.8,
            recommendation="Second",
        )
        queue.process(r1.value.id, decision="approved")
        next_item = queue.get_next()
        assert next_item.is_success
        assert next_item.value.id == r2.value.id

    def test_stats_after_processing(self):
        queue = DecisionQueue()
        ids = []
        for i in range(5):
            result = queue.add(
                article_id=f"art-{i}",
                provider="test",
                source="https://example.com",
                category="ai",
                topic="llm",
                score=0.8,
                recommendation=f"Rec {i}",
            )
            ids.append(result.value.id)

        # Approve 3, reject 2
        queue.process(ids[0], decision="approved")
        queue.process(ids[1], decision="approved")
        queue.process(ids[2], decision="approved")
        queue.process(ids[3], decision="rejected")
        queue.process(ids[4], decision="rejected")

        stats = queue.get_stats()
        assert stats["pending"] == 0
        assert stats["approved"] == 3
        assert stats["rejected"] == 2
        assert stats["skipped"] == 0
        assert stats["total"] == 5

    def test_stats_partial_processing(self):
        queue = DecisionQueue()
        for i in range(3):
            queue.add(
                article_id=f"art-{i}",
                provider="test",
                source="https://example.com",
                category="ai",
                topic="llm",
                score=0.8,
                recommendation=f"Rec {i}",
            )
        stats = queue.get_stats()
        assert stats["pending"] == 3
        assert stats["approved"] == 0
        assert stats["total"] == 3
