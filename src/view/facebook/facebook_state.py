from typing import List, Optional

from src.db.database import SessionLocal
from src.db.entities import PaginatedList
from src.facebook_posts.db import (
    get_facebook_post_job_details_list,
    update_facebook_post_details_bulk,
)
from src.facebook_posts.models.facebook_post_job_details import FacebookPostJobDetails


class FacebookState:
    paginated_jobs: PaginatedList[FacebookPostJobDetails]
    jobs: List[FacebookPostJobDetails]
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
    ) -> PaginatedList[FacebookPostJobDetails]:
        with SessionLocal() as db:
            active_category = category if category is not None else self.category
            paginated_jobs = get_facebook_post_job_details_list(
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
            update_facebook_post_details_bulk(db, jobs_to_update)

    @property
    def total_count(self):
        return len(self.jobs)


facebook_state = FacebookState()
