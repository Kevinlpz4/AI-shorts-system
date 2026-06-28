"""
Tests unitarios para SchedulerConfig (persistencia del scheduler).
"""
import tempfile
from pathlib import Path

import pytest

from research.infrastructure.persistence.scheduler_config import SchedulerConfig


class TestSchedulerConfig:
    """SchedulerConfig con DB temporal."""

    @pytest.fixture
    def config(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        sc = SchedulerConfig(db_path=db_path)
        yield sc
        Path(db_path).unlink(missing_ok=True)

    def test_default_interval(self, config: SchedulerConfig):
        """Intervalo por defecto debe ser 60."""
        assert config.get_interval() == 60

    def test_set_interval(self, config: SchedulerConfig):
        """Cambiar intervalo debe persistir."""
        config.set_interval(30)
        assert config.get_interval() == 30

    def test_interval_minimum(self, config: SchedulerConfig):
        """Intervalo mínimo debe ser 1."""
        config.set_interval(0)
        assert config.get_interval() >= 1

    def test_interval_negative(self, config: SchedulerConfig):
        """Intervalo negativo se convierte en mínimo."""
        config.set_interval(-5)
        assert config.get_interval() >= 1

    def test_enabled_default_false(self, config: SchedulerConfig):
        """Por defecto debe estar deshabilitado."""
        assert config.is_enabled() is False

    def test_set_enabled_true(self, config: SchedulerConfig):
        """Habilitar debe persistir."""
        config.set_enabled(True)
        assert config.is_enabled() is True

    def test_set_enabled_false(self, config: SchedulerConfig):
        """Deshabilitar debe persistir."""
        config.set_enabled(True)
        config.set_enabled(False)
        assert config.is_enabled() is False

    def test_default_queries(self, config: SchedulerConfig):
        """Queries por defecto debe incluir tecnología e IA."""
        queries = config.get_queries()
        assert len(queries) >= 1
        assert any("tecnología" in q.lower() for q in queries)

    def test_set_queries(self, config: SchedulerConfig):
        """Cambiar queries debe persistir."""
        config.set_queries(["IA", "Python", "Machine Learning"])
        assert config.get_queries() == ["IA", "Python", "Machine Learning"]

    def test_set_queries_empty(self, config: SchedulerConfig):
        """Queries vacías deben persistir."""
        config.set_queries([])
        assert config.get_queries() == []

    def test_last_run_default_none(self, config: SchedulerConfig):
        """last_run debe ser None por defecto."""
        assert config.get_last_run() is None

    def test_set_last_run(self, config: SchedulerConfig):
        """Guardar timestamp debe persistir."""
        config.set_last_run("2025-01-01T00:00:00+00:00")
        assert config.get_last_run() == "2025-01-01T00:00:00+00:00"

    def test_get_status(self, config: SchedulerConfig):
        """get_status debe retornar todas las configuraciones."""
        config.set_interval(45)
        config.set_enabled(True)
        config.set_queries(["test"])
        config.set_last_run("2025-06-01T12:00:00+00:00")

        status = config.get_status()
        assert status["interval_minutes"] == 45
        assert status["enabled"] is True
        assert status["queries"] == ["test"]
        assert status["last_run"] is not None

    def test_different_instances_same_db(self, config: SchedulerConfig):
        """Dos instancias apuntando a la misma DB deben compartir datos."""
        config.set_interval(15)
        config.set_enabled(True)

        # Nueva instancia, mismo archivo
        config2 = SchedulerConfig(db_path=config._db_path)
        assert config2.get_interval() == 15
        assert config2.is_enabled() is True
