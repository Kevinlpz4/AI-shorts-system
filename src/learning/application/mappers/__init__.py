"""
Application Mappers — convierten entidades de dominio a DTOs de aplicación.

Cada mapper convierte en una sola dirección: Domain Entity → DTO.
No realizan persistencia, no ejecutan reglas, no llaman repositorios.

Uso::

    from learning.application.mappers import FeedbackMapper

    summary = FeedbackMapper.to_summary(feedback_record)
    detail = FeedbackMapper.to_detail(feedback_record)
"""
from __future__ import annotations

from learning.application.mappers.analytics_mapper import AnalyticsMapper
from learning.application.mappers.dataset_mapper import DatasetMapper
from learning.application.mappers.feedback_mapper import FeedbackMapper
from learning.application.mappers.model_mapper import LearningModelMapper
from learning.application.mappers.signal_mapper import LearningSignalMapper
from learning.application.mappers.snapshot_mapper import FeatureSnapshotMapper
from learning.application.mappers.source_mapper import SourceQualityMapper

__all__ = [
    "FeedbackMapper",
    "LearningSignalMapper",
    "SourceQualityMapper",
    "LearningModelMapper",
    "FeatureSnapshotMapper",
    "DatasetMapper",
    "AnalyticsMapper",
]
