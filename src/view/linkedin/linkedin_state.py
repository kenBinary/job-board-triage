from typing import List, Optional

from src.db.database import SessionLocal
from src.db.entities import PaginatedList
from src.linkedin_posts.db import (
    get_linkedin_post_job_details_list,
    update_linkedin_post_details_bulk,
)
from src.linkedin_posts.models.linkedin_post_job_details import LinkedInPostJobDetails


class LinkedInState:
    paginated_jobs: PaginatedList[LinkedInPostJobDetails]
    jobs: List[LinkedInPostJobDetails]
    search_query: str
    show_new_only: bool
    category: Optional[str]

    def __init__(self):
        self.paginated_jobs = PaginatedList(items=[], total=0, page=1, page_size=25)
        self.jobs = []
        self.search_query = ""
        self.show_new_only = True
        self.category = None

    def get_jobs(
        self,
        keyword: Optional[str] = None,
        work_type: Optional[str] = None,
        category: Optional[str] = None,
        is_new: Optional[bool] = None,
        skip: int = 0,
        limit: int = 25,
    ) -> PaginatedList[LinkedInPostJobDetails]:
        with SessionLocal() as db:
            active_category = category if category is not None else self.category
            paginated_jobs = get_linkedin_post_job_details_list(
                db=db,
                keyword=keyword if keyword is not None else (self.search_query or None),
                work_type=work_type,
                category=active_category,
                is_new=is_new,
                skip=skip,
                limit=limit,
            )
            self.paginated_jobs = paginated_jobs
            self.jobs = paginated_jobs.items
            return paginated_jobs

    def update_all_jobs_as_seen(self):
        jobs_to_update = [job for job in self.jobs if job.is_new]
        for job in jobs_to_update:
            job.is_new = False
        with SessionLocal() as db:
            update_linkedin_post_details_bulk(db, jobs_to_update)

    @property
    def total_count(self):
        return len(self.jobs)


linkedin_state = LinkedInState()
