from pathlib import Path

import pytest

from mcp_auth.database import NotesDatabase


@pytest.fixture
def database(tmp_path: Path) -> NotesDatabase:
    db = NotesDatabase(tmp_path / "notes.db")
    db.initialize()
    return db


def test_crud_round_trip(database: NotesDatabase) -> None:
    created = database.create("user-a", "First", "Hello")
    assert created["title"] == "First"
    assert database.list("user-a") == [created]

    updated = database.update("user-a", created["id"], body="Updated")
    assert updated["title"] == "First"
    assert updated["body"] == "Updated"
    assert database.delete("user-a", created["id"]) is True
    assert database.list("user-a") == []


def test_notes_are_isolated_by_authenticated_owner(database: NotesDatabase) -> None:
    created = database.create("user-a", "Private")
    assert database.list("user-b") == []
    with pytest.raises(KeyError):
        database.get("user-b", created["id"])
    assert database.delete("user-b", created["id"]) is False
    assert database.get("user-a", created["id"])["title"] == "Private"
