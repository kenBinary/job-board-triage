from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.entities import JobDetails
from src.indeed.models.schemas import JobCard


class IndeedJobDetails(JobDetails):
    """Indeed-specific fields extracted from their JobCard payload."""

    __tablename__ = "indeed_job_details"

    # Platform Identifiers
    job_id: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, index=True, nullable=True
    )
    company_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Employer Metadata
    company_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    company_review_count: Mapped[Optional[int]] = mapped_column(
        Integer, default=0, nullable=True
    )
    is_top_rated_employer: Mapped[bool] = mapped_column(Boolean, default=False)

    # Structured Location & Mode
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False)
    formatted_salary: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Time & Normalized Metadata
    posted_relative_time: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    norm_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Taxonomy & Categorization
    job_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    taxonomy_attributes: Mapped[list[str]] = mapped_column(JSON, default=list)

    # Application & Status Flags
    indeed_apply_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    third_party_apply_url: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True
    )
    is_urgently_hiring: Mapped[bool] = mapped_column(Boolean, default=False)
    is_sponsored: Mapped[bool] = mapped_column(Boolean, default=False)
    num_hires: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    @classmethod
    def from_api_data(cls, job: JobCard) -> "IndeedJobDetails":
        # Parse timestamp to UTC string if available
        posted_at_utc = None
        if job.pubDate:
            try:
                # pubDate is usually in milliseconds
                ts = job.pubDate / 1000.0 if job.pubDate > 1e11 else float(job.pubDate)
                posted_at_utc = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            except Exception:
                posted_at_utc = None

        # Flatten taxonomy labels (e.g. skills, benefits)
        extracted_attributes = [
            attr_item.label
            for taxo in job.taxonomyAttributes
            for attr_item in taxo.attributes
            if attr_item.label
        ]

        formatted_salary = (
            job.salarySnippet.salaryTextFormatted if job.salarySnippet else None
        )

        # Resolve primary URL: prefer viewJobLink or full link
        url = job.viewJobLink or job.link
        if url and url.startswith("/"):
            url = f"https://www.indeed.com{url}"

        return cls(
            # Base JobDetails fields
            title=job.displayTitle or job.title or "",
            company_name=job.company,
            location=job.formattedLocation,
            url=url,
            short_description=job.snippet or "",
            salary_min=job.extractedSalary.min if job.extractedSalary else None,
            salary_max=job.extractedSalary.max if job.extractedSalary else None,
            salary_currency=job.salarySnippet.currency if job.salarySnippet else None,
            salary_period=job.extractedSalary.type if job.extractedSalary else None,
            posted_at_utc=posted_at_utc,
            is_new=True,
            # Indeed-specific fields
            job_id=job.jobkey,
            company_id=job.companyIdEncrypted
            or (str(job.fccompanyId) if job.fccompanyId else None),
            company_rating=job.companyRating,
            company_review_count=job.companyReviewCount,
            is_top_rated_employer=job.isTopRatedEmployer or False,
            city=job.jobLocationCity,
            state=job.jobLocationState,
            is_remote=job.remoteLocation or False,
            formatted_salary=formatted_salary,
            posted_relative_time=job.formattedRelativeTime,
            norm_title=job.normTitle,
            job_types=job.jobTypes or [],
            taxonomy_attributes=extracted_attributes,
            indeed_apply_enabled=job.indeedApplyEnabled or False,
            third_party_apply_url=job.thirdPartyApplyUrl,
            is_urgently_hiring=job.urgentlyHiring or False,
            is_sponsored=job.sponsored or False,
            num_hires=job.numHires if job.numHires and job.numHires > 0 else None,
        )
