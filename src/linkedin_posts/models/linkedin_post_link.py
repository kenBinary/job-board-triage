from dataclasses import dataclass, field
from typing import Literal
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
