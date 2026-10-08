import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal, Optional
from urllib.parse import urlencode

from src.jobstreet.get_jobs import JobSearchParams, WorkArrangementEnum
from src.common.models.base_link_model import BaseLinkModel


@dataclass
class JobStreetParams:
    """Parameters used to configure JobStreet search queries."""

    text: str = ""
    where: Optional[List[str]] = None
    distance_kms: int = 50
    sort: Literal["listedAt", "score"] = "listedAt"
    listed_at: Literal[None, "1d", "3d", "7d", "14d", "30d"] = "7d"
    work_arrangement_ids: Optional[List[WorkArrangementEnum]] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    work_type_ids: Optional[List[str]] = None
    category_ids: Optional[List[str]] = None
    organisation_id: Optional[str] = None
    organisation_name: Optional[str] = None
    page_size: int = 10
    country: str = "PH"
    locale: str = "en-PH"
    zone: str = "asia-6"
    timezone: str = "Asia/Manila"
    auth_token: Optional[str] = None

    def to_query_string(self, page: int = 1) -> str:
        data = {
            "text": self.text,
            "where": ",".join(self.where) if self.where else "",
            "page": page,
            "pageSize": self.page_size,
            "sort": self.sort,
            "listedAt": self.listed_at,
        }
        filtered = {k: v for k, v in data.items() if v}
        return urlencode(filtered)

    def to_job_search_params(self, page: int = 1) -> JobSearchParams:
        """Converts JobStreetParams into JobSearchParams required by fetch_jobs."""
        return JobSearchParams(
            text=self.text,
            where=self.where,
            distance_kms=self.distance_kms,
            sort=self.sort,
            listed_at=self.listed_at,
            work_arrangement_ids=self.work_arrangement_ids,
            salary_min=self.salary_min,
            salary_max=self.salary_max,
            work_type_ids=self.work_type_ids,
            category_ids=self.category_ids,
            organisation_id=self.organisation_id,
            organisation_name=self.organisation_name,
            page=page,
            page_size=self.page_size,
            country=self.country,
            locale=self.locale,
            zone=self.zone,
            timezone=self.timezone,
            auth_token=self.auth_token,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobStreetParams":
        data_copy = dict(data)
        if data_copy.get("work_arrangement_ids") is not None:
            data_copy["work_arrangement_ids"] = [
                (
                    WorkArrangementEnum(wa)
                    if not isinstance(wa, WorkArrangementEnum)
                    else wa
                )
                for wa in data_copy["work_arrangement_ids"]
            ]
        return cls(**data_copy)


@dataclass
class JobStreetLink(BaseLinkModel):
    params: JobStreetParams = field(default_factory=JobStreetParams)

    def get_next_page(self, page: int) -> str:
        if page < 1:
            raise ValueError("Page index must be 1 or greater.")

        if page > self.max_page:
            raise ValueError(
                f"Requested page {page} exceeds max_pages ({self.max_page})."
            )

        return f"{self.base_url}?{self.params.to_query_string(page)}"

    def get_search_params(self, page: int) -> JobSearchParams:
        if page < 1:
            raise ValueError("Page index must be 1 or greater.")

        if page > self.max_page:
            raise ValueError(
                f"Requested page {page} exceeds max_pages ({self.max_page})."
            )

        return self.params.to_job_search_params(page)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_page": self.max_page,
            "base_url": self.base_url,
            "params": self.params.to_dict(),
        }

    def to_json(self, indent: Optional[int] = None) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobStreetLink":
        params_raw = data.get("params", {})
        params = (
            JobStreetParams.from_dict(params_raw)
            if isinstance(params_raw, dict)
            else (params_raw or JobStreetParams())
        )
        return cls(
            max_page=data["max_page"],
            base_url=data["base_url"],
            params=params,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "JobStreetLink":
        data = json.loads(json_str)
        return cls.from_dict(data)
