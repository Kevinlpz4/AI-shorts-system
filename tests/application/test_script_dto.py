"""
Tests para Script DTOs (application/dtos/script.py).
"""
import pytest

from application.dtos.script import ScriptDTO, GenerateScriptRequest
from domain.entities.script import Script
from domain.value_objects.duration import Duration


class TestScriptDTO:

    def test_from_entity_with_valid_script(self):
        """ScriptDTO.from_entity debe convertir correctamente un Script válido."""
        script = Script(
            topic_id="topic-1",
            hook="Un hook largo que cumple el mínimo",
            body="x" * 50,
            cta="seguime",
            duration=Duration(60),
            tone="humor",
            format="list",
        )
        dto = ScriptDTO.from_entity(script)

        assert dto.id == script.id
        assert dto.topic_id == "topic-1"
        assert dto.hook == "Un hook largo que cumple el mínimo"
        assert dto.body == "x" * 50
        assert dto.cta == "seguime"
        assert dto.duration == 60
        assert dto.tone == "humor"
        assert dto.format == "list"
        assert dto.is_valid is True
        assert dto.word_count > 0
        assert dto.created_at is not None
        assert dto.updated_at is not None

    def test_from_entity_with_invalid_script(self):
        """ScriptDTO.from_entity debe reflejar script inválido."""
        script = Script(
            topic_id="topic-2",
            hook="corto",
            body="x" * 50,
            cta="seguime",
        )
        dto = ScriptDTO.from_entity(script)

        assert dto.is_valid is False
        assert dto.id == script.id

    def test_from_entity_pure_function(self):
        """from_entity debe ser función pura: mismo input → mismo output."""
        script = Script(
            topic_id="topic-3",
            hook="Hook largo suficiente",
            body="x" * 50,
            cta="seguime",
        )
        dto1 = ScriptDTO.from_entity(script)
        dto2 = ScriptDTO.from_entity(script)

        assert dto1.id == dto2.id
        assert dto1.is_valid == dto2.is_valid
        assert dto1.word_count == dto2.word_count

    def test_from_entity_with_topic_id_empty(self):
        """topic_id vacío debe funcionar (caso de entidad sin asociar)."""
        script = Script(
            hook="Hook largo válido",
            body="x" * 50,
            cta="seguime",
        )
        dto = ScriptDTO.from_entity(script)
        assert dto.topic_id == ""


class TestGenerateScriptRequest:

    def test_defaults(self):
        """GenerateScriptRequest debe tener valores por defecto."""
        req = GenerateScriptRequest(topic_id="topic-1")
        assert req.topic_id == "topic-1"
        assert req.duration == 45
        assert req.tone == "educational"

    def test_custom_values(self):
        """GenerateScriptRequest debe aceptar valores personalizados."""
        req = GenerateScriptRequest(topic_id="topic-2", duration=60, tone="humor")
        assert req.topic_id == "topic-2"
        assert req.duration == 60
        assert req.tone == "humor"

    def test_mutable_fields(self):
        """Los campos deben ser mutables (dataclass)."""
        req = GenerateScriptRequest(topic_id="topic-1")
        req.duration = 90
        req.tone = "dramatic"
        assert req.duration == 90
        assert req.tone == "dramatic"
