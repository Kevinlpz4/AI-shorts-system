"""
DeduplicateStep — deduplicates articles across sources.

This is the third step in the ingestion pipeline. It:
1. Reads normalized items from PipelineContext (set by NormalizeStep)
2. Deduplicates by content_hash (exact duplicate removal)
3. Optionally deduplicates by URL similarity (near-duplicates)
4. Stores deduplicated items in PipelineContext

Usage::

    step = DeduplicateStep()
    result = await step.execute(ctx)
"""
from __future__ import annotations

import logging
from urllib.parse import urlparse

from foundation.result.result import Result
from runtime.contracts.pipeline_context import PipelineContext
from runtime.contracts.pipeline_result import StepResult
from runtime.pipelines.base import PipelineStep

logger = logging.getLogger(__name__)


class DeduplicateStep:
    """Pipeline step that deduplicates items across sources.

    Uses content_hash for exact dedup and URL normalization for
    near-duplicate detection.
    """

    name: str = "deduplicate"
    order: int = 3
    is_fatal: bool = False

    async def execute(self, ctx: PipelineContext) -> Result[StepResult]:
        """Deduplicate all normalized items."""
        normalized: list[dict[str, str]] | None = ctx.get_step_result("normalize")  # type: ignore[assignment]
        if not normalized:
            logger.info("No normalized items to deduplicate — skipping")
            return Result.success(
                StepResult(
                    step_name=self.name,
                    success=True,
                    items_processed=0,
                    items_output=0,
                    metadata={"message": "No normalized items to deduplicate"},
                )
            )

        seen_hashes: set[str] = set()
        seen_urls: set[str] = set()
        deduplicated: list[dict[str, str]] = []
        duplicates_removed = 0

        for item in normalized:
            content_hash = item.get("content_hash", "")
            url = item.get("url", "")

            # Exact duplicate by content hash
            if content_hash and content_hash in seen_hashes:
                duplicates_removed += 1
                continue

            # Near-duplicate by normalized URL
            normalized_url = self._normalize_url(url)
            if normalized_url and normalized_url in seen_urls:
                duplicates_removed += 1
                continue

            if content_hash:
                seen_hashes.add(content_hash)
            if normalized_url:
                seen_urls.add(normalized_url)

            deduplicated.append(item)

        ctx.set_step_result("deduplicate", deduplicated)

        logger.info(
            "Deduplication: %d items → %d unique (%d duplicates removed)",
            len(normalized),
            len(deduplicated),
            duplicates_removed,
        )

        return Result.success(
            StepResult(
                step_name=self.name,
                success=True,
                items_processed=len(normalized),
                items_output=len(deduplicated),
                metadata={
                    "duplicates_removed": str(duplicates_removed),
                    "unique_items": str(len(deduplicated)),
                },
            )
        )

    def _normalize_url(self, url: str) -> str:
        """Normalize a URL for deduplication comparison.

        Strps tracking parameters, trailing slashes, normalizes scheme/host.
        """
        if not url:
            return ""

        try:
            parsed = urlparse(url)
            # Lowercase scheme and host
            scheme = parsed.scheme.lower()
            netloc = parsed.netloc.lower().removeprefix("www.")
            path = parsed.path.rstrip("/")

            return f"{scheme}://{netloc}{path}"
        except Exception:
            return url.lower().strip()
