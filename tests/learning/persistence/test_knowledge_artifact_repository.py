"""
Tests for KnowledgeArtifactRepository — CRUD, type/status queries, lifecycle.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from learning.domain.entities.knowledge_artifact import (
    ArtifactStatus,
    ArtifactType,
)
from learning.domain.entities.ids import KnowledgeArtifactId
from learning.persistence.repositories.knowledge_artifact_repository import KnowledgeArtifactRepository


class TestKnowledgeArtifactRepositorySave:
    def test_save_and_find(self, session, make_knowledge_artifact):
        repo = KnowledgeArtifactRepository(session)
        artifact = make_knowledge_artifact()
        repo.save(artifact)
        session.commit()

        found = repo.find_by_id(artifact.id)
        assert found is not None
        assert found.id == artifact.id

    def test_upsert_update(self, session, make_knowledge_artifact):
        repo = KnowledgeArtifactRepository(session)
        artifact = make_knowledge_artifact()
        repo.save(artifact)
        session.flush()

        artifact.activate()
        repo.save(artifact, version_int=2)
        session.commit()

        found = repo.find_by_id(artifact.id)
        assert found.status == ArtifactStatus.ACTIVE

    def test_save_multiple(self, session, make_knowledge_artifact):
        repo = KnowledgeArtifactRepository(session)
        for i in range(5):
            repo.save(make_knowledge_artifact(version=f"1.0.{i}"))
        session.commit()

        assert repo.count_all() == 5


class TestKnowledgeArtifactRepositoryFindById:
    def test_find_existing(self, session, make_knowledge_artifact):
        repo = KnowledgeArtifactRepository(session)
        artifact = make_knowledge_artifact()
        repo.save(artifact)
        session.commit()

        found = repo.find_by_id(artifact.id)
        assert found is not None

    def test_find_nonexistent(self, session):
        repo = KnowledgeArtifactRepository(session)
        found = repo.find_by_id(KnowledgeArtifactId.generate())
        assert found is None


class TestKnowledgeArtifactRepositoryFindByType:
    def test_find_by_type(self, session, make_knowledge_artifact):
        repo = KnowledgeArtifactRepository(session)
        repo.save(make_knowledge_artifact(artifact_type=ArtifactType.DATASET))
        repo.save(make_knowledge_artifact(artifact_type=ArtifactType.DATASET))
        repo.save(make_knowledge_artifact(artifact_type=ArtifactType.MODEL))
        session.commit()

        datasets = repo.find_by_type(ArtifactType.DATASET)
        assert len(datasets) == 2
        models = repo.find_by_type(ArtifactType.MODEL)
        assert len(models) == 1
        reports = repo.find_by_type(ArtifactType.REPORT)
        assert len(reports) == 0


class TestKnowledgeArtifactRepositoryFindByStatus:
    def test_find_by_status(self, session, make_knowledge_artifact):
        repo = KnowledgeArtifactRepository(session)
        a1 = make_knowledge_artifact()
        a2 = make_knowledge_artifact()
        repo.save(a1)
        repo.save(a2)
        session.flush()

        a1.activate()
        repo.save(a1)
        session.commit()

        pending = repo.find_by_status(ArtifactStatus.PENDING)
        active = repo.find_by_status(ArtifactStatus.ACTIVE)
        assert len(pending) == 1
        assert len(active) == 1


class TestKnowledgeArtifactRepositoryLifecycle:
    def test_full_lifecycle(self, session, make_knowledge_artifact):
        repo = KnowledgeArtifactRepository(session)
        artifact = make_knowledge_artifact()
        repo.save(artifact)
        session.commit()

        # PENDING -> ACTIVE
        artifact.activate()
        repo.save(artifact)
        session.commit()
        assert repo.find_by_id(artifact.id).status == ArtifactStatus.ACTIVE

        # ACTIVE -> ARCHIVED
        artifact.archive()
        repo.save(artifact)
        session.commit()
        assert repo.find_by_id(artifact.id).status == ArtifactStatus.ARCHIVED

    def test_find_all(self, session, make_knowledge_artifact):
        repo = KnowledgeArtifactRepository(session)
        repo.save(make_knowledge_artifact())
        repo.save(make_knowledge_artifact())
        session.commit()

        all_artifacts = repo.find_all()
        assert len(all_artifacts) == 2

    def test_count_all(self, session, make_knowledge_artifact):
        repo = KnowledgeArtifactRepository(session)
        assert repo.count_all() == 0
        repo.save(make_knowledge_artifact())
        session.commit()
        assert repo.count_all() == 1
