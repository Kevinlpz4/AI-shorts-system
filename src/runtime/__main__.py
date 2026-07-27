"""
Runtime Entry Point — levanta el sistema completo.

Uso:
    python -m runtime                    # Ejecutar un ciclo de ingesta + feedback
    python -m runtime ingest             # Solo ingesta (fetch de todas las fuentes)
    python -m runtime feedback           # Solo feedback CLI (revisar cola pendiente)
    python -m runtime schedule           # Scheduler continuo (APScheduler)
    python -m runtime stats              # Ver estadísticas de feedback
    python -m runtime list-sources       # Listar fuentes configuradas
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Ensure src/ is in the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from runtime.composition import build_full_runtime
from runtime.config import RuntimeConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="runtime",
        description="AI Shorts System — Runtime de orquestación",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Nivel de logging (default: INFO)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Intervalo del scheduler en minutos (default: 30)",
    )

    sub = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    sub.add_parser("ingest", help="Ejecutar un ciclo de ingesta de todas las fuentes")
    sub.add_parser("feedback", help="Abrir la CLI de feedback para revisar items pendientes")
    sub.add_parser("schedule", help="Iniciar scheduler continuo")
    sub.add_parser("stats", help="Ver estadísticas de feedback acumuladas")
    sub.add_parser("list-sources", help="Listar todas las fuentes configuradas")
    sub.add_parser("cycle", help="Ciclo completo: ingesta → feedback → stats")

    return parser


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s │ %(levelname)-7s │ %(name)s │ %(message)s",
        datefmt="%H:%M:%S",
    )
    # Silenciar logs verbosos de APScheduler y httpx
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("feedparser").setLevel(logging.WARNING)


# ── Commands ──────────────────────────────────────────────────────


async def cmd_ingest(runtime: dict) -> None:
    """Ejecutar un ciclo de ingesta de todas las fuentes habilitadas."""
    from datetime import datetime, timezone
    from uuid import uuid4
    from runtime.contracts.job_result import JobContext

    console = runtime["metrics"]
    job = runtime["ingestion_job"]

    print("\n🔄 Ejecutando ciclo de ingesta...\n")

    ctx = JobContext(
        correlation_id=uuid4(),
        triggered_at=datetime.now(timezone.utc),
    )

    result = await job.execute(ctx)

    if result.is_success:
        job_result = result.unwrap()
        print(f"✅ Ingesta completada en {job_result.duration_seconds:.1f}s")
        if hasattr(job_result, "items_fetched"):
            print(f"   Items obtenidos: {job_result.items_fetched}")
        if hasattr(job_result, "items_new"):
            print(f"   Items nuevos: {job_result.items_new}")
        if hasattr(job_result, "errors") and job_result.errors:
            print(f"   Errores: {len(job_result.errors)}")
            for err in job_result.errors[:5]:
                print(f"     - {err}")
    else:
        print(f"❌ Ingesta falló: {result.error}")


async def cmd_feedback(runtime: dict) -> None:
    """Abrir la CLI de feedback interactivo."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Confirm
    from runtime.feedback.cli import FeedbackCLI
    from runtime.feedback.models import FeedbackRecord, Decision
    import uuid
    from datetime import datetime, timezone

    console = Console()
    queue = runtime["decision_queue"]
    reasons = runtime["feedback_reasons"]

    # Si la cola está vacía, ofrecer poblarla con datos de ejemplo
    stats = queue.get_stats()
    if stats["pending"] == 0:
        console.print(
            Panel(
                "La cola de feedback está vacía.\n"
                "¿Quieres poblarla con items de ejemplo para probar?",
                title="📭 Cola vacía",
                border_style="yellow",
            )
        )
        if Confirm.ask("Poblar con datos de ejemplo", default=True):
            _populate_demo_queue(queue)
            stats = queue.get_stats()

    cli = FeedbackCLI(queue, reasons)
    cli.set_total(stats["pending"])

    console.print(
        Panel(
            f"Items pendientes: [bold]{stats['pending']}[/bold]\n"
            "Atajos: [A]pprove  [R]eject  [S]kip  [Q]uit  [O]pen URL  [U]ndo",
            title="🎬 AI Shorts — Feedback Review",
            border_style="green",
        )
    )

    records_sent = 0

    # Loop interactivo de feedback con Ctrl+C handling
    try:
        while True:
            cli.show_progress()
            result_info = cli.show_next_item()
            if result_info is None:
                console.print("\n[bold green]🎉 No hay más items pendientes.[/bold green]")
                break

            decision, reason, comment = cli.get_decision()

            # ── QUIT ────────────────────────────────────────────
            if reason == "quit":
                pending = stats["pending"] - cli.session_stats.processed
                if pending > 0:
                    if not Confirm.ask(
                        f"[yellow]Hay {pending} items sin procesar. ¿Salir?[/yellow]",
                        default=False,
                    ):
                        continue
                break

            item = result_info["item"]

            # ── Procesar decisión ───────────────────────────────
            process_result = queue.process(
                item_id=result_info["id"],
                decision=decision.value,
                reason=reason,
                comment=comment,
            )

            if process_result.is_success:
                # Record for undo/stats
                cli.record_decision(item, decision, reason, comment)

                # Show diff if human disagrees with system
                cli.show_decision_diff(item, decision)

                # Create FeedbackRecord
                record = FeedbackRecord(
                    id=str(uuid.uuid4()),
                    article_id=item.article_id,
                    provider=item.provider,
                    source=item.source,
                    category=item.category,
                    topic=item.topic,
                    recommended_score=item.score,
                    recommendation=item.recommendation,
                    decision=decision,
                    reason=reason,
                    comment=comment,
                    user_id=cli.user_id,
                    timestamp=datetime.now(timezone.utc),
                    algorithm_version="0.1.0",
                    feature_snapshot_version="0.1.0",
                    dataset_version="0.1.0",
                )

                # Add to analytics
                runtime["feedback_analytics"].add_record(record)

                # Emit events to Learning BC
                runtime["feedback_event_emitter"].emit_learning_signal(record)
                runtime["feedback_event_emitter"].emit_feedback_recorded(record)
                records_sent += 1
                cli.session_stats.records_sent = records_sent

                icon = "✅" if decision == Decision.APPROVE else (
                    "❌" if decision == Decision.REJECT else "⏭"
                )
                console.print(f"  {icon} {decision.value}\n")
            else:
                console.print(f"  [red]Error: {process_result.error}[/red]\n")

    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚡ Interrumpido por usuario.[/yellow]")
        pending = stats["pending"] - cli.session_stats.processed
        if pending > 0 and not Confirm.ask(
            f"[yellow]Hay {pending} items sin procesar. ¿Salir?[/yellow]",
            default=True,
        ):
            console.print("[dim]Continuando...[/dim]")
            # In real usage, would re-enter loop; for simplicity, exit here

    # ── Resumen final extendido ──────────────────────────────────
    analytics_summary = runtime["feedback_analytics"].get_summary()
    cli.show_session_summary(analytics_summary, records_sent)


