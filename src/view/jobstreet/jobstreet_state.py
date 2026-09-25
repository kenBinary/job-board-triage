from typing import List, Optional

from src.db.database import SessionLocal
from src.db.entities import PaginatedList
from src.jobstreet.db import (
    GetJobstreetDetailsFilters,
    get_jobstreet_job_details_list,
    update_jobstreet_details_bulk,
)
from src.jobstreet.models.jobstreet_job_details import JobStreetJobDetails


class JobStreetState:
    paginated_jobs: PaginatedList[JobStreetJobDetails]
    jobs: List[JobStreetJobDetails]
    search_query: str
    show_new_only: bool

    def __init__(self):
        self.paginated_jobs = PaginatedList(items=[], total=0, page=1, page_size=25)
        self.jobs = []
        self.search_query = ""
        self.show_new_only = True

    def get_jobs(
        self,
        filters: Optional[GetJobstreetDetailsFilters] = None,
        skip: int = 0,
        limit: int = 25,
    ) -> PaginatedList[JobStreetJobDetails]:
        with SessionLocal() as db:
            paginated_jobs = get_jobstreet_job_details_list(
                db, filters, skip=skip, limit=limit
            )
            self.paginated_jobs = paginated_jobs
            self.jobs = paginated_jobs.items
            return paginated_jobs

    def update_all_jobs_as_seen(self):

        jobs_to_update = [job for job in self.jobs if job.is_new]
        for job in jobs_to_update:
            job.is_new = False
        with SessionLocal() as db:
            update_jobstreet_details_bulk(db, jobs_to_update)

    @property
    def total_count(self):
        return len(self.jobs)


jobstreet_state = JobStreetState()
