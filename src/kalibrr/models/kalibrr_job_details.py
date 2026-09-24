from __future__ import annotations

from typing import Optional

from sqlalchemy import JSON, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.entities import JobDetails
from src.kalibrr.models.schemas import Job


class KalibrrJobDetails(JobDetails):
    """Kalibrr-specific job details entity."""

    __tablename__ = "kalibrr_job_details"

    job_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    slug: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    company_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    company_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    company_industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_company_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    qualifications: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    job_function: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    education_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    work_experience_years: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    num_vacancies: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_work_from_home: Mapped[bool] = mapped_column(Boolean, default=False)
    is_hybrid: Mapped[bool] = mapped_column(Boolean, default=False)
    is_open_to_fresh_grads: Mapped[bool] = mapped_column(Boolean, default=False)

    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    perks: Mapped[list[str]] = mapped_column(JSON, default=list)

    salary_shown: Mapped[bool] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    application_end_date: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    apply_redirect_url: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True
    )

    @classmethod
    def from_api_data(cls, job_data: Job) -> "KalibrrJobDetails":
        company_code = (
            job_data.company.code
            if job_data.company and job_data.company.code
            else (
                job_data.company_info.code
                if job_data.company_info and job_data.company_info.code
                else None
            )
        )

        if company_code and job_data.slug:
            url = f"https://www.kalibrr.com/c/{company_code}/jobs/{job_data.id}/{job_data.slug}"
        elif job_data.slug:
            url = f"https://www.kalibrr.com/c/jobs/jobs/{job_data.id}/{job_data.slug}"
        else:
            url = f"https://www.kalibrr.com/jobs/{job_data.id}"

        address = (
            job_data.google_location.address_components
            if job_data.google_location
            else None
        )
        location_parts: list[str] = []
        if address:
            seen: set[str] = set()
            for part in (
                address.address_line_1,
                address.city,
                address.region,
                address.country,
            ):
                if part and part.strip() and part.strip() not in seen:
                    seen.add(part.strip())
                    location_parts.append(part.strip())
        composite_location = ", ".join(location_parts) if location_parts else None

        salary_shown = bool(job_data.salary_shown)
        salary_min = (
            float(job_data.base_salary)
            if salary_shown and job_data.base_salary is not None
            else None
        )
        salary_max = (
            float(job_data.maximum_salary)
            if salary_shown and job_data.maximum_salary is not None
            else None
        )

        posted_at = job_data.activation_date or job_data.created_at
        posted_at_utc = posted_at.isoformat() if posted_at else None
        application_end_date = (
            job_data.application_end_date.isoformat()
            if job_data.application_end_date
            else None
        )

        skills = [
            skill_item.sds_skill.name
            for skill_item in job_data.job_sds_skills
            if skill_item.sds_skill and skill_item.sds_skill.name
        ]
        perks = job_data.perks.types if job_data.perks and job_data.perks.types else []

        return cls(
            title=job_data.name,
            company_name=job_data.company_name
            or (job_data.company.name if job_data.company else None),
            location=composite_location,
            url=url,
            short_description="",
            description=job_data.description or "",
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=job_data.salary_currency if salary_shown else None,
            salary_period=job_data.salary_interval if salary_shown else None,
            work_type=job_data.tenure,
            posted_at_utc=posted_at_utc,
            is_new=True,
            job_id=str(job_data.id),
            slug=job_data.slug,
            company_id=str(job_data.company.id) if job_data.company else None,
            company_code=company_code,
            company_industry=(
                job_data.company.industry
                if job_data.company and job_data.company.industry
                else (job_data.company_info.industry if job_data.company_info else None)
            ),
            is_company_verified=(
                job_data.company.verified_business if job_data.company else False
            ),
            qualifications=job_data.qualifications,
            job_function=job_data.function,
            education_level=job_data.education_level,
            work_experience_years=job_data.work_experience,
            num_vacancies=job_data.number_of_openings,
            city=address.city if address else None,
            region=address.region if address else None,
            country=address.country if address else None,
            is_work_from_home=job_data.is_work_from_home,
            is_hybrid=job_data.is_hybrid,
            is_open_to_fresh_grads=job_data.is_open_to_fresh_grads,
            skills=skills,
            perks=perks,
            salary_shown=salary_shown,
            is_featured=job_data.is_featured,
            application_end_date=application_end_date,
            apply_redirect_url=(
                str(job_data.apply_redirect_url)
                if job_data.apply_redirect_url
                else None
            ),
        )
