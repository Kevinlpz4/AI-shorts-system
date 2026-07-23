"""
Rejection reasons — extensible catalog of normalized reason codes.

Design principles:
    1. Default reasons cover common rejection patterns.
    2. Custom reasons can be added at runtime (extends catalog).
    3. 'other' always requires a free-text comment.
    4. Reasons are immutable once created (frozen dataclass).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from foundation.result.result import Error, ErrorCode, Result


@dataclass(frozen=True)
class RejectionReason:
    """A normalized rejection reason."""

    code: str
    label: str
    description: str
    is_default: bool = False


class FeedbackReasons:
    """Extensible catalog of rejection reasons.

    Default reasons are loaded at construction. Custom reasons can be
    added via ``add()`` or injected via ``custom_reasons`` parameter.
    """

    DEFAULT_REASONS: Dict[str, RejectionReason] = {
        "very_relevant": RejectionReason(
            code="very_relevant",
            label="Muy relevante",
            description="El artículo es muy relevante para el canal",
            is_default=True,
        ),
        "low_relevance": RejectionReason(
            code="low_relevance",
            label="Poco relevante",
            description="El artículo tiene poca relevancia",
        ),
        "duplicate": RejectionReason(
            code="duplicate",
            label="Tema repetido",
            description="El tema ya fue cubierto recientemente",
        ),
        "unreliable_source": RejectionReason(
            code="unreliable_source",
            label="Fuente poco confiable",
            description="La fuente no es confiable",
        ),
        "clickbait": RejectionReason(
            code="clickbait",
            label="Clickbait",
            description="El título es engañoso",
        ),
        "low_quality": RejectionReason(
            code="low_quality",
            label="Baja calidad",
            description="El contenido es de baja calidad",
        ),
        "too_local": RejectionReason(
            code="too_local",
            label="Demasiado local",
            description="La noticia es demasiado local para el canal",
        ),
        "not_channel_fit": RejectionReason(
            code="not_channel_fit",
            label="No corresponde al canal",
            description="El contenido no se alinea con el canal",
        ),
        "incomplete": RejectionReason(
            code="incomplete",
            label="Información incompleta",
            description="El artículo no contiene suficiente información",
        ),
        "other": RejectionReason(
            code="other",
            label="Otro",
            description="Otra razón (requiere comentario)",
        ),
    }

    def __init__(self, custom_reasons: Optional[Dict[str, RejectionReason]] = None) -> None:
        self._reasons: Dict[str, RejectionReason] = dict(self.DEFAULT_REASONS)
        if custom_reasons:
            self._reasons.update(custom_reasons)

    def get(self, code: str) -> Result[RejectionReason]:
        """Get a reason by code."""
        if code in self._reasons:
            return Result.success(self._reasons[code])
        return Result.failure(
            Error(code=ErrorCode.UNKNOWN, message=f"Unknown reason code: {code}")
        )

    def add(self, reason: RejectionReason) -> Result[None]:
        """Add a custom reason (extends catalog without code changes)."""
        self._reasons[reason.code] = reason
        return Result.success(None)

    def list_all(self) -> List[RejectionReason]:
        """List all available reasons."""
        return list(self._reasons.values())

    def validate(self, reason_code: str, comment: Optional[str] = None) -> Result[bool]:
        """Validate a reason code. 'other' requires a comment."""
        result = self.get(reason_code)
        if result.is_failure:
            return Result.failure(result.error)
        if reason_code == "other" and not comment:
            return Result.failure(
                Error(code=ErrorCode.UNKNOWN, message="'other' reason requires a comment")
            )
        return Result.success(True)
