"""
Tests de Integración para Studio Router.
==========================================
Usa TestClient con un ApiContainer real (temp DB, mock AI).
Dependencia: el router usa research_repository.find_approved_without_script()
y get_recommendations() — esta última es pura, sin dependencias externas.
"""
import pytest
from uuid import uuid4

from fastapi.testclient import TestClient

from presentation.api.main import create_app
from presentation.api.container import ApiContainer


@pytest.fixture
def api_app(tmp_path, monkeypatch):
    """Crea la app FastAPI con dependencias en temp (misma base que test_api_routes)."""
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
    # AI_PROVIDER eliminado — el Container siempre usa OpenRouter.
    # Sin OPENROUTER_API_KEY, automáticamente cae a MockAIProvider.
    container = ApiContainer()
    app = create_app(container)
    return app


@pytest.fixture
def client(api_app):
    """TestClient para la API."""
    return TestClient(api_app)


@pytest.fixture
def seed_approved_topic(client) -> str:
    """Crea y aprueba un topic, retorna su ID."""
    # 1. Crear topic manual
    create_resp = client.post(
        "/api/v1/topics/manual",
        json={
            "title": "Studio test topic",
            "url": "https://example.com/studio-test",
        },
    )
    assert create_resp.status_code == 201
    topic_id = create_resp.json()["topic"]["id"]

    # 2. Aprobar topic
    approve_resp = client.post(f"/api/v1/topics/{topic_id}/approve")
    assert approve_resp.status_code == 200
    assert approve_resp.json()["topic"]["status"] == "approved"

    return topic_id


# ── Tests ──────────────────────────────────────────────


class TestStudioAPI:

    def test_get_approved_topics_empty(self, client):
        """GET /api/v1/studio/approved-topics sin data → lista vacía."""
        resp = client.get("/api/v1/studio/approved-topics")

        assert resp.status_code == 200
        data = resp.json()
        assert "topics" in data
        assert "count" in data
        assert isinstance(data["topics"], list)
        assert data["count"] == 0

    def test_get_approved_topics_with_seeded_topic(self, client, seed_approved_topic):
        """GET /api/v1/studio/approved-topics con topic aprobado → lo incluye."""
        resp = client.get("/api/v1/studio/approved-topics")

        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        topic_ids = [t["id"] for t in data["topics"]]
        assert seed_approved_topic in topic_ids

    def test_get_approved_topics_only_approved(self, client):
        """Topics no aprobados NO deben aparecer en la lista."""
        # Crear topic pero NO aprobar
        cr = client.post(
            "/api/v1/topics/manual",
            json={"title": "No aprobado", "url": "https://example.com/no-aprobar"},
        )
        assert cr.status_code == 201

        # Verificar que no aparece en approved-topics
        resp = client.get("/api/v1/studio/approved-topics")
        assert resp.status_code == 200
        data = resp.json()
        topic_ids = [t["id"] for t in data["topics"]]
        assert cr.json()["topic"]["id"] not in topic_ids

    def test_get_recommendations_existing_topic(self, client, seed_approved_topic):
        """GET /api/v1/studio/recommendations/{id} → 200 + recomendaciones."""
        resp = client.get(f"/api/v1/studio/recommendations/{seed_approved_topic}")

        assert resp.status_code == 200
        data = resp.json()
        assert "tone" in data
        assert "duration" in data
        assert "niche" in data
        assert "reasoning" in data
        # Verificar que son los tipos correctos
        assert isinstance(data["tone"], str)
        assert isinstance(data["duration"], int)
        assert isinstance(data["niche"], str)
        assert isinstance(data["reasoning"], dict)
        assert "tone" in data["reasoning"]
        assert "duration" in data["reasoning"]
        assert "niche" in data["reasoning"]

    def test_get_recommendations_not_found(self, client):
        """GET /api/v1/studio/recommendations/{inexistente} → 404."""
        nonexistent_id = uuid4()
        resp = client.get(f"/api/v1/studio/recommendations/{nonexistent_id}")

        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data

    def test_get_recommendations_reasons_are_text(
        self, client, seed_approved_topic,
    ):
        """Los reasoning deben ser strings explicativos."""
        resp = client.get(f"/api/v1/studio/recommendations/{seed_approved_topic}")

        assert resp.status_code == 200
        data = resp.json()
        reasoning = data["reasoning"]
        assert len(reasoning["tone"]) > 5
        assert len(reasoning["duration"]) > 5
        assert len(reasoning["niche"]) > 5

    def test_get_approved_topics_ordered_by_score(self, client):
        """Approved topics deben venir ordenados por score DESC."""
        # Crear dos topics con diferentes scores
        # Esto depende del scorer interno, pero al menos verificamos forma
        t1 = client.post("/api/v1/topics/manual", json={
            "title": "Topic A",
            "url": "https://example.com/a",
        }).json()["topic"]["id"]
        client.post(f"/api/v1/topics/{t1}/approve")

        t2 = client.post("/api/v1/topics/manual", json={
            "title": "Topic B",
            "url": "https://example.com/b",
        }).json()["topic"]["id"]
        client.post(f"/api/v1/topics/{t2}/approve")

        resp = client.get("/api/v1/studio/approved-topics")
        data = resp.json()
        assert data["count"] >= 2
        # Los scores deben estar en orden descendente
        scores = [t["score_total"] for t in data["topics"]]
        assert scores == sorted(scores, reverse=True), (
            f"Topics should be ordered by score DESC, got {scores}"
        )
