import httpx

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    """Returns the singleton client instance."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=30.0)
    return _client


async def close_client() -> None:
    """Closes the singleton client connection pool."""
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None
