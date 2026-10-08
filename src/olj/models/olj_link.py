import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from src.common.models.base_link_model import BaseLinkModel


@dataclass
class OljParams:
    """Parameters used to build an OnlineJobs.ph job search link."""

    jobkeyword: Optional[str] = None

    def to_query_string(self) -> str:
        return urlencode({"jobkeyword": self.jobkeyword})


@dataclass
class OljLink(BaseLinkModel):
    params: OljParams

    def get_next_page(self, page: int) -> str:
        if page < 1:
            raise ValueError("Page index must be 1 or greater.")

        if page > self.max_page:
            raise ValueError(
                f"Requested page {page} exceeds max_pages ({self.max_page})."
            )

        page_path = self.base_url
        if page > 1:
            page_path = f"{page_path}/{(page - 1) * 30}"

        if self.params.jobkeyword is not None:
            return f"{page_path}?{self.params.to_query_string()}"

        return page_path

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_page": self.max_page,
            "base_url": self.base_url,
            "params": asdict(self.params),
        }

    def to_json(self, indent: Optional[int] = None) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OljLink":
        return cls(
            max_page=data["max_page"],
            base_url=data["base_url"],
            params=OljParams(**data.get("params", {})),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "OljLink":
        return cls.from_dict(json.loads(json_str))
