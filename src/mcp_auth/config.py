from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


@dataclass(frozen=True)
class Settings:
    stytch_project_id: str
    stytch_domain: str
    base_url: str
    database_path: Path
    host: str = "127.0.0.1"
    port: int = 8000
    token_ttl_seconds: int = 30 * 60

    @classmethod
    def from_env(cls) -> "Settings":
        project_id = os.getenv("STYTCH_PROJECT_ID", "").strip()
        domain = os.getenv("STYTCH_DOMAIN", "").strip().rstrip("/")
        base_url = os.getenv("MCP_BASE_URL", "http://127.0.0.1:8000").strip().rstrip("/")
        missing = [
            name
            for name, value in (
                ("STYTCH_PROJECT_ID", project_id),
                ("STYTCH_DOMAIN", domain),
            )
            if not value
        ]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        if urlparse(domain).scheme != "https":
            raise ValueError("STYTCH_DOMAIN must be an https:// URL")
        if urlparse(base_url).scheme not in {"http", "https"}:
            raise ValueError("MCP_BASE_URL must be an http:// or https:// URL")

        return cls(
            stytch_project_id=project_id,
            stytch_domain=domain,
            base_url=base_url,
            database_path=Path(os.getenv("MCP_DATABASE_PATH", "./data/notes.db")),
            host=os.getenv("MCP_HOST", "127.0.0.1"),
            port=int(os.getenv("MCP_PORT", "8000")),
        )
