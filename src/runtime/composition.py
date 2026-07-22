"""
Composition Root — wires all Runtime components together.

This is the ONLY place where concrete implementations are imported
and wired. All other modules depend on abstractions (Protocols, interfaces).

Usage::

    from runtime.composition import build_runtime

    manager, job = build_runtime()
    # manager is fully wired RegistryManager
    # job is the IngestionJob ready to execute
"""
from __future__ import annotations

import logging

from runtime.config import RuntimeConfig
from runtime.event_bridge import EventBridge
from runtime.jobs.ingestion_job import IngestionJob
from runtime.pipelines.deduplicate_step import DeduplicateStep
from runtime.pipelines.ingest_step import IngestStep
from runtime.pipelines.normalize_step import NormalizeStep
from runtime.providers.api.api_provider import APIProvider
from runtime.providers.catalog import ALL_SOURCES
from runtime.providers.reddit.reddit_provider import RedditProvider
from runtime.providers.rss.rss_provider import RSSProvider
from runtime.registry.registry_manager import RegistryManager

logger = logging.getLogger(__name__)


def build_runtime(config: RuntimeConfig | None = None) -> tuple[RegistryManager, IngestionJob]:
    """Build and wire the complete Runtime infrastructure.

    Args:
        config: Optional RuntimeConfig. If None, uses defaults.

    Returns:
        Tuple of (RegistryManager, IngestionJob) fully wired.
    """
    if config is None:
        config = RuntimeConfig()

    # ── Registry Manager ────────────────────────────────────────────
    manager = RegistryManager()

    # ── TechnologyAdapters (one per technology) ─────────────────────
    rss_provider = RSSProvider()
    reddit_provider = RedditProvider()
    api_provider = APIProvider()

    manager.providers.register(rss_provider)
    manager.providers.register(reddit_provider)
    manager.providers.register(api_provider)

    logger.info(
        "Registered TechnologyAdapters: %s",
        manager.providers.list_names(),
    )

    # ── SourceDefinitions ───────────────────────────────────────────
    for source in ALL_SOURCES:
        manager.sources.register(source)

    logger.info(
        "Registered %d SourceDefinitions: %s",
        len(ALL_SOURCES),
        [s.id for s in ALL_SOURCES],
    )

    # ── Pipeline Steps ──────────────────────────────────────────────
    ingest_step = IngestStep(
        source_registry=manager.sources,
        provider_registry=manager.providers,
    )
    normalize_step = NormalizeStep()
    deduplicate_step = DeduplicateStep()

    manager.steps.register(ingest_step)
    manager.steps.register(normalize_step)
    manager.steps.register(deduplicate_step)

    logger.info(
        "Registered PipelineSteps: %s",
        manager.steps.list_names(),
    )

    # ── EventBridge ─────────────────────────────────────────────────
    event_bridge = EventBridge(max_buffer=config.event_bridge_max_buffer)

    # ── IngestionJob ────────────────────────────────────────────────
    ingestion_job = IngestionJob(
        step_registry=manager.steps,
        event_bridge=event_bridge,
    )
    manager.jobs.register(ingestion_job)

    logger.info("IngestionJob registered and wired")

    return manager, ingestion_job
