from dataclasses import dataclass, field
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
