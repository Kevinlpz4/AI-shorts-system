"""
Script Use Cases
=================
Casos de uso del módulo de Script.

Cada caso de uso:
  1. Recibe un DTO de entrada
  2. ORQUESTA el dominio (entidades, servicios, puertos)
  3. Retorna un DTO de salida
  4. NO contiene lógica de negocio (eso es del dominio)
  5. NO conoce la infraestructura (solo puertos)

Casos de uso:
  - GenerateScriptUseCase: generar guion para un topic aprobado
  - GetScriptUseCase: obtener guion existente por topic
  - RegenerateScriptUseCase: regenerar guion (eliminar + generar)
"""

from application.use_cases.script.generate_script import GenerateScriptUseCase
from application.use_cases.script.get_script import GetScriptUseCase
from application.use_cases.script.regenerate_script import RegenerateScriptUseCase

__all__ = [
    "GenerateScriptUseCase",
    "GetScriptUseCase",
    "RegenerateScriptUseCase",
]
