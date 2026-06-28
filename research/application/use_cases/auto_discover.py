"""
AutoDiscoverTopicsUseCase — Caso de uso: descubrimiento automático
====================================================================
Busca nuevas noticias desde fuentes externas registradas (Google News,
Twitter, etc.), las procesa y las deja listas para aprobación humana.

Flujo:
  1. Obtener fuentes a consultar (especificadas o todas las disponibles)
  2. Para cada fuente:
     a. Fetch de resultados
     b. Por cada resultado: crear ResearchTopic
     c. Detección de duplicados (contra existentes y dentro del batch)
     d. Scoring
  3. Guardar NO duplicados
  4. Emitir eventos TopicDiscovered
  5. Retornar batch result

Reglas de negocio:
  - Los duplicados se reportan pero NO se guardan
  - Si una fuente falla, se reporta el error pero las otras siguen
  - Siempre se crean en PENDING_REVIEW (control editorial)
"""

import logging
from typing import Optional

from research.application.dtos import (
    AutoDiscoverDTO,
    DiscoverBatchResultDTO,
)
from research.application.source_registry import SourceRegistry
from research.application.mappers import topic_to_dto, event_to_dict
from research.domain.entities.research_topic import ResearchTopic
from research.domain.ports.research_repository import ResearchRepository
from research.domain.ports.research_source import RawResearchData
from research.domain.services.duplicate_detector import (
    CompositeDuplicateDetector,
)
from research.domain.services.research_scorer import ResearchScorer
from research.domain.value_objects.research_source import (
    ResearchSource as RS,
    SourceType,
)
from research.domain.exceptions import SourceNotAvailableError

logger = logging.getLogger(__name__)


class AutoDiscoverTopicsUseCase:
    """
    Caso de uso: descubrimiento automático de topics.

    Dependencias (inyectadas):
      - repository: ResearchRepository (port)
      - source_registry: SourceRegistry (application service)
      - duplicate_detector: CompositeDuplicateDetector (domain service)
      - scorer: ResearchScorer (domain service)
    """

    def __init__(
        self,
        repository: ResearchRepository,
        source_registry: SourceRegistry,
        duplicate_detector: CompositeDuplicateDetector,
        scorer: Optional[ResearchScorer] = None,
    ):
        self._repository = repository
        self._source_registry = source_registry
        self._detector = duplicate_detector
        self._scorer = scorer or ResearchScorer()

    async def execute(self, dto: AutoDiscoverDTO) -> DiscoverBatchResultDTO:
        """
        Ejecuta el descubrimiento automático.

        Args:
            dto: Parámetros de búsqueda

        Returns:
            DiscoverBatchResultDTO con resultados, duplicados y errores
        """
        # 1. Determinar fuentes a consultar
        sources = self._resolve_sources(dto.source_names)

        # 2. Obtener hashes existentes para dedup
        existing_hashes = await self._load_existing_hashes()

        # 3. Procesar cada fuente
        all_discovered: list[ResearchTopic] = []
        all_duplicates: list[ResearchTopic] = []
        errors: list[dict] = []

        for source in sources:
            try:
                raw_results = await source.fetch(
                    query=dto.query,
                    limit=dto.limit,
                )
            except SourceNotAvailableError:
                errors.append({
                    "source": source.source_name,
                    "error": "Fuente no disponible",
                })
                continue
            except Exception as e:
                logger.exception(
                    "Error fetching from source '%s': %s",
                    source.source_name, e
                )
                errors.append({
                    "source": source.source_name,
                    "error": str(e),
                })
                continue

            # Procesar resultados de esta fuente
            for raw in raw_results:
                topic = self._raw_to_topic(raw, source)

                # Detectar duplicados (contra existentes + batch actual)
                topic_hashes = self._detector.compute_hashes(topic)
                is_dup = bool(topic_hashes & existing_hashes)

                if topic_hashes:
                    topic.duplicate_hash = next(iter(topic_hashes))

                # Score
                topic.score = self._scorer.calculate(topic)

                if is_dup:
                    all_duplicates.append(topic)
                else:
                    topic.mark_as_discovered()
                    all_discovered.append(topic)
                    # Acumular hashes para detectar dups intra-batch
                    existing_hashes.update(topic_hashes)

        # 4. Guardar solo los no duplicados
        if all_discovered:
            await self._repository.save_many(all_discovered)

        # 5. Extraer eventos
        all_events: list[dict] = []
        for topic in all_discovered:
            for event in topic.pull_events():
                all_events.append(event_to_dict(event))

        # 6. Retornar resultado
        return DiscoverBatchResultDTO(
            discovered=[topic_to_dto(t) for t in all_discovered],
            duplicates=[topic_to_dto(t) for t in all_duplicates],
            errors=errors,
        )

    def _resolve_sources(self, source_names: Optional[list[str]]) -> list:
        """Resuelve qué fuentes consultar."""
        if source_names:
            sources = []
            for name in source_names:
                try:
                    sources.append(self._source_registry.get(name))
                except SourceNotAvailableError:
                    logger.warning("Source '%s' not registered, skipping", name)
            return sources
        return self._source_registry.get_all_available()

    async def _load_existing_hashes(self) -> set[str]:
        """Carga todos los hashes de duplicados existentes."""
        existing = await self._repository.find_all(limit=1000)
        hashes: set[str] = set()
        for t in existing:
            # Los hashes pueden estar separados por coma (formato multi-hash)
            if t.duplicate_hash:
                for h in t.duplicate_hash.split(","):
                    if h:
                        hashes.add(h)
            # También computar TODOS los hashes con las estrategias actuales
            hashes.update(self._detector.compute_hashes(t))
        return hashes

    def _raw_to_topic(self, raw: RawResearchData, source) -> ResearchTopic:
        """Convierte RawResearchData + source adapter → ResearchTopic."""
        domain_source = RS(
            name=source.source_name,
            type=SourceType.AUTOMATIC,
            reliability=80,  # Default para fuentes automáticas
        )

        return ResearchTopic(
            title=raw.title,
            description=raw.description,
            content=raw.content or raw.description,
            source=domain_source,
            url=raw.url,
            author=raw.author,
            published_at=raw.published_at,
        )
