# Tasks: Sprint 7.0 — Learning Bounded Context

## Phase 1: Domain Layer (Sprint 7.1)

- [ ] 1.1 Create `src/learning/domain/entities/ids.py` — DecisionId, SourceQualityId, KeywordId inheriting EntityId with generate() classmethod
- [ ] 1.2 Create `src/learning/domain/exceptions/errors.py` — LearningErrorCode str, Enum (DECISION_NOT_FOUND, SOURCE_QUALITY_NOT_FOUND, DUPLICATE_DECISION, INVALID_WEIGHTS, WEIGHT_OUT_OF_BOUNDS, KEYWORD_NOT_FOUND)
- [ ] 1.3 Create `src/learning/domain/value_objects/approval_rate.py` — frozen dataclass: approved/total ratio with properties is_high_quality, confidence
- [ ] 1.4 Create `src/learning/domain/value_objects/weight_adjustment.py` — frozen dataclass: scoring weight deltas with validate_bounds (min=0.05, max=0.60)
- [ ] 1.5 Create `src/learning/domain/value_objects/rejection_category.py` — frozen dataclass: classified rejection reason with RejectionReason enum
- [ ] 1.6 Create `src/learning/domain/value_objects/feature_vector.py` — frozen dataclass: extracted article features (title_keywords, source_type, language, word_count, has_author, has_url)
- [ ] 1.7 Create `src/learning/domain/entities/decision_history.py` — AggregateRoot: records approve/reject decisions with score snapshot, source, keywords; emits DecisionRecorded event
- [ ] 1.8 Create `src/learning/domain/entities/source_quality.py` — AggregateRoot: per-source quality profile with approval_rate, total_decisions, trend; emits SourceQualityChanged event
- [ ] 1.9 Create `src/learning/domain/entities/keyword_effectiveness.py` — Entity: per-keyword approval stats with effectiveness_score property
- [ ] 1.10 Create `src/learning/domain/events/learning_events.py` — ScoringWeightsUpdated(DomainEvent), SourceQualityChanged(DomainEvent), DecisionRecorded(DomainEvent)
- [ ] 1.11 Create `src/learning/domain/events/integration_events.py` — TopicApprovedIntegration, TopicRejectedIntegration inheriting IntegrationEvent with source_boundary="research"
- [ ] 1.12 Create `src/learning/domain/ports/repositories.py` — Protocol ports: DecisionHistoryRepository, SourceQualityRepository, KeywordEffectivenessRepository, ScoringWeightsRepository
- [ ] 1.13 Create `src/learning/domain/ports/ingestion_reader.py` — Protocol: IngestionReader (read-only: find_article_by_id, find_source_by_id, find_keywords_for_article)
- [ ] 1.14 Create `src/learning/__init__.py` and `src/learning/domain/__init__.py` — package init files
- [ ] 1.15 Write tests: `tests/learning/domain/` — unit tests for all entities, VOs, events, IDs, error codes (TDD: tests first)

## Phase 2: Application Layer (Sprint 7.2)

- [ ] 2.1 Create `src/learning/application/commands/decision_commands.py` — RecordDecisionCommand (frozen dataclass: topic_id, is_approved, source_name, score_components, keywords, rejection_reason)
- [ ] 2.2 Create `src/learning/application/commands/weight_commands.py` — AdjustScoringWeightsCommand (frozen dataclass: component, delta)
- [ ] 2.3 Create `src/learning/application/queries/quality_queries.py` — GetSourceQualityQuery, ListSourceQualitiesQuery, GetKeywordEffectivenessQuery
- [ ] 2.4 Create `src/learning/application/queries/prediction_queries.py` — PredictApprovalQuery (frozen dataclass: source_name, keywords, score_components)
- [ ] 2.5 Create `src/learning/application/dto/decision_dto.py` — DecisionSummaryDTO, DecisionDetailDTO (frozen dataclasses)
- [ ] 2.6 Create `src/learning/application/dto/quality_dto.py` — SourceQualityDTO, KeywordEffectivenessDTO, ScoringWeightsDTO
- [ ] 2.7 Create `src/learning/application/mappers/learning_mapper.py` — LearningMapper: entity→DTO conversions
- [ ] 2.8 Create `src/learning/application/errors/error_code.py` — ApplicationErrorCode (COMMAND_INVALID, RESOURCE_NOT_FOUND, OPERATION_FAILED)
- [ ] 2.9 Create `src/learning/application/errors/error_mapper.py` — ErrorMapper for LearningErrorCode → ApplicationErrorCode
- [ ] 2.10 Create `src/learning/application/services/learning_service.py` — record_decision, get_source_quality, get_keyword_effectiveness, predict_approval
- [ ] 2.11 Create `src/learning/application/services/weight_service.py` — adjust_weights, get_current_weights, revert_weights
- [ ] 2.12 Create `src/learning/application/services/feature_extractor.py` — extract_features_from_article (keyword extraction, word count, metadata)
- [ ] 2.13 Write tests: `tests/learning/application/` — service tests with InMemory repos, command/query tests

## Phase 3: Integration Layer (Sprint 7.3)

