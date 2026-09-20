from typing import Optional

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.entities import JobDetails
from src.jobstreet.models.schemas import Job


class JobStreetJobDetails(JobDetails):
    """JobStreet/Seek specific fields extracted from their GraphQL schema."""

    __tablename__ = "jobstreet_job_details"

    job_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    advertiser_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    organisation_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    company_logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    salary_display_text: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    posted_relative_time: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )

    role_titles: Mapped[list[str]] = mapped_column(JSON, default=list)
    location_hierarchy: Mapped[list[str]] = mapped_column(JSON, default=list)

    @classmethod
    def from_api_data(cls, job_data: Job) -> "JobStreetJobDetails":
        title = job_data.title
        company_name = job_data.advertiser.name if job_data.advertiser else None
        location = (
            job_data.location.displayName.text
            if job_data.location and job_data.location.displayName
            else None
        )
        url = f"https://ph.jobstreet.com/job/{job_data.id}" if job_data.id else None
        short_description = job_data.abstract if job_data.abstract else ""
        description = ""

        salary_min = (
            job_data.salary.min if job_data.salary and job_data.salary.min else None
        )
        salary_max = (
            job_data.salary.max if job_data.salary and job_data.salary.max else None
        )
        salary_currency = (
            job_data.salary.currency
            if job_data.salary and job_data.salary.currency
            else None
        )
        salary_period = (
            job_data.salary.period
            if job_data.salary and job_data.salary.period
            else None
        )

        work_type = (
            job_data.cjs.workTypes[0].name
            if job_data.cjs
            and job_data.cjs.workTypes
            and len(job_data.cjs.workTypes) > 0
            else None
        )

        posted_at_utc = job_data.listedAt.dateTimeUtc if job_data.listedAt else None

        advertiser_id = job_data.advertiser.id if job_data.advertiser else None
        organisation_id = job_data.organisation.id if job_data.organisation else None

        company_logo_url = None
        if job_data.cjs and job_data.cjs.product and job_data.cjs.product.branding:
            company_logo_url = job_data.cjs.product.branding.companyLogoURL

        salary_display_text = None
        if job_data.cjs and job_data.cjs.salary:
            salary_display_text = job_data.cjs.salary.displayValue

        posted_relative_time = job_data.listedAt.label if job_data.listedAt else None

        role_titles = []
        if job_data.cjs and job_data.cjs.roleTitles:
            role_titles = [rt.shortId for rt in job_data.cjs.roleTitles if rt.shortId]

        location_hierarchy = []
        if job_data.location and job_data.location.seoHierarchy:
            for node in job_data.location.seoHierarchy:
                text = None
                if node.contextualName and node.contextualName.text:
                    text = node.contextualName.text
                elif node.label and node.label.text:
                    text = node.label.text

                if text:
                    location_hierarchy.append(text)

        return cls(
            title=title,
            company_name=company_name,
            location=location,
            url=url,
            short_description=short_description,
            description=description,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=salary_currency,
            salary_period=salary_period,
            work_type=work_type,
            posted_at_utc=posted_at_utc,
            job_id=job_data.id,
            advertiser_id=advertiser_id,
            organisation_id=organisation_id,
            company_logo_url=company_logo_url,
            salary_display_text=salary_display_text,
            posted_relative_time=posted_relative_time,
            role_titles=role_titles,
            location_hierarchy=location_hierarchy,
        )
