# Horizon Notes MCP

A small FastMCP notes server prepared for deployment on [Prefect Horizon](https://www.prefect.io/horizon/deploy).

Horizon owns the public deployment boundary: GitHub builds, TLS, OAuth, access control, scaling,
preview environments, and request observability. The repository only owns the MCP tools and their
application data.

```text
MCP client -> Horizon OAuth gateway -> FastMCP server -> SQLite
```

The five tools create, list, read, update, and delete notes in one shared workspace. Horizon decides
who can reach that workspace. The server deliberately does not trust undocumented identity headers
or pretend that gateway users map to application-level note owners.

## Deploy on Horizon

1. Push this repository to GitHub.
2. Sign in at [horizon.prefect.io](https://horizon.prefect.io) and connect the GitHub repository.
3. Create a server with these values:

   - Server name: `horizon-notes` or another available name
   - Entrypoint: `server.py:mcp`
   - Authentication: enabled
   - Environment variable: `FASTMCP_STATELESS_HTTP=true`

4. Deploy the server. Horizon detects `pyproject.toml`, installs the Python dependencies,
   and publishes an endpoint such as `https://horizon-notes.fastmcp.app/mcp`.
5. Test every tool in Horizon Inspector or ChatMCP before connecting another client.

Every push to the configured production branch triggers a deployment. Pull requests receive preview
deployments, so this branch can be pushed and opened as a PR before it is merged.

## Connect a client

Use the connection snippet produced by Horizon. For the included Claude Code plugin:

```bash
export SQLITE_NOTES_MCP_URL=https://your-server-name.fastmcp.app/mcp
claude plugin marketplace add "$PWD" --scope project
claude plugin install sqlite-notes@mcp-auth-local --scope project
```

Open `/mcp`, choose `sqlite-notes`, and complete the Horizon sign-in flow.

## Run locally

Local HTTP mode intentionally has no authentication. It is for development on loopback only.

```bash
uv sync
uv run horizon-notes
```

The MCP endpoint is `http://127.0.0.1:8000/mcp`. Optional environment variables are documented in
`.env.example`.

Verify the exact object Horizon imports:

```bash
uv run fastmcp inspect server.py:mcp
```

## Test

```bash
uv run pytest
```

## Persistence boundary

SQLite keeps this demo easy to understand, but the default `/tmp/horizon-notes/notes.db` file is
ephemeral on a scale-to-zero deployment and is not shared by multiple instances. Do not use it for
durable production data. Before relying on stored notes, replace `NotesDatabase` with a managed,
network-accessible database and add migrations, backups, connection pooling, and application-level
tenant authorization.

Horizon authentication protects the MCP endpoint. It does not by itself make rows private to each
user, so this server correctly describes the notes as shared.
