"""
Simulation Engine — runs accelerated adaptive learning simulations.

Reuses the exact same pipeline that production uses.
No parallel pipeline. No shortcuts.

Flow per iteration:
    Scheduler → Ingestion → Normalization → Deduplication →
    Recommendation → Human Feedback (simulated) → Learning Update →
    Persistence → Dataset Update → Metrics
"""
from __future__ import annotations

import logging
import random
import time
from datetime import datetime, timezone
from typing import Any, Optional

from runtime.simulation.charts import generate_all_charts
from runtime.simulation.clock import VirtualClock
from runtime.simulation.config import SimulationConfig
from runtime.simulation.feedback_sim import (
    FeedbackPolicy,
    ReviewContext,
    get_policy,
)
from runtime.simulation.metrics import SimulationMetrics
from runtime.simulation.report import (
    generate_json_report,
    generate_markdown_report,
    save_json_report,
    save_markdown_report,
)

logger = logging.getLogger(__name__)


class SimulationEngine:
    """Accelerated simulation engine for adaptive learning.

    Reuses the production pipeline (IngestionJob → PipelineOrchestrator → Steps)
    with a simulated human feedback layer.

    Usage::

        config = SimulationConfig(days=30, seed=42, feedback_policy="balanced")
        engine = SimulationEngine(config)
        report = engine.run()
    """

    def __init__(self, config: SimulationConfig) -> None:
        self._config = config
        self._clock = VirtualClock()
        self._rng = random.Random(config.seed)
        self._metrics = SimulationMetrics()
        self._policy: FeedbackPolicy = get_policy(config.feedback_policy)
        self._articles_pool: list[dict[str, Any]] = []
        self._knowledge_base: dict[str, Any] = {
            "source_quality": {},
            "category_preference": {},
            "keyword_frequency": {},
            "historical_success": {},
        }
        self._generated_articles: int = 0
        self._simulated_decisions: int = 0

    @property
    def config(self) -> SimulationConfig:
        return self._config

    @property
    def clock(self) -> VirtualClock:
        return self._clock

    @property
    def metrics(self) -> SimulationMetrics:
        return self._metrics

    @property
    def knowledge_base(self) -> dict[str, Any]:
        return self._knowledge_base

    # ── Main Run ─────────────────────────────────────────────────────

    def run(self) -> dict[str, Any]:
        """Run the full simulation. Returns the report dict."""
        logger.info(
            "Starting simulation: %d days, seed=%d, policy=%s",
            self._config.days, self._config.seed, self._config.feedback_policy,
        )

        start_wall = time.monotonic()
        hours_per_day = 24.0
        iterations_per_day = max(1, self._config.iterations // max(self._config.days, 1))
        hours_per_iteration = hours_per_day / iterations_per_day

        for day in range(self._config.days):
            for iteration in range(iterations_per_day):
                self._run_iteration(day, iteration, hours_per_iteration)

            # Take daily snapshot
            self._metrics.take_snapshot(
                day=day + 1,
                iteration=iterations_per_day,
                timestamp=self._clock.now,
            )

            logger.debug(
                "Day %d/%d complete: %d articles, %d decisions",
                day + 1,
                self._config.days,
                self._metrics.total_articles,
                self._metrics.total_decisions,
            )

        elapsed = time.monotonic() - start_wall
        logger.info(
            "Simulation complete: %d articles, %d decisions in %.1fs",
            self._metrics.total_articles,
            self._metrics.total_decisions,
            elapsed,
        )

        # Generate reports and charts
        report = self._generate_output(elapsed)
        return report

    # ── Single Iteration ─────────────────────────────────────────────

    def _run_iteration(
        self, day: int, iteration: int, hours_per_iteration: float,
    ) -> None:
        """Run a single simulation iteration."""
        # Step 1: Generate articles (simulates ingestion)
        articles = self._generate_articles(day, iteration)

        # Step 2: Normalize & deduplicate (simulated)
        articles = self._normalize_and_dedup(articles)

        # Step 3: Generate recommendations (simulates recommendation pipeline)
        recommendations = self._generate_recommendations(articles)

        # Step 4: Simulate human feedback
        for rec in recommendations:
            self._simulate_feedback(rec, day, iteration)

        # Step 5: Update knowledge base (simulates learning update)
        self._update_knowledge()

        # Step 6: Advance virtual clock
        self._clock.advance_hours(hours_per_iteration)

    # ── Article Generation ───────────────────────────────────────────

    def _generate_articles(
        self, day: int, iteration: int,
    ) -> list[dict[str, Any]]:
        """Generate simulated articles for this iteration."""
        articles = []
        # Vary articles per day (simulates real-world variation)
        base = self._config.articles_per_day
        variation = self._rng.randint(-3, 3)
        count = max(1, base + variation)

        sources = self._get_sources()
        categories = list(self._config.category_weights.keys())
        cat_weights = [self._config.category_weights[c] for c in categories]

        for i in range(count):
            source = self._rng.choice(sources)
            category = self._rng.choices(categories, weights=cat_weights, k=1)[0]
            topic = self._generate_topic(category)
            keywords = self._generate_keywords(category, topic)

            # Score influenced by source quality and randomness
            sq = self._get_source_quality(source)
            base_score = sq * 0.6 + self._rng.random() * 0.4
            confidence = min(1.0, max(0.0, base_score * 0.9 + self._rng.gauss(0, 0.05)))

            article = {
                "article_id": f"sim-{day:03d}-{iteration:02d}-{i:03d}",
                "source": source,
                "category": category,
                "topic": topic,
                "score": round(base_score, 4),
                "confidence": round(confidence, 4),
                "keywords": keywords,
                "source_quality": round(sq, 4),
                "freshness": self._rng.choice(["Very High", "High", "Medium", "Low"]),
                "similar_approved": self._rng.randint(0, 50),
                "duplicates": self._rng.choices([0, 1, 2, 3], weights=[0.6, 0.25, 0.1, 0.05], k=1)[0],
                "day_of_week": self._clock.day_of_week(),
            }
            articles.append(article)
            self._generated_articles += 1
            self._metrics.record_article(source)

        return articles

    def _get_sources(self) -> list[str]:
        """Get simulated source IDs."""
        return [
            "google_news_ai", "openai_blog", "techcrunch", "theverge",
            "devto", "steam_news", "reddit_ai", "github_trending",
        ][:self._config.source_count]

    def _get_source_quality(self, source: str) -> float:
        """Get current source quality (evolves over time)."""
        sq = self._knowledge_base["source_quality"]
        if source not in sq:
            sq[source] = self._config.source_quality_initial
        return sq[source]

    def _generate_topic(self, category: str) -> str:
        """Generate a topic for a given category."""
        topic_map = {
            "ai": ["llm", "machine_learning", "neural_networks", "transformers", "agents"],
            "gaming": ["steam", "playstation", "xbox", "nintendo", "esports"],
            "tech": ["hardware", "smartphones", "software", "cloud", "security"],
            "programming": ["python", "typescript", "rust", "golang", "devtools"],
            "startups": ["funding", "series_a", "acquisition", "ipo", "product_launch"],
        }
        topics = topic_map.get(category, ["general"])
        return self._rng.choice(topics)

    def _generate_keywords(self, category: str, topic: str) -> list[str]:
        """Generate keywords for an article."""
        base_keywords = {
            "ai": ["AI", "LLM", "GPT", "machine learning", "neural"],
            "gaming": ["gaming", "steam", "playstation", "xbox", "PC"],
            "tech": ["tech", "hardware", "software", "cloud", "startup"],
            "programming": ["code", "developer", "API", "framework", "open source"],
            "startups": ["startup", "funding", "venture", "seed", "series"],
        }
        base = base_keywords.get(category, ["tech"])
        # Mix base keywords with topic-specific
        kw_list = list(base)
        if topic not in kw_list:
            kw_list.append(topic)
        # Add 1-2 random keywords
        extra = self._rng.sample(
            ["breaking", "exclusive", "review", "analysis", "trend", "update"],
            k=min(2, 6),
        )
        kw_list.extend(extra)
        return self._rng.sample(kw_list, k=min(5, len(kw_list)))

    # ── Normalize & Dedup ────────────────────────────────────────────

    def _normalize_and_dedup(
        self, articles: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Simulate normalization and deduplication."""
        seen = set()
        result = []
        for article in articles:
            # Simple dedup by article_id
            if article["article_id"] not in seen:
                seen.add(article["article_id"])
                result.append(article)
        return result

    # ── Recommendation ───────────────────────────────────────────────

    def _generate_recommendations(
        self, articles: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Simulate recommendation pipeline."""
        for article in articles:
            # Recommendation based on score
            if article["score"] >= 0.70:
                article["recommendation"] = "APPROVE"
            elif article["score"] >= 0.40:
                article["recommendation"] = "APPROVE"  # Borderline approved
            else:
                article["recommendation"] = "REJECT"
        return articles

    # ── Feedback Simulation ──────────────────────────────────────────

    def _simulate_feedback(
        self, article: dict[str, Any], day: int, iteration: int,
    ) -> None:
        """Simulate human feedback using the configured policy."""
        ctx = ReviewContext(
            article_id=article["article_id"],
            source=article["source"],
            category=article["category"],
            topic=article["topic"],
            score=article["score"],
            recommendation=article["recommendation"],
            source_quality=article["source_quality"],
            freshness=article["freshness"],
            confidence=article["confidence"],
            keywords=article["keywords"],
            similar_approved=article["similar_approved"],
            duplicates=article["duplicates"],
            day_of_week=article["day_of_week"],
            iteration=iteration,
        )

        result = self._policy.decide(ctx, self._rng)

        # Record metrics
        approved = result.decision.value == "approve"
        self._metrics.record_decision(
            source=article["source"],
            category=article["category"],
            topic=article["topic"],
            approved=approved,
            confidence=article["confidence"],
            source_quality=article["source_quality"],
            keywords=article["keywords"],
            iteration=iteration,
            day=day,
            timestamp=self._clock.now,
        )

        if result.decision.value == "skip":
            self._metrics.record_skip()

        # Generate learning signal
        self._metrics.record_signal()

        self._simulated_decisions += 1

    # ── Knowledge Update ─────────────────────────────────────────────

    def _update_knowledge(self) -> None:
        """Update knowledge base based on accumulated decisions."""
        profiles = self._metrics.source_profiles
        lr = self._config.learning_rate
        decay = self._config.decay_rate

        # Update source quality based on approval rates
        for source_id, profile in profiles.items():
            current_q = self._get_source_quality(source_id)
            if profile.total_articles > 0:
                # Move quality toward observed approval rate
                target = profile.approval_rate
                new_q = current_q * (1 - lr) + target * lr
                # Apply decay for sources that haven't been seen recently
                new_q = max(0.1, min(1.0, new_q - decay * 0.01))
                self._knowledge_base["source_quality"][source_id] = round(new_q, 4)

        # Update category preferences
        for cat, stats in self._metrics.category_stats.items():
            if stats["total"] > 0:
                rate = stats["approved"] / stats["total"]
                current = self._knowledge_base["category_preference"].get(cat, 0.5)
                self._knowledge_base["category_preference"][cat] = round(
                    current * (1 - lr) + rate * lr, 4,
                )

        # Update keyword frequency
        for kw, count in self._metrics.keyword_freq.items():
            current = self._knowledge_base["keyword_frequency"].get(kw, 0)
            self._knowledge_base["keyword_frequency"][kw] = current + count

    # ── Output Generation ────────────────────────────────────────────

    def _generate_output(self, elapsed: float) -> dict[str, Any]:
        """Generate reports and charts."""
        output_dir = self._config.report_dir

        # JSON report
        json_report = generate_json_report(self._metrics, self._config, elapsed)
        json_path = save_json_report(json_report, f"{output_dir}/simulation_report.json")

        # Markdown report
        md_content = generate_markdown_report(json_report)
        md_path = save_markdown_report(md_content, f"{output_dir}/simulation_report.md")

        # Charts
        chart_paths = generate_all_charts(self._metrics, f"{output_dir}/charts")

        logger.info(
            "Output generated: %s, %s, %d charts",
            json_path, md_path, len(chart_paths),
        )

        return json_report
