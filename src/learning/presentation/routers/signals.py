"""
Signals router — GET /signals.

Queries active learning signals with optional filters.
Signals represent aggregated insights from accumulated feedback.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from learning.presentation.dependencies import ServiceDependencies, get_services
from learning.presentation.schemas.responses import SignalResponse

router = APIRouter()


@router.get(
    "/signals",
    response_model=list[SignalResponse],
    summary="Query active learning signals",
)
async def signals(
    signal_type: str | None = Query(
        default=None,
        description="Filter by type: KEYWORD, SOURCE, CATEGORY, TOPIC, TIME",
    ),
    min_strength: float | None = Query(
        default=None, ge=0.0, le=1.0,
        description="Minimum signal strength filter",
    ),
    services: ServiceDependencies = Depends(get_services),
) -> list[SignalResponse]:
    """Query active learning signals with optional filters.

    Signals represent aggregated insights from accumulated feedback.
    Filter by signal type and/or minimum strength.
    """
    all_signals = services.signal_repo.find_all_active()
    result: list[SignalResponse] = []

    for s in all_signals:
        if signal_type and s.signal_type.value != signal_type:
            continue
        if min_strength is not None and s.strength.value < min_strength:
            continue
        result.append(
            SignalResponse(
                signal_type=s.signal_type.value,
                dimension=s.dimension,
                strength=s.strength.value,
                decay_factor=s.strength.decay_factor,
                sample_size=s.sample_size,
                approval_rate=s.approval_rate,
                window_start=s.window.start.isoformat(),
                window_end=s.window.end.isoformat(),
                last_updated=s.last_updated.isoformat(),
            )
        )

    return result
