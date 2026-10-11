from typing import List, Optional
import uuid
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db.entities import PaginatedList
from .models.facebook_post_job_details import FacebookPostJobDetails


def create_facebook_post_details(
    db: Session,
    job: FacebookPostJobDetails,
) -> uuid.UUID:
    db.add(job)
    db.commit()
    db.refresh(job)
    return job.id


def create_facebook_post_details_bulk(
    db: Session,
    jobs: List[FacebookPostJobDetails],
) -> List[uuid.UUID]:
    db.add_all(jobs)
    db.commit()
    return [j.id for j in jobs]


def get_facebook_post_by_job_id(
    db: Session,
    job_id: str,
) -> Optional[FacebookPostJobDetails]:
    stmt = select(FacebookPostJobDetails).where(FacebookPostJobDetails.job_id == job_id)
    return db.scalar(stmt)


def get_facebook_post_job_details_list(
    db: Session,
    keyword: Optional[str] = None,
    work_type: Optional[str] = None,
    category: Optional[str] = None,
    is_new: Optional[bool] = None,
    skip: int = 0,
    limit: int = 25,
) -> PaginatedList[FacebookPostJobDetails]:
    from sqlalchemy import or_

    stmt = select(FacebookPostJobDetails)

    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                FacebookPostJobDetails.title.ilike(pattern),
                FacebookPostJobDetails.company_name.ilike(pattern),
                FacebookPostJobDetails.short_description.ilike(pattern),
                FacebookPostJobDetails.description.ilike(pattern),
            )
        )

    if work_type is not None:
        stmt = stmt.where(FacebookPostJobDetails.work_type == work_type)

    if category is not None:
        stmt = stmt.where(FacebookPostJobDetails.category == category)

    if is_new is not None:
        stmt = stmt.where(FacebookPostJobDetails.is_new == is_new)

    total_count = db.scalar(select(func.count()).select_from(stmt.subquery()))

    stmt = (
        stmt.order_by(FacebookPostJobDetails.posted_at_utc.desc().nullslast())
        .offset(skip)
        .limit(limit)
    )

    items = db.scalars(stmt).all()
    return PaginatedList[FacebookPostJobDetails](
        items=list(items),
        total=total_count if total_count is not None else 0,
        page=(skip // limit) + 1 if limit > 0 else 1,
        page_size=limit,
    )


def update_facebook_post_details(db: Session, job: FacebookPostJobDetails) -> None:
    db.merge(job)
    db.commit()


def update_facebook_post_details_bulk(
    db: Session, jobs: List[FacebookPostJobDetails]
) -> None:
    for job in jobs:
        db.merge(job)
    db.commit()
