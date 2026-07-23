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
    from runtime.feedback.cli import FeedbackCLI

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
        from rich.prompt import Confirm
        if Confirm.ask("Poblar con datos de ejemplo", default=True):
            _populate_demo_queue(queue)
            stats = queue.get_stats()

    cli = FeedbackCLI(queue, reasons)

    console.print(
        Panel(
            f"Items pendientes: [bold]{stats['pending']}[/bold]\n"
            "Escribe 'q' en cualquier momento para salir.",
            title="🎬 AI Shorts — Feedback Review",
            border_style="green",
        )
    )

    # Loop interactivo de feedback
    while True:
        result_info = cli.show_next_item()
        if result_info is None:
            console.print("\n[bold green]🎉 No hay más items pendientes.[/bold green]")
            break

        decision, reason, comment = cli.get_decision()

        from runtime.feedback.models import FeedbackRecord, Decision
        import uuid
        from datetime import datetime, timezone

        item = result_info["item"]

        # Procesar decisión en la cola
        process_result = queue.process(
            item_id=result_info["id"],
            decision=decision.value,
            reason=reason,
            comment=comment,
        )

        if process_result.is_ok():
            # Crear FeedbackRecord
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
                user_id=cli._user_id,
                timestamp=datetime.now(timezone.utc),
                algorithm_version="0.1.0",
                feature_snapshot_version="0.1.0",
                dataset_version="0.1.0",
            )

            # Agregar al analytics
            runtime["feedback_analytics"].add_record(record)

            # Emitir evento a Learning BC
            runtime["feedback_event_emitter"].emit_learning_signal(record)
            runtime["feedback_event_emitter"].emit_feedback_recorded(record)

            icon = "✅" if decision == Decision.APPROVE else "❌" if decision == Decision.REJECT else "⏭"
            console.print(f"  {icon} Decisión registrada: {decision.value}\n")
        else:
            console.print(f"  [red]Error: {process_result.error}[/red]\n")

    # Mostrar resumen final
    stats = queue.get_stats()
    cli.show_stats(stats)

    analytics = runtime["feedback_analytics"].get_summary()
    if analytics["total_records"] > 0:
        cli.show_analytics(analytics)


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
            "recommendation": "OpenAI announced GPT-5 with breakthrough reasoning capabilities",
        },
        {
            "article_id": "demo-002",
            "provider": "techcrunch",
            "source": "https://techcrunch.com",
            "category": "ai",
            "topic": "startups",
            "score": 0.85,
            "recommendation": "AI startup raises $100M for autonomous coding assistant",
        },
        {
            "article_id": "demo-003",
            "provider": "steam_news",
            "source": "https://store.steampowered.com",
            "category": "gaming",
            "topic": "steam",
            "score": 0.78,
            "recommendation": "Major Steam sale event starts next week with 5000+ deals",
        },
        {
            "article_id": "demo-004",
            "provider": "the_verge",
            "source": "https://theverge.com",
            "category": "tech",
            "topic": "hardware",
            "score": 0.71,
            "recommendation": "Apple Vision Pro 2 leaks reveal lighter design and lower price",
        },
        {
            "article_id": "demo-005",
            "provider": "reddit_ai",
            "source": "https://reddit.com/r/artificial",
            "category": "ai",
            "topic": "research",
            "score": 0.65,
            "recommendation": "New paper on efficient transformer architectures achieves SOTA with 10x less compute",
        },
        {
            "article_id": "demo-006",
            "provider": "hackernews",
            "source": "https://news.ycombinator.com",
            "category": "dev",
            "topic": "programming",
            "score": 0.88,
            "recommendation": "Show HN: Open-source alternative to GitHub Copilot with local LLM support",
        },
        {
            "article_id": "demo-007",
            "provider": "ign",
            "source": "https://ign.com",
            "category": "gaming",
            "topic": "console",
            "score": 0.74,
            "recommendation": "Nintendo Switch 2 confirmed with backward compatibility and 4K output",
        },
        {
            "article_id": "demo-008",
            "provider": "github_trending",
            "source": "https://github.com/trending",
            "category": "dev",
            "topic": "open-source",
            "score": 0.82,
            "recommendation": "Rust-based JavaScript runtime gains 10k stars in a week, challenging Bun",
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
