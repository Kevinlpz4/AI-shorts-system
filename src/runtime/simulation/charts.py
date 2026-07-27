"""
Chart Generator — produces PNG charts from simulation metrics.

Generates 6 charts:
1. approval_rate.png — Approval rate over time
2. confidence.png — Confidence evolution
3. source_quality.png — Source quality evolution
4. learning_curve.png — Knowledge growth curve
5. dataset_growth.png — Dataset size over time
6. signals.png — Learning signals generation

Uses matplotlib for chart generation. Falls back gracefully if not available.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from runtime.simulation.metrics import SimulationMetrics


def _check_matplotlib() -> bool:
    """Check if matplotlib is available."""
    try:
        import matplotlib
        matplotlib.use("Agg")  # Non-interactive backend
        return True
    except ImportError:
        return False


def _get_style() -> dict[str, Any]:
    """Get consistent chart styling."""
    return {
        "figure.figsize": (10, 6),
        "figure.dpi": 150,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }


def generate_approval_rate_chart(
    metrics: SimulationMetrics, output_dir: str,
) -> str | None:
    """Generate approval rate over time chart."""
    if not _check_matplotlib():
        return None

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    history = metrics.approval_rate_history
    if not history:
        return None

    plt.rcParams.update(_get_style())
    fig, ax = plt.subplots()

    ax.plot(range(len(history)), [r * 100 for r in history],
            color="#2ecc71", linewidth=1.5, label="Approval Rate")
    ax.fill_between(range(len(history)), [r * 100 for r in history],
                    alpha=0.1, color="#2ecc71")
    ax.set_xlabel("Iteration", fontsize=11)
    ax.set_ylabel("Approval Rate (%)", fontsize=11)
    ax.set_title("Approval Rate Over Time", fontsize=13, fontweight="bold")
    ax.set_ylim(0, 100)
    ax.legend()

    path = Path(output_dir) / "approval_rate.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def generate_confidence_chart(
    metrics: SimulationMetrics, output_dir: str,
) -> str | None:
    """Generate confidence evolution chart."""
    if not _check_matplotlib():
        return None

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    history = metrics.confidence_history
    if not history:
        return None

    plt.rcParams.update(_get_style())
    fig, ax = plt.subplots()

    # Rolling average for smoother visualization
    window = min(50, len(history))
    if window > 1:
        rolling = []
        for i in range(len(history)):
            start = max(0, i - window + 1)
            rolling.append(sum(history[start:i+1]) / (i - start + 1))
    else:
        rolling = history

    ax.plot(range(len(rolling)), [c * 100 for c in rolling],
            color="#3498db", linewidth=1.5, label=f"Confidence (avg-{window})")
    ax.fill_between(range(len(rolling)), [c * 100 for c in rolling],
                    alpha=0.1, color="#3498db")
    ax.set_xlabel("Decision", fontsize=11)
    ax.set_ylabel("Confidence (%)", fontsize=11)
    ax.set_title("Confidence Evolution", fontsize=13, fontweight="bold")
    ax.set_ylim(0, 100)
    ax.legend()

    path = Path(output_dir) / "confidence.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def generate_source_quality_chart(
    metrics: SimulationMetrics, output_dir: str,
) -> str | None:
    """Generate source quality evolution chart."""
    if not _check_matplotlib():
        return None

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    history = metrics.source_quality_history
    if not history:
        return None

    plt.rcParams.update(_get_style())
    fig, ax = plt.subplots()

    ax.plot(range(len(history)), [q * 100 for q in history],
            color="#e67e22", linewidth=1.5, label="Avg Source Quality")
    ax.fill_between(range(len(history)), [q * 100 for q in history],
                    alpha=0.1, color="#e67e22")
    ax.set_xlabel("Iteration", fontsize=11)
    ax.set_ylabel("Quality Score (%)", fontsize=11)
    ax.set_title("Source Quality Evolution", fontsize=13, fontweight="bold")
    ax.set_ylim(0, 100)
    ax.legend()

    path = Path(output_dir) / "source_quality.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def generate_learning_curve_chart(
    metrics: SimulationMetrics, output_dir: str,
) -> str | None:
    """Generate knowledge growth curve chart."""
    if not _check_matplotlib():
        return None

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    snapshots = metrics.snapshots
    if not snapshots:
        return None

    plt.rcParams.update(_get_style())
    fig, ax = plt.subplots()

    days = [s.day for s in snapshots]
    growth = [s.knowledge_growth for s in snapshots]

    ax.plot(days, growth, color="#9b59b6", linewidth=1.5, label="Knowledge Growth")
    ax.fill_between(days, growth, alpha=0.1, color="#9b59b6")
    ax.set_xlabel("Day", fontsize=11)
    ax.set_ylabel("Knowledge Items", fontsize=11)
    ax.set_title("Learning Curve — Knowledge Growth", fontsize=13, fontweight="bold")
    ax.legend()

    path = Path(output_dir) / "learning_curve.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def generate_dataset_growth_chart(
    metrics: SimulationMetrics, output_dir: str,
) -> str | None:
    """Generate dataset size over time chart."""
    if not _check_matplotlib():
        return None

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    history = metrics.dataset_growth
    if not history:
        return None

    plt.rcParams.update(_get_style())
    fig, ax = plt.subplots()

    ax.plot(range(len(history)), history, color="#1abc9c", linewidth=1.5,
            label="Dataset Size")
    ax.fill_between(range(len(history)), history, alpha=0.1, color="#1abc9c")
    ax.set_xlabel("Iteration", fontsize=11)
    ax.set_ylabel("Articles in Dataset", fontsize=11)
    ax.set_title("Dataset Growth Over Time", fontsize=13, fontweight="bold")
    ax.legend()

    path = Path(output_dir) / "dataset_growth.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def generate_signals_chart(
    metrics: SimulationMetrics, output_dir: str,
) -> str | None:
    """Generate learning signals generation chart."""
    if not _check_matplotlib():
        return None

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    history = metrics.signals_count
    if not history:
        return None

    plt.rcParams.update(_get_style())
    fig, ax = plt.subplots()

    ax.plot(range(len(history)), history, color="#e74c3c", linewidth=1.5,
            label="Cumulative Signals")
    ax.fill_between(range(len(history)), history, alpha=0.1, color="#e74c3c")
    ax.set_xlabel("Iteration", fontsize=11)
    ax.set_ylabel("Signals Generated", fontsize=11)
    ax.set_title("Learning Signals Generation", fontsize=13, fontweight="bold")
    ax.legend()

    path = Path(output_dir) / "signals.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def generate_all_charts(
    metrics: SimulationMetrics, output_dir: str,
) -> list[str]:
    """Generate all 6 charts. Returns list of generated file paths."""
    generators = [
        generate_approval_rate_chart,
        generate_confidence_chart,
        generate_source_quality_chart,
        generate_learning_curve_chart,
        generate_dataset_growth_chart,
        generate_signals_chart,
    ]

    paths = []
    for gen in generators:
        result = gen(metrics, output_dir)
        if result:
            paths.append(result)

    return paths
