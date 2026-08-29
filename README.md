# Horizon Notes MCP

A small FastMCP notes server prepared for deployment on [Prefect Horizon](https://www.prefect.io/horizon/deploy),
with a production Supabase Postgres database managed by Pulumi.

Horizon owns the public deployment boundary: GitHub builds, TLS, OAuth, access control, scaling,
preview environments, and request observability. The repository only owns the MCP tools and their
application data.

```text
MCP client -> Horizon OAuth gateway -> FastMCP server -> Supabase Postgres
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

4. Provision Supabase by following [`infra/README.md`](infra/README.md), then add the secret Pulumi
   `databaseUrl` output to Horizon as `DATABASE_URL`.
5. Deploy the server. Horizon detects `pyproject.toml`, installs the Python dependencies,
   and publishes an endpoint such as `https://horizon-notes.fastmcp.app/mcp`.
6. Test every tool in Horizon Inspector or ChatMCP before connecting another client.

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

The MCP endpoint is `http://127.0.0.1:8000/mcp`. Without `DATABASE_URL`, local development falls
back to SQLite at `MCP_DATABASE_PATH`. Optional variables are documented in `.env.example`.

Verify the exact object Horizon imports:

```bash
uv run fastmcp inspect server.py:mcp
```

## Test

```bash
uv run pytest
```

## Environment variables

- `DATABASE_URL`: secret Supabase transaction-pooler URL used by the deployed MCP.
- `FASTMCP_STATELESS_HTTP=true`: enables stateless HTTP for Horizon autoscaling.
- `MCP_DATABASE_PATH`: optional SQLite path for local development only.
- `MCP_HOST` and `MCP_PORT`: optional local server bind settings.

Pulumi itself uses `SUPABASE_ACCESS_TOKEN` and usually `PULUMI_ACCESS_TOKEN`; neither belongs in
Horizon. `SUPABASE_URL`, anon keys, and service-role keys are not needed because the service uses a
direct Postgres connection.

## Data boundary

Production notes live in the private `horizon_notes` Postgres schema, outside Supabase's default
Data API schemas. The MCP creates the schema and table idempotently at startup. Local SQLite remains
available only as a zero-configuration development fallback.

Horizon authentication protects the MCP endpoint. It does not by itself make rows private to each
user, so this server correctly describes the notes as shared.
