import asyncio
from pathlib import Path

import httpx

from mcp_auth.config import Settings
from mcp_auth.server import create_server


def test_oauth_discovery_and_unauthenticated_rejection(tmp_path: Path) -> None:
    settings = Settings(
        stytch_project_id="project-test-example",
        stytch_domain="https://example.customers.stytch.com",
        base_url="http://127.0.0.1:8000",
        database_path=tmp_path / "notes.db",
    )

    async def exercise_server() -> None:
        app = create_server(settings).http_app()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url=settings.base_url
        ) as client:
            metadata = await client.get("/.well-known/oauth-protected-resource/mcp")
            assert metadata.status_code == 200
            assert metadata.json() == {
                "resource": "http://127.0.0.1:8000/mcp",
                "authorization_servers": ["https://example.customers.stytch.com/"],
                "scopes_supported": ["openid"],
                "bearer_methods_supported": ["header"],
            }

            response = await client.post(
                "/mcp",
                headers={"accept": "application/json, text/event-stream"},
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1"},
                    },
                },
            )
            assert response.status_code == 401
            assert "resource_metadata=" in response.headers["www-authenticate"]

    asyncio.run(exercise_server())
