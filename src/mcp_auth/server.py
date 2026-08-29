from __future__ import annotations

from fastmcp import FastMCP

from .config import Settings
from .database import NotesDatabase, PostgresNotesDatabase


def create_server(settings: Settings) -> FastMCP:
    database = (
        PostgresNotesDatabase(settings.database_url)
        if settings.database_url
        else NotesDatabase(settings.database_path)
    )
    database.initialize()

    mcp = FastMCP(
        name="Horizon Notes",
        instructions=(
            "A small shared notes service. Prefect Horizon authenticates and authorizes "
            "access to the deployed MCP endpoint."
        ),
    )

    @mcp.tool
    def create_note(title: str, body: str = "") -> dict[str, object]:
        """Create a note in the shared workspace."""
        return database.create(title, body)

    @mcp.tool
    def list_notes() -> list[dict[str, object]]:
        """List every note in the shared workspace."""
        return database.list()

    @mcp.tool
    def get_note(note_id: int) -> dict[str, object]:
        """Get one note by numeric ID."""
        return database.get(note_id)

    @mcp.tool
    def update_note(
        note_id: int, title: str | None = None, body: str | None = None
    ) -> dict[str, object]:
        """Update the title, body, or both for a note."""
        return database.update(note_id, title, body)

    @mcp.tool
    def delete_note(note_id: int) -> bool:
        """Delete a note. Returns false when it does not exist."""
        return database.delete(note_id)

    return mcp


mcp = create_server(Settings.from_env())


def main() -> None:
    settings = Settings.from_env()
    mcp.run(
        transport="http",
        host=settings.host,
        port=settings.port,
        show_banner=True,
        stateless_http=True,
    )


if __name__ == "__main__":
    main()
