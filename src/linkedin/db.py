from typing import List, Optional, Set
import uuid
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db.entities import PaginatedList
from src.linkedin.models.linkedin_job_details import LinkedInJobDetails


def create_linkedin_details(
    db: Session,
    job: LinkedInJobDetails,
) -> uuid.UUID:
    db.add(job)
    db.commit()
    db.refresh(job)
    return job.id


def create_linkedin_details_bulk(
    db: Session,
    jobs: List[LinkedInJobDetails],
) -> List[uuid.UUID]:
    if not jobs:
        return []
    db.add_all(jobs)
    db.commit()
    return [j.id for j in jobs]


def get_linkedin_details_by_job_id(
    db: Session,
    job_id: str,
) -> Optional[LinkedInJobDetails]:
    stmt = select(LinkedInJobDetails).where(LinkedInJobDetails.job_id == job_id)
    return db.scalar(stmt)


def get_existing_job_ids(
    db: Session,
    job_ids: List[str],
) -> Set[str]:
    """Return the subset of job_ids that already exist in the database."""
    if not job_ids:
        return set()
    stmt = select(LinkedInJobDetails.job_id).where(
        LinkedInJobDetails.job_id.in_(job_ids)
    )
    results = db.scalars(stmt).all()
    return set(results)


def get_linkedin_details_list(
    db: Session,
    keyword: Optional[str] = None,
    work_type: Optional[str] = None,
    category: Optional[str] = None,
    is_new: Optional[bool] = None,
    skip: int = 0,
    limit: int = 25,
) -> PaginatedList[LinkedInJobDetails]:
    from sqlalchemy import or_

    stmt = select(LinkedInJobDetails)

    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                LinkedInJobDetails.title.ilike(pattern),
                LinkedInJobDetails.company_name.ilike(pattern),
                LinkedInJobDetails.short_description.ilike(pattern),
                LinkedInJobDetails.description.ilike(pattern),
            )
        )

    if work_type is not None:
        stmt = stmt.where(LinkedInJobDetails.work_type == work_type)

    if category is not None:
        stmt = stmt.where(LinkedInJobDetails.category == category)

    if is_new is not None:
        stmt = stmt.where(LinkedInJobDetails.is_new == is_new)

    total_count = db.scalar(select(func.count()).select_from(stmt.subquery()))

    stmt = (
        stmt.order_by(LinkedInJobDetails.posted_at_utc.desc().nullslast())
        .offset(skip)
        .limit(limit)
    )

    items = db.scalars(stmt).all()
    return PaginatedList[LinkedInJobDetails](
        items=list(items),
        total=total_count if total_count is not None else 0,
        page=(skip // limit) + 1 if limit > 0 else 1,
        page_size=limit,
    )


def update_linkedin_details(db: Session, job: LinkedInJobDetails) -> None:
    db.merge(job)
    db.commit()


def update_linkedin_details_bulk(db: Session, jobs: List[LinkedInJobDetails]) -> None:
    for job in jobs:
        db.merge(job)
    db.commit()