- [ ] 3.1 Create `src/learning/application/integration/topic_event_adapter.py` — maps Research TopicApproved/TopicRejected → RecordDecisionCommand
- [ ] 3.2 Create `src/learning/application/integration/ingestion_adapter.py` — implements IngestionReader port, delegates to Ingestion repositories (read-only)
- [ ] 3.3 Create `src/learning/application/integration/event_handler.py` — IntegrationEventHandler: consumes IntegrationEvents, routes to LearningService
- [ ] 3.4 Write tests: `tests/learning/integration/` — adapter tests verifying event→command mapping

## Phase 4: Infrastructure Layer (Sprint 7.4)

- [ ] 4.1 Create `src/learning/infrastructure/inmemory/repositories.py` — InMemoryDecisionHistoryRepository, InMemorySourceQualityRepository, InMemoryKeywordEffectivenessRepository, InMemoryScoringWeightsRepository
- [ ] 4.2 Create `src/learning/infrastructure/inmemory/unit_of_work.py` — InMemoryUnitOfWork for Learning BC
- [ ] 4.3 Create `src/learning/infrastructure/persistence/types.py` — EntityIdType TypeDecorator for Learning IDs
- [ ] 4.4 Create `src/learning/infrastructure/persistence/models.py` — SQLAlchemy models: DecisionHistoryModel, SourceQualityModel, KeywordEffectivenessModel, ScoringWeightsModel
- [ ] 4.5 Create `src/learning/infrastructure/persistence/repositories/` — SQLAlchemy implementations of all 4 repository ports
- [ ] 4.6 Create `src/learning/infrastructure/persistence/unit_of_work.py` — SQLAlchemyUnitOfWork for Learning BC
- [ ] 4.7 Create `src/learning/infrastructure/event_publisher.py` — SQLAlchemyEventPublisher (or reuse Ingestion's pattern)
- [ ] 4.8 Write tests: `tests/learning/infrastructure/` — InMemory repo tests + SQLAlchemy repo tests (integration)

## Phase 5: Persistence & Analytics (Sprint 7.5)

- [ ] 5.1 Create migration script: `scripts/migrations/learning_tables.sql` — DDL for learning_decision_history, learning_source_quality, learning_keyword_effectiveness, learning_scoring_weights
- [ ] 5.2 Create `src/learning/application/analytics/score_calibration.py` — score calibration analytics: predicted vs actual outcome
- [ ] 5.3 Create `src/learning/application/analytics/rejection_patterns.py` — rejection pattern analysis: common reasons, trends
- [ ] 5.4 Create `src/learning/application/analytics/temporal_patterns.py` — time-based approval patterns
- [ ] 5.5 Write tests: `tests/learning/analytics/` — analytics query tests

## Phase 6: Presentation Layer (Sprint 7.6)

- [ ] 6.1 Create `src/learning/presentation/schemas/decisions.py` — Pydantic request/response: RecordDecisionRequest, DecisionSummaryResponse, DecisionDetailResponse
- [ ] 6.2 Create `src/learning/presentation/schemas/quality.py` — Pydantic: SourceQualityResponse, KeywordEffectivenessResponse, ScoringWeightsResponse
- [ ] 6.3 Create `src/learning/presentation/routers/decisions.py` — POST /api/v1/learning/decisions, GET /api/v1/learning/decisions, GET /api/v1/learning/decisions/{id}
- [ ] 6.4 Create `src/learning/presentation/routers/quality.py` — GET /api/v1/learning/sources/{id}/quality, GET /api/v1/learning/keywords, GET /api/v1/learning/weights
- [ ] 6.5 Create `src/learning/presentation/routers/predictions.py` — POST /api/v1/learning/predict
- [ ] 6.6 Create `src/learning/presentation/dependencies.py` — DI providers: get_learning_service, get_weight_service, get_uow
- [ ] 6.7 Create `src/learning/presentation/exceptions.py` — Problem Detail handlers + error code→HTTP status mapper
- [ ] 6.8 Register Learning router in main app — mount Learning routers under /api/v1/learning
- [ ] 6.9 Write tests: `tests/learning/presentation/` — endpoint tests with InMemory repos

## Phase 7: Dataset Generation (Sprint 7.7)

- [ ] 7.1 Create `src/learning/application/dataset/dataset_service.py` — generate_training_dataset: extracts features + labels from decision history
- [ ] 7.2 Create `src/learning/application/dataset/feature_pipeline.py` — feature extraction pipeline: article→FeatureVector with keyword extraction
- [ ] 7.3 Create `src/learning/application/dataset/exporters.py` — CSV/JSON export for training datasets
- [ ] 7.4 Write tests: `tests/learning/dataset/` — dataset generation tests with synthetic data

## Phase 8: Testing & Quality (Sprint 7.8)

- [ ] 8.1 Write integration tests: `tests/learning/integration/test_cross_bc.py` — end-to-end: Research event → Learning decision record → source quality update
- [ ] 8.2 Write integration tests: `tests/learning/integration/test_analytics.py` — analytics queries against populated data
- [ ] 8.3 Write E2E tests: `tests/learning/e2e/` — full API flow tests via HTTP client
- [ ] 8.4 Create `tests/learning/conftest.py` — shared fixtures: InMemory repos, sample data factories
- [ ] 8.5 Verify: zero regressions in existing test suite (1838+ tests)
