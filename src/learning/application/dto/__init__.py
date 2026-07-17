"""
Application DTOs — Data Transfer Objects inmutables para el BC Learning.

Cada DTO es un ``@dataclass(frozen=True)`` con solo tipos primitivos
y otros DTOs. No dependen de entidades de dominio.

Uso::

    from learning.application.dto import (
        FeedbackSummaryDTO,
        FeedbackDetailDTO,
    )
"""
from __future__ import annotations

from learning.application.dto.analytics_dto import AnalyticsDTO
from learning.application.dto.common_dto import ErrorDTO, PaginatedDTO, ResultDTO
from learning.application.dto.dataset_dto import DatasetDTO
from learning.application.dto.explanation_dto import ExplanationDTO
from learning.application.dto.feedback_dto import FeedbackDetailDTO, FeedbackSummaryDTO
from learning.application.dto.model_dto import LearningModelDTO
from learning.application.dto.prediction_dto import PredictionDTO
from learning.application.dto.signal_dto import LearningSignalDTO
from learning.application.dto.source_dto import KeywordStatDTO, SourceQualityDTO

__all__ = [
    # Feedback DTOs
    "FeedbackSummaryDTO",
    "FeedbackDetailDTO",
    # Signal DTOs
    "LearningSignalDTO",
    # Source DTOs
    "SourceQualityDTO",
    "KeywordStatDTO",
    # Model DTOs
    "LearningModelDTO",
    # Prediction DTOs
    "PredictionDTO",
    # Analytics DTOs
    "AnalyticsDTO",
    # Dataset DTOs
    "DatasetDTO",
    # Explanation DTOs
    "ExplanationDTO",
    # Common DTOs
    "PaginatedDTO",
    "ResultDTO",
    "ErrorDTO",
]
