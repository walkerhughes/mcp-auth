import sqlite3
from pathlib import Path

import pytest

from mcp_auth.database import NotesDatabase, PostgresNotesDatabase


@pytest.fixture
def database(tmp_path: Path) -> NotesDatabase:
    db = NotesDatabase(tmp_path / "notes.db")
    db.initialize()
    return db


def test_crud_round_trip(database: NotesDatabase) -> None:
    created = database.create("First", "Hello")
    assert created["title"] == "First"
    assert database.list() == [created]

    updated = database.update(created["id"], body="Updated")
    assert updated["title"] == "First"
    assert updated["body"] == "Updated"
    assert database.delete(created["id"]) is True
    assert database.list() == []


def test_missing_note_is_not_accessible(database: NotesDatabase) -> None:
    created = database.create("A note")
    with pytest.raises(KeyError):
        database.get(created["id"] + 1)
    assert database.delete(created["id"] + 1) is False


def test_initialize_migrates_the_previous_stytch_schema(tmp_path: Path) -> None:
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            "INSERT INTO notes(owner_id, title, body) VALUES (?, ?, ?)",
            ("stytch-user", "Migrated", "Still here"),
        )

    database = NotesDatabase(path)
    database.initialize()

    assert database.list()[0]["title"] == "Migrated"
    with sqlite3.connect(path) as connection:
        columns = connection.execute("PRAGMA table_info(notes)").fetchall()
    assert "owner_id" not in {column[1] for column in columns}


def test_postgres_connection_disables_prepared_statements(monkeypatch) -> None:
    captured: dict[str, object] = {}
    sentinel = object()

    def fake_connect(database_url: str, **kwargs: object) -> object:
        captured["database_url"] = database_url
        captured.update(kwargs)
        return sentinel

    monkeypatch.setattr("mcp_auth.database.psycopg.connect", fake_connect)

    database = PostgresNotesDatabase("postgresql://example")

    assert database._connect() is sentinel
    assert captured["database_url"] == "postgresql://example"
    assert captured["connect_timeout"] == 10
    assert captured["prepare_threshold"] is None
