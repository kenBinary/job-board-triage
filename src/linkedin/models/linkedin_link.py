from enum import StrEnum
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Literal, Optional
from urllib.parse import urlencode

from src.common.models.base_link_model import BaseLinkModel


class LocationEnum(StrEnum):
    PHILIPPINES = "103121230"
    CEBU = "105344578"
    CAGAYAN_DE_ORO = "108067882"


@dataclass
class LinkedInParams:
    """Parameters for LinkedIn official job board search query.

    Attributes:
        keywords (str): The search keywords (e.g. 'developer', 'software').
        location (Optional[str]): Location query, defaults to 'Philippines'.
        f_TPR (Optional[str]): Recency filter (e.g. 'r604800' for past week, 'r86400' for 24h, 'r2592000' for past month).
        f_SAL (Optional[str]): Salary / Remote arrangement filter (e.g. 'f_SA_id_225001:272001' or None).
    """

    keywords: str
    location: Optional[LocationEnum] = LocationEnum.PHILIPPINES
    f_TPR: Optional[Literal["r604800", "r86400", "r2592000"]] = "r604800"
    f_SAL: Optional[str] = None

    def to_query_string(self) -> str:
        params: dict[str, Any] = {"keywords": self.keywords}
        if self.location:
            params["geoId"] = self.location
        if self.f_TPR:
            params["f_TPR"] = self.f_TPR
        if self.f_SAL:
            params["f_SAL"] = self.f_SAL
        return urlencode(params)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LinkedInParams":
        return cls(**data)


@dataclass
class LinkedInLink(BaseLinkModel):
    """Pagination link model for LinkedIn Job Board search results.

    Attributes:
        max_page (int): Maximum pages to scrape.
        base_url (str): The base search endpoint.
        params (LinkedInParams): Search query parameters.
    """

    params: LinkedInParams = field(kw_only=True)

    def get_next_page(self, page: int) -> str:
        if page < 1:
            raise ValueError("Page index must be 1 or greater.")
        if page > self.max_page:
            raise ValueError(
                f"Requested page {page} exceeds max_pages ({self.max_page})."
            )

        url = f"{self.base_url}?{self.params.to_query_string()}"
        if page > 1:
            start_offset = (page - 1) * 25
            url += f"&start={start_offset}"
        return url

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_page": self.max_page,
            "base_url": self.base_url,
            "params": self.params.to_dict(),
        }

    def to_json(self, indent: Optional[int] = None) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LinkedInLink":
        params_raw = data.get("params", {})
        params = (
            LinkedInParams.from_dict(params_raw)
            if isinstance(params_raw, dict)
            else LinkedInParams(keywords="")
        )
        return cls(
            max_page=data.get("max_page", 2),
            base_url=data.get(
                "base_url", "https://www.linkedin.com/jobs/search-results/"
            ),
            params=params,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "LinkedInLink":
        data = json.loads(json_str)
        return cls.from_dict(data)
