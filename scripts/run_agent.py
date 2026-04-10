"""
Script de Ejemplo - Uso del Agente
===================================
Este script muestra cómo usar el AI Shorts Agent.
"""

import asyncio
import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import AIShortsAgent


async def main():
    """
    Ejemplo de uso del Agente Maestro.
    """
    print("🚀 Inicializando AI Shorts Agent...")
    
    # Inicializar el agente
    agent = AIShortsAgent(config={
        "default_voice": "spanish_male",
        "default_platform": "youtube"
    })
    
    print("\n📊 Estado inicial del agente:")
    status = await agent.get_status()
    print(f"   Agent ID: {status['agent_id']}")
    print(f"   Total ejecuciones: {status['total_executions']}")
    
    # Ejecutar un ciclo completo
    print("\n🎬 Ejecutando ciclo completo de generación...")
    print("=" * 50)
    
    result = await agent.run_full_cycle(
        goal="Crear contenido viral sobre inteligencia artificial",
        niche="tecnología",
        platform="youtube"
    )
    
    print("\n📋 RESULTADO:")
    print(f"   Status: {result.get('status')}")
    print(f"   Cycle ID: {result.get('cycle_id')}")
    print(f"   Video URL: {result.get('video_url')}")
    
    if result.get('recommendations'):
        print("\n💡 RECOMENDACIONES:")
        for rec in result['recommendations']:
            print(f"   - {rec}")
    
    # Obtener resumen de memoria
    print("\n📈 Resumen de Memoria:")
    memory_summary = await agent.memory.get_memory_summary()
    print(f"   Total ciclos: {memory_summary['total_cycles']}")
    print(f"   Exitosos: {memory_summary['successful']}")
    print(f"   Promedio retención: {memory_summary['avg_metrics'].get('retention', 0):.1f}%")


if __name__ == "__main__":
    asyncio.run(main())