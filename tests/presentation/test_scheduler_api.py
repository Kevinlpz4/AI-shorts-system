"""
Tests de Integración para Scheduler Router.
=============================================
Usa TestClient con un ApiContainer y mocks para research_scheduler y
scheduler_config, evitando dependencias de red y tareas asyncio reales.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from presentation.api.main import create_app
from presentation.api.container import ApiContainer


@pytest.fixture
def mock_research_scheduler():
    """Mock completo del ResearchScheduler.

    NOTA: get_status() es sync (no await), start/stop/run_once son async.
    Usamos MagicMock para get_status y AsyncMock para los métodos async.
    """
    scheduler = MagicMock()
    scheduler.get_status.return_value = {
        "is_running": False,
        "running_query": None,
        "enabled": False,
        "interval_minutes": 60,
        "queries": ["tecnología"],
        "last_run": None,
    }
    scheduler.start = AsyncMock()
    scheduler.stop = AsyncMock()
    scheduler.run_once = AsyncMock(return_value={
        "discovered_count": 0,
        "duplicates_count": 0,
        "errors": [],
    })
    return scheduler


@pytest.fixture
def mock_scheduler_config():
    """Mock del SchedulerConfig."""
    config = MagicMock()
    config.get_interval.return_value = 60
    config.get_queries.return_value = ["tecnología", "ia"]
    config.is_auto_generate_enabled.return_value = False
    config.set_interval = MagicMock()
    config.set_queries = MagicMock()
    config.set_auto_generate = MagicMock()
    config.is_enabled.return_value = False
    config.get_last_run.return_value = None
    return config


@pytest.fixture
def api_app(tmp_path, monkeypatch, mock_research_scheduler, mock_scheduler_config):
    """Crea la app FastAPI con mocks en el container."""
    # Configuración base para evitar errores de path
    db_path = tmp_path / "test_research.db"
    data_dir = tmp_path / "test_data"
    data_dir.mkdir(exist_ok=True)
    audio_dir = tmp_path / "test_audio"
    audio_dir.mkdir(exist_ok=True)
    video_dir = tmp_path / "test_video"
    video_dir.mkdir(exist_ok=True)

    monkeypatch.setattr("app.config.settings.RESEARCH_DB_PATH", db_path)
    monkeypatch.setattr("app.config.settings.DATA_DIR", data_dir)
    monkeypatch.setattr("app.config.settings.AUDIO_DIR", audio_dir)
    monkeypatch.setattr("app.config.settings.VIDEO_DIR", video_dir)
    monkeypatch.setattr("app.config.settings.AI_PROVIDER", "mock")
    monkeypatch.setenv("AI_PROVIDER", "mock")

    container = ApiContainer()
    # Reemplazar con mocks para aislar tests
    container.research_scheduler = mock_research_scheduler
    container.scheduler_config = mock_scheduler_config

    app = create_app(container)
    return app


@pytest.fixture
def client(api_app):
    """TestClient para la API."""
    return TestClient(api_app)


# ── Tests ──────────────────────────────────────────────


class TestSchedulerAPI:

    def test_get_scheduler_status(self, client):
        """GET /api/v1/scheduler/status → 200 + status dict."""
        resp = client.get("/api/v1/scheduler/status")

        assert resp.status_code == 200
        data = resp.json()
        assert "is_running" in data
        assert "enabled" in data
        assert "interval_minutes" in data
        assert "queries" in data

    def test_post_scheduler_start(self, client):
        """POST /api/v1/scheduler/start → 200 + started."""
        resp = client.post("/api/v1/scheduler/start")

        assert resp.status_code == 200
        assert resp.json() == {"status": "started"}

    def test_post_scheduler_stop(self, client):
        """POST /api/v1/scheduler/stop → 200 + stopped."""
        resp = client.post("/api/v1/scheduler/stop")

        assert resp.status_code == 200
        assert resp.json() == {"status": "stopped"}

    def test_post_scheduler_run_now(self, client):
        """POST /api/v1/scheduler/run-now → 200 + cycle results."""
        resp = client.post("/api/v1/scheduler/run-now")

        assert resp.status_code == 200
        data = resp.json()
        assert "discovered_count" in data
        assert "duplicates_count" in data
        assert "errors" in data
        assert data["discovered_count"] == 0
        assert data["duplicates_count"] == 0
        assert data["errors"] == []

    def test_get_scheduler_config(self, client):
        """GET /api/v1/scheduler/config → 200 + config dict."""
        resp = client.get("/api/v1/scheduler/config")

        assert resp.status_code == 200
        data = resp.json()
        assert "interval_minutes" in data
        assert "queries" in data
        assert "auto_generate_script" in data
        assert data["interval_minutes"] == 60
        assert data["auto_generate_script"] is False

    def test_put_scheduler_config_interval(self, client):
        """PUT /api/v1/scheduler/config con interval → updated config."""
        resp = client.put("/api/v1/scheduler/config", json={"interval_minutes": 30})

        assert resp.status_code == 200
        data = resp.json()
        assert "interval_minutes" in data
        assert "queries" in data
        assert "auto_generate_script" in data

    def test_put_scheduler_config_queries(self, client):
        """PUT /api/v1/scheduler/config con queries → updated config."""
        resp = client.put(
            "/api/v1/scheduler/config",
            json={"queries": ["python", "testing"]},
        )

        assert resp.status_code == 200

    def test_put_scheduler_config_auto_generate(self, client):
        """PUT /api/v1/scheduler/config con auto_generate_script → updated."""
        resp = client.put(
            "/api/v1/scheduler/config",
            json={"auto_generate_script": True},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "auto_generate_script" in data

    def test_put_scheduler_config_all_fields(self, client):
        """PUT /api/v1/scheduler/config con todos los campos → 200 + estructura."""
        resp = client.put(
            "/api/v1/scheduler/config",
            json={
                "interval_minutes": 15,
                "queries": ["test1", "test2"],
                "auto_generate_script": True,
            },
        )

        assert resp.status_code == 200
        data = resp.json()
        # Verificar estructura (valores exactos se testean en unit tests)
        assert "interval_minutes" in data
        assert "queries" in data
        assert "auto_generate_script" in data
        assert isinstance(data["interval_minutes"], int)
        assert isinstance(data["queries"], list)
        assert isinstance(data["auto_generate_script"], bool)

    def test_put_scheduler_config_empty_body(self, client):
        """PUT /api/v1/scheduler/config con body vacío → 200 (no changes)."""
        resp = client.put("/api/v1/scheduler/config", json={})

        assert resp.status_code == 200

    def test_scheduler_full_lifecycle(self, client):
        """Start → status running → stop → status stopped."""
        # Start
        resp_start = client.post("/api/v1/scheduler/start")
        assert resp_start.json() == {"status": "started"}

        # Status
        resp_status = client.get("/api/v1/scheduler/status")
        assert resp_status.status_code == 200
        # Con mocks, el status no cambia automágicamente

        # Stop
        resp_stop = client.post("/api/v1/scheduler/stop")
        assert resp_stop.json() == {"status": "stopped"}

        # Run now
        resp_run = client.post("/api/v1/scheduler/run-now")
        data = resp_run.json()
        assert "discovered_count" in data
        assert "duplicates_count" in data
        assert "errors" in data
