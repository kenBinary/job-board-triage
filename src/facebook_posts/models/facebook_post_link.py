import json
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, Dict, Optional
from urllib.parse import quote, urlencode

from src.common.models.base_infinite_scroll_model import BaseInfiniteScrollModel

RECENT_POSTS_FILTER = "eyJyZWNlbnRfcG9zdHM6MCI6IntcIm5hbWVcIjpcInJlY2VudF9wb3N0c1wiLFwiYXJnc1wiOlwiXCJ9In0%3D"

BASE_HASHTAG_URL = "https://www.facebook.com/hashtag"
BASE_SEARCH_URL = "https://www.facebook.com/search/top"


class FacebookLinkType(StrEnum):
    """Type of Facebook post search target."""

    HASHTAG = "hashtag"
    SEARCH = "search"


@dataclass
class FacebookPostParams:
    """Parameters for a Facebook post search or hashtag feed.

    Attributes:
        query (str): For HASHTAG, the bare tag (e.g. 'remotejobsph').
                     For SEARCH, the search query (e.g. 'hiring').
        link_type (FacebookLinkType): HASHTAG or SEARCH.
        recent_posts (bool): If True, appends the recent_posts filter so only
                             recent posts are returned.
    """

    query: str
    link_type: FacebookLinkType = FacebookLinkType.HASHTAG
    recent_posts: bool = True

    def build_url(self) -> str:
        """Build the full Facebook URL from params."""
        if self.link_type == FacebookLinkType.HASHTAG:
            base = f"{BASE_HASHTAG_URL}/{quote(self.query, safe='')}"
            if self.recent_posts:
                return f"{base}?filters={RECENT_POSTS_FILTER}"
            return base
        else:
            qs = urlencode({"q": self.query})
            if self.recent_posts:
                return f"{BASE_SEARCH_URL}?{qs}&filters={RECENT_POSTS_FILTER}"
            return f"{BASE_SEARCH_URL}?{qs}"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FacebookPostParams":
        data = dict(data)
        if "link_type" in data:
            data["link_type"] = FacebookLinkType(data["link_type"])
        return cls(**data)


@dataclass
class FacebookPostLink(BaseInfiniteScrollModel):
    """
    Attributes:
        params (FacebookPostParams): Query parameters defining the target feed.
        base_url (str): Overridden to point to Facebook; not used directly
                        (URL is built from params).
        max_scrolls (int): Maximum number of incremental scroll steps.
    """

    params: FacebookPostParams = field(
        default_factory=lambda: FacebookPostParams(query="")
    )
    base_url: str = BASE_HASHTAG_URL

    def get_url(self) -> str:
        """Build the full Facebook feed URL from stored params."""
        return self.params.build_url()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_url": self.base_url,
            "max_scrolls": self.max_scrolls,
            "params": self.params.to_dict(),
        }

    def to_json(self, indent: Optional[int] = None) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FacebookPostLink":
        params_raw = data.get("params", {})
        params = (
            FacebookPostParams.from_dict(params_raw)
            if isinstance(params_raw, dict)
            else (params_raw or FacebookPostParams(query=""))
        )
        return cls(
            base_url=data.get("base_url", BASE_HASHTAG_URL),
            max_scrolls=data.get("max_scrolls", 10),
            params=params,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "FacebookPostLink":
        data = json.loads(json_str)
        return cls.from_dict(data)
