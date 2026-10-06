from typing import List, Optional
import uuid
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.db.entities import PaginatedList
from .models.linkedin_post_job_details import LinkedInPostJobDetails


def create_linkedin_post_details(
    db: Session,
    job: LinkedInPostJobDetails,
) -> uuid.UUID:
    db.add(job)
    db.commit()
    db.refresh(job)
    return job.id


def create_linkedin_post_details_bulk(
    db: Session,
    jobs: List[LinkedInPostJobDetails],
) -> List[uuid.UUID]:
    db.add_all(jobs)
    db.commit()
    return [j.id for j in jobs]


def get_linkedin_post_by_job_id(
    db: Session,
    job_id: str,
) -> Optional[LinkedInPostJobDetails]:
    stmt = select(LinkedInPostJobDetails).where(
        LinkedInPostJobDetails.job_id == job_id
    )
    return db.scalar(stmt)


def get_linkedin_post_job_details_list(
    db: Session,
    keyword: Optional[str] = None,
    work_type: Optional[str] = None,
    is_new: Optional[bool] = None,
    skip: int = 0,
    limit: int = 25,
) -> PaginatedList[LinkedInPostJobDetails]:
    from sqlalchemy import or_

    stmt = select(LinkedInPostJobDetails)

    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                LinkedInPostJobDetails.title.ilike(pattern),
                LinkedInPostJobDetails.company_name.ilike(pattern),
                LinkedInPostJobDetails.short_description.ilike(pattern),
                LinkedInPostJobDetails.description.ilike(pattern),
            )
        )

    if work_type is not None:
        stmt = stmt.where(LinkedInPostJobDetails.work_type == work_type)

    if is_new is not None:
        stmt = stmt.where(LinkedInPostJobDetails.is_new == is_new)

    total_count = db.scalar(select(func.count()).select_from(stmt.subquery()))

    stmt = (
        stmt.order_by(LinkedInPostJobDetails.posted_at_utc.desc().nullslast())
        .offset(skip)
        .limit(limit)
    )

    items = db.scalars(stmt).all()
    return PaginatedList[LinkedInPostJobDetails](
        items=list(items),
        total=total_count if total_count is not None else 0,
        page=(skip // limit) + 1 if limit > 0 else 1,
        page_size=limit,
    )
