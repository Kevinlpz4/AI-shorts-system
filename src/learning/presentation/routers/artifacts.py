"""
Artifacts router — GET /artifacts.

Lists all knowledge artifacts with version history.
Every artifact (dataset, model, report, snapshot) is tracked
with full provenance and integrity verification.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from learning.presentation.dependencies import ServiceDependencies, get_services
from learning.presentation.schemas.responses import ArtifactResponse

router = APIRouter()


def _artifact_to_response(artifact: object) -> ArtifactResponse:
    """Convert a KnowledgeArtifact entity to a response model."""
    return ArtifactResponse(
        artifact_id=str(artifact.id),  # type: ignore[arg-type]
        artifact_type=artifact.artifact_type_name,  # type: ignore[union-attr]
        version=artifact.version,  # type: ignore[union-attr]
        created_at=artifact.created_at.isoformat(),  # type: ignore[union-attr]
        created_by=artifact.created_by,  # type: ignore[union-attr]
        source_dataset=artifact.source_dataset,  # type: ignore[union-attr]
        algorithm_version=artifact.algorithm_version,  # type: ignore[union-attr]
        checksum=artifact.checksum,  # type: ignore[union-attr]
        status=artifact.status.value,  # type: ignore[union-attr]
    )


@router.get(
    "/artifacts",
    response_model=list[ArtifactResponse],
    summary="List knowledge artifacts",
)
async def list_artifacts(
    artifact_type: str | None = Query(
        default=None,
        description="Filter: DATASET, MODEL, REPORT, SNAPSHOT",
    ),
    services: ServiceDependencies = Depends(get_services),
) -> list[ArtifactResponse]:
    """List all knowledge artifacts with version history.

    Every artifact (dataset, model, report, snapshot) is tracked
    with full provenance and integrity verification.
    """
    if services.artifact_repo is None:
        return []

    if artifact_type:
        from learning.domain.entities.knowledge_artifact import ArtifactType

        artifacts = services.artifact_repo.find_by_type(ArtifactType(artifact_type))
    else:
        artifacts = services.artifact_repo.find_all()

    return [_artifact_to_response(a) for a in artifacts]
