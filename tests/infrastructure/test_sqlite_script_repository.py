"""
Tests para SQLiteScriptRepository.
"""
import sqlite3
import pytest
from uuid import uuid4

from infrastructure.persistence.sqlite_script_repository import SQLiteScriptRepository
from domain.entities.script import Script
from domain.value_objects.duration import Duration


def _ensure_topic(conn: sqlite3.Connection, topic_id: str) -> None:
    """Crea un research_topic dummy para satisfacer FK constraints."""
    conn.execute(
        "INSERT OR IGNORE INTO research_topics (id, title) VALUES (?, ?)",
        (topic_id, f"Test topic {topic_id}"),
    )
    conn.commit()


@pytest.fixture
def sqlite_script_repo(tmp_path):
    """Repositorio SQLite en archivo temporal con research_topics creada."""
    db_path = str(tmp_path / "test_scripts.db")

    # Crear la tabla research_topics para FK
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS research_topics (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'pending_review'
        )
    """)
    conn.commit()
    conn.close()

    return SQLiteScriptRepository(db_path=db_path)


class TestSQLiteScriptRepository:

    @pytest.mark.asyncio
    async def test_save_and_find_by_topic_id(self, sqlite_script_repo):
        """Guardar y recuperar un script por topic_id."""
        topic_id = "topic-1"
        # Crear research_topic dummy
        conn = sqlite3.connect(sqlite_script_repo._db_path)
        conn.execute("PRAGMA foreign_keys=ON")
        _ensure_topic(conn, topic_id)
        conn.close()

        script = Script(
            topic_id=topic_id,
            hook="Un hook largo que cumple el mínimo",
            body="x" * 50,
            cta="seguime ahora",
        )
        await sqlite_script_repo.save(script)

        retrieved = await sqlite_script_repo.find_by_topic_id(topic_id)
        assert retrieved is not None
        assert retrieved.id == script.id
        assert retrieved.topic_id == topic_id
        assert retrieved.hook == "Un hook largo que cumple el mínimo"
        assert retrieved.body == "x" * 50
        assert retrieved.cta == "seguime ahora"

    @pytest.mark.asyncio
    async def test_find_by_topic_id_not_found(self, sqlite_script_repo):
        """Buscar un topic_id que no existe debe retornar None."""
        result = await sqlite_script_repo.find_by_topic_id("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_save_and_update(self, sqlite_script_repo):
        """Guardar el mismo topic_id dos veces debe actualizarlo (upsert)."""
        topic_id = "topic-update"
        conn = sqlite3.connect(sqlite_script_repo._db_path)
        conn.execute("PRAGMA foreign_keys=ON")
        _ensure_topic(conn, topic_id)
        conn.close()

        script = Script(
            topic_id=topic_id,
            hook="Hook original largo válido",
            body="x" * 50,
            cta="seguime",
        )
        await sqlite_script_repo.save(script)

        # Modificar
        script.hook = "Hook actualizado largo válido"
        script.body = "y" * 50
        await sqlite_script_repo.save(script)

        retrieved = await sqlite_script_repo.find_by_topic_id(topic_id)
        assert retrieved.hook == "Hook actualizado largo válido"
        assert retrieved.body == "y" * 50

    @pytest.mark.asyncio
    async def test_delete_by_topic_id(self, sqlite_script_repo):
        """Eliminar un script por topic_id."""
        topic_id = "topic-delete"
        conn = sqlite3.connect(sqlite_script_repo._db_path)
        conn.execute("PRAGMA foreign_keys=ON")
        _ensure_topic(conn, topic_id)
        conn.close()

        script = Script(
            topic_id=topic_id,
            hook="Hook largo para eliminar",
            body="x" * 50,
            cta="seguime",
        )
        await sqlite_script_repo.save(script)

        # Verificar que existe
        assert await sqlite_script_repo.find_by_topic_id(topic_id) is not None

        # Eliminar
        await sqlite_script_repo.delete_by_topic_id(topic_id)
        assert await sqlite_script_repo.find_by_topic_id(topic_id) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, sqlite_script_repo):
        """Eliminar un topic_id que no existe no debe lanzar error."""
        await sqlite_script_repo.delete_by_topic_id("no-existe")
        # No debe lanzar excepción

    @pytest.mark.asyncio
    async def test_save_preserves_duration(self, sqlite_script_repo):
        """Guardar debe preservar duración."""
        topic_id = "topic-duration"
        conn = sqlite3.connect(sqlite_script_repo._db_path)
        conn.execute("PRAGMA foreign_keys=ON")
        _ensure_topic(conn, topic_id)
        conn.close()

        script = Script(
            topic_id=topic_id,
            hook="Hook largo válido para pruebas",
            body="x" * 50,
            cta="seguime",
            duration=Duration(90),
        )
        await sqlite_script_repo.save(script)

        retrieved = await sqlite_script_repo.find_by_topic_id(topic_id)
        assert int(retrieved.duration) == 90

    @pytest.mark.asyncio
    async def test_save_preserves_tone_and_format(self, sqlite_script_repo):
        """Guardar debe preservar tone y format."""
        topic_id = "topic-style"
        conn = sqlite3.connect(sqlite_script_repo._db_path)
        conn.execute("PRAGMA foreign_keys=ON")
        _ensure_topic(conn, topic_id)
        conn.close()

        script = Script(
            topic_id=topic_id,
            hook="Hook largo válido para pruebas",
            body="x" * 50,
            cta="seguime",
            tone="humor",
            format="list",
        )
        await sqlite_script_repo.save(script)

        retrieved = await sqlite_script_repo.find_by_topic_id(topic_id)
        assert retrieved.tone == "humor"
        assert retrieved.format == "list"

    @pytest.mark.asyncio
    async def test_multiple_topics_independent(self, sqlite_script_repo):
        """Múltiples scripts deben ser independientes."""
        conn = sqlite3.connect(sqlite_script_repo._db_path)
        conn.execute("PRAGMA foreign_keys=ON")
        _ensure_topic(conn, "t1")
        _ensure_topic(conn, "t2")
        conn.close()

        s1 = Script(topic_id="t1", hook="Hook largo valido uno", body="x" * 50, cta="seguime")
        s2 = Script(topic_id="t2", hook="Hook largo valido dos", body="y" * 50, cta="seguime")

        await sqlite_script_repo.save(s1)
        await sqlite_script_repo.save(s2)

        r1 = await sqlite_script_repo.find_by_topic_id("t1")
        r2 = await sqlite_script_repo.find_by_topic_id("t2")

        assert r1.id == s1.id
        assert r2.id == s2.id
        assert r1.id != r2.id

    @pytest.mark.asyncio
    async def test_save_preserves_timestamps(self, sqlite_script_repo):
        """Guardar debe preservar created_at y actualizar updated_at."""
        topic_id = "topic-ts"
        conn = sqlite3.connect(sqlite_script_repo._db_path)
        conn.execute("PRAGMA foreign_keys=ON")
        _ensure_topic(conn, topic_id)
        conn.close()

        import datetime as dt_module
        fixed_ts = "2026-01-01T00:00:00"
        script = Script(
            topic_id=topic_id,
            hook="Hook largo con timestamp",
            body="x" * 50,
            cta="seguime",
            created_at=fixed_ts,
            updated_at=fixed_ts,
        )
        await sqlite_script_repo.save(script)

        retrieved = await sqlite_script_repo.find_by_topic_id(topic_id)
        assert retrieved.created_at == fixed_ts
        # updated_at debe haberse actualizado
        assert retrieved.updated_at != fixed_ts
        assert retrieved.updated_at > fixed_ts

    @pytest.mark.asyncio
    async def test_fk_cascade_deletes_script(self, sqlite_script_repo):
        """Eliminar research_topic debe eliminar script en cascada."""
        topic_id = "topic-cascade"
        conn = sqlite3.connect(sqlite_script_repo._db_path)
        conn.execute("PRAGMA foreign_keys=ON")
        _ensure_topic(conn, topic_id)
        conn.close()

        script = Script(
            topic_id=topic_id,
            hook="Hook cascade test",
            body="x" * 50,
            cta="seguime",
        )
        await sqlite_script_repo.save(script)
        assert await sqlite_script_repo.find_by_topic_id(topic_id) is not None

        # Eliminar el research_topic (cascade debe borrar el script)
        conn = sqlite3.connect(sqlite_script_repo._db_path)
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("DELETE FROM research_topics WHERE id = ?", (topic_id,))
        conn.commit()
        conn.close()

        assert await sqlite_script_repo.find_by_topic_id(topic_id) is None
