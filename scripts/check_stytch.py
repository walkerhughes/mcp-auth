from __future__ import annotations

import asyncio
import os
import sys

import httpx


async def check() -> int:
    domain = os.getenv("STYTCH_DOMAIN", "").rstrip("/")
    project_id = os.getenv("STYTCH_PROJECT_ID", "")
    if not domain or not project_id:
        print("Source .env first: set -a; source .env; set +a", file=sys.stderr)
        return 2

    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        metadata_response, jwks_response = await asyncio.gather(
            client.get(f"{domain}/.well-known/oauth-authorization-server"),
            client.get(f"{domain}/.well-known/jwks.json"),
        )

    failures: list[str] = []
    if metadata_response.status_code != 200:
        try:
            error = metadata_response.json()
            detail = error.get("error_message") or error.get("error_type")
        except ValueError:
            detail = metadata_response.text[:200]
        failures.append(
            f"authorization metadata returned {metadata_response.status_code}: {detail}"
        )
    else:
        metadata = metadata_response.json()
        required_fields = {
            "authorization_endpoint",
            "registration_endpoint",
            "token_endpoint",
        }
        missing = sorted(required_fields - metadata.keys())
        if missing:
            failures.append(f"authorization metadata is missing: {', '.join(missing)}")
        if "S256" not in metadata.get("code_challenge_methods_supported", []):
            failures.append("authorization server does not advertise PKCE S256")
        advertised_scopes = set(metadata.get("scopes_supported", []))
        if "openid" not in advertised_scopes:
            failures.append("authorization server does not advertise openid")
        if "offline_access" in advertised_scopes:
            print(
                "NOTICE: Stytch advertises offline_access; Claude Code may refresh tokens "
                "without interactive login."
            )

    if jwks_response.status_code != 200:
        failures.append(f"JWKS returned {jwks_response.status_code}")
    else:
        keys = jwks_response.json().get("keys", [])
        if not any(key.get("kty") == "RSA" and key.get("alg") == "RS256" for key in keys):
            failures.append("JWKS contains no RS256 RSA signing key")

    if not project_id.startswith(("project-test-", "project-live-")):
        failures.append("STYTCH_PROJECT_ID has an unexpected format")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    print("PASS: Stytch authorization metadata and JWKS are ready for MCP OAuth.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(check()))
