from typing import List, Optional

from src.db.database import SessionLocal
from src.db.entities import PaginatedList
from src.kalibrr.db import (
    GetKalibrrDetailsFilters,
    get_kalibrr_job_details_list,
    update_kalibrr_details_bulk,
)
from src.kalibrr.models.kalibrr_job_details import KalibrrJobDetails


class KalibrrState:
    paginated_jobs: PaginatedList[KalibrrJobDetails]
    jobs: List[KalibrrJobDetails]
    search_query: str
    show_new_only: bool

    def __init__(self):
        self.paginated_jobs = PaginatedList(items=[], total=0, page=1, page_size=25)
        self.jobs = []
        self.search_query = ""
        self.show_new_only = True

    def get_jobs(
        self,
        filters: Optional[GetKalibrrDetailsFilters] = None,
        skip: int = 0,
        limit: int = 10,
    ) -> PaginatedList[KalibrrJobDetails]:
        with SessionLocal() as db:
            paginated_jobs = get_kalibrr_job_details_list(
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
            update_kalibrr_details_bulk(db, jobs_to_update)

    @property
    def total_count(self):
        return len(self.jobs)


kalibrr_state = KalibrrState()
