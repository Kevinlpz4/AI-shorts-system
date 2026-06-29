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
  - ai_provider (con fallback wrapper)

Agrega:
  - script_repo: SQLiteScriptRepository
  - generate_script_use_case, get_script_use_case, regenerate_script_use_case
"""
import logging

from app.config import settings
from presentation.cli.container import Container

# ── Script Module ──
from infrastructure.persistence.sqlite_script_repository import (
    SQLiteScriptRepository,
)
from application.use_cases.script.generate_script import GenerateScriptUseCase
from application.use_cases.script.get_script import GetScriptUseCase
from application.use_cases.script.regenerate_script import RegenerateScriptUseCase

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
        logger.info("🌐 ApiContainer: dependencias de API inicializadas")

    def _init_script_module(self):
        """Inicializa dependencias del módulo Script."""
        # ── Repositorio de Scripts (misma DB que research) ──
        db_path = str(settings.RESEARCH_DB_PATH)
        self.script_repo = SQLiteScriptRepository(db_path=db_path)

        # ── Fallback AI wrapper (ya incluye generate_script) ──
        ai = self._create_fallback_ai_wrapper()

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
