"""
AI Shorts System - Main Entry Point
====================================
Punto de entrada principal de la aplicación.
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Agregar raíz del proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.logger import logger
from pipelines.content_pipeline import ContentPipeline
from pipelines.trends_pipeline import TrendsPipeline


async def main():
    """Función principal de la aplicación."""
    
    parser = argparse.ArgumentParser(
        description="AI Shorts System - Generador de contenido viral automático"
    )
    
    parser.add_argument(
        "command",
        choices=["run", "trends", "test"],
        help="Comando a ejecutar"
    )
    
    parser.add_argument(
        "--niche",
        type=str,
        default=None,
        help="Nichos a usar (ej: tecnología, negocios, salud)"
    )
    
    parser.add_argument(
        "--platform",
        type=str,
        default="youtube",
        choices=["youtube", "tiktok", "instagram"],
        help="Plataforma destino"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Número de videos a generar"
    )
    
    args = parser.parse_args()
    
    logger.info(f"🚀 Iniciando AI Shorts System v{settings.VERSION}")
    logger.info(f"   Plataforma: {args.platform}")
    logger.info(f"   Nicho: {args.niche or 'general'}")
    
    try:
        if args.command == "run":
            # Ejecutar pipeline completo
            pipeline = ContentPipeline(
                niche=args.niche,
                platform=args.platform
            )
            
            results = await pipeline.run(num_videos=args.limit)
            
            logger.info(f"✅ Pipeline completado: {len(results)} videos generados")
            
            for i, result in enumerate(results, 1):
                logger.info(f"   {i}. {result.get('video_id', 'N/A')} - {result.get('status', 'unknown')}")
                
        elif args.command == "trends":
            # Solo obtener tendencias
            pipeline = TrendsPipeline(niche=args.niche)
            trends = await pipeline.run()
            
            logger.info(f"📡 Trends encontrados: {len(trends)}")
            for trend in trends[:5]:
                logger.info(f"   - {trend.get('topic')} (score: {trend.get('viral_score')})")
                
        elif args.command == "test":
            # Modo test
            logger.info("🧪 Modo test activado")
            await test_system()
            
    except Exception as e:
        logger.error(f"❌ Error en la ejecución: {e}")
        sys.exit(1)


async def test_system():
    """Ejecuta pruebas básicas del sistema."""
    logger.info("Testing...")
    
    # Test 1: Configuración
    assert settings.OPENAI_API_KEY is not None, "OpenAI API key no configurada"
    logger.info("✅ Configuración cargada")
    
    # Test 2: Pipelines
    from pipelines import ContentPipeline, TrendsPipeline
    logger.info("✅ Pipelines importados")
    
    logger.info("✅ Todos los tests pasaron")


if __name__ == "__main__":
    asyncio.run(main())