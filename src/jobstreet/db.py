from dataclasses import dataclass
from typing import List, Optional
import uuid
from sqlalchemy import UUID, func, or_, select
from sqlalchemy.orm import Session
from src.db.entities import PaginatedList
from src.jobstreet.models.jobstreet_job_details import JobStreetJobDetails


def create_jobstreet_details(
    db: Session, job_street_detail: JobStreetJobDetails
) -> uuid.UUID:

    db.add(job_street_detail)
    db.commit()
    db.refresh(job_street_detail)

    return job_street_detail.id


def create_jobstreet_details_bulk(
    db: Session, job_street_details: List[JobStreetJobDetails]
) -> List[uuid.UUID]:

    db.add_all(job_street_details)
    db.commit()

    return [job.id for job in job_street_details]


def update_jobstreet_details(
    db: Session, job_street_detail: JobStreetJobDetails
) -> None:

    db.merge(job_street_detail)
    db.commit()


def update_jobstreet_details_bulk(
    db: Session, job_street_details: List[JobStreetJobDetails]
) -> None:

    for job in job_street_details:
        db.merge(job)
    db.commit()


def get_jobstreet_details_by_job_id(
    db: Session, job_id: str
) -> Optional[JobStreetJobDetails]:

    stmt = select(JobStreetJobDetails).where(JobStreetJobDetails.job_id == job_id)
    db_job = db.scalar(stmt)

    return db_job


@dataclass
class GetJobstreetDetailsFilters:
    """Filter parameters for querying JobStreet job details."""

    keyword: Optional[str] = (
        None  # Searches across title, company_name, and description
    )
    title: Optional[str] = None  # Filter by specific job title
    company_name: Optional[str] = None  # Filter by company name
    location: Optional[str] = None  # Filter by location
    work_type: Optional[str] = None  # e.g., "Full-time", "Part-time", "Contract"
    min_salary: Optional[float] = None  # Jobs offering at least this amount
    max_salary: Optional[float] = None  # Jobs capped under this amount
    salary_currency: Optional[str] = None  # e.g., "PHP", "USD", "MYR"
    salary_period: Optional[str] = None  # e.g., "monthly", "hourly", "annual"
    is_new: Optional[bool] = None  # Filter newly posted jobs
    advertiser_id: Optional[str] = None
    organisation_id: Optional[str] = None


def get_jobstreet_job_details_list(
    db: Session,
    filters: Optional[GetJobstreetDetailsFilters] = None,
    skip: int = 0,
    limit: int = 25,
) -> PaginatedList[JobStreetJobDetails]:
    stmt = select(JobStreetJobDetails)

    if filters:
        # General free-text keyword search across multiple fields
        if filters.keyword:
            pattern = f"%{filters.keyword}%"
            stmt = stmt.where(
                or_(
                    JobStreetJobDetails.title.ilike(pattern),
                    JobStreetJobDetails.company_name.ilike(pattern),
                    JobStreetJobDetails.short_description.ilike(pattern),
                )
            )

        # Partial text matching (case-insensitive)
        if filters.title:
            stmt = stmt.where(JobStreetJobDetails.title.ilike(f"%{filters.title}%"))

        if filters.company_name:
            stmt = stmt.where(
                JobStreetJobDetails.company_name.ilike(f"%{filters.company_name}%")
            )

        if filters.location:
            stmt = stmt.where(
                JobStreetJobDetails.location.ilike(f"%{filters.location}%")
            )

        # Exact matching
        if filters.work_type:
            stmt = stmt.where(JobStreetJobDetails.work_type == filters.work_type)

        if filters.salary_currency:
            stmt = stmt.where(
                JobStreetJobDetails.salary_currency == filters.salary_currency
            )

        if filters.salary_period:
            stmt = stmt.where(
                JobStreetJobDetails.salary_period == filters.salary_period
            )

        if filters.is_new is not None:
            stmt = stmt.where(JobStreetJobDetails.is_new == filters.is_new)

        if filters.advertiser_id:
            stmt = stmt.where(
                JobStreetJobDetails.advertiser_id == filters.advertiser_id
            )

        if filters.organisation_id:
            stmt = stmt.where(
                JobStreetJobDetails.organisation_id == filters.organisation_id
            )

        # Salary threshold checks
        if filters.min_salary is not None:
            # Matches jobs where the max (or min) salary can meet the minimum expectation
            stmt = stmt.where(
                or_(
                    JobStreetJobDetails.salary_max >= filters.min_salary,
                    JobStreetJobDetails.salary_min >= filters.min_salary,
                )
            )

        if filters.max_salary is not None:
            stmt = stmt.where(JobStreetJobDetails.salary_min <= filters.max_salary)

    total_count = db.scalar(select(func.count()).select_from(stmt.subquery()))

    stmt = (
        stmt.order_by(JobStreetJobDetails.posted_at_utc.desc().nullslast())
        .offset(skip)
        .limit(limit)
    )

    job_details = db.scalars(stmt).all()
    return PaginatedList[JobStreetJobDetails](
        items=list(job_details),
        total=total_count if total_count is not None else 0,
        page=(skip // limit) + 1 if limit > 0 else 1,
        page_size=limit,
    )
