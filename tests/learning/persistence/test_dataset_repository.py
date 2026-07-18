"""
Tests for DatasetRepository — save, find, version immutability.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from learning.persistence.mappers.dataset_metadata_mapper import _DatasetMetadata
from learning.persistence.repositories.dataset_repository import DatasetRepository


def _make_dataset(
    dataset_version: str = "1.0.0",
    algorithm_version: str = "1.0.0",
    feature_schema_version: str = "1.0.0",
    record_count: int = 100,
    status: str = "PENDING",
) -> _DatasetMetadata:
    from uuid import uuid4
    return _DatasetMetadata(
        id=str(uuid4()),
        dataset_version=dataset_version,
        algorithm_version=algorithm_version,
        feature_schema_version=feature_schema_version,
        record_count=record_count,
        approved_count=int(record_count * 0.7),
        rejected_count=int(record_count * 0.3),
        export_format="JSON",
        checksum="abc123",
        description="Test dataset",
        status=status,
        created_at=datetime.now(timezone.utc),
    )


class TestDatasetRepositorySave:
    def test_save_and_find(self, session):
        repo = DatasetRepository(session)
        dataset = _make_dataset()
        result = repo.save(dataset)
        session.commit()

        assert result.dataset_version == "1.0.0"

    def test_save_duplicate_version_raises(self, session):
        repo = DatasetRepository(session)
        repo.save(_make_dataset(dataset_version="1.0.0"))
        session.flush()

        with pytest.raises(ValueError, match="already exists"):
            repo.save(_make_dataset(dataset_version="1.0.0"))

    def test_save_different_versions(self, session):
        repo = DatasetRepository(session)
        repo.save(_make_dataset(dataset_version="1.0.0"))
        repo.save(_make_dataset(dataset_version="1.0.1"))
        repo.save(_make_dataset(dataset_version="2.0.0"))
        session.commit()

        assert repo.count_all() == 3


class TestDatasetRepositoryFindByVersion:
    def test_find_existing(self, session):
        repo = DatasetRepository(session)
        repo.save(_make_dataset(dataset_version="1.5.0"))
        session.commit()

        found = repo.find_by_version("1.5.0")
        assert found is not None
        assert found.dataset_version == "1.5.0"

    def test_find_nonexistent(self, session):
        repo = DatasetRepository(session)
        found = repo.find_by_version("99.0.0")
        assert found is None


class TestDatasetRepositoryFindAll:
    def test_find_all(self, session):
        repo = DatasetRepository(session)
        repo.save(_make_dataset(dataset_version="1.0.0"))
        repo.save(_make_dataset(dataset_version="2.0.0"))
        session.commit()

        all_datasets = repo.find_all()
        assert len(all_datasets) == 2


class TestDatasetRepositoryFindByStatus:
    def test_find_by_status(self, session):
        repo = DatasetRepository(session)
        repo.save(_make_dataset(dataset_version="1.0", status="ACTIVE"))
        repo.save(_make_dataset(dataset_version="2.0", status="PENDING"))
        repo.save(_make_dataset(dataset_version="3.0", status="ACTIVE"))
        session.commit()

        active = repo.find_by_status("ACTIVE")
        assert len(active) == 2

    def test_find_by_status_empty(self, session):
        repo = DatasetRepository(session)
        results = repo.find_by_status("NONEXISTENT")
        assert len(results) == 0


class TestDatasetRepositoryVersionImmutability:
    def test_versions_never_overwrite(self, session):
        repo = DatasetRepository(session)
        v1 = _make_dataset(dataset_version="1.0", record_count=100)
        repo.save(v1)
        session.flush()

        v2 = _make_dataset(dataset_version="1.0", record_count=200)
        with pytest.raises(ValueError, match="versions are immutable"):
            repo.save(v2)

    def test_all_versions_preserved(self, session):
        repo = DatasetRepository(session)
        repo.save(_make_dataset(dataset_version="1.0", record_count=100))
        repo.save(_make_dataset(dataset_version="2.0", record_count=200))
        session.commit()

        v1 = repo.find_by_version("1.0")
        v2 = repo.find_by_version("2.0")
        assert v1.record_count == 100
        assert v2.record_count == 200

    def test_count_all(self, session):
        repo = DatasetRepository(session)
        assert repo.count_all() == 0
        repo.save(_make_dataset())
        session.commit()
        assert repo.count_all() == 1