async def cmd_schedule(runtime: dict) -> None:
    """Iniciar scheduler continuo."""
    from rich.console import Console

    console = Console()
    scheduler = runtime["scheduler"]

    console.print("[bold green]🚀 Iniciando PipelineScheduler...[/bold green]")
    console.print(
        f"   Intervalo: {runtime['config'].pipeline_interval_minutes} minutos"
    )
    console.print("   Ctrl+C para detener\n")

    scheduler.start()

    try:
        # Mantener vivo con asyncio
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]⏹ Deteniendo scheduler...[/yellow]")
        scheduler.stop()
        console.print("[green]✅ Scheduler detenido correctamente[/green]")


async def cmd_stats(runtime: dict) -> None:
    """Ver estadísticas de feedback."""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    analytics = runtime["feedback_analytics"]
    queue = runtime["decision_queue"]

    # Stats de la cola
    queue_stats = queue.get_stats()
    table = Table(title="📊 Cola de Decisiones", show_header=True)
    table.add_column("Métrica", style="cyan")
    table.add_column("Valor", style="green", justify="right")
    table.add_row("Pendientes", str(queue_stats["pending"]))
    table.add_row("Aprobados", str(queue_stats["approved"]))
    table.add_row("Rechazados", str(queue_stats["rejected"]))
    table.add_row("Saltados", str(queue_stats["skipped"]))
    table.add_row("Total", str(queue_stats["total"]))
    console.print(table)

    # Stats de analytics
    summary = analytics.get_summary()
    if summary["total_records"] > 0:
        console.print()
        a_table = Table(title="📈 Analytics de Feedback", show_header=True)
        a_table.add_column("Métrica", style="cyan")
        a_table.add_column("Valor", style="green", justify="right")
        a_table.add_row("Total Records", str(summary["total_records"]))
        a_table.add_row("Approval Rate", f"{summary['approval_rate']:.1%}")
        a_table.add_row("Rejection Rate", f"{summary['rejection_rate']:.1%}")
        console.print(a_table)

        if summary["top_reasons"]:
            console.print()
            r_table = Table(title="🔍 Top Motivos de Rechazo")
            r_table.add_column("Motivo", style="red")
            r_table.add_column("Count", style="yellow", justify="right")
            for r in summary["top_reasons"]:
                r_table.add_row(r["reason"], str(r["count"]))
            console.print(r_table)

        if summary["top_sources"]:
            console.print()
            s_table = Table(title="📰 Top Fuentes (por Approval Rate)")
            s_table.add_column("Fuente", style="cyan")
            s_table.add_column("Approval Rate", style="green", justify="right")
            s_table.add_column("Total", justify="right")
            for s in summary["top_sources"][:5]:
                s_table.add_row(
                    s["source"],
                    f"{s['approval_rate']:.1%}",
                    str(s["total"]),
                )
            console.print(s_table)
    else:
        console.print("\n[dim]Aún no hay registros de feedback procesados.[/dim]")


