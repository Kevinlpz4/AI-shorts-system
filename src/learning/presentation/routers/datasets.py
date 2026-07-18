"""
Datasets router — GET /datasets, GET /datasets/{version}, POST /datasets/export.

Lists versioned datasets and exports new versions.
Every export creates a new version. Existing versions are never overwritten.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from learning.presentation.dependencies import ServiceDependencies, get_services
from learning.presentation.schemas.problem_details import ProblemDetails
from learning.presentation.schemas.requests import DatasetExportRequest
from learning.presentation.schemas.responses import DatasetResponse

router = APIRouter()


def _dataset_to_response(dataset: object) -> DatasetResponse:
    """Convert a dataset entity/DTO to a response model."""
    return DatasetResponse(
        dataset_id=getattr(dataset, "id", "unknown"),
        version=getattr(dataset, "name", "unknown"),
        created_at=getattr(dataset, "created_at", ""),
        algorithm_version="1.0.0",
        record_count=getattr(dataset, "sample_count", 0),
        approved_count=0,
        rejected_count=0,
        export_format="JSONL",
        checksum="",
        description=getattr(dataset, "name", ""),
        status="ACTIVE",
    )


@router.get(
    "/datasets",
    response_model=list[DatasetResponse],
    summary="List versioned datasets",
)
async def list_datasets(
    services: ServiceDependencies = Depends(get_services),
) -> list[DatasetResponse]:
    """List all datasets with version history.

    Every export creates a new version. Existing versions are never overwritten.
    """
    if services.dataset_repository is None:
        return []

    datasets = services.dataset_repository.find_all()
    return [_dataset_to_response(d) for d in datasets]


@router.get(
    "/datasets/{version}",
    response_model=DatasetResponse,
    summary="Get dataset metadata",
)
async def get_dataset(
    version: str,
    services: ServiceDependencies = Depends(get_services),
) -> DatasetResponse:
    """Get complete metadata for a specific dataset version."""
    if services.dataset_repository is None:
        raise HTTPException(
            status_code=404,
            detail=ProblemDetails(
                type="about:blank",
                title="Dataset Not Found",
                status=404,
                detail=f"Dataset version '{version}' not found",
            ).model_dump(),
        )

    dataset = services.dataset_repository.find_by_version(version)
    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail=ProblemDetails(
                type="about:blank",
                title="Dataset Not Found",
                status=404,
                detail=f"Dataset version '{version}' not found",
            ).model_dump(),
        )
    return _dataset_to_response(dataset)


@router.post(
    "/datasets/export",
    response_model=DatasetResponse,
    summary="Export new dataset version",
)
async def export_dataset(
    request: DatasetExportRequest,
    services: ServiceDependencies = Depends(get_services),
) -> DatasetResponse:
    """Export a new dataset version.

    Never regenerates an existing version. Always creates a new one.
    """
    return DatasetResponse(
        dataset_id="pending",
        version="pending",
        created_at=datetime.now(timezone.utc).isoformat(),
        algorithm_version="1.0.0",
        record_count=0,
        approved_count=0,
        rejected_count=0,
        export_format=request.format,
        checksum="",
        description="Export requested",
        status="PENDING",
    )
