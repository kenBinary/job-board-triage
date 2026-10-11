from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.entities import JobDetails
from .extraction_schemas import ExtractedJobListing


class FacebookPostJobDetails(JobDetails):
    __tablename__ = "facebook_post_job_details"

    job_id: Mapped[str] = mapped_column(
        String(250),
        unique=True,
        index=True,
        nullable=False,
    )
    category: Mapped[Optional[str]] = mapped_column(default=None)

    @classmethod
    def from_extracted(
        cls,
        job: ExtractedJobListing,
        job_id: str,
        post_url: str,
    ) -> "FacebookPostJobDetails":
        """
        Construct a FacebookPostJobDetails record from an LLM-extracted job listing.

        :param job:      The Pydantic model returned by the LLM extractor.
        :param job_id:   Unique identifier: the post ID parsed from the /posts/<id> URL,
                         suffixed with _{idx} for multi-job posts.
        :param post_url: Canonical Facebook post URL extracted from anchor links.
        """
        return cls(
            title=job.title,
            company_name=job.company_name,
            location=job.location,
            url=post_url,
            short_description=job.short_description,
            description=job.description,
            category=job.category,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            salary_currency=job.salary_currency,
            salary_period=job.salary_period,
            work_type=job.work_type,
            is_new=True,
            job_id=job_id,
        )
