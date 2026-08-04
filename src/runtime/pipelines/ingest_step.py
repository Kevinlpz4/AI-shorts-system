"""
IngestStep — fetches from all enabled sources via TechnologyAdapters.

This is the first step in the ingestion pipeline. It:
1. Reads enabled sources from SourceRegistry
2. For each source, gets the appropriate TechnologyAdapter from ProviderRegistry
3. Fetches data from each source
4. Stores raw ProviderResults in PipelineContext

Usage::

    step = IngestStep(source_registry, provider_registry)
    result = await step.execute(ctx)
"""
from __future__ import annotations

import logging

from foundation.result.result import Result
from runtime.contracts.pipeline_context import PipelineContext
from runtime.contracts.pipeline_result import StepResult
from runtime.contracts.provider_result import ProviderResult
from runtime.contracts.source_definition import SourceDefinition
from runtime.registry.provider_registry import ProviderRegistry
from runtime.registry.source_registry import SourceRegistry

logger = logging.getLogger(__name__)


class IngestStep:
    """Pipeline step that fetches data from all enabled sources.

    Uses SourceRegistry to find enabled sources, ProviderRegistry
    to get the right TechnologyAdapter, and fetches data.
    """

    name: str = "ingest"
    order: int = 1
    is_fatal: bool = False

    def __init__(
        self,
        source_registry: SourceRegistry,
        provider_registry: ProviderRegistry,
    ) -> None:
        self._source_registry = source_registry
        self._provider_registry = provider_registry

    async def execute(self, ctx: PipelineContext) -> Result[StepResult]:
        """Execute ingestion across all enabled sources."""
        sources = self._source_registry.get_enabled()
        if not sources:
            logger.info("No enabled sources — skipping ingestion")
            return Result.success(
                StepResult(
                    step_name=self.name,
                    success=True,
                    items_processed=0,
                    items_output=0,
                    metadata={"message": "No enabled sources"},
                )
            )

        all_results: list[ProviderResult] = []
        total_errors: list[str] = []
        total_items = 0

        for source in sources:
            try:
                result = await self._fetch_source(source)
                all_results.append(result)
                total_items += len(result.items)
                if result.errors:
                    total_errors.extend(result.errors)
            except Exception as exc:
                error_msg = f"Failed to fetch source '{source.id}': {exc}"
                logger.warning(error_msg)
                total_errors.append(error_msg)
                # Create a failed result so pipeline continues
                all_results.append(
                    ProviderResult(
                        source_id=source.id,
                        provider=source.technology,
                        errors=[error_msg],
                    )
                )

        ctx.set_step_result("ingest", all_results)

        success = len(total_errors) < len(sources)
        return Result.success(
            StepResult(
                step_name=self.name,
                success=success,
                items_processed=len(sources),
                items_output=total_items,
                errors=total_errors,
                metadata={
                    "sources_fetched": str(len(sources)),
                    "sources_with_errors": str(len(total_errors)),
                },
            )
        )

    async def _fetch_source(self, source: SourceDefinition) -> ProviderResult:
        """Fetch data from a single source using its TechnologyAdapter.

        Uses ``source.technology`` to look up the correct adapter
        (e.g., ``"rss"`` → RSSProvider, ``"api"`` → APIProvider).
        """
        adapter = self._provider_registry.get(source.technology)
        if adapter is None:
            return ProviderResult(
                source_id=source.id,
                provider=source.technology,
                errors=[f"Technology adapter '{source.technology}' not found in registry"],
            )

        # Build config from source metadata
        config = dict(source.metadata)
        items = await adapter.fetch(source.id, config)

        return ProviderResult(
            source_id=source.id,
            provider=source.technology,
            items=items,
            metadata={"item_count": str(len(items))},
        )
