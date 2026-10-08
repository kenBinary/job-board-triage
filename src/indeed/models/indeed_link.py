import json
from dataclasses import asdict
from typing import Any, Dict, Optional
from urllib.parse import urlencode
from typing_extensions import Literal
from dataclasses import dataclass

from src.common.models.base_link_model import BaseLinkModel


@dataclass
class IndeedParams:
    """Class to hold parameters for Indeed job search links.

    Attributes:
        q (str): The job query string.
        l (str): The location for the job search.
        sort (str): The sorting order of the job listings.
        fromage (int): The age of the job listings in days.
        radius (int): The search radius in miles.
        sc (str): The search criteria. `0kf:attr(DSQF7);` is for remote
    """

    q: Optional[str] = None
    l: Optional[str] = None
    sort: Literal["date", "relevance"] = "date"
    fromage: Optional[Literal[1, 3, 7, 14]] = 7
    radius: Optional[int] = 25
    sc: Optional[str] = "0kf:attr(DSQF7);"

    def __post_init__(self) -> None:
        if self.q is None and self.l is None:
            raise ValueError("Either 'q' or 'l' must be provided.")

    def to_query_string(self) -> str:
        params = {
            "q": self.q,
            "l": self.l,
            "sort": self.sort,
            "fromage": self.fromage,
            "radius": self.radius,
            "sc": self.sc,
        }
        filtered_params = {k: v for k, v in params.items() if v is not None}
        return urlencode(filtered_params, doseq=True)


@dataclass
class IndeedLink(BaseLinkModel):
    params: IndeedParams

    def get_next_page(self, page: int) -> str:
        if page < 1:
            raise ValueError("Page index must be 1 or greater.")

        if page > self.max_page:
            raise ValueError(
                f"Requested page {page} exceeds max_pages ({self.max_page})."
            )

        url = f"{self.base_url}?{self.params.to_query_string()}"
        if page > 1:
            url += f"&start={(page - 1) * 10}"

        return url

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_page": self.max_page,
            "base_url": self.base_url,
            "params": asdict(self.params),
        }

    def to_json(self, indent: Optional[int] = None) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IndeedLink":
        return cls(
            max_page=data["max_page"],
            base_url=data["base_url"],
            params=IndeedParams(**data.get("params", {})),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "IndeedLink":
        return cls.from_dict(json.loads(json_str))
