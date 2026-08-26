from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.server.auth import RemoteAuthProvider
from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.server.dependencies import get_access_token

from .auth import MaximumTokenAgeVerifier
from .config import Settings
from .database import NotesDatabase


def create_server(settings: Settings) -> FastMCP:
    database = NotesDatabase(settings.database_path)
    database.initialize()

    stytch_verifier = JWTVerifier(
        jwks_uri=f"{settings.stytch_domain}/.well-known/jwks.json",
        issuer=settings.stytch_domain,
        audience=settings.stytch_project_id,
        algorithm="RS256",
        required_scopes=["openid"],
    )
    auth = RemoteAuthProvider(
        token_verifier=MaximumTokenAgeVerifier(
            stytch_verifier, max_age_seconds=settings.token_ttl_seconds
        ),
        authorization_servers=[settings.stytch_domain],
        base_url=settings.base_url,
        scopes_supported=["openid"],
    )
    mcp = FastMCP(
        name="Authenticated SQLite Notes",
        instructions=(
            "A learning service for private notes. Every note is isolated by the "
            "authenticated Stytch user ID."
        ),
        auth=auth,
    )

    def owner_id() -> str:
        token = get_access_token()
        subject = token.claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise ValueError("The access token has no valid subject")
        return subject

    @mcp.tool
    def whoami() -> dict[str, object]:
        """Return the authenticated Stytch identity and granted scopes."""
        token = get_access_token()
        return {"user_id": owner_id(), "scopes": token.scopes}

    @mcp.tool
    def create_note(title: str, body: str = "") -> dict[str, object]:
        """Create a private note owned by the authenticated user."""
        return database.create(owner_id(), title, body)

    @mcp.tool
    def list_notes() -> list[dict[str, object]]:
        """List all private notes owned by the authenticated user."""
        return database.list(owner_id())

    @mcp.tool
    def get_note(note_id: int) -> dict[str, object]:
        """Get one private note by numeric ID."""
        return database.get(owner_id(), note_id)

    @mcp.tool
    def update_note(
        note_id: int, title: str | None = None, body: str | None = None
    ) -> dict[str, object]:
        """Update the title, body, or both for a private note."""
        return database.update(owner_id(), note_id, title, body)

    @mcp.tool
    def delete_note(note_id: int) -> bool:
        """Delete a private note. Returns false when it does not exist."""
        return database.delete(owner_id(), note_id)

    return mcp


def main() -> None:
    settings = Settings.from_env()
    create_server(settings).run(
        transport="http", host=settings.host, port=settings.port, show_banner=True
    )


if __name__ == "__main__":
    main()
