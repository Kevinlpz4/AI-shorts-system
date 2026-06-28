"""
RegisterManualInputUseCase — Caso de uso: input manual del usuario
====================================================================
El usuario provee contenido manualmente (un enlace, un texto, o un tema)
para ser evaluado como posible candidato a Short.

Flujo:
  1. Validar que el input no esté vacío
  2. Crear ResearchTopic desde el input del usuario
  3. Verificar duplicados contra topics existentes
  4. Calcular score
  5. Guardar en repositorio
  6. Emitir evento TopicDiscovered
  7. Retornar resultado

Reglas de negocio (enforzadas por el dominio):
  - El topic siempre se crea en PENDING_REVIEW
  - Si es duplicado, se marca como tal pero igual se guarda
    (el usuario puede forzar un duplicado si quiere)
"""

from typing import Optional

from research.application.dtos import (
    ManualInputDTO,
    ResearchResultDTO,
)
from research.application.mappers import topic_to_dto, event_to_dict
from research.domain.entities.research_topic import ResearchTopic
from research.domain.ports.research_repository import ResearchRepository
from research.domain.services.duplicate_detector import (
    CompositeDuplicateDetector,
)
from research.domain.services.research_scorer import ResearchScorer
from research.domain.value_objects.research_source import ResearchSource
from research.domain.exceptions import InvalidManualInputError


class RegisterManualInputUseCase:
    """
    Caso de uso: registrar un topic manualmente.

    Dependencias (inyectadas):
      - repository: ResearchRepository (port)
      - duplicate_detector: CompositeDuplicateDetector (domain service)
      - scorer: ResearchScorer (domain service)
    """

    def __init__(
        self,
        repository: ResearchRepository,
        duplicate_detector: CompositeDuplicateDetector,
        scorer: Optional[ResearchScorer] = None,
    ):
        self._repository = repository
        self._detector = duplicate_detector
        self._scorer = scorer or ResearchScorer()

    async def execute(self, dto: ManualInputDTO) -> ResearchResultDTO:
        """
        Ejecuta el caso de uso.

        Args:
            dto: ManualInputDTO con los datos del usuario

        Returns:
            ResearchResultDTO con el topic creado y eventos
        """
        # 1. Validar input
        self._validate(dto)

        # 2. Crear fuente
        source = ResearchSource.manual(dto.source_name)

        # 3. Crear entidad
        topic = ResearchTopic(
            title=dto.title or self._extract_title_from_url(dto.url) or "Sin título",
            description=dto.description or "",
            content=dto.content or "",
            source=source,
            url=dto.url,
            author=dto.author,
        )

        # 4. Verificar duplicados
        # Cargar hashes existentes: tanto el guardado como los computados
        # de todas las estrategias (por si solo se guardó un subconjunto)
        existing = await self._repository.find_all(limit=200)
        existing_hashes: set[str] = set()
        for t in existing:
            # Los hashes pueden estar separados por coma (formato multi-hash)
            if t.duplicate_hash:
                for h in t.duplicate_hash.split(","):
                    if h:
                        existing_hashes.add(h)
            # También computar TODOS los hashes con las estrategias actuales
            existing_hashes.update(self._detector.compute_hashes(t))

        topic_hashes = self._detector.compute_hashes(topic)
        is_duplicate = bool(topic_hashes & existing_hashes)

        # Guardar TODOS los hashes como string separado por coma
        # para que futuras detecciones tengan toda la info
        topic.duplicate_hash = ",".join(sorted(topic_hashes)) if topic_hashes else None

        # 5. Calcular score
        topic.score = self._scorer.calculate(topic)

        # 6. Marcar como descubierto (genera evento)
        topic.mark_as_discovered()

        # 7. Guardar
        await self._repository.save(topic)

        # 8. Extraer eventos
        events = topic.pull_events()

        # 9. Retornar DTO
        return ResearchResultDTO(
            topic=topic_to_dto(topic),
            is_duplicate=is_duplicate,
            events=[event_to_dict(e) for e in events],
        )

    def _validate(self, dto: ManualInputDTO) -> None:
        """Valida que el input tenga al menos algún contenido."""
        if not any([dto.url, dto.title, dto.content, dto.description]):
            raise InvalidManualInputError(
                reason="Debe proporcionar al menos url, título o contenido"
            )

    def _extract_title_from_url(self, url: Optional[str]) -> Optional[str]:
        """Extrae un título tentativo de la URL (placeholder básico)."""
        if not url:
            return None
        # Futuro: SummarizerExtension podría extraer el título real
        return None
