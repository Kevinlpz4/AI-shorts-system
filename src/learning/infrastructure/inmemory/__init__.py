"""In-memory implementations of Learning BC infrastructure ports.

These implementations use only Python collections (dict, list) and are
intended for testing and development. They are NOT thread-safe and do NOT
persist data across process restarts.

Domain/Infrastructure ports:
    - InMemoryFeedbackRepository
    - InMemoryLearningSignalRepository
    - InMemorySourceQualityRepository
    - InMemoryLearningModelRepository
    - InMemoryLearningUnitOfWork
    - InMemoryLearningEventPublisher
    - InMemoryTypedEventPublisher
    - InMemoryDatasetExporter
    - LearningSystemClock
    - LearningFrozenClock

Cross-BC adapters:
    - InMemoryIngestionReader
    - InMemoryResearchReader

Integration (event buses + read models):
    - InMemoryIntegrationEventBus
    - InMemoryIngestionEventBus
    - InMemoryResearchEventBus
    - InMemoryPublicationEventBus
    - InMemoryArticleReadModel
    - InMemorySourceReadModel
    - InMemoryTopicReadModel
"""

from learning.infrastructure.inmemory.clock import (
    LearningFrozenClock,
    LearningSystemClock,
)
from learning.infrastructure.inmemory.cross_bc_adapters import (
    InMemoryIngestionReader,
    InMemoryResearchReader,
)
from learning.infrastructure.inmemory.dataset_exporter import (
    InMemoryDatasetExporter,
)
from learning.infrastructure.inmemory.event_publisher import (
    InMemoryLearningEventPublisher,
)
from learning.infrastructure.inmemory.integration.event_buses import (
    InMemoryIngestionEventBus,
    InMemoryIntegrationEventBus,
    InMemoryPublicationEventBus,
    InMemoryResearchEventBus,
)
from learning.infrastructure.inmemory.integration.read_models import (
    InMemoryArticleReadModel,
    InMemorySourceReadModel,
    InMemoryTopicReadModel,
)
from learning.infrastructure.inmemory.learning_event_publisher import (
    InMemoryTypedEventPublisher,
)
from learning.infrastructure.inmemory.repositories import (
    InMemoryFeedbackRepository,
    InMemoryLearningModelRepository,
    InMemoryLearningSignalRepository,
    InMemorySourceQualityRepository,
)
from learning.infrastructure.inmemory.unit_of_work import (
    InMemoryLearningUnitOfWork,
)

__all__ = [
    # Domain/Infrastructure ports
    "InMemoryDatasetExporter",
    "InMemoryFeedbackRepository",
    "InMemoryLearningEventPublisher",
    "InMemoryLearningModelRepository",
    "InMemoryLearningSignalRepository",
    "InMemoryLearningUnitOfWork",
    "InMemorySourceQualityRepository",
    "InMemoryTypedEventPublisher",
    "LearningFrozenClock",
    "LearningSystemClock",
    # Cross-BC adapters
    "InMemoryIngestionReader",
    "InMemoryResearchReader",
    # Integration event buses
    "InMemoryIntegrationEventBus",
    "InMemoryIngestionEventBus",
    "InMemoryResearchEventBus",
    "InMemoryPublicationEventBus",
    # Read models
    "InMemoryArticleReadModel",
    "InMemorySourceReadModel",
    "InMemoryTopicReadModel",
]
