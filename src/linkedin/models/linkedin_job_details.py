from typing import Optional
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.entities import JobDetails
from src.linkedin.models.extraction_schemas import ExtractedJobListing


class LinkedInJobDetails(JobDetails):
    __tablename__ = "linkedin_job_details"

    job_id: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        index=True,
        nullable=False,
    )
    category: Mapped[Optional[str]] = mapped_column(default=None)
    is_early_applicant: Mapped[Optional[bool]] = mapped_column(
        Boolean, default=None, nullable=True
    )

    @classmethod
    def from_extracted(
        cls,
        job: ExtractedJobListing,
        card_raw_text: str = "",
    ) -> "LinkedInJobDetails":
        canonical_url = f"https://www.linkedin.com/jobs/view/{job.job_id}/"
        return cls(
            job_id=job.job_id,
            title=job.title,
            company_name=job.company_name,
            location=job.location,
            url=canonical_url,
            short_description=job.short_description,
            description=card_raw_text,
            category=job.category,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            salary_currency=job.salary_currency,
            salary_period=job.salary_period,
            work_type=job.work_type,
            is_new=True,
            posted_at_utc=job.posted_date_utc,
            is_early_applicant=job.is_early_applicant,
        )
