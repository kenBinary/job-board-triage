import asyncio
import random
from dataclasses import dataclass, field
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.orm import Session

from src.db.database import SessionLocal
from src.mynimo.db import create_mynimo_details_bulk, get_mynimo_details_by_job_id
from src.mynimo.get_jobs import fetch_jobs
from src.mynimo.models.mynimo_job_details import MynimoJobDetails


@dataclass
class MynimoLink:
    """Represents a single Mynimo search target with its own max_pages setting."""

    url: str
    max_pages: int = field(default=2)

    def get_page_url(self, page: int) -> str:
        parsed = urlsplit(self.url)
        params = parse_qsl(parsed.query, keep_blank_values=True)
        params = [(key, value) for key, value in params if key.lower() != "page"]
        params.append(("page", str(page)))

        query = urlencode(params)
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, ""))


LINKS: list[MynimoLink] = [
    MynimoLink(
        url="https://www.mynimo.com/api/jobs/local/browse?path=%2Fcebu-jobs&page=1",
        max_pages=2,
    ),
    MynimoLink(
        url="https://www.mynimo.com/api/jobs/local/browse?path=%2Fcdo-jobs&page=1",
        max_pages=2,
    ),
    MynimoLink(
        url="https://www.mynimo.com/api/jobs/local/browse?path=%2Fdavao-jobs&page=1",
        max_pages=2,
    ),
    MynimoLink(
        url="https://www.mynimo.com/api/jobs/local/browse?path=%2Fhome-based-jobs&page=1",
        max_pages=2,
    ),
]


async def scrape_mynimo_link(db: Session, link_target: MynimoLink) -> None:
    """Scrape a single Mynimo search target across up to max_pages pages."""
    print(f"Scraping Mynimo link: {link_target.url}")

    for page_num in range(1, link_target.max_pages + 1):
        page_url = link_target.get_page_url(page_num)
        print(f"  Fetching page {page_num}: {page_url}")

        try:
            response = await fetch_jobs(page_url)
            pagination = response.data.jobs.result

            last_page = pagination.last_page
            total = pagination.total
            print(f"  Total jobs: {total} | Page {page_num} of {last_page}")

            new_jobs: list[MynimoJobDetails] = []

            for job in pagination.data:
                job_id_str = str(job.id)

                existing = get_mynimo_details_by_job_id(db, job_id_str)
                if existing:
                    print(f"  [SKIP] [{job_id_str}] {job.title} — already in DB")
                    print("  " + "-" * 48)
                    continue

                if any(j.job_id == job_id_str for j in new_jobs):
                    continue

                job_details = MynimoJobDetails.from_api_data(job)
                new_jobs.append(job_details)

                location_parts = [
                    p
                    for p in (
                        job.barangay_name,
                        job.location_name,
                        job.location_parent_name,
                    )
                    if p and p.strip()
                ]
                location_display = (
                    ", ".join(location_parts) or job.overseas_location or "N/A"
                )

                salary_display = "N/A"
                if not job.hide_salary and (job.min_salary or job.max_salary):
                    salary_display = (
                        f"PHP {job.min_salary:,} - {job.max_salary:,} / Monthly"
                    )

                print(f"  [{job_id_str}] {job.title}")
                print(f"    Company  : {job.company or 'N/A'}")
                print(f"    Location : {location_display}")
                print(f"    Salary   : {salary_display}")
                print(f"    URL      : https://www.mynimo.com/jobs/view/{job_id_str}")
                print("  " + "-" * 48)

            if new_jobs:
                create_mynimo_details_bulk(db, new_jobs)
                print(f"  Saved {len(new_jobs)} new job(s) from page {page_num}.")

            if page_num >= last_page:
                print(f"  Reached last page ({last_page}). Stopping pagination.")
                break

            if page_num < link_target.max_pages:
                delay = random.uniform(4.0, 10.0)
                print(f"  Sleeping {delay:.1f}s before next page...")
                await asyncio.sleep(delay)

        except Exception as e:
            print(f"  Error on page {page_num} of {link_target.url}: {e}")
            break


async def scrape_mynimo(links: list[MynimoLink] | None = None) -> None:
    """Scrape all configured Mynimo search targets."""
    targets = links if links is not None else LINKS

    try:
        with SessionLocal() as db:
            total = len(targets)
            for index, link_target in enumerate(targets):
                print("=" * 50)
                await scrape_mynimo_link(db, link_target)

                if index < total - 1:
                    delay = random.uniform(3.0, 6.0)
                    print(f"Sleeping {delay:.1f}s before next search target...")
                    await asyncio.sleep(delay)

        print("=" * 50)
        print("Mynimo scraping complete.")

    except Exception as e:
        print(f"Error occurred while scraping Mynimo: {e}")


if __name__ == "__main__":
    asyncio.run(scrape_mynimo())
