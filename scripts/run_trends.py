"""
AI Shorts System - Run Trends Script
====================================
Script CLI para ejecutar solo el pipeline de tendencias.
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.logger import logger
from pipelines.trends_pipeline import TrendsPipeline


async def main():
    """Función principal del script."""
    
    parser = argparse.ArgumentParser(
        description="Obtiene tendencias actuales"
    )
    
    parser.add_argument(
        "--niche",
        type=str,
        default=None,
        help="Filtrar por nicho"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Número de trends a obtener"
    )
    
    parser.add_argument(
        "--min-score",
        type=int,
        default=0,
        help="Score mínimo de viralidad"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Archivo de salida (JSON)"
    )
    
    args = parser.parse_args()
    
    logger.info("📡 AI Shorts System - Trends Pipeline")
    
    # Ejecutar
    pipeline = TrendsPipeline(niche=args.niche)
    
    if args.min_score > 0:
        trends = await pipeline.filter_by_score(min_score=args.min_score)
    else:
        trends = await pipeline.run(limit=args.limit)
    
    # Output
    if args.output:
        with open(args.output, "w") as f:
            json.dump([t.__dict__ for t in trends], f, indent=2)
        logger.info(f"✓ Guardado en: {args.output}")
    else:
        logger.info("\n📊 Trends:")
        for t in trends:
            logger.info(f"   {t.viral_score} - {t.topic}")


if __name__ == "__main__":
    asyncio.run(main())