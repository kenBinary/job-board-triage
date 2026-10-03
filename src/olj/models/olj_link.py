from dataclasses import dataclass
from typing import Optional
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
