# SQLite Notes Claude Code plugin

This plugin contains a pinned `mcp-remote@0.2.1` bridge to the hosted MCP connection. It
intentionally contains no credentials. The bridge performs OAuth discovery, Dynamic Client
Registration, PKCE, the browser callback, and token storage on the user's machine.

The bridge is used because it requests only the scopes advertised by the MCP protected resource.
It does not automatically add `offline_access`, so an expired access token requires interactive
authorization again.

After installing it, open `/mcp`, select `sqlite-notes`, and authenticate in the browser.

Set `SQLITE_NOTES_MCP_URL` before launching Claude Code when the service is not running at
`http://127.0.0.1:8000/mcp`.
