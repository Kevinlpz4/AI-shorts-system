"""
AI Shorts System - Run Pipeline Script
=======================================
Script CLI para ejecutar el pipeline completo.
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Agregar raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.logger import logger
from pipelines.content_pipeline import ContentPipeline


async def main():
    """Función principal del script."""
    
    parser = argparse.ArgumentParser(
        description="Ejecuta el pipeline de generación de contenido"
    )
    
    parser.add_argument(
        "--niche",
        type=str,
        default=None,
        help="Nicho del contenido (tecnología, negocios, etc.)"
    )
    
    parser.add_argument(
        "--platform",
        type=str,
        default="youtube",
        choices=["youtube", "tiktok", "instagram"],
        help="Plataforma de publicación"
    )
    
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Cantidad de videos a generar"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Modo verbose"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        import logging
        logger.setLevel(logging.DEBUG)
    
    logger.info("🚀 AI Shorts System - Pipeline de Contenido")
    logger.info(f"   Nicho: {args.niche or 'general'}")
    logger.info(f"   Plataforma: {args.platform}")
    logger.info(f"   Videos: {args.count}")
    
    # Verificar API keys
    if not settings.OPENAI_API_KEY:
        logger.warning("⚠️ OPENAI_API_KEY no configurada - usando modo mock")
    
    # Ejecutar pipeline
    pipeline = ContentPipeline(
        niche=args.niche,
        platform=args.platform
    )
    
    results = await pipeline.run(num_videos=args.count)
    
    # Resumen
    logger.info("\n" + "="*50)
    logger.info("📊 RESUMEN")
    logger.info("="*50)
    
    successful = sum(1 for r in results if r.get("status") == "success")
    failed = len(results) - successful
    
    logger.info(f"Total: {len(results)}")
    logger.info(f"✅ Exitosos: {successful}")
    logger.info(f"❌ Fallidos: {failed}")
    
    if successful > 0:
        logger.info("\nVideos generados:")
        for r in results:
            if r.get("status") == "success":
                logger.info(f"   • {r.get('url', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(main())