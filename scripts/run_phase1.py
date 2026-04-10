"""
Script para ejecutar el pipeline mínimo (Fase 1)
==================================================
Trends → Idea → Script → output.txt
"""

import asyncio
import sys
from pathlib import Path

# Agregar raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.trends import TrendsAnalyzer
from modules.idea_generator import IdeaGenerator
from modules.script_generator import ScriptGenerator


async def main():
    print("🚀 Iniciando Pipeline - Fase 1")
    print("=" * 50)
    
    # Inicializar módulos
    trends_analyzer = TrendsAnalyzer()
    idea_generator = IdeaGenerator()
    script_generator = ScriptGenerator()
    
    # Step 1: Obtener trends
    print("\n📡 Paso 1: Obteniendo trends...")
    trends = await trends_analyzer.get_trends(
        sources=["news", "twitter", "youtube"],
        niche="tecnología",
        limit=5
    )
    print(f"   ✓ {len(trends)} trends obtenidos")
    
    if not trends:
        print("❌ Error: No se pudieron obtener trends")
        return
    
    # Step 2: Generar idea
    print("\n🧠 Paso 2: Generando idea...")
    ideas = await idea_generator.generate_ideas(
        trends=trends,
        niche="tecnología",
        styles=["story", "list", "tutorial"],
        count=1
    )
    print(f"   ✓ {len(ideas)} ideas generadas")
    
    if not ideas:
        print("❌ Error: No se pudieron generar ideas")
        return
    
    best_idea = ideas[0]
    print(f"   ✓ Idea seleccionada: {best_idea.hook[:50]}...")
    
    # Step 3: Generar script
    print("\n✍️ Paso 3: Generando script...")
    script = await script_generator.generate_script(
        idea=best_idea,
        duration=45,
        tone="educational"
    )
    print(f"   ✓ Script generado ({script.duration}s, {script.word_count} palabras)")
    
    # Step 4: Guardar output
    print("\n💾 Paso 4: Guardando output...")
    output_path = Path("data/output.txt")
    
    output_content = f"""TRENDS:
{'-' * 40}
{chr(10).join([f"- {t.topic} (score: {t.viral_score}, source: {t.source})" for t in trends])}

IDEA:
{'-' * 40}
ID: {best_idea.id}
Hook: {best_idea.hook}
Formato: {best_idea.format}
Potencial viral: {best_idea.viral_potential}
Descripción: {best_idea.description}

SCRIPT:
{'-' * 40}
Hook: {script.hook}
Body: {script.body}
CTA: {script.cta}
Duración: {script.duration}s
Palabras: {script.word_count}
Tono: {script.tone}
---
Texto completo:
{script.full_text}
"""
    
    output_path.write_text(output_content, encoding="utf-8")
    print(f"   ✓ Guardado en: {output_path}")
    
    # Resumen
    print("\n" + "=" * 50)
    print("✅ PIPELINE COMPLETADO")
    print("=" * 50)
    print(f"Trends: {len(trends)}")
    print(f"Idea: {best_idea.hook[:30]}...")
    print(f"Script: {script.duration}s, {script.word_count} palabras")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())