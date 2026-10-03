from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlencode

from src.common.models.base_link_model import BaseLinkModel

_FIXED_PARAMS = {
    "sort_direction": "desc",
    "sort_field": "activation_date",
}


@dataclass
class KalibrrParams:
    """Parameters used to build a Kalibrr job search link."""

    text: Optional[str] = None
    offset: int = 0
    limit: int = 15
    country: Optional[str] = None
    location: Optional[str] = None
    is_work_from_home: bool = False

    def to_query_string(self, page: int = 1) -> str:
        current_offset = self.offset + ((page - 1) * self.limit)
        params: dict[str, str] = {
            "limit": str(self.limit),
            "offset": str(current_offset),
            **_FIXED_PARAMS,
        }

        if self.is_work_from_home:
            params["is_work_from_home"] = "true"
        if self.text is not None:
            params["text"] = self.text
        if self.country is not None:
            params["country"] = self.country
        if self.location is not None:
            params["location"] = self.location

        return urlencode(params)


@dataclass
class KalibrrLink(BaseLinkModel):
    params: KalibrrParams = field(default_factory=KalibrrParams)

    def get_next_page(self, page: int) -> str:
        if page < 1:
            raise ValueError("Page index must be 1 or greater.")

        if page > self.max_page:
            raise ValueError(
                f"Requested page {page} exceeds max_pages ({self.max_page})."
            )

        return f"{self.base_url}?{self.params.to_query_string(page)}"
