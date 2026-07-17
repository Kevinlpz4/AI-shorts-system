"""
Application Queries — 8 consultas CQRS para el BC Learning.

Cada query es un ``@dataclass(frozen=True)`` sin lógica ni validaciones.
Solo transporte de datos.

Uso::

    from learning.application.queries import (
        GetFeedbackQuery,
        ListFeedbackQuery,
    )
"""
from __future__ import annotations

from learning.application.queries.analytics_queries import GetAnalyticsQuery
from learning.application.queries.dataset_queries import ListDatasetsQuery
from learning.application.queries.feedback_queries import (
    GetFeedbackQuery,
    ListFeedbackQuery,
)
from learning.application.queries.model_queries import (
    GetLearningModelQuery,
    GetLearningSignalsQuery,
    GetSourceQualityQuery,
)
from learning.application.queries.prediction_queries import (
    ExplainScoreQuery,
    PredictApprovalQuery,
)

__all__ = [
    # Feedback queries
    "GetFeedbackQuery",
    "ListFeedbackQuery",
    # Model queries
    "GetLearningModelQuery",
    "GetSourceQualityQuery",
    "GetLearningSignalsQuery",
    # Analytics queries
    "GetAnalyticsQuery",
    # Prediction queries
    "PredictApprovalQuery",
    "ExplainScoreQuery",
    # Dataset queries
    "ListDatasetsQuery",
]
