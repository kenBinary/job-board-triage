import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from src.common.models.base_link_model import BaseLinkModel


@dataclass
class MynimoParams:
    """Parameters used to build a Mynimo job search link."""

    path: str

    def to_query_string(self, page: int = 1) -> str:
        return urlencode({"path": self.path, "page": str(page)})


@dataclass
class MynimoLink(BaseLinkModel):
    params: MynimoParams

    def get_next_page(self, page: int) -> str:
        if page < 1:
            raise ValueError("Page index must be 1 or greater.")

        if page > self.max_page:
            raise ValueError(
                f"Requested page {page} exceeds max_pages ({self.max_page})."
            )

        return f"{self.base_url}?{self.params.to_query_string(page)}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_page": self.max_page,
            "base_url": self.base_url,
            "params": asdict(self.params),
        }

    def to_json(self, indent: Optional[int] = None) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MynimoLink":
        return cls(
            max_page=data["max_page"],
            base_url=data["base_url"],
            params=MynimoParams(**data.get("params", {})),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "MynimoLink":
        return cls.from_dict(json.loads(json_str))
