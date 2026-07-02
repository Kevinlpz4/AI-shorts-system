"""
ApiContainer — Composition Root para FastAPI
==============================================
Extiende el Container CLI y agrega dependencias del módulo Script
para servir la API REST.

Reusa del Container CLI:
  - research_repository
  - research_source_registry
  - research_scorer
  - auto_discover_topics, list_topics, approve_topic, reject_topic,
    register_manual_input
  - fallback_ai, _build_wrapped_provider (para crear AI wrappers)

Agrega:
  - script_repo: PostgresScriptRepository
  - generate_script_use_case, get_script_use_case, regenerate_script_use_case
"""
import logging

from app.config import settings
from presentation.cli.container import Container

# ── Script Module ──
from infrastructure.persistence.postgres_script_repository import (
    PostgresScriptRepository,
)
from application.use_cases.script.generate_script import GenerateScriptUseCase
from application.use_cases.script.get_script import GetScriptUseCase
from application.use_cases.script.regenerate_script import RegenerateScriptUseCase
from research.application.use_cases.approve_topic import ApproveTopicUseCase

logger = logging.getLogger(__name__)


class ApiContainer(Container):
    """
    Contenedor de dependencias para la API REST.

    Extiende el CLI Container y agrega los componentes
    necesarios para el módulo de Scripts.
    """

    def __init__(self):
        super().__init__()
        self._init_script_module()
        self._upgrade_approve_topic()
        logger.info("🌐 ApiContainer: dependencias de API inicializadas")

    def _init_script_module(self):
        """Inicializa dependencias del módulo Script."""
        # ── Repositorio de Scripts (PostgreSQL via SQLAlchemy) ──
        self.script_repo = PostgresScriptRepository()

        # ── AI provider para scripts (modelo configurable vía MODEL_SCRIPT) ──
        ai = self._build_wrapped_provider(
            model=settings.MODEL_SCRIPT or settings.DEFAULT_MODEL,
        )

        # ── Use Cases ──
        self.generate_script_use_case = GenerateScriptUseCase(
            research_repo=self.research_repository,
            script_repo=self.script_repo,
            ai_provider=ai,
        )
        self.get_script_use_case = GetScriptUseCase(
            script_repo=self.script_repo,
        )
        self.regenerate_script_use_case = RegenerateScriptUseCase(
            script_repo=self.script_repo,
            generate_uc=self.generate_script_use_case,
        )

    def _upgrade_approve_topic(self):
        """Reemplaza approve_topic con la versión que soporta auto-generate."""
        self.approve_topic = ApproveTopicUseCase(
            repository=self.research_repository,
            generate_script_uc=self.generate_script_use_case,
            script_repo=self.script_repo,
            scheduler_config=self.scheduler_config,
        )
