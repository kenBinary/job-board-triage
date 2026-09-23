from typing import Optional

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.entities import JobDetails
from src.olj.models.schemas import OljJobSchema


class OljJobDetails(JobDetails):
    """OnlineJobs/Seek specific fields extracted from their GraphQL schema."""

    __tablename__ = "olj_job_details"

    job_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    formatted_salary: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)

    @classmethod
    def from_api_data(cls, job_data: OljJobSchema) -> "OljJobDetails":
        """Map an OljJobSchema instance to an OljJobDetails ORM model."""

        return cls(
            job_id=job_data.id,
            title=job_data.title,
            company_name=job_data.author,
            url=f"https://www.onlinejobs.ph{job_data.link}",
            work_type=job_data.job_type,
            description=job_data.description,
            short_description="",
            formatted_salary=job_data.salary,
            posted_at_utc=job_data.posted_date,
            tags=job_data.tags,
            is_new=True,
        )
