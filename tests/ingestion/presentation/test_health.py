"""
Tests for Health Check Endpoints (REQ-F6).

Validates:
- GET /health/live always returns 200 with {"status": "alive"}
- GET /health/ready returns 200 when DB is reachable (SELECT 1 succeeds)
- GET /health/ready returns 503 when DB is unreachable (exception raised)

Uses DI override for session_factory to mock database interactions.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ingestion.presentation.dependencies import get_session_factory


# ── Helpers ──


class _FakeSessionContext:
    """Real context manager wrapping a mock session.

    Using a real class avoids MagicMock's method-wrapping behavior
    which breaks ``with session_factory() as session:`` by injecting
    a spurious ``self`` argument into ``__enter__``.
    """

    def __init__(self, session: MagicMock):
        self._session = session

    def __enter__(self):
        return self._session

    def __exit__(self, *args):
        return False


class _FailingSessionContext:
    """Context manager that raises on __enter__ (simulates unreachable DB)."""

    def __enter__(self):
        raise RuntimeError("DB connection refused")

    def __exit__(self, *args):
        return False


def _make_mock_session_factory(healthy: bool = True):
    """Create a mock sessionmaker for health check tests.

    Args:
        healthy: If True, session.execute succeeds. If False, it raises.

    Returns:
        A callable mock that behaves like ``sessionmaker``.
    """
    mock_sf = MagicMock()
    mock_session = MagicMock()

    if healthy:
        mock_session.execute.return_value = None  # SELECT 1 succeeds
        mock_sf.return_value = _FakeSessionContext(mock_session)
    else:
        mock_sf.return_value = _FailingSessionContext()

    return mock_sf


# ── Tests ──


class TestLiveness:
    """Test GET /health/live endpoint."""

    @pytest.mark.anyio
    async def test_liveness_returns_200(self, client):
        """Liveness probe should always return 200 with status alive."""
        response = await client.get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "alive"}


class TestReadiness:
    """Test GET /health/ready endpoint."""

    @pytest.mark.anyio
    async def test_readiness_healthy_db(self, app, client):
        """Readiness probe returns 200 when DB responds to SELECT 1."""
        mock_sf = _make_mock_session_factory(healthy=True)
        app.dependency_overrides[get_session_factory] = lambda: mock_sf

        response = await client.get("/health/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}

    @pytest.mark.anyio
    async def test_readiness_unhealthy_db(self, app, client):
        """Readiness probe returns 503 when DB raises on SELECT 1."""
        mock_sf = _make_mock_session_factory(healthy=False)
        app.dependency_overrides[get_session_factory] = lambda: mock_sf

        response = await client.get("/health/ready")
        assert response.status_code == 503
        assert response.json() == {"status": "not_ready"}
