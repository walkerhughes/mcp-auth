import asyncio
import time

from fastmcp.server.auth import AccessToken, TokenVerifier

from mcp_auth.auth import MaximumTokenAgeVerifier


class FakeVerifier(TokenVerifier):
    def __init__(self, issued_at: float | None) -> None:
        super().__init__(required_scopes=["openid"])
        self.issued_at = issued_at

    async def verify_token(self, token: str) -> AccessToken | None:
        claims = {} if self.issued_at is None else {"iat": self.issued_at}
        return AccessToken(token=token, client_id="client", scopes=["openid"], claims=claims)


def test_rejects_token_at_30_minute_boundary() -> None:
    verifier = MaximumTokenAgeVerifier(FakeVerifier(time.time() - 1800), 1800)
    assert asyncio.run(verifier.verify_token("token")) is None


def test_accepts_fresh_token() -> None:
    verifier = MaximumTokenAgeVerifier(FakeVerifier(time.time()), 1800)
    assert asyncio.run(verifier.verify_token("token")) is not None
