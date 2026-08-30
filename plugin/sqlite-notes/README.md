# Horizon Notes Claude Code plugin

This plugin contains a pinned `mcp-remote@0.2.1` bridge to the hosted MCP connection. It contains
no credentials. The bridge discovers and completes the OAuth flow exposed by Prefect Horizon.

Set `SQLITE_NOTES_MCP_URL` to the URL shown by Horizon before launching Claude Code. Then install
the plugin, open `/mcp`, select `sqlite-notes`, and authenticate in the browser.

For local development, leave the variable unset to use `http://127.0.0.1:8000/mcp`.
