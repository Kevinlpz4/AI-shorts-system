"""
Research Domain Ports
=====================
Puertos (interfaces) del módulo Research.

Regla: los puertos definen QUÉ necesita el dominio, no CÓMO se implementa.
Las implementaciones concretas viven en research/infrastructure/.

Puertos definidos:
  - ResearchSourcePort: fuente externa de investigación
  - ResearchRepository: persistencia de topics
  - ResearchScorerExtension: (futuro) IA para puntuar
  - ResearchSummarizerExtension: (futuro) IA para resumir
  - FakeNewsDetectorExtension: (futuro) IA para detectar fake news
"""
