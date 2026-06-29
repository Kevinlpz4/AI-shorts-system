"""
Tests para Script Domain Exceptions.
"""
import pytest

from domain.exceptions.script import ScriptNotFoundError, ScriptAlreadyExistsError
from domain.exceptions.base import DomainError


class TestScriptExceptions:

    def test_script_not_found_error(self):
        """ScriptNotFoundError debe tener code, status_code y message correctos."""
        err = ScriptNotFoundError(topic_id="topic-123")
        assert err.code == "SCRIPT_NOT_FOUND"
        assert err.status_code == 404
        assert "topic-123" in err.detail
        assert isinstance(err, DomainError)

    def test_script_not_found_default_detail(self):
        """Detail por defecto debe ser informativo."""
        err = ScriptNotFoundError(topic_id="abc-123")
        assert "abc-123" in err.detail
        assert "no se encontr" in err.detail.lower()

    def test_script_not_found_custom_detail(self):
        """Debe aceptar detail personalizado."""
        err = ScriptNotFoundError(topic_id="abc", detail="Custom detail")
        assert err.detail == "Custom detail"

    def test_script_already_exists_error(self):
        """ScriptAlreadyExistsError debe tener code, status_code y message correctos."""
        err = ScriptAlreadyExistsError(topic_id="topic-123")
        assert err.code == "SCRIPT_ALREADY_EXISTS"
        assert err.status_code == 409
        assert "topic-123" in err.detail
        assert isinstance(err, DomainError)

    def test_script_already_exists_message(self):
        """Mensaje debe mencionar regenerate."""
        err = ScriptAlreadyExistsError(topic_id="abc")
        assert "regenerate" in err.detail.lower()

    def test_script_already_exists_custom_detail(self):
        """Debe aceptar detail personalizado."""
        err = ScriptAlreadyExistsError(topic_id="abc", detail="Overwrite")
        assert err.detail == "Overwrite"
