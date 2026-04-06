import httpx
from config.settings import settings

_client: httpx.AsyncClient | None = None


def get_retell_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url="https://api.retellai.com",
            headers={"Authorization": f"Bearer {settings.retell_api_key}"},
            timeout=30.0,
        )
    return _client


async def close_retell_client() -> None:
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
