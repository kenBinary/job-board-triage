import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Literal, Optional
from urllib.parse import urlencode

from src.common.models.base_infinite_scroll_model import BaseInfiniteScrollModel

BASE_SEARCH_URL = "https://www.linkedin.com/search/results/content/"


@dataclass
class LinkedInPostParams:
    """Parameters for a LinkedIn content search query.

    Attributes:
        keywords (str): The search keyword or hashtag (e.g. '#remotejobsph').
        sort_by (str): Sort order. LinkedIn expects '[\"date_posted\"]'.
        date_posted (str): Recency filter. LinkedIn expects '[\"past-week\"]'.
    """

    keywords: str
    sort_by: Literal["date_posted", "relevance"] = "date_posted"
    date_posted: Literal["past-week", "past-month", "past-24h"] = "past-week"

    def to_query_string(self) -> str:
        params = {
            "keywords": self.keywords,
            "sortBy": f'["{self.sort_by}"]',
            "datePosted": f'["{self.date_posted}"]',
        }
        return urlencode(params)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LinkedInPostParams":
        return cls(**data)


@dataclass
class LinkedInPostLink(BaseInfiniteScrollModel):
    """Infinite scroll model for a LinkedIn content search URL.

    Attributes:
        params (LinkedInPostParams): Query parameters for the search.
        base_url (str): The LinkedIn content search endpoint.
        max_scrolls (int): Maximum number of scroll attempts before stopping.
    """

    params: LinkedInPostParams = field(
        default_factory=lambda: LinkedInPostParams(keywords="")
    )
    base_url: str = BASE_SEARCH_URL

    def get_url(self) -> str:
        """Build the full LinkedIn content search URL from the stored params."""
        return f"{self.base_url}?{self.params.to_query_string()}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_url": self.base_url,
            "max_scrolls": self.max_scrolls,
            "params": self.params.to_dict(),
        }

    def to_json(self, indent: Optional[int] = None) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LinkedInPostLink":
        params_raw = data.get("params", {})
        params = (
            LinkedInPostParams.from_dict(params_raw)
            if isinstance(params_raw, dict)
            else (params_raw or LinkedInPostParams(keywords=""))
        )
        return cls(
            base_url=data.get("base_url", BASE_SEARCH_URL),
            max_scrolls=data.get("max_scrolls", 10),
            params=params,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "LinkedInPostLink":
        data = json.loads(json_str)
        return cls.from_dict(data)
