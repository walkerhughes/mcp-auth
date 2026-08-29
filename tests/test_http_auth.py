import asyncio
import json
from pathlib import Path

import httpx

from mcp_auth.config import Settings
from mcp_auth.server import create_server


def response_json(response: httpx.Response) -> dict[str, object]:
    if response.headers["content-type"].startswith("application/json"):
        return response.json()
    data = next(
        line for line in response.text.splitlines() if line.startswith("data: ")
    )
    return json.loads(data.removeprefix("data: "))


def test_streamable_http_initialize_and_list_tools(tmp_path: Path) -> None:
    settings = Settings(
        database_path=tmp_path / "notes.db",
    )

    async def exercise_server() -> None:
        app = create_server(settings).http_app(stateless_http=True)
        transport = httpx.ASGITransport(app=app)
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=transport, base_url="http://testserver"
            ) as client,
        ):
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
            assert response.status_code == 200
            initialize = response_json(response)
            assert initialize["result"]["serverInfo"]["name"] == "Horizon Notes"

            response = await client.post(
                "/mcp",
                headers={"accept": "application/json, text/event-stream"},
                json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            )
            assert response.status_code == 200
            tools = response_json(response)
            assert {tool["name"] for tool in tools["result"]["tools"]} == {
                "create_note",
                "list_notes",
                "get_note",
                "update_note",
                "delete_note",
            }

            response = await client.post(
                "/mcp",
                headers={"accept": "application/json, text/event-stream"},
                json={
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "create_note",
                        "arguments": {"title": "Horizon", "body": "Ready"},
                    },
                },
            )
            created = response_json(response)
            assert response.status_code == 200
            assert created["result"]["isError"] is False
            assert json.loads(created["result"]["content"][0]["text"])["title"] == (
                "Horizon"
            )

            response = await client.post(
                "/mcp",
                headers={"accept": "application/json, text/event-stream"},
                json={
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {"name": "list_notes", "arguments": {}},
                },
            )
            listed = response_json(response)
            assert response.status_code == 200
            assert (
                json.loads(listed["result"]["content"][0]["text"])[0]["body"] == "Ready"
            )

    asyncio.run(exercise_server())
