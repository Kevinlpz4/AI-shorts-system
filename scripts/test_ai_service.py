"""
Test AI Service - Verifica conexión a las APIs
==============================================
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai_service import AIService
from app.logger import logger


async def test_ai_service():
    """Prueba el servicio de IA."""
    print("=" * 50)
    print("🧪 TESTEANDO AI SERVICE")
    print("=" * 50)
    
    # Inicializar servicio
    ai = AIService()
    
    # Ver proveedores disponibles
    print("\n📊 Proveedores disponibles:")
    providers = ai.get_available_providers()
    for prov, available in providers.items():
        status = "✅" if available else "❌"
        print(f"   {status} {prov}: {available}")
    
    # Si no hay proveedores, salir
    if not any(providers.values()):
        print("\n⚠️ No hay proveedores disponibles. Agregá las API keys en .env")
        return
    
    # Test de generación
    print("\n🧠 Probando generación de idea...")
    try:
        idea = await ai.generate_idea([
            "Inteligencia artificial revolucionando industrias",
            "Nuevas herramientas de IA para creadores",
            "El futuro del trabajo con IA"
        ])
        print(f"   ✅ Idea generada: {idea}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test de generación de script
    print("\n✍️ Probando generación de script...")
    try:
        script = await ai.generate_script("Tema sobre IA que está trending")
        print(f"   ✅ Script generado: {script}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ TEST COMPLETADO")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_ai_service())