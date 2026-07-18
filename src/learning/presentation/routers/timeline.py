"""
Timeline router — GET /timeline.

Queries the historical evolution of knowledge metrics.
Shows how source quality, keyword effectiveness, or model weights
changed over time. Every change is recorded — never overwritten.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from learning.presentation.dependencies import ServiceDependencies, get_services
from learning.presentation.schemas.responses import TimelineResponse, TimelineSnapshotResponse

router = APIRouter()


@router.get(
    "/timeline",
    response_model=TimelineResponse,
    summary="Query knowledge evolution timeline",
)
async def timeline(
    entity_type: str = Query(
        ..., description="Entity type: source, keyword, category, topic"
    ),
    entity_id: str = Query(..., description="Entity identifier"),
    metric_name: str = Query(
        default="approval_rate", description="Metric to track"
    ),
    services: ServiceDependencies = Depends(get_services),
) -> TimelineResponse:
    """Query the historical evolution of knowledge metrics.

    Shows how source quality, keyword effectiveness, or model weights
    changed over time. Every change is recorded — never overwritten.
    """
    if services.timeline_storage is None:
        return TimelineResponse(
            entity_type=entity_type,
            entity_id=entity_id,
            metric_name=metric_name,
            snapshots=[],
            trend="INSUFFICIENT_DATA",
        )

    evolution = services.timeline_storage.get_timeline(
        entity_type, entity_id, metric_name
    )
    snapshots = [
        TimelineSnapshotResponse(
            value=s.metric_value,
            sample_size=s.sample_size,
            recorded_at=s.snapshot_at.isoformat(),
        )
        for s in evolution.snapshots
    ]
    return TimelineResponse(
        entity_type=entity_type,
        entity_id=entity_id,
        metric_name=metric_name,
        snapshots=snapshots,
        trend=evolution.trend(),
    )
