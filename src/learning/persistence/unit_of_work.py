"""
SqlAlchemyUnitOfWork — Unit of Work pattern for Learning BC.

Manages a single Session with property accessors for each repository.
Supports commit/rollback and optimistic locking via version columns.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from learning.persistence.repositories.feedback_repository import FeedbackRepository
from learning.persistence.repositories.learning_signal_repository import LearningSignalRepository
from learning.persistence.repositories.source_quality_repository import SourceQualityRepository
from learning.persistence.repositories.learning_model_repository import LearningModelRepository
from learning.persistence.repositories.knowledge_timeline_repository import KnowledgeTimelineRepository
from learning.persistence.repositories.feature_store_repository import FeatureStoreRepository
from learning.persistence.repositories.dataset_repository import DatasetRepository
from learning.persistence.repositories.knowledge_artifact_repository import KnowledgeArtifactRepository


class SqlAlchemyUnitOfWork:
    """Unit of Work for Learning BC using SQLAlchemy.

    Usage::

        uow = SqlAlchemyUnitOfWork(session_factory)
        with uow:
            uow.feedback.save(feedback_record)
            uow.commit()
    """

    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self._feedback_repo: FeedbackRepository | None = None
        self._signal_repo: LearningSignalRepository | None = None
        self._source_repo: SourceQualityRepository | None = None
        self._model_repo: LearningModelRepository | None = None
        self._timeline_repo: KnowledgeTimelineRepository | None = None
        self._feature_store_repo: FeatureStoreRepository | None = None
        self._dataset_repo: DatasetRepository | None = None
        self._artifact_repo: KnowledgeArtifactRepository | None = None

    def __enter__(self) -> SqlAlchemyUnitOfWork:
        self._session = self._session_factory()
        self._feedback_repo = FeedbackRepository(self._session)
        self._signal_repo = LearningSignalRepository(self._session)
        self._source_repo = SourceQualityRepository(self._session)
        self._model_repo = LearningModelRepository(self._session)
        self._timeline_repo = KnowledgeTimelineRepository(self._session)
        self._feature_store_repo = FeatureStoreRepository(self._session)
        self._dataset_repo = DatasetRepository(self._session)
        self._artifact_repo = KnowledgeArtifactRepository(self._session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self._session.close()

    def commit(self) -> None:
        """Flush and commit all pending changes."""
        self._session.flush()
        self._session.commit()

    def rollback(self) -> None:
        """Roll back all pending changes."""
        self._session.rollback()

    @property
    def session(self) -> Session:
        """Access the underlying session directly."""
        assert self._session is not None, "UnitOfWork not entered. Use 'with' statement."
        return self._session

    @property
    def feedback(self) -> FeedbackRepository:
        assert self._feedback_repo is not None, "UnitOfWork not entered."
        return self._feedback_repo

    @property
    def signal(self) -> LearningSignalRepository:
        assert self._signal_repo is not None, "UnitOfWork not entered."
        return self._signal_repo

    @property
    def source_quality(self) -> SourceQualityRepository:
        assert self._source_repo is not None, "UnitOfWork not entered."
        return self._source_repo

    @property
    def learning_model(self) -> LearningModelRepository:
        assert self._model_repo is not None, "UnitOfWork not entered."
        return self._model_repo

    @property
    def knowledge_timeline(self) -> KnowledgeTimelineRepository:
        assert self._timeline_repo is not None, "UnitOfWork not entered."
        return self._timeline_repo

    @property
    def feature_store(self) -> FeatureStoreRepository:
        assert self._feature_store_repo is not None, "UnitOfWork not entered."
        return self._feature_store_repo

    @property
    def dataset(self) -> DatasetRepository:
        assert self._dataset_repo is not None, "UnitOfWork not entered."
        return self._dataset_repo

    @property
    def artifact(self) -> KnowledgeArtifactRepository:
        assert self._artifact_repo is not None, "UnitOfWork not entered."
        return self._artifact_repo
