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
            columns = connection.execute("PRAGMA table_info(notes)").fetchall()
            if any(column["name"] == "owner_id" for column in columns):
                self._migrate_stytch_schema(connection)
            self._create_schema(connection)

    @staticmethod
    def _create_schema(connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    @classmethod
    def _migrate_stytch_schema(cls, connection: sqlite3.Connection) -> None:
        connection.execute("ALTER TABLE notes RENAME TO notes_stytch")
        cls._create_schema(connection)
        connection.execute(
            """
            INSERT INTO notes(id, title, body, created_at, updated_at)
            SELECT id, title, body, created_at, updated_at FROM notes_stytch
            """
        )
        connection.execute("DROP TABLE notes_stytch")

    def create(self, title: str, body: str = "") -> dict[str, Any]:
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO notes(title, body) VALUES (?, ?)",
                (title, body),
            )
            return self.get(cursor.lastrowid, connection=connection)

    def list(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, title, body, created_at, updated_at FROM notes ORDER BY id"
            ).fetchall()
        return [dict(row) for row in rows]

    def get(
        self,
        note_id: int,
        *,
        connection: sqlite3.Connection | None = None,
    ) -> dict[str, Any]:
        owns_connection = connection is None
        connection = connection or self._connect()
        try:
            row = connection.execute(
                "SELECT id, title, body, created_at, updated_at FROM notes WHERE id = ?",
                (note_id,),
            ).fetchone()
        finally:
            if owns_connection:
                connection.close()
        if row is None:
            raise KeyError(f"Note {note_id} not found")
        return dict(row)

    def update(
        self,
        note_id: int,
        title: str | None = None,
        body: str | None = None,
    ) -> dict[str, Any]:
        if title is None and body is None:
            raise ValueError("Provide title, body, or both")
        with self._connect() as connection:
            existing = self.get(note_id, connection=connection)
            connection.execute(
                "UPDATE notes SET title = ?, body = ?, updated_at = CURRENT_TIMESTAMP "
                "WHERE id = ?",
                (
                    title if title is not None else existing["title"],
                    body if body is not None else existing["body"],
                    note_id,
                ),
            )
            return self.get(note_id, connection=connection)

    def delete(self, note_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        return cursor.rowcount == 1

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode = WAL")
        return connection
