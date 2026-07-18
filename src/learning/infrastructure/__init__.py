"""Learning BC Infrastructure — port implementations and runtime infrastructure.

Provides:
    - InMemory implementations of all Learning BC ports (repositories,
      unit of work, event publisher, dataset exporter, clock)
    - Cross-BC adapters for testing (InMemoryIngestionReader, etc.)
    - Integration event buses and read models
    - Composition Root (LearningServiceFactory) for wiring all services
"""
