import base64
import httpx

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch_image_as_data_url(url: str) -> str:
    """Download an image and return it as a base64 data URL."""
    try:
        resp = httpx.get(url, headers=HEADERS, timeout=10, follow_redirects=True)
        resp.raise_for_status()

        media_type = resp.headers.get("content-type", "image/jpeg").split(";")[0]
        encoded = base64.b64encode(resp.content).decode("ascii")
        return f"data:{media_type};base64,{encoded}"

    except Exception as e:
        raise RuntimeError(f"Failed to fetch {url[:80]}...: {e}") from e


def base64_to_data_url(base64_str: str, media_type: str = "image/jpeg") -> str:
    """Convert a base64 string to a data URL."""
    return f"data:{media_type};base64,{base64_str}"
