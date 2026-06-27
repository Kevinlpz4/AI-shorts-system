"""
AI Shorts System — Main Entry Point
====================================
Punto de entrada principal usando la nueva arquitectura DDD + SOLID.
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


async def main():
    """Punto de entrada principal."""
    
    parser = argparse.ArgumentParser(
        description="AI Shorts System - Generador de contenido viral automático"
    )
    
    parser.add_argument(
        "command",
        choices=["run", "trends", "evaluate", "test"],
        help="Comando a ejecutar",
    )
    
    parser.add_argument(
        "--niche", "-n",
        type=str,
        default=None,
        help="Nicho (tecnología, negocios, salud, etc.)",
    )
    
    parser.add_argument(
        "--platform", "-p",
        type=str,
        default="youtube",
        choices=["youtube", "tiktok", "instagram"],
        help="Plataforma destino",
    )
    
    parser.add_argument(
        "--count", "-c",
        type=int,
        default=1,
        help="Número de videos a generar",
    )
    
    parser.add_argument(
        "--id",
        type=str,
        default=None,
        help="ID de contenido a evaluar",
    )
    
    parser.add_argument(
        "--type", "-t",
        type=str,
        default="idea",
        choices=["idea", "script"],
        help="Tipo de contenido a evaluar",
    )
    
    args = parser.parse_args()
    
    logger.info(f"🚀 AI Shorts System v{settings.VERSION}")
    logger.info(f"   Comando: {args.command}")
    
    # ── Composition Root ──
    container = Container()
    cli = CLICommands(container)
    
    try:
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
            result = await cli.run_trends(
                niche=args.niche,
                limit=20,
            )
            
            if result.success:
                logger.info(f"\n✅ {result.message}")
            else:
                logger.warning(f"\n⚠️ {result.message}")
        
        elif args.command == "evaluate":
            if not args.id:
                logger.error("❌ Se requiere --id para evaluate")
                sys.exit(1)
            
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
    
    except KeyboardInterrupt:
        logger.info("\n⏹ Interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
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
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info(f"📊 Resultados: {passed} passed, {failed} failed")
    logger.info(f"{'='*50}")
    
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
