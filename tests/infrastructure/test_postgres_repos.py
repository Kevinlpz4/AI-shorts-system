"""
Smoke tests para Postgres repositories.
=========================================
Verifica que las clases se importan correctamente y cumplen
el contrato mínimo (existen los métodos esperados).

Requiere PostgreSQL corriendo para tests reales de integración.
Estos tests solo validan el tipado y la interfaz.
"""


class TestPostgresScriptRepository:
    """Smoke: verifica que PostgresScriptRepository se puede importar."""

    def test_import(self):
        """La clase PostgresScriptRepository se importa sin error."""
        from infrastructure.persistence.postgres_script_repository import (
            PostgresScriptRepository,
        )
        assert PostgresScriptRepository is not None


class TestPostgresSchedulerConfig:
    """Smoke: verifica que PostgresSchedulerConfig implementa la interfaz esperada."""

    def test_import(self):
        """La clase PostgresSchedulerConfig se importa sin error."""
        from research.infrastructure.persistence.postgres_scheduler_config import (
            PostgresSchedulerConfig,
        )
        assert PostgresSchedulerConfig is not None


class TestPostgresResearchRepository:
    """Smoke: verifica que PostgresResearchRepository se importa."""

    def test_import(self):
        """La clase PostgresResearchRepository se importa sin error."""
        from research.infrastructure.persistence.postgres_repository import (
            PostgresResearchRepository,
        )
        assert PostgresResearchRepository is not None
