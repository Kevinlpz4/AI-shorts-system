"""
NormalizeStep — normalizes raw provider results to a standard format.

This is the second step in the ingestion pipeline. It:
1. Reads raw ProviderResults from PipelineContext (set by IngestStep)
2. Normalizes each item to a standard format:
   - title, url, published, summary, source_id, content_hash
   - tags from source defaults
3. Stores normalized items in PipelineContext for downstream steps

Usage::

    step = NormalizeStep()
    result = await step.execute(ctx)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from foundation.result.result import Result
from runtime.contracts.pipeline_context import PipelineContext
from runtime.contracts.pipeline_result import StepResult
from runtime.contracts.provider_result import ProviderResult
from runtime.pipelines.base import PipelineStep

logger = logging.getLogger(__name__)

# Fields that every normalized item must have
REQUIRED_FIELDS = {"title", "url", "source_id", "content_hash"}


class NormalizeStep:
    """Pipeline step that normalizes raw items from providers.

    Ensures all items have a consistent schema regardless of
    which TechnologyAdapter produced them.
    """

    name: str = "normalize"
    order: int = 2
    is_fatal: bool = False

    async def execute(self, ctx: PipelineContext) -> Result[StepResult]:
        """Normalize all provider results from the ingest step."""
        raw_results: list[ProviderResult] | None = ctx.get_step_result("ingest")  # type: ignore[assignment]
        if not raw_results:
            logger.info("No raw results to normalize — skipping")
            return Result.success(
                StepResult(
                    step_name=self.name,
                    success=True,
                    items_processed=0,
                    items_output=0,
                    metadata={"message": "No raw results to normalize"},
                )
            )

        all_normalized: list[dict[str, str]] = []
        total_errors: list[str] = []

        for provider_result in raw_results:
            if provider_result.errors:
                total_errors.extend(provider_result.errors)

            for item in provider_result.items:
                normalized = self._normalize_item(item, provider_result)
                if normalized:
                    all_normalized.append(normalized)

        ctx.set_step_result("normalize", all_normalized)

        return Result.success(
            StepResult(
                step_name=self.name,
                success=True,
                items_processed=sum(len(pr.items) for pr in raw_results),
                items_output=len(all_normalized),
                errors=total_errors,
                metadata={
                    "sources_processed": str(len(raw_results)),
                    "total_normalized": str(len(all_normalized)),
                },
            )
        )

    def _normalize_item(
        self, item: dict[str, str], provider_result: ProviderResult,
    ) -> dict[str, str] | None:
        """Normalize a single item from a provider result.

        Returns None if the item is missing critical fields.
        """
        title = (item.get("title") or "").strip()
        url = (item.get("url") or "").strip()
        source_id = item.get("source_id", provider_result.source_id)

        if not title and not url:
            return None

        normalized: dict[str, str] = {
            "title": title or "Untitled",
            "url": url,
            "published": item.get("published", ""),
            "summary": (item.get("summary") or "")[:500],
            "source_id": source_id,
            "content_hash": item.get("content_hash", ""),
            "normalized_at": datetime.now(timezone.utc).isoformat(),
        }

        # Carry forward provider-specific fields (tags, scores, etc.)
        for key, value in item.items():
            if key not in normalized and key not in ("fetched_at",):
                normalized[key] = value

        return normalized
