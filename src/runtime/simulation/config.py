"""
Simulation configuration — immutable config for simulation runs.

All fields are frozen dataclasses. No mutation after creation.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SimulationConfig:
    """Configuration for a simulation run.

    Attributes:
        days: Number of virtual days to simulate.
        iterations: Max iterations per day (pipeline cycles).
        seed: Random seed for reproducibility.
        feedback_policy: Name of the feedback reviewer policy.
        speed: Execution speed ("accelerated" or "realtime").
        report_dir: Directory for reports and charts.
        articles_per_day: Base number of articles generated per day.
        source_count: Number of virtual sources to simulate.
        category_weights: Weight distribution per category.
    """

    days: int = 30
    iterations: int = 500
    seed: int = 42
    feedback_policy: str = "balanced"
    speed: str = "accelerated"
    report_dir: str = "simulation_reports"
    articles_per_day: int = 20
    source_count: int = 8
    category_weights: dict = field(default_factory=lambda: {
        "ai": 0.30,
        "gaming": 0.25,
        "tech": 0.20,
        "programming": 0.15,
        "startups": 0.10,
    })
    source_quality_initial: float = 0.60
    confidence_initial: float = 0.50
    learning_rate: float = 0.05
    decay_rate: float = 0.01

    @property
    def total_hours(self) -> float:
        return self.days * 24

    @property
    def total_articles(self) -> int:
        return self.days * self.articles_per_day

    def with_overrides(self, **kwargs) -> SimulationConfig:
        """Return a new config with overridden values."""
        from dataclasses import replace
        return replace(self, **kwargs)
