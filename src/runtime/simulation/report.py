"""
Report Generator — produces JSON and Markdown improvement reports.

Generates comprehensive simulation reports answering:
- How many articles processed?
- How many decisions made?
- Which categories grew?
- Which sources improved/worsened?
- How did confidence evolve?
- How did precision evolve?
- How much did the dataset grow?
- What new signals appeared?
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.simulation.metrics import SimulationMetrics


def generate_json_report(
    metrics: SimulationMetrics,
    config: Any,
    elapsed_seconds: float,
) -> dict[str, Any]:
    """Generate a comprehensive JSON report dict."""
    snapshots = metrics.snapshots
    first_snap = snapshots[0] if snapshots else None
    last_snap = snapshots[-1] if snapshots else None

    # Evolution deltas
    confidence_delta = 0.0
    approval_delta = 0.0
    quality_delta = 0.0
    if first_snap and last_snap:
        confidence_delta = last_snap.avg_confidence - first_snap.avg_confidence
        approval_delta = last_snap.approval_rate - first_snap.approval_rate
        quality_delta = last_snap.avg_source_quality - first_snap.avg_source_quality

    # Top/worst sources
    top_sources = metrics.top_sources
    worst_sources = metrics.worst_sources

    # Category breakdown
    category_breakdown = metrics.category_breakdown

    # Keywords
    top_keywords = [
        {"keyword": kw, "count": count}
        for kw, count in metrics.top_keywords
    ]

    # Confidence evolution (daily snapshots)
    confidence_evolution = [
        {"day": s.day, "value": s.avg_confidence}
        for s in snapshots
        if s.iteration == 0 or s == last_snap
    ]

    # Dataset growth
    dataset_evolution = [
        {"day": s.day, "size": s.dataset_size}
        for s in snapshots
        if s.iteration == 0 or s == last_snap
    ]

    report = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "simulation_config": {
                "days": config.days,
                "iterations": config.iterations,
                "seed": config.seed,
                "feedback_policy": config.feedback_policy,
                "articles_per_day": config.articles_per_day,
            },
            "elapsed_seconds": round(elapsed_seconds, 2),
        },
        "summary": {
            "articles_processed": metrics.total_articles,
            "decisions_made": metrics.total_decisions,
            "approved": metrics.total_approved,
            "rejected": metrics.total_rejected,
            "skipped": metrics.total_skipped,
            "signals_generated": metrics.total_signals,
            "artifacts_created": metrics.total_artifacts,
        },
        "evolution": {
            "confidence_start": first_snap.avg_confidence if first_snap else 0,
            "confidence_end": last_snap.avg_confidence if last_snap else 0,
            "confidence_delta": round(confidence_delta, 4),
            "approval_rate_start": first_snap.approval_rate if first_snap else 0,
            "approval_rate_end": last_snap.approval_rate if last_snap else 0,
            "approval_rate_delta": round(approval_delta, 4),
            "source_quality_start": first_snap.avg_source_quality if first_snap else 0,
            "source_quality_end": last_snap.avg_source_quality if last_snap else 0,
            "source_quality_delta": round(quality_delta, 4),
            "knowledge_growth": last_snap.knowledge_growth if last_snap else 0,
        },
        "sources": {
            "top": top_sources[:5],
            "worst": worst_sources[:5],
            "total_profiled": len(metrics.source_profiles),
        },
        "categories": category_breakdown,
        "keywords": {
            "top": top_keywords[:10],
            "unique_count": len(metrics.keyword_freq),
        },
        "confidence_evolution": confidence_evolution,
        "dataset_evolution": dataset_evolution,
        "signals": {
            "total_generated": metrics.total_signals,
            "per_iteration": (
                metrics.total_signals / metrics.total_articles
                if metrics.total_articles > 0
                else 0
            ),
        },
    }

    return report


def save_json_report(report: dict[str, Any], output_path: str) -> str:
    """Save the report as JSON. Returns the file path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    return str(path)


