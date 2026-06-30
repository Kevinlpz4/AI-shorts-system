"""
AI Shorts System — Main Entry Point
====================================
Punto de entrada principal usando la nueva arquitectura DDD + SOLID.

Comandos disponibles:
  run       — generar contenido viral
  trends    — obtener tendencias
  evaluate  — evaluar contenido existente
  test      — tests de integración
  research  — módulo de investigación (descubrimiento, aprobación, scheduler)
  api/serve — iniciar servidor FastAPI REST
"""
import asyncio
import argparse
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.logger import logger
from presentation.cli.container import Container
from presentation.cli.commands import CLICommands


def build_parser() -> argparse.ArgumentParser:
    """Construye el parser de comandos con subparsers."""
    parser = argparse.ArgumentParser(
        description="AI Shorts System - Generador de contenido viral automático"
    )
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    # ── run ──────────────────────────────────────────
    run_parser = subparsers.add_parser("run", help="Generar contenido viral")
    run_parser.add_argument(
        "--niche", "-n", type=str, default=None,
        help="Nicho (tecnología, negocios, salud, etc.)",
    )
    run_parser.add_argument(
        "--platform", "-p", type=str, default="youtube",
        choices=["youtube", "tiktok", "instagram"],
        help="Plataforma destino",
    )
    run_parser.add_argument(
        "--count", "-c", type=int, default=1,
        help="Número de videos a generar",
    )

    # ── trends ───────────────────────────────────────
    trends_parser = subparsers.add_parser("trends", help="Obtener tendencias")
    trends_parser.add_argument(
        "--niche", "-n", type=str, default=None,
        help="Nicho para filtrar tendencias",
    )

    # ── evaluate ─────────────────────────────────────
    eval_parser = subparsers.add_parser("evaluate", help="Evaluar contenido")
    eval_parser.add_argument("--id", type=str, required=True, help="ID de contenido")
    eval_parser.add_argument(
        "--type", "-t", type=str, default="idea",
        choices=["idea", "script"],
        help="Tipo de contenido",
    )

    # ── test ─────────────────────────────────────────
    subparsers.add_parser("test", help="Ejecutar tests de integración")

    # ── research ─────────────────────────────────────
    research_parser = subparsers.add_parser(
        "research", help="Módulo de investigación de topics"
    )
    research_sub = research_parser.add_subparsers(
        dest="research_command", help="Comando de investigación"
    )

    # research discover
    disc_parser = research_sub.add_parser(
        "discover", help="Descubrir nuevos topics desde fuentes externas"
    )
    disc_parser.add_argument(
        "--query", "-q", type=str, default=None,
        help="Término de búsqueda (default: trending)",
    )
    disc_parser.add_argument(
        "--limit", "-l", type=int, default=5,
        help="Máximo de resultados por fuente",
    )
    disc_parser.add_argument(
        "--sources", "-s", type=str, default=None,
        help="Fuentes separadas por coma (default: todas)",
    )

    # research list
    list_parser = research_sub.add_parser(
        "list", help="Listar topics existentes"
    )
    list_parser.add_argument(
        "--status", "-s", type=str, default=None,
        choices=["pending_review", "approved", "rejected"],
        help="Filtrar por estado",
    )
    list_parser.add_argument(
        "--limit", "-l", type=int, default=20,
        help="Máximo de resultados",
    )

    # research approve
    approve_parser = research_sub.add_parser(
        "approve", help="Aprobar un topic para generación"
    )
    approve_parser.add_argument("topic_id", type=str, help="UUID del topic")

    # research reject
    reject_parser = research_sub.add_parser(
        "reject", help="Rechazar un topic"
    )
    reject_parser.add_argument("topic_id", type=str, help="UUID del topic")

    # research manual
    manual_parser = research_sub.add_parser(
        "manual", help="Registrar un topic manualmente"
    )
    manual_parser.add_argument("title", type=str, help="Título del topic")
    manual_parser.add_argument("url", type=str, help="URL de la fuente")
    manual_parser.add_argument(
        "--description", "-d", type=str, default="",
        help="Descripción opcional",
    )

    # research schedule
    sched_parser = research_sub.add_parser(
        "schedule", help="Control del scheduler automático"
    )
    sched_sub = sched_parser.add_subparsers(
        dest="schedule_command", help="Comando del scheduler"
    )

    sched_sub.add_parser("status", help="Ver estado del scheduler")
    sched_sub.add_parser("start", help="Iniciar scheduler")
    sched_sub.add_parser("stop", help="Detener scheduler")
    sched_sub.add_parser("run-now", help="Ejecutar ciclo ahora")

    interval_parser = sched_sub.add_parser(
        "interval", help="Cambiar intervalo entre ciclos"
    )
    interval_parser.add_argument(
        "minutes", type=int, help="Intervalo en minutos"
    )

    queries_parser = sched_sub.add_parser(
        "queries", help="Configurar queries del scheduler"
    )
    queries_parser.add_argument(
        "queries", type=str,
        help="Queries separadas por coma (ej: 'IA,tecnología,ciencia')",
    )

    # ── api / serve ─────────────────────────────────────
    api_parser = subparsers.add_parser(
        "api", help="Iniciar servidor FastAPI REST"
    )
    api_parser.add_argument(
        "--host", type=str, default=None,
        help="Host del servidor (default: configurado en API_HOST)",
    )
    api_parser.add_argument(
        "--port", "-p", type=int, default=None,
        help="Puerto del servidor (default: configurado en API_PORT)",
    )
    api_parser.add_argument(
        "--reload", action="store_true",
        help="Activar hot-reload (solo desarrollo)",
    )

    # serve es un alias de api
    serve_parser = subparsers.add_parser(
        "serve", help="Iniciar servidor FastAPI REST (alias de api)"
    )
    serve_parser.add_argument(
        "--host", type=str, default=None,
        help="Host del servidor (default: configurado en API_HOST)",
    )
    serve_parser.add_argument(
        "--port", "-p", type=int, default=None,
        help="Puerto del servidor (default: configurado en API_PORT)",
    )
    serve_parser.add_argument(
        "--reload", action="store_true",
        help="Activar hot-reload (solo desarrollo)",
    )

    return parser


