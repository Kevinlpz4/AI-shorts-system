"""
Concurrency Tests — Optimistic Locking, Versioning & Transaction Isolation.

SQLite ``:memory:`` creates a SEPARATE database per connection. Since these
tests require TWO INDEPENDENT SESSIONS sharing the same database, we use a
temporary file-based database (``tempfile.mkstemp``).

Covers:
    - C01: Version column increments after each save
    - C02: Two sessions, same entity → StaleDataError → ConcurrentModificationError
    - C03: ConcurrentModificationError via Repository (UoW flow)
    - C04: Events NOT published on concurrent modification failure
    - C05: Rollback does not corrupt data
    - C06: Data integrity after concurrent modification
"""

from __future__ import annotations

import os
import tempfile

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.exc import StaleDataError

from ingestion.domain.entities.category import Category
from ingestion.domain.entities.feed import Feed
from ingestion.domain.entities.ids import (
    CategoryId,
    FeedId,
    SourceId,
    TopicId,
)
from ingestion.domain.entities.news_source import NewsSource
from ingestion.domain.entities.topic import Topic
from ingestion.domain.value_objects.article_title import ArticleTitle
from ingestion.domain.value_objects.category_name import CategoryName
from ingestion.domain.value_objects.article_url import ArticleUrl
from ingestion.domain.value_objects.language import Language
from ingestion.domain.value_objects.source_type import SourceType
from ingestion.domain.value_objects.source_url import SourceUrl
from ingestion.domain.value_objects.sync_mode import SyncMode
from ingestion.domain.value_objects.sync_policy import SyncPolicy

from ingestion.infrastructure.persistence import (
    PersistenceBase,
    SQLAlchemyUnitOfWork,
)
from ingestion.infrastructure.persistence.models import (
    NewsSourceModel,
    FeedModel,
    CategoryModel,
    TopicModel,
)
from ingestion.infrastructure.persistence.exceptions import (
    ConcurrentModificationError,
)
from ingestion.infrastructure.event_publisher import SQLAlchemyEventPublisher


# ══════════════════════════════════════════════════════════════════════════════
# Shared-fixture: temporary file database (not :memory:)
# ══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def db_path():
    """Create a temporary file for the SQLite database.

    Yields the path; cleans up the file after the test.
    """
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def shared_engine(db_path):
    """SQLite engine backed by a file — all sessions share the same DB."""
    engine = create_engine(f"sqlite:///{db_path}")
    yield engine
    engine.dispose()


@pytest.fixture
def shared_tables(shared_engine):
    """Create all tables on the shared engine; drop after test."""
    PersistenceBase.metadata.create_all(shared_engine)
    yield
    PersistenceBase.metadata.drop_all(shared_engine)


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════


