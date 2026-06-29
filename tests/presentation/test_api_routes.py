"""
Tests de Integración para FastAPI Routes.
Usa TestClient con un ApiContainer configurado con temp db y mock AI.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from presentation.api.main import create_app
from presentation.api.container import ApiContainer


@pytest.fixture
def api_app(tmp_path, monkeypatch):
    """Crea la app FastAPI con dependencias en temp."""
    # ── Configuración para test ──
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
    app = create_app(container)
    return app


@pytest.fixture
def client(api_app):
    """TestClient para la API."""
    return TestClient(api_app)


# ── Root Endpoint ─────────────────────────────────────


class TestRootEndpoint:

    def test_root_returns_service_info(self, client):
        """GET / debe retornar service info."""
        resp = client.get("/")

        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "AI Shorts System API"
        assert "version" in data


# ── Topics Endpoints ──────────────────────────────────


class TestTopicsEndpoints:

    def test_list_topics_empty(self, client):
        """GET /api/v1/topics debe retornar lista vacía inicial."""
        resp = client.get("/api/v1/topics")

        assert resp.status_code == 200
        data = resp.json()
        assert "topics" in data
        assert data["count"] == 0
        assert data["topics"] == []

    def test_list_topics_with_limit(self, client):
        """GET /api/v1/topics acepta limit param."""
        resp = client.get("/api/v1/topics?limit=5")

        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_get_topic_not_found(self, client):
        """GET /api/v1/topics/{id} para ID inexistente debe dar 404."""
        resp = client.get("/api/v1/topics/00000000-0000-0000-0000-000000000000")

        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data

    def test_create_manual_topic(self, client):
        """POST /api/v1/topics/manual debe crear un topic."""
        resp = client.post(
            "/api/v1/topics/manual",
            json={"title": "Test topic", "url": "https://example.com/test"},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert "topic" in data
        assert data["topic"]["title"] == "Test topic"

    def test_create_manual_topic_empty_body(self, client):
        """POST /api/v1/topics/manual sin body debe dar error."""
        resp = client.post("/api/v1/topics/manual", json={})

        assert resp.status_code == 422 or resp.status_code == 400

    def test_create_and_approve_topic(self, client):
        """Crear topic manual → aprobar debe funcionar."""
        # Crear
        create_resp = client.post(
            "/api/v1/topics/manual",
            json={"title": "Aprobar test", "url": "https://example.com/approve"},
        )
        assert create_resp.status_code == 201
        topic_id = create_resp.json()["topic"]["id"]

        # Aprobar
        approve_resp = client.post(f"/api/v1/topics/{topic_id}/approve")
        assert approve_resp.status_code == 200
        assert approve_resp.json()["topic"]["status"] == "approved"

    def test_create_and_reject_topic(self, client):
        """Crear topic manual → rechazar debe funcionar."""
        create_resp = client.post(
            "/api/v1/topics/manual",
            json={"title": "Reject test", "url": "https://example.com/reject"},
        )
        assert create_resp.status_code == 201
        topic_id = create_resp.json()["topic"]["id"]

        reject_resp = client.post(f"/api/v1/topics/{topic_id}/reject")
        assert reject_resp.status_code == 200
        assert reject_resp.json()["topic"]["status"] == "rejected"

    def test_list_topics_with_status_filter(self, client):
        """Listar topics filtrados por estado."""
        # Crear y aprobar un topic
        cr = client.post("/api/v1/topics/manual", json={
            "title": "Filtrar", "url": "https://example.com/filter",
        })
        tid = cr.json()["topic"]["id"]
        client.post(f"/api/v1/topics/{tid}/approve")

        # Listar aprobados
        resp = client.get("/api/v1/topics?status=approved")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1

    def test_approve_already_approved_returns_error(self, client):
        """Aprobar topic ya aprobado debe dar error."""
        cr = client.post("/api/v1/topics/manual", json={
            "title": "Doble aprobar", "url": "https://example.com/double",
        })
        tid = cr.json()["topic"]["id"]
        client.post(f"/api/v1/topics/{tid}/approve")

        resp = client.post(f"/api/v1/topics/{tid}/approve")
        assert resp.status_code == 409

    def test_discover_endpoint(self, client):
        """POST /api/v1/discover debe descubrir topics."""
        resp = client.post("/api/v1/discover", json={
            "query": "tecnología",
            "limit": 3,
        })

        assert resp.status_code == 200
        data = resp.json()
        assert "discovered" in data
        assert "errors" in data
        assert data["count"] >= 0


# ── Script Endpoints ──────────────────────────────────


class TestScriptEndpoints:

    def test_get_script_not_found(self, client):
        """GET /api/v1/topics/{id}/script sin guion debe dar 404."""
        topic_id = "00000000-0000-0000-0000-000000000000"
        resp = client.get(f"/api/v1/topics/{topic_id}/script")

        assert resp.status_code == 404

    def test_generate_script_topic_not_found(self, client):
        """POST generate con topic inexistente debe dar 404."""
        topic_id = "00000000-0000-0000-0000-000000000000"
        resp = client.post(f"/api/v1/topics/{topic_id}/script/generate")

        assert resp.status_code == 404

    def test_generate_script_topic_not_approved(self, client):
        """POST generate con topic no aprobado debe dar 409."""
        # Crear topic (va a PENDING_REVIEW)
        cr = client.post("/api/v1/topics/manual", json={
            "title": "No aprobado",
            "url": "https://example.com/noapprove",
        })
        tid = cr.json()["topic"]["id"]

        resp = client.post(f"/api/v1/topics/{tid}/script/generate")
        assert resp.status_code == 409

    def test_generate_and_get_script(self, client):
        """Flujo completo: crear topic → aprobar → generar → obtener."""
        # 1. Crear topic
        cr = client.post("/api/v1/topics/manual", json={
            "title": "Script completo",
            "url": "https://example.com/script-test",
        })
        assert cr.status_code == 201
        tid = cr.json()["topic"]["id"]

        # 2. Aprobar topic
        ar = client.post(f"/api/v1/topics/{tid}/approve")
        assert ar.status_code == 200

        # 3. Generar script
        gr = client.post(
            f"/api/v1/topics/{tid}/script/generate",
            json={"tone": "educational", "duration": 45},
        )
        assert gr.status_code == 201
        script = gr.json()
        assert script["topic_id"] == tid
        assert script["is_valid"] is True
        assert script["tone"] == "educational"

        # 4. Obtener script
        gr2 = client.get(f"/api/v1/topics/{tid}/script")
        assert gr2.status_code == 200
        assert gr2.json()["id"] == script["id"]

    def test_generate_script_duplicate(self, client):
        """Generar script dos veces debe dar 409 Conflict."""
        # 1. Crear topic
        cr = client.post("/api/v1/topics/manual", json={
            "title": "Script duplicado",
            "url": "https://example.com/dup-script",
        })
        tid = cr.json()["topic"]["id"]

        # 2. Aprobar
        client.post(f"/api/v1/topics/{tid}/approve")

        # 3. Primera generación
        r1 = client.post(f"/api/v1/topics/{tid}/script/generate")
        assert r1.status_code == 201

        # 4. Segunda generación → 409
        r2 = client.post(f"/api/v1/topics/{tid}/script/generate")
        assert r2.status_code == 409

    def test_regenerate_script(self, client):
        """Regenerar script debe funcionar y devolver script nuevo."""
        # 1. Crear topic
        cr = client.post("/api/v1/topics/manual", json={
            "title": "Script regenerar",
            "url": "https://example.com/regen-script",
        })
        tid = cr.json()["topic"]["id"]

        # 2. Aprobar
        client.post(f"/api/v1/topics/{tid}/approve")

        # 3. Generar
        r1 = client.post(f"/api/v1/topics/{tid}/script/generate")
        original_id = r1.json()["id"]

        # 4. Regenerar
        r2 = client.post(
            f"/api/v1/topics/{tid}/script/regenerate",
            json={"tone": "humor"},
        )
        assert r2.status_code == 200
        new_script = r2.json()
        assert new_script["id"] != original_id
        assert new_script["tone"] == "humor"

    def test_regenerate_script_no_existing(self, client):
        """Regenerar sin script existente debe crear uno nuevo."""
        cr = client.post("/api/v1/topics/manual", json={
            "title": "Regen sin existente",
            "url": "https://example.com/regen-new",
        })
        tid = cr.json()["topic"]["id"]
        client.post(f"/api/v1/topics/{tid}/approve")

        resp = client.post(f"/api/v1/topics/{tid}/script/regenerate")
        assert resp.status_code == 200
        assert resp.json()["is_valid"] is True
