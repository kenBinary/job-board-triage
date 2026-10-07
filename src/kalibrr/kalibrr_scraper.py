import asyncio
import math
import random
from sqlalchemy.orm import Session

from src.common.error_tracker import ConsecutiveErrorTracker
from src.db.database import SessionLocal
from src.kalibrr.db import create_kalibrr_details_bulk, get_kalibrr_details_by_job_id
from src.kalibrr.get_jobs import fetch_jobs
from src.kalibrr.models.kalibrr_job_details import KalibrrJobDetails
from src.kalibrr.models.kalibrr_link import KalibrrLink, KalibrrParams

BASE_URL = "https://www.kalibrr.com/kjs/job_board/search"

LINKS: list[KalibrrLink] = [
    # KalibrrLink(
    #     max_page=2,
    #     base_url=BASE_URL,
    #     params=KalibrrParams(text="developer", is_work_from_home=True, country="Philippines"),
    # ),
    # KalibrrLink(
    #     max_page=2,
    #     base_url=BASE_URL,
    #     params=KalibrrParams(text="software", is_work_from_home=True, country="Philippines"),
    # ),
    # KalibrrLink(
    #     max_page=2,
    #     base_url=BASE_URL,
    #     params=KalibrrParams(text="engineer", is_work_from_home=True, country="Philippines"),
    # ),
    # KalibrrLink(
    #     max_page=2,
    #     base_url=BASE_URL,
    #     params=KalibrrParams(text="web", is_work_from_home=True, country="Philippines"),
    # ),
    # KalibrrLink(
    #     max_page=2,
    #     base_url=BASE_URL,
    #     params=KalibrrParams(text=".net", is_work_from_home=True, country="Philippines"),
    # ),
    KalibrrLink(
        max_page=2,
        base_url=BASE_URL,
        params=KalibrrParams(location="Cagayan de Oro"),
    ),
    KalibrrLink(
        max_page=2,
        base_url=BASE_URL,
        params=KalibrrParams(location="Davao City"),
    ),
    KalibrrLink(
        max_page=2,
        base_url=BASE_URL,
        params=KalibrrParams(location="Cebu City"),
    ),
]


async def scrape_kalibrr_link(db: Session, link_target: KalibrrLink) -> None:
    """Scrape a single Kalibrr search target across up to max_page pages."""
    print(f"Scraping Kalibrr — text: '{link_target.params.text}'")

    for current_page in range(1, link_target.max_page + 1):
        page_url = link_target.get_next_page(current_page)
        current_offset = link_target.params.offset + (
            (current_page - 1) * link_target.params.limit
        )
        print(f"  Fetching page {current_page} (offset={current_offset}): {page_url}")

        try:
            response = await fetch_jobs(page_url)

            total = response.count
            max_reachable_pages = (
                math.ceil(total / link_target.params.limit) if total > 0 else 0
            )

            print(
                f"  Total jobs available: {total} | "
                f"Page {current_page} of {max_reachable_pages}"
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
                print(f"  Saved {len(new_jobs)} new job(s) from page {current_page}.")

            if current_page >= max_reachable_pages:
                print(
                    f"  Reached last available page ({max_reachable_pages}). Stopping."
                )
                break

            if current_page < link_target.max_page:
                delay = random.uniform(5.0, 10.0)
                print(f"  Sleeping {delay:.1f}s before next page...")
                await asyncio.sleep(delay)

        except Exception as e:
            print(
                f"  Error on page {current_page} for '{link_target.params.text}': {e}"
            )
            raise


async def scrape_kalibrr(links: list[KalibrrLink] | None = None) -> None:
    """Scrape all configured Kalibrr search targets."""
    targets = links if links is not None else LINKS
    tracker = ConsecutiveErrorTracker("Kalibrr")

    try:
        with SessionLocal() as db:
            total = len(targets)
            for index, link_target in enumerate(targets):
                print("=" * 50)
                try:
                    await scrape_kalibrr_link(db, link_target)
                    tracker.record_success()
                except Exception as e:
                    if tracker.record_error(e):
                        break

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
