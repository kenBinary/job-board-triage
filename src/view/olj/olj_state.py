from typing import List, Optional

from src.db.database import SessionLocal
from src.db.entities import PaginatedList
from src.olj.db import (
    GetOljDetailsFilters,
    get_olj_job_details_list,
    update_olj_details_bulk,
)
from src.olj.models.olj_job_details import OljJobDetails


class OljState:
    paginated_jobs: PaginatedList[OljJobDetails]
    jobs: List[OljJobDetails]
    search_query: str
    show_new_only: bool

    def __init__(self):
        self.paginated_jobs = PaginatedList(items=[], total=0, page=1, page_size=25)
        self.jobs = []
        self.search_query = ""
        self.show_new_only = True

    def get_jobs(
        self,
        filters: Optional[GetOljDetailsFilters] = None,
        skip: int = 0,
        limit: int = 10,
    ) -> PaginatedList[OljJobDetails]:
        with SessionLocal() as db:
            paginated_jobs = get_olj_job_details_list(
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
            update_olj_details_bulk(db, jobs_to_update)

    @property
    def total_count(self):
        return len(self.jobs)


olj_state = OljState()
