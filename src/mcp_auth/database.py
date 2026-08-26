from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class NotesDatabase:
    def __init__(self, path: Path) -> None:
        self.path = path

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS notes (
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
                "CREATE INDEX IF NOT EXISTS notes_owner_id_id ON notes(owner_id, id)"
            )

    def create(self, owner_id: str, title: str, body: str = "") -> dict[str, Any]:
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO notes(owner_id, title, body) VALUES (?, ?, ?)",
                (owner_id, title, body),
            )
            return self.get(owner_id, cursor.lastrowid, connection=connection)

    def list(self, owner_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, title, body, created_at, updated_at FROM notes "
                "WHERE owner_id = ? ORDER BY id",
                (owner_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get(
        self,
        owner_id: str,
        note_id: int,
        *,
        connection: sqlite3.Connection | None = None,
    ) -> dict[str, Any]:
        owns_connection = connection is None
        connection = connection or self._connect()
        try:
            row = connection.execute(
                "SELECT id, title, body, created_at, updated_at FROM notes "
                "WHERE owner_id = ? AND id = ?",
                (owner_id, note_id),
            ).fetchone()
        finally:
            if owns_connection:
                connection.close()
        if row is None:
            raise KeyError(f"Note {note_id} not found")
        return dict(row)

    def update(
        self,
        owner_id: str,
        note_id: int,
        title: str | None = None,
        body: str | None = None,
    ) -> dict[str, Any]:
        if title is None and body is None:
            raise ValueError("Provide title, body, or both")
        with self._connect() as connection:
            existing = self.get(owner_id, note_id, connection=connection)
            connection.execute(
                "UPDATE notes SET title = ?, body = ?, updated_at = CURRENT_TIMESTAMP "
                "WHERE owner_id = ? AND id = ?",
                (title if title is not None else existing["title"],
                 body if body is not None else existing["body"], owner_id, note_id),
            )
            return self.get(owner_id, note_id, connection=connection)

    def delete(self, owner_id: str, note_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM notes WHERE owner_id = ? AND id = ?", (owner_id, note_id)
            )
        return cursor.rowcount == 1

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection
