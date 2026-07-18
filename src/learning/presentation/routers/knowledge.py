"""
Knowledge router — GET /knowledge.

Returns a summary of all knowledge accumulated by the learning system:
top sources, keywords, categories, topics, and signal distribution.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from learning.presentation.dependencies import ServiceDependencies, get_services
from learning.presentation.schemas.responses import KnowledgeResponse, SourceQualityResponse, KeywordStatResponse

router = APIRouter()


def _profile_to_response(profile: object) -> SourceQualityResponse:
    """Convert a SourceQualityProfile entity to a response model."""
    confidence = min(1.0, profile.total_decisions / 30) if profile.total_decisions > 0 else 0.0  # type: ignore[union-attr]
    keywords = [
        KeywordStatResponse(
            keyword=kw.keyword,
            count=kw.count,
            approved_count=kw.approved_count,
            approval_rate=kw.approval_rate,
        )
        for kw in profile.keywords.values()  # type: ignore[union-attr]
    ]
    return SourceQualityResponse(
        source_name=profile.source_name,  # type: ignore[union-attr]
        approval_rate=profile.approval_rate,  # type: ignore[union-attr]
        total_decisions=profile.total_decisions,  # type: ignore[union-attr]
        approved_count=profile.approved_count,  # type: ignore[union-attr]
        rejected_count=profile.rejected_count,  # type: ignore[union-attr]
        confidence=confidence,
        trend="STABLE",
        keywords=keywords,
    )


@router.get(
    "/knowledge",
    response_model=KnowledgeResponse,
    summary="Get accumulated knowledge summary",
)
async def knowledge(
    services: ServiceDependencies = Depends(get_services),
) -> KnowledgeResponse:
    """Get a summary of all knowledge accumulated by the learning system.

    Shows top sources, keywords, categories, topics, and signal distribution.
    """
    # Get all active source profiles
    profiles = services.source_quality_repo.find_all_active()
    top_sources = sorted(profiles, key=lambda p: p.approval_rate, reverse=True)[:10]

    # Get all active signals
    signals = services.signal_repo.find_all_active()

    # Group by signal type
    keywords: set[str] = set()
    categories: set[str] = set()
    topics: set[str] = set()
    for s in signals:
        if s.signal_type.value == "KEYWORD":
            keywords.add(s.dimension)
        elif s.signal_type.value == "CATEGORY":
            categories.add(s.dimension)
        elif s.signal_type.value == "TOPIC":
            topics.add(s.dimension)

    # Calculate knowledge coverage
    total_possible = max(len(profiles) * 3, 1)
    covered = len([p for p in profiles if p.total_decisions > 0])
    coverage = min(1.0, covered / total_possible)

    # Get model version
    model_version = "unknown"
    model_result = services.model_repo.find_current()
    if model_result.is_success:
        model_version = str(model_result.value.algorithm_version)

    return KnowledgeResponse(
        top_sources=[_profile_to_response(p) for p in top_sources],
        top_keywords=sorted(keywords)[:20],
        top_categories=sorted(categories)[:10],
        top_topics=sorted(topics)[:10],
        active_signals_count=len(signals),
        knowledge_coverage=coverage,
        model_version=model_version,
    )