def _create_source(name: str = "Original") -> NewsSource:
    """Create a minimal NewsSource domain entity."""
    return NewsSource(
        id=SourceId.generate(),
        name=name,
        source_type=SourceType.RSS,
        source_url=SourceUrl("https://example.com"),
        is_active=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# C01 — Version increments
# ══════════════════════════════════════════════════════════════════════════════


class TestVersionIncrement:
    """C01: Version column increments correctly after each modification."""

    def test_version_starts_at_one(self, shared_engine, shared_tables):
        """New entity MUST start with version=1."""
        source_id = SourceId.generate()
        session = Session(bind=shared_engine)
        try:
            model = NewsSourceModel(
                id=source_id,
                name="Fresh",
                source_type=SourceType.RSS,
                source_url=SourceUrl("https://example.com"),
                is_active=True,
            )
            session.add(model)
            session.commit()

            loaded = session.get(NewsSourceModel, source_id)
            assert loaded.version == 1
        finally:
            session.close()

    def test_version_increments_on_update(self, shared_engine, shared_tables):
        """Modifying and committing MUST increment version."""
        source_id = SourceId.generate()

        session = Session(bind=shared_engine)
        try:
            model = NewsSourceModel(
                id=source_id,
                name="Versioned",
                source_type=SourceType.RSS,
                source_url=SourceUrl("https://example.com"),
                is_active=True,
            )
            session.add(model)
            session.commit()

            loaded = session.get(NewsSourceModel, source_id)
            assert loaded.version == 1
            loaded.name = "Modified once"
            session.commit()

            loaded = session.get(NewsSourceModel, source_id)
            assert loaded.version == 2
        finally:
            session.close()

    def test_version_increments_multiple_times(self, shared_engine, shared_tables):
        """N modifications MUST produce version = N+1."""
        source_id = SourceId.generate()

        session = Session(bind=shared_engine)
        try:
            model = NewsSourceModel(
                id=source_id,
                name="Multi",
                source_type=SourceType.RSS,
                source_url=SourceUrl("https://example.com"),
                is_active=True,
            )
            session.add(model)
            session.commit()

            for i in range(1, 5):
                loaded = session.get(NewsSourceModel, source_id)
                loaded.name = f"Update {i}"
                session.commit()
                loaded = session.get(NewsSourceModel, source_id)
                assert loaded.version == i + 1
        finally:
            session.close()

    def test_version_increments_for_all_roots(self, shared_engine, shared_tables):
        """ALL mutable aggregate roots MUST increment version on update."""
        session = Session(bind=shared_engine)
        try:
            # Feed
            feed_id = FeedId.generate()
            source_id = SourceId.generate()
            src = NewsSourceModel(
                id=source_id, name="S", source_type=SourceType.RSS,
                source_url=SourceUrl("https://s.com"), is_active=True,
            )
            session.add(src)
            session.commit()

            feed = FeedModel(
                id=feed_id, source_id=source_id,
                url=ArticleUrl("https://example.com/feed"),
                label=ArticleTitle("Test Feed"), language=Language("en"),
                is_active=True,
                sync_policy=SyncPolicy(mode=SyncMode.MANUAL),
            )
            session.add(feed)
            session.commit()
            assert feed.version == 1
            feed.label = ArticleTitle("Updated Feed")
            session.commit()
            assert feed.version == 2

            from ingestion.domain.value_objects.category_name import CategoryName
            cat_id = CategoryId.generate()
            cat = CategoryModel(
                id=cat_id, name=CategoryName("Tech"), slug="tech", is_active=True,
            )
            session.add(cat)
            session.commit()
            assert cat.version == 1
            cat.name = CategoryName("Technology")
            session.commit()
            assert cat.version == 2

            # Topic
            topic_id = TopicId.generate()
            topic = TopicModel(
                id=topic_id, name="AI", is_active=True,
            )
            session.add(topic)
            session.commit()
            assert topic.version == 1
            topic.name = "Artificial Intelligence"
            session.commit()
            assert topic.version == 2
        finally:
            session.close()

    def test_read_only_operations_do_not_increment_version(
        self, shared_engine, shared_tables,
    ):
        """Read-only get() MUST NOT increment version."""
        source_id = SourceId.generate()
        session = Session(bind=shared_engine)
        try:
            model = NewsSourceModel(
                id=source_id, name="ReadOnly", source_type=SourceType.RSS,
                source_url=SourceUrl("https://example.com"), is_active=True,
            )
            session.add(model)
            session.commit()

            # Multiple reads — version must stay 1
            for _ in range(3):
                loaded = session.get(NewsSourceModel, source_id)
                assert loaded.version == 1
        finally:
            session.close()


# ══════════════════════════════════════════════════════════════════════════════
# C02 — Concurrent modification detection (SQLAlchemy level)
# ══════════════════════════════════════════════════════════════════════════════


class TestStaleDataError:
    """C02: Two independent sessions → StaleDataError on second commit."""

    def test_stale_data_error_on_concurrent_modification(
        self, shared_engine, shared_tables,
    ):
        """Session A holds version=1, B commits (version=2), A flush → StaleDataError."""
        source_id = SourceId.generate()

        # Create entity
        session = Session(bind=shared_engine)
        try:
            model = NewsSourceModel(
                id=source_id, name="Initial", source_type=SourceType.RSS,
                source_url=SourceUrl("https://example.com"), is_active=True,
            )
            session.add(model)
            session.commit()
        finally:
            session.close()

        # Session A loads (identity map: version=1)
        session_a = Session(bind=shared_engine)
        try:
            model_a = session_a.get(NewsSourceModel, source_id)
            assert model_a.version == 1

            # Session B loads, modifies, commits (version 1→2)
            session_b = Session(bind=shared_engine)
            try:
                model_b = session_b.get(NewsSourceModel, source_id)
                model_b.name = "Modified by B"
                session_b.commit()
            finally:
                session_b.close()

            # Session A modifies and tries to commit → StaleDataError
            model_a.name = "Modified by A"
            with pytest.raises(StaleDataError):
                session_a.commit()
        finally:
            session_a.close()

    def test_identity_map_preserves_old_version(
        self, shared_engine, shared_tables,
    ):
        """Identity map MUST NOT reload — keeps cached version after external change."""
        source_id = SourceId.generate()

        session = Session(bind=shared_engine)
        try:
            model = NewsSourceModel(
                id=source_id, name="Initial", source_type=SourceType.RSS,
                source_url=SourceUrl("https://example.com"), is_active=True,
            )
            session.add(model)
            session.commit()
        finally:
            session.close()

        session_a = Session(bind=shared_engine)
        try:
            model_a = session_a.get(NewsSourceModel, source_id)

            session_b = Session(bind=shared_engine)
            try:
                model_b = session_b.get(NewsSourceModel, source_id)
                model_b.name = "B wins"
                session_b.commit()
            finally:
                session_b.close()

            # A's identity map should still have version=1
            model_a_again = session_a.get(NewsSourceModel, source_id)
            assert model_a_again is model_a
            assert model_a_again.version == 1
        finally:
            session_a.close()


# ══════════════════════════════════════════════════════════════════════════════
# C03 — Concurrent modification detection (Repository level)
# ══════════════════════════════════════════════════════════════════════════════


class TestRepositoryConcurrentModification:
    """C03: Repository.save() MUST raise ConcurrentModificationError."""

    def test_repo_detects_concurrent_modification(
        self, shared_engine, shared_tables,
    ):
        """Two UoWs, same entity → save on second raises ConcurrentModificationError."""
        session_factory = sessionmaker(bind=shared_engine)
        source = _create_source("Initial")

        # 1. Create source
        with SQLAlchemyUnitOfWork(session_factory) as uow:
            uow.news_sources.save(source)
            uow.commit()

        # 2. A loads into identity map
        uow_a = SQLAlchemyUnitOfWork(session_factory)
        uow_a.__enter__()
        result_a = uow_a.news_sources.find_by_id(source.id)
        assert result_a.is_success
        source_a = result_a.value

        # 3. B loads, modifies, commits (version 1→2)
        with SQLAlchemyUnitOfWork(session_factory) as uow_b:
            result_b = uow_b.news_sources.find_by_id(source.id)
            assert result_b.is_success
            source_b = result_b.value
            source_b.name = "Modified by B"
            uow_b.news_sources.save(source_b)
            uow_b.commit()

        # 4. A tries to save → ConcurrentModificationError
        source_a.name = "Modified by A"
        with pytest.raises(ConcurrentModificationError) as excinfo:
            uow_a.news_sources.save(source_a)

        assert str(source.id) in str(excinfo.value), (
            "Error message MUST include entity ID"
        )

        uow_a.rollback()
        uow_a.__exit__(None, None, None)

    def test_all_mutable_repos_detect_concurrent_modification(
        self, shared_engine, shared_tables,
    ):
        """Source, Feed, Category, Topic — ALL must detect concurrent modification."""
        session_factory = sessionmaker(bind=shared_engine)

        # ── Seed entities ──
        source = _create_source("Source OL")
        with SQLAlchemyUnitOfWork(session_factory) as uow:
            uow.news_sources.save(source)
            uow.commit()
        source_id = source.id

        feed_id = FeedId.generate()
        with SQLAlchemyUnitOfWork(session_factory) as uow:
            feed = Feed(
                id=feed_id, source_id=source_id,
                url=ArticleUrl("https://example.com/feed"),
                label=ArticleTitle("Feed OL"), language=Language("en"),
                is_active=True,
                sync_policy=SyncPolicy(mode=SyncMode.PULL, interval_minutes=30),
            )
            uow.feeds.save(feed)
            uow.commit()

        cat_id = CategoryId.generate()
        with SQLAlchemyUnitOfWork(session_factory) as uow:
            cat = Category(id=cat_id, name=CategoryName("Cat OL"), slug="cat-ol")
            uow.categories.save(cat)
            uow.commit()

        topic_id = TopicId.generate()
        with SQLAlchemyUnitOfWork(session_factory) as uow:
            topic = Topic(id=topic_id, name="Topic OL")
            uow.topics.save(topic)
            uow.commit()

        # ── Test each repo ──
        scenarios = [
            ("Source", lambda u: u.news_sources.find_by_id(source_id),
             lambda e: setattr(e, "name", "A's Source"),
             lambda u, e: u.news_sources.save(e)),
            ("Feed", lambda u: u.feeds.find_by_id(feed_id),
             lambda e: setattr(e, "label", ArticleTitle("A's Feed")),
             lambda u, e: u.feeds.save(e)),
             ("Category", lambda u: u.categories.find_by_id(cat_id),
             lambda e: setattr(e, "name", CategoryName("A Cat One")),
             lambda u, e: u.categories.save(e)),
            ("Topic", lambda u: u.topics.find_by_id(topic_id),
             lambda e: setattr(e, "name", "A's Topic"),
             lambda u, e: u.topics.save(e)),
        ]

        for name, load_fn, modify_fn, save_fn in scenarios:
            uow_a = SQLAlchemyUnitOfWork(session_factory)
            uow_a.__enter__()
            result = load_fn(uow_a)
            assert result.is_success, f"{name}: load in A failed"
            entity = result.value

            # B loads and commits
            with SQLAlchemyUnitOfWork(session_factory) as uow_b:
                result_b = load_fn(uow_b)
                assert result_b.is_success, f"{name}: load in B failed"
                entity_b = result_b.value
                modify_fn(entity_b)
                save_fn(uow_b, entity_b)
                uow_b.commit()

            # A tries → ConcurrentModificationError
            modify_fn(entity)
            with pytest.raises(
                ConcurrentModificationError,
                match=name,
            ):
                save_fn(uow_a, entity)

            uow_a.rollback()
            uow_a.__exit__(None, None, None)

    def test_final_state_is_b_winner(self, shared_engine, shared_tables):
        """After concurrent modification, DB state MUST be B's change."""
        session_factory = sessionmaker(bind=shared_engine)
        source = _create_source("Who wins?")

        with SQLAlchemyUnitOfWork(session_factory) as uow:
            uow.news_sources.save(source)
            uow.commit()

        uow_a = SQLAlchemyUnitOfWork(session_factory)
        uow_a.__enter__()
        result_a = uow_a.news_sources.find_by_id(source.id)
        source_a = result_a.value

        with SQLAlchemyUnitOfWork(session_factory) as uow_b:
            result_b = uow_b.news_sources.find_by_id(source.id)
            source_b = result_b.value
            source_b.name = "B WINS"
            uow_b.news_sources.save(source_b)
            uow_b.commit()

        source_a.name = "A tries"
        try:
            uow_a.news_sources.save(source_a)
        except ConcurrentModificationError:
            pass

        uow_a.rollback()
        uow_a.__exit__(None, None, None)

        with SQLAlchemyUnitOfWork(session_factory) as uow_c:
            result_c = uow_c.news_sources.find_by_id(source.id)
            assert result_c.value.name == "B WINS"


# ══════════════════════════════════════════════════════════════════════════════
# C04 — Events not published on concurrent modification failure
# ══════════════════════════════════════════════════════════════════════════════


class TestConcurrentModificationNoEvents:
    """C04: ConcurrentModificationError → events MUST NOT be published."""

    def test_no_events_on_concurrent_modification(
        self, shared_engine, shared_tables,
    ):
        """Failed save due to concurrent modification → no events published."""
        session_factory = sessionmaker(bind=shared_engine)
        publisher = SQLAlchemyEventPublisher()
        source = _create_source("No Events")

        with SQLAlchemyUnitOfWork(session_factory, event_publisher=publisher) as uow:
            uow.news_sources.save(source)
            uow.register_modified(source)
            uow.commit()

        uow_a = SQLAlchemyUnitOfWork(session_factory, event_publisher=publisher)
        uow_a.__enter__()
        result_a = uow_a.news_sources.find_by_id(source.id)
        source_a = result_a.value

        with SQLAlchemyUnitOfWork(session_factory, event_publisher=publisher) as uow_b:
            result_b = uow_b.news_sources.find_by_id(source.id)
            source_b = result_b.value
            source_b.name = "B modifies"
            uow_b.news_sources.save(source_b)
            uow_b.register_modified(source_b)
            uow_b.commit()

        b_events = len(publisher.events)

        source_a.name = "A fails"
        with pytest.raises(ConcurrentModificationError):
            uow_a.news_sources.save(source_a)

        assert len(publisher.events) == b_events

        uow_a.rollback()
        uow_a.__exit__(None, None, None)

    def test_commit_not_reached_when_save_fails(
        self, shared_engine, shared_tables,
    ):
        """save() raises ConcurrentModificationError → commit() is never called."""
        session_factory = sessionmaker(bind=shared_engine)
        publisher = SQLAlchemyEventPublisher()
        source = _create_source("No Commit")

        with SQLAlchemyUnitOfWork(session_factory, event_publisher=publisher) as uow:
            uow.news_sources.save(source)
            uow.commit()

        uow_a = SQLAlchemyUnitOfWork(session_factory, event_publisher=publisher)
        uow_a.__enter__()
        result_a = uow_a.news_sources.find_by_id(source.id)
        source_a = result_a.value

        with SQLAlchemyUnitOfWork(session_factory, event_publisher=publisher) as uow_b:
            result_b = uow_b.news_sources.find_by_id(source.id)
            source_b = result_b.value
            source_b.name = "B wins"
            uow_b.news_sources.save(source_b)
            uow_b.commit()

        source_a.name = "A loses"
        with pytest.raises(ConcurrentModificationError):
            uow_a.news_sources.save(source_a)

        uow_a.rollback()
        uow_a.__exit__(None, None, None)


# ══════════════════════════════════════════════════════════════════════════════
# C05 — Rollback safety
# ══════════════════════════════════════════════════════════════════════════════


class TestConcurrentModificationRollback:
    """C05: Rollback after concurrent modification → data intact."""

    def test_rollback_preserves_b_data(self, shared_engine, shared_tables):
        """Rollback after ConcurrentModificationError → B's data unchanged."""
        session_factory = sessionmaker(bind=shared_engine)
        source = _create_source("Rollback Test")

        with SQLAlchemyUnitOfWork(session_factory) as uow:
            uow.news_sources.save(source)
            uow.commit()

        uow_a = SQLAlchemyUnitOfWork(session_factory)
        uow_a.__enter__()
        result_a = uow_a.news_sources.find_by_id(source.id)
        source_a = result_a.value

        with SQLAlchemyUnitOfWork(session_factory) as uow_b:
            result_b = uow_b.news_sources.find_by_id(source.id)
            source_b = result_b.value
            source_b.name = "B's data"
            uow_b.news_sources.save(source_b)
            uow_b.commit()

        source_a.name = "A's attempt"
        with pytest.raises(ConcurrentModificationError):
            uow_a.news_sources.save(source_a)

        uow_a.rollback()
        uow_a.__exit__(None, None, None)

        with SQLAlchemyUnitOfWork(session_factory) as uow_c:
            result_c = uow_c.news_sources.find_by_id(source.id)
            assert result_c.value.name == "B's data"

    def test_session_reusable_after_rollback(self, shared_engine, shared_tables):
        """Session after rollback of concurrent modification → reusable."""
        session_factory = sessionmaker(bind=shared_engine)
        source = _create_source("Reuse Session")

        with SQLAlchemyUnitOfWork(session_factory) as uow:
            uow.news_sources.save(source)
            uow.commit()

        uow_a = SQLAlchemyUnitOfWork(session_factory)
        uow_a.__enter__()
        result_a = uow_a.news_sources.find_by_id(source.id)
        source_a = result_a.value

        with SQLAlchemyUnitOfWork(session_factory) as uow_b:
            result_b = uow_b.news_sources.find_by_id(source.id)
            source_b = result_b.value
            source_b.name = "B reusable"
            uow_b.news_sources.save(source_b)
            uow_b.commit()

        source_a.name = "A fails"
        with pytest.raises(ConcurrentModificationError):
            uow_a.news_sources.save(source_a)

        uow_a.rollback()

        # Re-fetch — should see B's data
        result_a = uow_a.news_sources.find_by_id(source.id)
        assert result_a.value.name == "B reusable"

        uow_a.__exit__(None, None, None)


# ══════════════════════════════════════════════════════════════════════════════
# C06 — Data integrity
# ══════════════════════════════════════════════════════════════════════════════


class TestConcurrentModificationDataIntegrity:
    """C06: Concurrent modification → no corruption, isolation preserved."""

    def test_all_b_fields_intact(self, shared_engine, shared_tables):
        """All B fields intact after A's failed modification attempt."""
        session_factory = sessionmaker(bind=shared_engine)
        source = NewsSource(
            id=SourceId.generate(),
            name="Full Entity",
            source_type=SourceType.API,
            source_url=SourceUrl("https://api.example.com"),
            is_active=True,
        )

        with SQLAlchemyUnitOfWork(session_factory) as uow:
            uow.news_sources.save(source)
            uow.commit()

        uow_a = SQLAlchemyUnitOfWork(session_factory)
        uow_a.__enter__()
        result_a = uow_a.news_sources.find_by_id(source.id)
        source_a = result_a.value

        with SQLAlchemyUnitOfWork(session_factory) as uow_b:
            result_b = uow_b.news_sources.find_by_id(source.id)
            source_b = result_b.value
            source_b.name = "B Changed Name"
            source_b.source_type = SourceType.RSS
            source_b.source_url = SourceUrl("https://b-changed.com")
            source_b.is_active = False
            uow_b.news_sources.save(source_b)
            uow_b.commit()

        source_a.name = "A Tries"
        with pytest.raises(ConcurrentModificationError):
            uow_a.news_sources.save(source_a)

        uow_a.rollback()
        uow_a.__exit__(None, None, None)

        with SQLAlchemyUnitOfWork(session_factory) as uow_c:
            final = uow_c.news_sources.find_by_id(source.id).value
            assert final.name == "B Changed Name"
            assert final.source_type == SourceType.RSS
            assert final.source_url.value == "https://b-changed.com"
            assert final.is_active is False

    def test_other_entities_unaffected(self, shared_engine, shared_tables):
        """Conflict on entity A MUST NOT affect entity B."""
        session_factory = sessionmaker(bind=shared_engine)
        source_a = _create_source("First Source")
        source_b = _create_source("Second Source")

        with SQLAlchemyUnitOfWork(session_factory) as uow:
            uow.news_sources.save(source_a)
            uow.news_sources.save(source_b)
            uow.commit()

        uow_a = SQLAlchemyUnitOfWork(session_factory)
        uow_a.__enter__()
        result_a1 = uow_a.news_sources.find_by_id(source_a.id)
        result_a2 = uow_a.news_sources.find_by_id(source_b.id)
        entity_a1 = result_a1.value
        entity_a2_domain = result_a2.value  # keep domain copy

        with SQLAlchemyUnitOfWork(session_factory) as uow_b:
            result_b = uow_b.news_sources.find_by_id(source_a.id)
            b_entity = result_b.value
            b_entity.name = "B Modified A"
            uow_b.news_sources.save(b_entity)
            uow_b.commit()

        # A tries source_a → ConcurrentModificationError
        entity_a1.name = "A Modify A"
        with pytest.raises(ConcurrentModificationError):
            uow_a.news_sources.save(entity_a1)

        uow_a.rollback()

        # A can still modify source_b (no conflict on source_b)
        result_a2 = uow_a.news_sources.find_by_id(source_b.id)
        entity_a2 = result_a2.value
        entity_a2.name = "A Modify B"
        uow_a.news_sources.save(entity_a2)
        uow_a.commit()
        uow_a.__exit__(None, None, None)

        with SQLAlchemyUnitOfWork(session_factory) as uow_c:
            r1 = uow_c.news_sources.find_by_id(source_a.id)
            assert r1.value.name == "B Modified A"
            r2 = uow_c.news_sources.find_by_id(source_b.id)
            assert r2.value.name == "A Modify B"
