from dataclasses import dataclass
from typing import List, Optional
import uuid
from sqlalchemy import Boolean, func, or_, select
from sqlalchemy.orm import Session
from src.db.entities import PaginatedList
from src.kalibrr.models.kalibrr_job_details import KalibrrJobDetails


def create_kalibrr_details(db: Session, kalibrr_detail: KalibrrJobDetails) -> uuid.UUID:

    db.add(kalibrr_detail)
    db.commit()
    db.refresh(kalibrr_detail)

    return kalibrr_detail.id


def create_kalibrr_details_bulk(
    db: Session, kalibrr_details: List[KalibrrJobDetails]
) -> List[uuid.UUID]:

    db.add_all(kalibrr_details)
    db.commit()

    return [job.id for job in kalibrr_details]


def update_kalibrr_details(db: Session, kalibrr_detail: KalibrrJobDetails) -> None:

    db.merge(kalibrr_detail)
    db.commit()


def update_kalibrr_details_bulk(
    db: Session, kalibrr_details: List[KalibrrJobDetails]
) -> None:

    for job in kalibrr_details:
        db.merge(job)
    db.commit()


def get_kalibrr_details_by_job_id(
    db: Session, job_id: str
) -> Optional[KalibrrJobDetails]:

    stmt = select(KalibrrJobDetails).where(KalibrrJobDetails.job_id == job_id)
    db_job = db.scalar(stmt)

    return db_job


@dataclass
class GetKalibrrDetailsFilters:
    """Filter parameters for querying Kalibrr job details."""

    keyword: Optional[str] = (
        None  # Searches across title, company_name, and description
    )
    title: Optional[str] = None  # Filter by specific job title
    company_name: Optional[str] = None  # Filter by company name
    company_industry: Optional[str] = None  # Filter by industry
    location: Optional[str] = None  # Filter by composite location string
    city: Optional[str] = None  # Filter by city
    region: Optional[str] = None  # Filter by region
    country: Optional[str] = None  # Filter by country
    job_function: Optional[str] = None  # e.g., "Software Development"
    work_type: Optional[str] = None  # e.g., "Full-time", "Part-time", "Contract"
    is_work_from_home: Optional[bool] = None
    is_hybrid: Optional[bool] = None
    is_open_to_fresh_grads: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_new: Optional[bool] = None
    min_salary: Optional[float] = None  # Jobs offering at least this amount
    max_salary: Optional[float] = None  # Jobs capped under this amount
    salary_currency: Optional[str] = None  # e.g., "PHP", "USD"
    salary_period: Optional[str] = None  # e.g., "Monthly"


def get_kalibrr_job_details_list(
    db: Session,
    filters: Optional[GetKalibrrDetailsFilters] = None,
    skip: int = 0,
    limit: int = 10,
) -> PaginatedList[KalibrrJobDetails]:
    stmt = select(KalibrrJobDetails)

    if filters:
        if filters.keyword:
            pattern = f"%{filters.keyword}%"
            stmt = stmt.where(
                or_(
                    KalibrrJobDetails.title.ilike(pattern),
                    KalibrrJobDetails.company_name.ilike(pattern),
                    KalibrrJobDetails.short_description.ilike(pattern),
                    KalibrrJobDetails.description.ilike(pattern),
                )
            )

        if filters.title:
            stmt = stmt.where(KalibrrJobDetails.title.ilike(f"%{filters.title}%"))

        if filters.company_name:
            stmt = stmt.where(
                KalibrrJobDetails.company_name.ilike(f"%{filters.company_name}%")
            )

        if filters.company_industry:
            stmt = stmt.where(
                KalibrrJobDetails.company_industry.ilike(
                    f"%{filters.company_industry}%"
                )
            )

        if filters.location:
            stmt = stmt.where(KalibrrJobDetails.location.ilike(f"%{filters.location}%"))

        if filters.city:
            stmt = stmt.where(KalibrrJobDetails.city.ilike(f"%{filters.city}%"))

        if filters.region:
            stmt = stmt.where(KalibrrJobDetails.region.ilike(f"%{filters.region}%"))

        if filters.country:
            stmt = stmt.where(KalibrrJobDetails.country.ilike(f"%{filters.country}%"))

        if filters.job_function:
            stmt = stmt.where(
                KalibrrJobDetails.job_function.ilike(f"%{filters.job_function}%")
            )

        if filters.work_type:
            stmt = stmt.where(KalibrrJobDetails.work_type == filters.work_type)

        if filters.salary_currency:
            stmt = stmt.where(
                KalibrrJobDetails.salary_currency == filters.salary_currency
            )

        if filters.salary_period:
            stmt = stmt.where(KalibrrJobDetails.salary_period == filters.salary_period)

        if filters.is_new is not None:
            stmt = stmt.where(KalibrrJobDetails.is_new == filters.is_new)

        for field_name in (
            "is_work_from_home",
            "is_hybrid",
            "is_open_to_fresh_grads",
            "is_featured",
        ):
            value = getattr(filters, field_name)
            if value is not None:
                stmt = stmt.where(getattr(KalibrrJobDetails, field_name) == value)

        if filters.min_salary is not None:
            stmt = stmt.where(
                or_(
                    KalibrrJobDetails.salary_max >= filters.min_salary,
                    KalibrrJobDetails.salary_min >= filters.min_salary,
                )
            )

        if filters.max_salary is not None:
            stmt = stmt.where(KalibrrJobDetails.salary_min <= filters.max_salary)

    total_count = db.scalar(select(func.count()).select_from(stmt.subquery()))

    stmt = (
        stmt.order_by(KalibrrJobDetails.posted_at_utc.desc().nullslast())
        .offset(skip)
        .limit(limit)
    )

    job_details = db.scalars(stmt).all()
    return PaginatedList[KalibrrJobDetails](
        items=list(job_details),
        total=total_count if total_count is not None else 0,
        page=(skip // limit) + 1 if limit > 0 else 1,
        page_size=limit,
    )
