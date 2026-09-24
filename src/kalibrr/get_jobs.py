from src.http_client import get_client
from src.kalibrr.models.schemas import KalibrrJobSearchResponse

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:156.0) Gecko/20100101 Firefox/156.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}


async def fetch_jobs(link: str) -> KalibrrJobSearchResponse:
    headers = DEFAULT_HEADERS.copy()

    client = get_client()
    response = await client.get(link, headers=headers)
    response.raise_for_status()

    return KalibrrJobSearchResponse.model_validate(response.json())
