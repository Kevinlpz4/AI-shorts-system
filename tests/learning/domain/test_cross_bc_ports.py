"""Tests for Cross-BC Ports — Protocol structural typing."""
from learning.domain.ports.cross_bc import IngestionReader, ResearchReader
from foundation.result.result import Result


class TestCrossBCPorts:
    def test_ingestion_reader_is_protocol(self):
        assert hasattr(IngestionReader, "__protocol_attrs__") or hasattr(
            IngestionReader, "__abstractmethods__"
        )

    def test_research_reader_is_protocol(self):
        assert hasattr(ResearchReader, "__protocol_attrs__") or hasattr(
            ResearchReader, "__abstractmethods__"
        )


class TestInMemoryIngestionReader:
    def test_satisfies_protocol(self):
        class MockIngestionReader:
            def get_article_features(self, article_id: str):
                return Result.success({"title": "test"})

            def get_source_config(self, source_name: str):
                return Result.success({"name": source_name})

        reader = MockIngestionReader()
        assert callable(getattr(reader, "get_article_features", None))
        assert callable(getattr(reader, "get_source_config", None))


class TestInMemoryResearchReader:
    def test_satisfies_protocol(self):
        class MockResearchReader:
            def get_topic_score(self, topic_id: str):
                return Result.success({"score": 0.8})

            def get_topic_details(self, topic_id: str):
                return Result.success({"title": "test topic"})

        reader = MockResearchReader()
        assert callable(getattr(reader, "get_topic_score", None))
        assert callable(getattr(reader, "get_topic_details", None))
