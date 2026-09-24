from dataclasses import dataclass
from typing import List, Optional
import uuid
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from src.db.entities import PaginatedList
from src.mynimo.models.mynimo_job_details import MynimoJobDetails


def create_mynimo_details(db: Session, mynimo_detail: MynimoJobDetails) -> uuid.UUID:

    db.add(mynimo_detail)
    db.commit()
    db.refresh(mynimo_detail)

    return mynimo_detail.id


def create_mynimo_details_bulk(
    db: Session, mynimo_details: List[MynimoJobDetails]
) -> List[uuid.UUID]:

    db.add_all(mynimo_details)
    db.commit()

    return [job.id for job in mynimo_details]


def update_mynimo_details(db: Session, mynimo_detail: MynimoJobDetails) -> None:

    db.merge(mynimo_detail)
    db.commit()


def update_mynimo_details_bulk(
    db: Session, mynimo_details: List[MynimoJobDetails]
) -> None:

    for job in mynimo_details:
        db.merge(job)
    db.commit()


def get_mynimo_details_by_job_id(
    db: Session, job_id: str
) -> Optional[MynimoJobDetails]:

    stmt = select(MynimoJobDetails).where(MynimoJobDetails.job_id == job_id)
    db_job = db.scalar(stmt)

    return db_job


@dataclass
class GetMynimoDetailsFilters:
    """Filter parameters for querying Mynimo job details."""

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
    salary_period: Optional[str] = None  # e.g., "Monthly"
    is_new: Optional[bool] = None
    job_level: Optional[str] = None
    company_size: Optional[str] = None
    direct_employer: Optional[str] = None
    is_urgent: Optional[bool] = None
    work_from_home: Optional[bool] = None
    hide_salary: Optional[bool] = None
    high_school: Optional[bool] = None
    is_pwd: Optional[bool] = None
    is_senior_citizen: Optional[bool] = None
    overseas_location: Optional[str] = None
    min_vacancies: Optional[int] = None


def get_mynimo_job_details_list(
    db: Session,
    filters: Optional[GetMynimoDetailsFilters] = None,
    skip: int = 0,
    limit: int = 10,
) -> PaginatedList[MynimoJobDetails]:
    stmt = select(MynimoJobDetails)

    if filters:
        if filters.keyword:
            pattern = f"%{filters.keyword}%"
            stmt = stmt.where(
                or_(
                    MynimoJobDetails.title.ilike(pattern),
                    MynimoJobDetails.company_name.ilike(pattern),
                    MynimoJobDetails.short_description.ilike(pattern),
                    MynimoJobDetails.description.ilike(pattern),
                )
            )

        if filters.title:
            stmt = stmt.where(MynimoJobDetails.title.ilike(f"%{filters.title}%"))

        if filters.company_name:
            stmt = stmt.where(
                MynimoJobDetails.company_name.ilike(f"%{filters.company_name}%")
            )

        if filters.location:
            stmt = stmt.where(MynimoJobDetails.location.ilike(f"%{filters.location}%"))

        if filters.work_type:
            stmt = stmt.where(MynimoJobDetails.work_type == filters.work_type)

        if filters.salary_currency:
            stmt = stmt.where(
                MynimoJobDetails.salary_currency == filters.salary_currency
            )

        if filters.salary_period:
            stmt = stmt.where(MynimoJobDetails.salary_period == filters.salary_period)

        if filters.is_new is not None:
            stmt = stmt.where(MynimoJobDetails.is_new == filters.is_new)

        for field_name in (
            "job_level",
            "company_size",
            "direct_employer",
            "overseas_location",
        ):
            value = getattr(filters, field_name)
            if value:
                stmt = stmt.where(
                    getattr(MynimoJobDetails, field_name).ilike(f"%{value}%")
                )

        for field_name in (
            "is_urgent",
            "work_from_home",
            "hide_salary",
            "high_school",
            "is_pwd",
            "is_senior_citizen",
        ):
            value = getattr(filters, field_name)
            if value is not None:
                stmt = stmt.where(getattr(MynimoJobDetails, field_name) == value)

        if filters.min_vacancies is not None:
            stmt = stmt.where(MynimoJobDetails.num_vacancies >= filters.min_vacancies)

        if filters.min_salary is not None:
            stmt = stmt.where(
                or_(
                    MynimoJobDetails.salary_max >= filters.min_salary,
                    MynimoJobDetails.salary_min >= filters.min_salary,
                )
            )

        if filters.max_salary is not None:
            stmt = stmt.where(MynimoJobDetails.salary_min <= filters.max_salary)

    total_count = db.scalar(select(func.count()).select_from(stmt.subquery()))

    stmt = (
        stmt.order_by(MynimoJobDetails.posted_at_utc.desc().nullslast())
        .offset(skip)
        .limit(limit)
    )

    job_details = db.scalars(stmt).all()
    return PaginatedList[MynimoJobDetails](
        items=list(job_details),
        total=total_count if total_count is not None else 0,
        page=(skip // limit) + 1 if limit > 0 else 1,
        page_size=limit,
    )
