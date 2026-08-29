from mcp_auth.config import Settings


def test_database_url_is_optional(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert Settings.from_env().database_url is None


def test_database_url_comes_from_the_environment(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://supabase")
    assert Settings.from_env().database_url == "postgresql://supabase"