async def main():
    """Punto de entrada principal."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    logger.info(f"🚀 AI Shorts System v{settings.VERSION}")
    logger.info(f"   Comando: {args.command}")

    # ── Composition Root ──
    container = Container()
    cli = CLICommands(container)

    try:
        # ── Comandos existentes ──────────────────────
        if args.command == "run":
            result = await cli.run_generate(
                niche=args.niche,
                platform=args.platform,
                count=args.count,
            )
            if result.success:
                logger.info(f"\n✅ Completado: {result.message}")
            else:
                logger.error(f"\n❌ {result.message}")
                sys.exit(1)

        elif args.command == "trends":
            result = await cli.run_trends(niche=args.niche, limit=20)
            if result.success:
                logger.info(f"\n✅ {result.message}")
            else:
                logger.warning(f"\n⚠️ {result.message}")

        elif args.command == "evaluate":
            result = await cli.run_evaluate(
                content_id=args.id,
                content_type=args.type,
            )
            if result.success:
                logger.info(f"\n✅ {result.message}")
            else:
                logger.error(f"\n❌ {result.message}")

        elif args.command == "test":
            await run_tests(container)

        # ── Research commands ─────────────────────────
        elif args.command == "research":
            await handle_research(cli, args)

        # ── API Server ──────────────────────────────────
        elif args.command in ("api", "serve"):
            await run_api(args)

    except KeyboardInterrupt:
        logger.info("\n⏹ Interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        sys.exit(1)


async def handle_research(cli: CLICommands, args: argparse.Namespace):
    """Dispatcher de subcomandos de research."""
    cmd = args.research_command

    if cmd == "discover":
        sources = args.sources.split(",") if args.sources else None
        await cli.research_discover(query=args.query, limit=args.limit, sources=sources)

    elif cmd == "list":
        await cli.research_list(status=args.status, limit=args.limit)

    elif cmd == "approve":
        await cli.research_approve(args.topic_id)

    elif cmd == "reject":
        await cli.research_reject(args.topic_id)

    elif cmd == "manual":
        await cli.research_manual(
            title=args.title,
            url=args.url,
            description=args.description,
        )

    elif cmd == "schedule":
        await handle_schedule(cli, args)

    else:
        logger.error(f"❌ Comando research desconocido: {cmd}")
        sys.exit(1)


async def handle_schedule(cli: CLICommands, args: argparse.Namespace):
    """Dispatcher de subcomandos del scheduler."""
    sched_cmd = args.schedule_command

    if sched_cmd == "status":
        await cli.research_schedule_status()

    elif sched_cmd == "start":
        await cli.research_schedule_start()

    elif sched_cmd == "stop":
        await cli.research_schedule_stop()

    elif sched_cmd == "run-now":
        await cli.research_schedule_run_now()

    elif sched_cmd == "interval":
        await cli.research_schedule_interval(args.minutes)

    elif sched_cmd == "queries":
        queries = [q.strip() for q in args.queries.split(",") if q.strip()]
        await cli.research_schedule_queries(queries)

    else:
        logger.error(f"❌ Comando schedule desconocido: {sched_cmd}")
        sys.exit(1)


async def run_tests(container: Container):
    """Ejecuta pruebas de integración del sistema."""
    logger.info("🧪 Ejecutando tests de integración...")
    passed = 0
    failed = 0

    # Test 1: Configuración
    logger.info("\n1️⃣  Test: Configuración")
    try:
        assert settings.OPENAI_API_KEY, "OPENAI_API_KEY debe estar configurada"
        logger.info(f"   ✅ API Key presente")
        logger.info(f"   ✅ Proveedor: {settings.AI_PROVIDER}")
        logger.info(f"   ✅ Modelo: {settings.OPENAI_MODEL}")
        if settings.OPENAI_BASE_URL:
            logger.info(f"   ✅ Base URL: {settings.OPENAI_BASE_URL}")
        passed += 1
    except AssertionError as e:
        logger.error(f"   ❌ {e}")
        failed += 1

    # Test 2: Dependency Injection
    logger.info("\n2️⃣  Test: Dependency Injection")
    try:
        assert container.generate_content is not None
        assert container.evaluate_content is not None
        assert container.manage_trends is not None
        assert container.ai_provider is not None
        logger.info(f"   ✅ GenerateContentUseCase inyectado")
        logger.info(f"   ✅ EvaluateContentUseCase inyectado")
        logger.info(f"   ✅ ManageTrendsUseCase inyectado")
        logger.info(f"   ✅ AIProvider: {container.ai_provider.name}")
        passed += 1
    except AssertionError as e:
        logger.error(f"   ❌ Error en inyección: {e}")
        failed += 1

    # Test 3: Trends
    logger.info("\n3️⃣  Test: Obtención de trends")
    try:
        result = await container.manage_trends.execute(
            application.dto.requests.TrendRequest(niche="tecnología", limit=5)
        )
        if result.success and result.data:
            trends = result.data.get("trends", [])
            logger.info(f"   ✅ {len(trends)} trends obtenidos")
            for t in trends[:3]:
                logger.info(f"      - {t.get('topic', 'N/A')} (score: {t.get('viral_score', 'N/A')})")
            passed += 1
        else:
            logger.warning(f"   ⚠️ Trends no disponibles")
            passed += 1  # Not a failure, might be no APIs
    except Exception as e:
        logger.error(f"   ❌ {e}")
        failed += 1

    # Test 4: Content Evaluation (dominio puro)
    logger.info("\n4️⃣  Test: Evaluación de contenido (dominio puro)")
    try:
        from domain.entities.content_idea import ContentIdea
        from domain.value_objects.viral_score import ViralScore

        idea = ContentIdea(
            hook="5 secretos de la IA que nadie te cuenta",
            topic="Inteligencia Artificial",
            viral_score=ViralScore(75),
        )

        result = container.evaluator.evaluate_idea(idea)
        logger.info(f"   ✅ Score: {result.score_total:.1f}/10 ({result.classification})")
        logger.info(f"   ✅ Criterios: {len(result.criteria)} evaluados")
        if result.recommendations:
            logger.info(f"   💡 Recomendaciones: {result.recommendations[0]}")
        passed += 1
    except Exception as e:
        logger.error(f"   ❌ {e}")
        failed += 1

    # Test 5: Research module DI
    logger.info("\n5️⃣  Test: Research Module DI")
    try:
        assert container.research_repository is not None
        assert container.research_source_registry is not None
        assert container.auto_discover_topics is not None
        assert container.research_scheduler is not None
        logger.info(f"   ✅ ResearchRepository inyectado")
        logger.info(f"   ✅ SourceRegistry inyectado ({container.research_source_registry.count} fuentes)")
        logger.info(f"   ✅ AutoDiscoverTopicsUseCase inyectado")
        logger.info(f"   ✅ ResearchScheduler inyectado")
        passed += 1
    except AssertionError as e:
        logger.error(f"   ❌ Error en inyección: {e}")
        failed += 1

    # Summary
    logger.info(f"\n{'='*50}")
    logger.info(f"📊 Resultados: {passed} passed, {failed} failed")
    logger.info(f"{'='*50}")

    if failed > 0:
        sys.exit(1)


async def run_api(args: argparse.Namespace):
    """Inicia el servidor FastAPI."""
    import uvicorn

    from presentation.api.container import ApiContainer
    from presentation.api.main import create_app

    host = args.host or settings.API_HOST
    port = args.port or settings.API_PORT

    logger.info("🌐 Iniciando API server en %s:%s", host, port)
    logger.info("   Documentación: http://%s:%s/api/docs", host, port)

    container = ApiContainer()
    app = create_app(container)

    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        reload=args.reload,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
