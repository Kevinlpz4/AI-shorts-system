"""
Research Use Cases
==================
Casos de uso del módulo Research.

Cada caso de uso:
  1. Recibe un DTO de entrada
  2. ORQUESTA el dominio (entidades, servicios, puertos)
  3. Retorna un DTO de salida
  4. NO contiene lógica de negocio (eso es del dominio)
  5. NO conoce la infraestructura (solo puertos)

Casos de uso:
  - RegisterManualInputUseCase: usuario agrega topic manualmente
  - AutoDiscoverTopicsUseCase: descubrimiento automático desde fuentes
  - ApproveTopicUseCase: aprobar un topic para generación
  - RejectTopicUseCase: rechazar un topic
  - ListTopicsUseCase: listar topics con filtros
"""