def generate_markdown_report(report: dict[str, Any]) -> str:
    """Generate a human-readable Markdown report."""
    meta = report["metadata"]
    summary = report["summary"]
    evolution = report["evolution"]
    sources = report["sources"]
    categories = report["categories"]
    keywords = report["keywords"]
    signals = report["signals"]

    lines: list[str] = []

    lines.append("# Simulation Report — Adaptive Learning")
    lines.append("")
    lines.append(f"**Generated**: {meta['generated_at']}")
    lines.append(f"**Elapsed**: {meta['elapsed_seconds']:.1f}s")
    lines.append(f"**Config**: {meta['simulation_config']['days']}d, "
                 f"{meta['simulation_config']['iterations']} iterations, "
                 f"seed={meta['simulation_config']['seed']}, "
                 f"policy={meta['simulation_config']['feedback_policy']}")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Articles processed | **{summary['articles_processed']}** |")
    lines.append(f"| Decisions made | **{summary['decisions_made']}** |")
    lines.append(f"| Approved | {summary['approved']} |")
    lines.append(f"| Rejected | {summary['rejected']} |")
    lines.append(f"| Skipped | {summary['skipped']} |")
    lines.append(f"| Signals generated | {summary['signals_generated']} |")
    lines.append(f"| Artifacts created | {summary['artifacts_created']} |")
    lines.append("")

    # Evolution
    lines.append("## Learning Evolution")
    lines.append("")
    lines.append("| Metric | Start | End | Delta |")
    lines.append("|--------|-------|-----|-------|")
    lines.append(
        f"| Confidence | {evolution['confidence_start']:.3f} | "
        f"{evolution['confidence_end']:.3f} | "
        f"{evolution['confidence_delta']:+.4f} |"
    )
    lines.append(
        f"| Approval Rate | {evolution['approval_rate_start']:.3f} | "
        f"{evolution['approval_rate_end']:.3f} | "
        f"{evolution['approval_rate_delta']:+.4f} |"
    )
    lines.append(
        f"| Source Quality | {evolution['source_quality_start']:.3f} | "
        f"{evolution['source_quality_end']:.3f} | "
        f"{evolution['source_quality_delta']:+.4f} |"
    )
    lines.append(f"| Knowledge Growth | — | {evolution['knowledge_growth']} | — |")
    lines.append("")

    # Sources
    lines.append("## Source Profiles")
    lines.append("")
    lines.append(f"**Total sources profiled**: {sources['total_profiled']}")
    lines.append("")
    lines.append("### Top Sources")
    lines.append("")
    lines.append("| Source | Approval Rate | Quality | Articles |")
    lines.append("|--------|---------------|---------|----------|")
    for s in sources["top"][:5]:
        lines.append(
            f"| {s['source']} | {s['approval_rate']:.1%} | "
            f"{s['quality']:.3f} | {s['total']} |"
        )
    lines.append("")

    if sources["worst"]:
        lines.append("### Worst Sources")
        lines.append("")
        lines.append("| Source | Approval Rate | Quality | Articles |")
        lines.append("|--------|---------------|---------|----------|")
        for s in sources["worst"][:3]:
            lines.append(
                f"| {s['source']} | {s['approval_rate']:.1%} | "
                f"{s['quality']:.3f} | {s['total']} |"
            )
        lines.append("")

    # Categories
    lines.append("## Category Breakdown")
    lines.append("")
    lines.append("| Category | Approval Rate | Total | Approved | Rejected |")
    lines.append("|----------|---------------|-------|----------|----------|")
    for c in categories:
        lines.append(
            f"| {c['category']} | {c['approval_rate']:.1%} | "
            f"{c['total']} | {c['approved']} | {c['rejected']} |"
        )
    lines.append("")

    # Keywords
    lines.append("## Top Keywords")
    lines.append("")
    lines.append(f"**Unique keywords**: {keywords['unique_count']}")
    lines.append("")
    lines.append("| Keyword | Frequency |")
    lines.append("|---------|-----------|")
    for kw in keywords["top"][:10]:
        lines.append(f"| {kw['keyword']} | {kw['count']} |")
    lines.append("")

    # Signals
    lines.append("## Learning Signals")
    lines.append("")
    lines.append(f"- Total generated: **{signals['total_generated']}**")
    lines.append(f"- Per article: {signals['per_iteration']:.2f}")
    lines.append("")

    # Charts reference
    lines.append("## Charts")
    lines.append("")
    lines.append("The following PNG charts were generated:")
    lines.append("")
    lines.append("- `approval_rate.png` — Approval rate over time")
    lines.append("- `confidence.png` — Confidence evolution")
    lines.append("- `source_quality.png` — Source quality evolution")
    lines.append("- `learning_curve.png` — Knowledge growth curve")
    lines.append("- `dataset_growth.png` — Dataset size over time")
    lines.append("- `signals.png` — Learning signals generation")
    lines.append("")

    lines.append("---")
    lines.append("*Report generated by AI Shorts Runtime Simulation Engine*")

    return "\n".join(lines)


def save_markdown_report(content: str, output_path: str) -> str:
    """Save the Markdown report. Returns the file path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return str(path)
