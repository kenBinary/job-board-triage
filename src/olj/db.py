from dataclasses import dataclass
from typing import List, Optional
import uuid
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from src.db.entities import PaginatedList
from src.olj.models.olj_job_details import OljJobDetails


def create_olj_details(db: Session, olj_detail: OljJobDetails) -> uuid.UUID:
    db.add(olj_detail)
    db.commit()
    db.refresh(olj_detail)

    return olj_detail.id


def create_olj_details_bulk(
    db: Session, olj_details: List[OljJobDetails]
) -> List[uuid.UUID]:
    db.add_all(olj_details)
    db.commit()

    return [job.id for job in olj_details]


def update_olj_details(db: Session, olj_detail: OljJobDetails) -> None:
    db.merge(olj_detail)
    db.commit()


def update_olj_details_bulk(db: Session, olj_details: List[OljJobDetails]) -> None:
    for job in olj_details:
        db.merge(job)
    db.commit()


def get_olj_details_by_job_id(db: Session, job_id: str) -> Optional[OljJobDetails]:
    stmt = select(OljJobDetails).where(OljJobDetails.job_id == job_id)
    db_job = db.scalar(stmt)

    return db_job


@dataclass
class GetOljDetailsFilters:
    """Filter parameters for querying OLJ job details."""

    keyword: Optional[str] = (
        None  # Searches across title, company_name, description, and short_description
    )
    title: Optional[str] = None  # Filter by specific job title
    company_name: Optional[str] = None  # Filter by author / company name
    location: Optional[str] = None  # Filter by location
    work_type: Optional[str] = None  # e.g., "Full Time", "Part Time", "Freelance"
    min_salary: Optional[float] = None  # Jobs offering at least this amount
    max_salary: Optional[float] = None  # Jobs capped under this amount
    salary_currency: Optional[str] = None  # e.g., "PHP", "USD"
    salary_period: Optional[str] = None  # e.g., "monthly", "hourly"
    is_new: Optional[bool] = None  # Filter newly posted jobs


def get_olj_job_details_list(
    db: Session,
    filters: Optional[GetOljDetailsFilters] = None,
    skip: int = 0,
    limit: int = 25,
) -> PaginatedList[OljJobDetails]:
    stmt = select(OljJobDetails)

    if filters:
        # General free-text keyword search across multiple fields
        if filters.keyword:
            pattern = f"%{filters.keyword}%"
            stmt = stmt.where(
                or_(
                    OljJobDetails.title.ilike(pattern),
                    OljJobDetails.company_name.ilike(pattern),
                    OljJobDetails.description.ilike(pattern),
                    OljJobDetails.short_description.ilike(pattern),
                )
            )

        # Partial text matching (case-insensitive)
        if filters.title:
            stmt = stmt.where(OljJobDetails.title.ilike(f"%{filters.title}%"))

        if filters.company_name:
            stmt = stmt.where(
                OljJobDetails.company_name.ilike(f"%{filters.company_name}%")
            )

        if filters.location:
            stmt = stmt.where(OljJobDetails.location.ilike(f"%{filters.location}%"))

        # Exact matching
        if filters.work_type:
            stmt = stmt.where(OljJobDetails.work_type == filters.work_type)

        if filters.salary_currency:
            stmt = stmt.where(OljJobDetails.salary_currency == filters.salary_currency)

        if filters.salary_period:
            stmt = stmt.where(OljJobDetails.salary_period == filters.salary_period)

        if filters.is_new is not None:
            stmt = stmt.where(OljJobDetails.is_new == filters.is_new)

        # Salary threshold checks
        if filters.min_salary is not None:
            stmt = stmt.where(
                or_(
                    OljJobDetails.salary_max >= filters.min_salary,
                    OljJobDetails.salary_min >= filters.min_salary,
                )
            )

        if filters.max_salary is not None:
            stmt = stmt.where(OljJobDetails.salary_min <= filters.max_salary)

    total_count = db.scalar(select(func.count()).select_from(stmt.subquery()))

    stmt = (
        stmt.order_by(OljJobDetails.posted_at_utc.desc().nullslast())
        .offset(skip)
        .limit(limit)
    )

    job_details = db.scalars(stmt).all()
    return PaginatedList[OljJobDetails](
        items=list(job_details),
        total=total_count if total_count is not None else 0,
        page=(skip // limit) + 1 if limit > 0 else 1,
        page_size=limit,
    )
