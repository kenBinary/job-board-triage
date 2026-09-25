from dataclasses import dataclass
from typing import List, Optional
import uuid
from sqlalchemy import UUID, String, cast, func, or_, select
from sqlalchemy.orm import Session
from src.db.entities import PaginatedList
from src.indeed.models.indeed_job_details import IndeedJobDetails


def create_indeed_details(
    db: Session, indeed_job_details: IndeedJobDetails
) -> uuid.UUID:

    db.add(indeed_job_details)
    db.commit()
    db.refresh(indeed_job_details)

    return indeed_job_details.id


def create_indeed_details_bulk(
    db: Session, indeed_job_details: List[IndeedJobDetails]
) -> List[uuid.UUID]:

    db.add_all(indeed_job_details)
    db.commit()

    return [job.id for job in indeed_job_details]


def update_indeed_details(db: Session, indeed_job_details: IndeedJobDetails) -> None:

    db.merge(indeed_job_details)
    db.commit()


def update_indeed_details_bulk(
    db: Session, indeed_job_details: List[IndeedJobDetails]
) -> None:

    for job in indeed_job_details:
        db.merge(job)
    db.commit()


def get_indeed_details_by_job_id(
    db: Session, job_id: str
) -> Optional[IndeedJobDetails]:

    stmt = select(IndeedJobDetails).where(IndeedJobDetails.job_id == job_id)
    db_job = db.scalar(stmt)

    return db_job


@dataclass
class GetIndeedDetailsFilters:
    """Filter parameters for querying Indeed job details."""

    keyword: Optional[str] = (
        None  # Searches title, company_name, description, norm_title
    )
    title: Optional[str] = None  # Filter by specific job title / normalized title
    company_name: Optional[str] = None  # Filter by company name
    location: Optional[str] = None  # Filter by general location string
    city: Optional[str] = None  # Filter by city
    state: Optional[str] = None  # Filter by state
    is_remote: Optional[bool] = None  # Remote / Work-from-home jobs

    # Taxonomy & Type
    job_type: Optional[str] = None  # e.g., "Full-time", "Part-time"

    # Compensation
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    salary_currency: Optional[str] = None  # e.g., "USD", "PHP"
    salary_period: Optional[str] = None  # e.g., "hourly", "monthly", "yearly"

    # Company & Application Metadata
    min_rating: Optional[float] = None  # Minimum employer rating (0.0 - 5.0)
    is_top_rated_employer: Optional[bool] = None
    is_urgently_hiring: Optional[bool] = None
    is_sponsored: Optional[bool] = None
    indeed_apply_enabled: Optional[bool] = None
    is_new: Optional[bool] = None

    # Identifiers
    job_id: Optional[str] = None
    company_id: Optional[str] = None


def get_indeed_job_details_list(
    db: Session,
    filters: Optional[GetIndeedDetailsFilters] = None,
    skip: int = 0,
    limit: int = 25,
) -> PaginatedList[IndeedJobDetails]:
    stmt = select(IndeedJobDetails)

    if filters:
        # General free-text keyword search across core text fields
        if filters.keyword:
            pattern = f"%{filters.keyword}%"
            stmt = stmt.where(
                or_(
                    IndeedJobDetails.title.ilike(pattern),
                    IndeedJobDetails.norm_title.ilike(pattern),
                    IndeedJobDetails.company_name.ilike(pattern),
                    IndeedJobDetails.short_description.ilike(pattern),
                )
            )

        # Partial text matching (case-insensitive)
        if filters.title:
            stmt = stmt.where(
                or_(
                    IndeedJobDetails.title.ilike(f"%{filters.title}%"),
                    IndeedJobDetails.norm_title.ilike(f"%{filters.title}%"),
                )
            )

        if filters.company_name:
            stmt = stmt.where(
                IndeedJobDetails.company_name.ilike(f"%{filters.company_name}%")
            )

        if filters.location:
            stmt = stmt.where(IndeedJobDetails.location.ilike(f"%{filters.location}%"))

        if filters.city:
            stmt = stmt.where(IndeedJobDetails.city.ilike(f"%{filters.city}%"))

        if filters.state:
            stmt = stmt.where(IndeedJobDetails.state.ilike(f"%{filters.state}%"))

        # Job type matching (checks work_type and the JSON job_types list)
        if filters.job_type:
            stmt = stmt.where(
                or_(
                    IndeedJobDetails.work_type.ilike(f"%{filters.job_type}%"),
                    cast(IndeedJobDetails.job_types, String).ilike(
                        f"%{filters.job_type}%"
                    ),
                )
            )

        # Identifiers
        if filters.job_id:
            stmt = stmt.where(IndeedJobDetails.job_id == filters.job_id)

        if filters.company_id:
            stmt = stmt.where(IndeedJobDetails.company_id == filters.company_id)

        # Boolean flags (use `is not None` so `False` is not ignored)
        if filters.is_remote is not None:
            stmt = stmt.where(IndeedJobDetails.is_remote == filters.is_remote)

        if filters.is_top_rated_employer is not None:
            stmt = stmt.where(
                IndeedJobDetails.is_top_rated_employer == filters.is_top_rated_employer
            )

        if filters.is_urgently_hiring is not None:
            stmt = stmt.where(
                IndeedJobDetails.is_urgently_hiring == filters.is_urgently_hiring
            )

        if filters.is_sponsored is not None:
            stmt = stmt.where(IndeedJobDetails.is_sponsored == filters.is_sponsored)

        if filters.indeed_apply_enabled is not None:
            stmt = stmt.where(
                IndeedJobDetails.indeed_apply_enabled == filters.indeed_apply_enabled
            )

        if filters.is_new is not None:
            stmt = stmt.where(IndeedJobDetails.is_new == filters.is_new)

        # Rating threshold
        if filters.min_rating is not None:
            stmt = stmt.where(IndeedJobDetails.company_rating >= filters.min_rating)

        # Salary matching
        if filters.salary_currency:
            stmt = stmt.where(
                IndeedJobDetails.salary_currency == filters.salary_currency
            )

        if filters.salary_period:
            stmt = stmt.where(IndeedJobDetails.salary_period == filters.salary_period)

        if filters.min_salary is not None:
            stmt = stmt.where(
                or_(
                    IndeedJobDetails.salary_max >= filters.min_salary,
                    IndeedJobDetails.salary_min >= filters.min_salary,
                )
            )

        if filters.max_salary is not None:
            stmt = stmt.where(IndeedJobDetails.salary_min <= filters.max_salary)

    # Compute total count for pagination
    total_count = db.scalar(select(func.count()).select_from(stmt.subquery()))

    # Apply ordering, pagination, and fetch
    stmt = (
        stmt.order_by(IndeedJobDetails.posted_at_utc.desc().nullslast())
        .offset(skip)
        .limit(limit)
    )

    job_details = db.scalars(stmt).all()
    return PaginatedList[IndeedJobDetails](
        items=list(job_details),
        total=total_count if total_count is not None else 0,
        page=(skip // limit) + 1 if limit > 0 else 1,
        page_size=limit,
    )
