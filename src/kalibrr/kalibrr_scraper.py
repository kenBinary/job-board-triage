import asyncio
import math
import random
from dataclasses import dataclass, field
from urllib.parse import urlencode

from sqlalchemy.orm import Session

from src.db.database import SessionLocal
from src.kalibrr.db import create_kalibrr_details_bulk, get_kalibrr_details_by_job_id
from src.kalibrr.get_jobs import fetch_jobs
from src.kalibrr.models.kalibrr_job_details import KalibrrJobDetails

_BASE_URL = "https://www.kalibrr.com/kjs/job_board/search"
_FIXED_PARAMS = {
    "sort_direction": "desc",
    "sort_field": "activation_date",
}


@dataclass
class KalibrrLink:
    """Represents a single Kalibrr search target.

    ``text``, ``offset``, ``country``, and ``location`` can be configured per
    search target. Other query parameters are fixed by the platform.
    """

    text: str | None = field(default=None)
    offset: int = field(default=0)
    limit: int = field(default=15)
    max_pages: int = field(default=2)
    country: str | None = field(default=None)
    location: str | None = field(default=None)
    is_work_from_home: bool = field(default=False)

    def get_page_url(self, page_index: int) -> str:
        """Build the full API URL for a given page index (0-based)."""
        current_offset = self.offset + (page_index * self.limit)
        params = {
            "limit": str(self.limit),
            "offset": str(current_offset),
            **_FIXED_PARAMS,
        }

        if self.is_work_from_home:
            params["is_work_from_home"] = "true"
        if self.text is not None:
            params["text"] = self.text
        if self.country is not None:
            params["country"] = self.country
        if self.location is not None:
            params["location"] = self.location

        return f"{_BASE_URL}?{urlencode(params)}"


LINKS: list[KalibrrLink] = [
    # KalibrrLink(
    #     text="developer", max_pages=2, is_work_from_home=True, country="Philippines"
    # ),
    # KalibrrLink(
    #     text="software", max_pages=2, is_work_from_home=True, country="Philippines"
    # ),
    # KalibrrLink(
    #     text="engineer", max_pages=2, is_work_from_home=True, country="Philippines"
    # ),
    # KalibrrLink(text="web", max_pages=2, is_work_from_home=True, country="Philippines"),
    # KalibrrLink(
    #     text=".net", max_pages=2, is_work_from_home=True, country="Philippines"
    # ),
    KalibrrLink(max_pages=2, location="Cagayan de Oro"),
    KalibrrLink(max_pages=2, location="Davao City"),
    KalibrrLink(max_pages=2, location="Cebu City"),
]


async def scrape_kalibrr_link(db: Session, link_target: KalibrrLink) -> None:
    """Scrape a single Kalibrr search target across up to max_pages pages."""
    print(f"Scraping Kalibrr — text: '{link_target.text}'")

    for page_index in range(link_target.max_pages):
        page_url = link_target.get_page_url(page_index)
        current_offset = link_target.offset + (page_index * link_target.limit)
        print(f"  Fetching page {page_index + 1} (offset={current_offset}): {page_url}")

        try:
            response = await fetch_jobs(page_url)

            total = response.count
            max_reachable_pages = (
                math.ceil(total / link_target.limit) if total > 0 else 0
            )

            print(
                f"  Total jobs available: {total} | "
                f"Page {page_index + 1} of {max_reachable_pages}"
            )

            if not response.jobs:
                print("  No jobs returned. Stopping pagination.")
                break

            new_jobs: list[KalibrrJobDetails] = []

            for job in response.jobs:
                job_id_str = str(job.id)

                existing = get_kalibrr_details_by_job_id(db, job_id_str)
                if existing:
                    print(f"  [SKIP] [{job_id_str}] {job.name} — already in DB")
                    print("  " + "-" * 48)
                    continue

                if any(j.job_id == job_id_str for j in new_jobs):
                    continue

                job_details = KalibrrJobDetails.from_api_data(job)
                new_jobs.append(job_details)

                salary_display = "N/A"
                if job.salary_shown and (job.base_salary or job.maximum_salary):
                    currency = job.salary_currency or ""
                    lo = f"{job.base_salary:,.0f}" if job.base_salary else "?"
                    hi = f"{job.maximum_salary:,.0f}" if job.maximum_salary else "?"
                    interval = job.salary_interval or ""
                    salary_display = f"{currency} {lo} - {hi} / {interval}".strip()

                location_display = job_details.location or "N/A"

                print(f"  [{job_id_str}] {job.name}")
                print(f"    Company  : {job.company_name or 'N/A'}")
                print(f"    Location : {location_display}")
                print(f"    Salary   : {salary_display}")
                print(
                    f"    WFH      : {job.is_work_from_home} | Hybrid: {job.is_hybrid}"
                )
                print(f"    URL      : {job_details.url}")
                print("  " + "-" * 48)

            if new_jobs:
                create_kalibrr_details_bulk(db, new_jobs)
                print(f"  Saved {len(new_jobs)} new job(s) from page {page_index + 1}.")

            if page_index + 1 >= max_reachable_pages:
                print(
                    f"  Reached last available page ({max_reachable_pages}). Stopping."
                )
                break

            if page_index < link_target.max_pages - 1:
                delay = random.uniform(5.0, 10.0)
                print(f"  Sleeping {delay:.1f}s before next page...")
                await asyncio.sleep(delay)

        except Exception as e:
            print(f"  Error on page {page_index + 1} for '{link_target.text}': {e}")
            break


async def scrape_kalibrr(links: list[KalibrrLink] | None = None) -> None:
    """Scrape all configured Kalibrr search targets."""
    targets = links if links is not None else LINKS

    try:
        with SessionLocal() as db:
            total = len(targets)
            for index, link_target in enumerate(targets):
                print("=" * 50)
                await scrape_kalibrr_link(db, link_target)

                if index < total - 1:
                    delay = random.uniform(4.0, 8.0)
                    print(f"Sleeping {delay:.1f}s before next search target...")
                    await asyncio.sleep(delay)

        print("=" * 50)
        print("Kalibrr scraping complete.")

    except Exception as e:
        print(f"Error occurred while scraping Kalibrr: {e}")


if __name__ == "__main__":
    asyncio.run(scrape_kalibrr())
