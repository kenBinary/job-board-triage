import re
from typing import Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def extract_linkedin_post_data(
    payload: str, clean_search_params: bool = True
) -> Tuple[str, Optional[str]]:
    """
    Extracts the LinkedIn post share URL and its shareId from a decoded SDUI/Flight payload.

    :param payload: The raw decoded base64 string.
    :param clean_search_params: If True, strips internal transient parameters
                                ('highlightedUpdateUrn', 'highlightedUpdateType', 'origin').
    :return: A tuple of (clean_url, share_id).
    """
    url_match = re.search(
        r'"longUrl"\s*:\s*"(https://www\.linkedin\.com/posts/[^"]+)"', payload
    )
    if not url_match:
        url_match = re.search(
            r'https://www\.linkedin\.com/posts/[^\s"\'<>\\]+', payload
        )

    if not url_match:
        raise ValueError("No LinkedIn post URL found in the payload.")

    url = url_match.group(1) if url_match.groups() else url_match.group(0)

    if clean_search_params:
        parsed = urlsplit(url)
        params_to_remove = {"highlightedUpdateUrn", "highlightedUpdateType", "origin"}

        filtered_query = [
            (k, v)
            for k, v in parse_qsl(parsed.query, keep_blank_values=True)
            if k not in params_to_remove
        ]

        url = urlunsplit(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                urlencode(filtered_query),
                parsed.fragment,
            )
        )

    share_id_match = re.search(r'shareId\s*[:=]\s*["\']?(\d+)["\']?', payload)
    share_id = share_id_match.group(1) if share_id_match else None

    return url, share_id
