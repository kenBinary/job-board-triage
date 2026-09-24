from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.entities import JobDetails
from src.mynimo.models.schemas import JobItem


class MynimoJobDetails(JobDetails):
    """Mynimo-specific job details entity."""

    __tablename__ = "mynimo_job_details"

    job_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    job_level: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    num_vacancies: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    is_urgent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    work_from_home: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hide_salary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    high_school: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_pwd: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_senior_citizen: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    company_size: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    direct_employer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    barangay: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    province: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    overseas_location: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    @classmethod
    def from_api_data(cls, job_data: JobItem) -> "MynimoJobDetails":
        location_parts = [
            part.strip()
            for part in (
                job_data.barangay_name,
                job_data.location_name,
                job_data.location_parent_name,
            )
            if part and part.strip()
        ]
        composite_location = (
            ", ".join(location_parts)
            if location_parts
            else (job_data.overseas_location or None)
        )

        is_salary_hidden = bool(job_data.hide_salary)
        min_salary = (
            float(job_data.min_salary)
            if job_data.min_salary > 0 and not is_salary_hidden
            else None
        )
        max_salary = (
            float(job_data.max_salary)
            if job_data.max_salary > 0 and not is_salary_hidden
            else None
        )

        work_type = "Part-time" if job_data.part_time else "Full-time"

        return cls(
            title=job_data.title,
            company_name=job_data.company or None,
            location=composite_location,
            short_description="",
            description=job_data.content,
            salary_min=min_salary,
            salary_max=max_salary,
            salary_currency="PHP" if not job_data.overseas_location else None,
            salary_period="Monthly" if (min_salary or max_salary) else None,
            work_type=work_type,
            posted_at_utc=job_data.starts_iso or job_data.starts,
            url=f"https://www.mynimo.com/jobs/view/{job_data.id}",
            is_new=True,
            # Mynimo-specific fields
            job_id=str(job_data.id),
            job_level=job_data.job_level or None,
            num_vacancies=job_data.num_vacancies,
            is_urgent=bool(job_data.urgent),
            work_from_home=bool(job_data.work_from_home),
            hide_salary=is_salary_hidden,
            high_school=bool(job_data.high_school),
            is_pwd=bool(job_data.is_pwd) if job_data.is_pwd is not None else False,
            is_senior_citizen=(
                bool(job_data.is_senior_citizen)
                if job_data.is_senior_citizen is not None
                else False
            ),
            company_size=job_data.size or None,
            direct_employer=job_data.direct_employer,
            barangay=job_data.barangay_name or None,
            city=job_data.location_name or None,
            province=job_data.location_parent_name or None,
            overseas_location=job_data.overseas_location or None,
        )
