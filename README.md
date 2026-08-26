# Stytch-authenticated SQLite MCP

A deliberately small remote MCP service for learning the shape of a SaaS integration:

- FastMCP serves six tools over Streamable HTTP.
- Stytch Connected Apps handles OAuth 2.1 discovery, Dynamic Client Registration, PKCE,
  browser login, consent, and token issuance.
- The service validates every access token's signature, issuer, audience, expiry, and `openid`
  scope against Stytch's rotating JWKS.
- SQLite rows are keyed by the token's `sub`, so each Stytch user sees only their own notes.
- Access is capped at 30 minutes by the server, even if a Stytch client is accidentally configured
  with a longer access-token lifetime.
- The Claude Code plugin runs a pinned `mcp-remote` bridge, which performs OAuth and connects Claude
  Code to the remote MCP endpoint.

## Architecture

```text
Claude Code plugin -> http(s)://MCP/mcp -> validate Stytch JWT -> per-user SQLite CRUD
         |                                      ^
         +-> Stytch discovery -> browser login/consent app -> Stytch token endpoint
```

The browser app is necessary. Stytch hosts discovery, registration, and token endpoints, while your
application hosts the `IdentityProvider` component used for login and consent.

## 1. Configure Stytch

Create a **Consumer Authentication** project, then configure:

1. In **Frontend SDK**, enable the SDK and authorize `http://localhost:3000`.
2. In **Redirect URLs**, add `http://localhost:3000/authenticate` for both login and signup.
3. Enable **Email Magic Links** with Login or Create.
4. In **Connected Apps**, set the Authorization URL to
   `http://localhost:3000/oauth/authorize`.
5. Enable **Dynamic Client Registration**. The MCP client uses DCR because its callback port can
   vary.
6. Set the Connected Apps access-token expiry to **30 minutes** where Stytch permits it.

The service and plugin request only `openid`, because the MCP server needs only the stable `sub`
identifier. It does not need profile or email data.

The server rejects every access token 30 minutes after that token's `iat`. The plugin uses the
pinned `mcp-remote@0.2.1` bridge, which requests the scopes advertised by the MCP protected resource
without adding `offline_access`. Stytch therefore does not issue a refresh token, and expiration
returns the user to interactive authorization.

This bridge is intentional. Native Claude Code OAuth automatically adds `offline_access` when the
authorization server advertises it, allowing silent token refresh and defeating the forced-login
requirement.

Copy `.env.example` to `.env` and set:

- `STYTCH_PROJECT_ID`: the `project-test-...` project ID, used as JWT audience.
- `STYTCH_DOMAIN`: the full project domain shown by Stytch, such as
  `https://...customers.stytch.dev`, used as issuer and JWKS host. Do not use the API secret or
  public token here.
- `STYTCH_PUBLIC_TOKEN`: the browser-safe `public-token-test-...` value used by the login and
  consent UI.
- `MCP_BASE_URL`: externally visible origin of the MCP server, without `/mcp`.

No Stytch secret key belongs in this project. JWT verification only needs public signing keys.

After saving the dashboard configuration, verify Stytch discovery and signing keys:

```bash
set -a; source .env; set +a
uv run python scripts/check_stytch.py
```

Do not continue to the browser login test until this prints
`PASS: Stytch authorization metadata and JWKS are ready for MCP OAuth.`

## 2. Run locally

```bash
uv sync
set -a; source .env; set +a
uv run mcp-auth
```

In another terminal:

```bash
cd web
npm install
npm run dev
```

For a true OAuth test, both the MCP endpoint and authorization page should normally be reachable at
stable HTTPS URLs. A development tunnel can publish ports 8000 and 3000. Update `MCP_BASE_URL`, the
Stytch Frontend SDK authorized environment and redirect URL, the Connected Apps Authorization URL,
and `SQLITE_NOTES_MCP_URL` to those HTTPS URLs. The plain localhost setup is useful while building,
but production must use HTTPS.

## 3. Install and authenticate the Claude Code plugin

From the repository root, register the local marketplace and install the plugin for this project:

```bash
claude plugin marketplace add "$PWD" --scope project
claude plugin install sqlite-notes@mcp-auth-local --scope project
```

The local server URL defaults to `http://127.0.0.1:8000/mcp`. For a hosted or tunneled server, set
the URL before starting Claude Code:

```bash
export SQLITE_NOTES_MCP_URL=https://your-mcp-tunnel.example/mcp
```

Then run `/reload-plugins`, open `/mcp`, and select `sqlite-notes`. The pinned `mcp-remote` bridge
discovers the Stytch authorization server through the MCP server, registers itself, opens the
browser, uses PKCE, and returns with an access token.

Try prompts such as:

- "Create a note titled Grocery list with body coffee and oranges."
- "List my notes."
- "Update note 1 to add milk."
- "Delete note 1."

After 30 minutes the MCP server rejects the current access token. Because the bridge does not
request `offline_access`, it cannot silently refresh and must repeat interactive authorization.

## Tests

```bash
uv run pytest
cd web && npm run build
```

The automated tests cover CRUD and cross-user isolation plus the 30-minute access-token boundary.
A complete login cannot be automated without a configured Stytch project and an email inbox, so the
browser flow is an explicit manual end-to-end check.

## Production notes

SQLite and a single process are intentional for this exercise. For a paid multi-instance service,
use a managed database, migrations, backups, HTTPS, structured audit logs, rate limits, and explicit
authorization scopes. Keep the same boundary: Stytch authenticates the user, while your database and
service decide which rows and actions that user may access.
