from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit


def add_password(connection_url: str, password: str) -> str:
    """Replace the password in a Supabase connection template and require TLS."""
    normalized_url = connection_url.replace("[YOUR-PASSWORD]", "placeholder")
    parsed = urlsplit(normalized_url)
    if not parsed.username or not parsed.hostname:
        raise ValueError("Supabase returned an invalid pooler connection URL")

    host = parsed.hostname
    if ":" in host:
        host = f"[{host}]"
    port = f":{parsed.port}" if parsed.port else ""
    netloc = (
        f"{quote(parsed.username, safe='')}:{quote(password, safe='')}@{host}{port}"
    )
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["sslmode"] = "require"
    return urlunsplit(
        (parsed.scheme, netloc, parsed.path, urlencode(query), parsed.fragment)
    )
