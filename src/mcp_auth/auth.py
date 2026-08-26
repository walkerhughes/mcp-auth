from __future__ import annotations

import time

from fastmcp.server.auth import AccessToken, TokenVerifier


class MaximumTokenAgeVerifier(TokenVerifier):
    """Reject otherwise-valid JWTs once they are older than the service TTL."""

    def __init__(self, inner: TokenVerifier, max_age_seconds: int) -> None:
        super().__init__(required_scopes=inner.required_scopes)
        self.inner = inner
        self.max_age_seconds = max_age_seconds

    async def verify_token(self, token: str) -> AccessToken | None:
        access_token = await self.inner.verify_token(token)
        if access_token is None:
            return None

        issued_at = access_token.claims.get("iat")
        if not isinstance(issued_at, (int, float)):
            return None
        if issued_at > time.time() + 60:
            return None
        if time.time() - issued_at >= self.max_age_seconds:
            return None
        return access_token