async def cmd_list_sources(runtime: dict) -> None:
    """Listar todas las fuentes configuradas."""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    manager = runtime["registry_manager"]

    sources = manager.sources.get_all()
    table = Table(title="📡 Fuentes Configuradas", show_header=True)
    table.add_column("#", justify="right", style="dim")
    table.add_column("ID", style="cyan")
    table.add_column("Proveedor", style="green")
    table.add_column("Tecnología", style="yellow")
    table.add_column("URL")
    table.add_column("Activa", justify="center")

    for i, source in enumerate(sources, 1):
        url = source.metadata.get("url", "—")
        activa = "✅" if source.enabled else "❌"
        table.add_row(
            str(i),
            source.id,
            source.provider,
            source.technology,
            url[:50] + "..." if len(url) > 50 else url,
            activa,
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(sources)} fuentes[/dim]")


async def cmd_cycle(runtime: dict) -> None:
    """Ciclo completo: ingesta → feedback."""
    await cmd_ingest(runtime)
    await cmd_feedback(runtime)


def _populate_demo_queue(queue) -> None:
    """Poblar la cola con items de ejemplo para testing."""
    demo_items = [
        {
            "article_id": "demo-001",
            "provider": "google_news_ai",
            "source": "https://news.google.com",
            "category": "ai",
            "topic": "llm",
            "score": 0.92,
            "recommendation": "APPROVE",
            "title": "OpenAI GPT-5 Launches with Breakthrough Reasoning",
            "url": "https://openai.com/blog/gpt-5",
            "published": "2026-07-27",
            "summary": "OpenAI announces GPT-5 with 10x performance gains and native multimodal support across text, image, and video.",
            "metadata": {
                "reasons": {
                    "source_quality": 0.95,
                    "freshness": "Very High",
                    "keywords": ["GPT-5", "OpenAI", "reasoning"],
                    "similar_approved": 38,
                    "confidence": 0.94,
                },
            },
        },
        {
            "article_id": "demo-002",
            "provider": "techcrunch",
            "source": "https://techcrunch.com",
            "category": "ai",
            "topic": "startups",
            "score": 0.85,
            "recommendation": "APPROVE",
            "title": "AI Startup Raises $100M for Autonomous Coding Assistant",
            "url": "https://techcrunch.com/2026/07/26/ai-coding-100m",
            "published": "2026-07-26",
            "summary": "A new AI coding startup secures Series B funding to build an autonomous agent that can write, test, and deploy code.",
            "metadata": {
                "reasons": {
                    "source_quality": 0.91,
                    "freshness": "High",
                    "keywords": ["AI", "coding", "startup", "funding"],
                    "similar_approved": 25,
                    "confidence": 0.87,
                },
            },
        },
        {
            "article_id": "demo-003",
            "provider": "steam_news",
            "source": "https://store.steampowered.com",
            "category": "gaming",
            "topic": "steam",
            "score": 0.78,
            "recommendation": "APPROVE",
            "title": "Major Steam Summer Sale Starts Next Week",
            "url": "https://store.steampowered.com/news/steam-sale",
            "published": "2026-07-25",
            "summary": "Valve confirms the biggest Steam sale event yet with over 5000 discounted titles.",
            "metadata": {
                "reasons": {
                    "source_quality": 0.88,
                    "freshness": "High",
                    "keywords": ["Steam", "sale", "gaming", "deals"],
                    "similar_approved": 15,
                    "confidence": 0.80,
                },
            },
        },
        {
            "article_id": "demo-004",
            "provider": "the_verge",
            "source": "https://theverge.com",
            "category": "tech",
            "topic": "hardware",
            "score": 0.71,
            "recommendation": "REJECT",
            "title": "Apple Vision Pro 2 Leaks Reveal Lighter Design",
            "url": "https://theverge.com/2026/07/25/vision-pro-2",
            "published": "2026-07-25",
            "summary": "Supply chain leaks suggest Apple Vision Pro 2 will be 40% lighter with a $2000 price point.",
            "metadata": {
                "reasons": {
                    "source_quality": 0.85,
                    "freshness": "Medium",
                    "keywords": ["Apple", "Vision Pro", "VR"],
                    "similar_approved": 8,
                    "confidence": 0.62,
                },
            },
        },
        {
            "article_id": "demo-005",
            "provider": "reddit_ai",
            "source": "https://reddit.com/r/artificial",
            "category": "ai",
            "topic": "research",
            "score": 0.65,
            "recommendation": "REJECT",
            "title": "Efficient Transformer Paper Achieves SOTA with 10x Less Compute",
            "url": "https://arxiv.org/abs/2026.12345",
            "published": "2026-07-24",
            "summary": "New paper proposes a sparse attention mechanism that reduces transformer compute by 10x while maintaining SOTA benchmarks.",
            "metadata": {
                "reasons": {
                    "source_quality": 0.70,
                    "freshness": "Medium",
                    "keywords": ["transformer", "efficiency", "SOTA"],
                    "similar_approved": 5,
                    "confidence": 0.58,
                },
            },
        },
        {
            "article_id": "demo-006",
            "provider": "hackernews",
            "source": "https://news.ycombinator.com",
            "category": "dev",
            "topic": "programming",
            "score": 0.88,
            "recommendation": "APPROVE",
            "title": "Show HN: Open-Source GitHub Copilot Alternative with Local LLM",
            "url": "https://news.ycombinator.com/item?id=99999",
            "published": "2026-07-27",
            "summary": "A new open-source coding assistant that runs entirely locally using quantized LLMs, no API key needed.",
            "metadata": {
                "reasons": {
                    "source_quality": 0.82,
                    "freshness": "Very High",
                    "keywords": ["open-source", "Copilot", "LLM", "local"],
                    "similar_approved": 32,
                    "confidence": 0.90,
                },
            },
        },
        {
            "article_id": "demo-007",
            "provider": "ign",
            "source": "https://ign.com",
            "category": "gaming",
            "topic": "console",
            "score": 0.74,
            "recommendation": "APPROVE",
            "title": "Nintendo Switch 2 Confirmed with Backward Compatibility",
            "url": "https://ign.com/articles/switch-2-confirmed",
            "published": "2026-07-23",
            "summary": "Nintendo officially confirms Switch 2 with full backward compatibility and 4K docked output.",
            "metadata": {
                "reasons": {
                    "source_quality": 0.90,
                    "freshness": "Medium",
                    "keywords": ["Nintendo", "Switch 2", "console"],
                    "similar_approved": 20,
                    "confidence": 0.76,
                },
            },
        },
        {
            "article_id": "demo-008",
            "provider": "github_trending",
            "source": "https://github.com/trending",
            "category": "dev",
            "topic": "open-source",
            "score": 0.82,
            "recommendation": "APPROVE",
            "title": "Rust JS Runtime Gains 10k Stars in a Week",
            "url": "https://github.com/example/rust-runtime",
            "published": "2026-07-27",
            "summary": "A Rust-based JavaScript runtime challenges Bun with native TypeScript support and 2x faster cold starts.",
            "metadata": {
                "reasons": {
                    "source_quality": 0.78,
                    "freshness": "Very High",
                    "keywords": ["Rust", "JavaScript", "runtime", "Bun"],
                    "similar_approved": 18,
                    "confidence": 0.83,
                },
            },
        },
    ]

    for item in demo_items:
        queue.add(**item)


# ── Main ──────────────────────────────────────────────────────────


def main():
    parser = build_parser()
    args = parser.parse_args()

    setup_logging(args.log_level)

    print("🎬 AI Shorts System — Runtime v0.1.0\n")

    runtime = build_full_runtime(RuntimeConfig(
        pipeline_interval_minutes=args.interval,
        log_level=args.log_level,
    ))

    command = args.command or "cycle"

    dispatch = {
        "ingest": cmd_ingest,
        "feedback": cmd_feedback,
        "schedule": cmd_schedule,
        "stats": cmd_stats,
        "list-sources": cmd_list_sources,
        "cycle": cmd_cycle,
    }

    handler = dispatch.get(command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    asyncio.run(handler(runtime))


if __name__ == "__main__":
    main()
