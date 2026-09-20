from typing import List, Optional
from sqlalchemy import UUID, select
from sqlalchemy.orm import Session
from src.jobstreet.models.jobstreet_job_details import JobStreetJobDetails


def create_jobstreet_details(
    db: Session, job_street_detail: JobStreetJobDetails
) -> UUID:

    db.add(job_street_detail)
    db.commit()
    db.refresh(job_street_detail)

    return job_street_detail.id


def create_jobstreet_details_bulk(
    db: Session, job_street_details: List[JobStreetJobDetails]
) -> List[UUID]:

    db.add_all(job_street_details)
    db.commit()

    return [job.id for job in job_street_details]


def update_jobstreet_details(
    db: Session, job_street_detail: JobStreetJobDetails
) -> None:

    db.merge(job_street_detail)
    db.commit()


def get_jobstreet_details_by_job_id(
    db: Session, job_id: str
) -> Optional[JobStreetJobDetails]:

    stmt = select(JobStreetJobDetails).where(JobStreetJobDetails.job_id == job_id)
    db_job = db.scalar(stmt)

    return db_job


def get_jobstreet_details(
    db: Session, skip: int = 0, limit: int = 10
) -> List[JobStreetJobDetails]:

    stmt = select(JobStreetJobDetails).offset(skip).limit(limit)
    job_details = db.scalars(stmt).all()

    return job_details
