import asyncio
from datetime import datetime, timezone
import random
from typing import Optional
from playwright.async_api import BrowserContext, Page

from src.common.infra.browser_context import CamoufoxSingleton
from src.db.database import SessionLocal
from src.linkedin_posts.linkedin_posts_run_tracker import LinkedinPostsRunTracker
from src.linkedin_posts.models.linkedin_post_link import (
    LinkedInPostLink,
    LinkedInPostParams,
)
from .db import (
    create_linkedin_post_details_bulk,
    get_linkedin_post_by_job_id,
)
from .llm_extractor import extract_jobs_from_post
from .models.linkedin_post_job_details import LinkedInPostJobDetails
from .utils import extract_linkedin_post_data

PROFILE_DIR = "./camoufox_profile"

POST_CLICK_DELAY_MIN: float = 2.0
POST_CLICK_DELAY_MAX: float = 3.5

CONTROL_MENU_URL_FRAGMENT = "feedUpdateControlMenuRequest"

DEFAULT_LINKS: list[LinkedInPostLink] = [
    LinkedInPostLink(params=LinkedInPostParams(keywords="#remotejobsph")),
    LinkedInPostLink(params=LinkedInPostParams(keywords="#jobsphilippines")),
    LinkedInPostLink(params=LinkedInPostParams(keywords="#hiringphilippines")),
    LinkedInPostLink(params=LinkedInPostParams(keywords="#jobsph")),
    LinkedInPostLink(params=LinkedInPostParams(keywords="#hiringph")),
    LinkedInPostLink(params=LinkedInPostParams(keywords="#philippinejobs")),
    LinkedInPostLink(params=LinkedInPostParams(keywords="#onlinejobsph")),
    LinkedInPostLink(params=LinkedInPostParams(keywords="#workfromhomeph")),
    LinkedInPostLink(params=LinkedInPostParams(keywords="#cebujobs")),
    LinkedInPostLink(params=LinkedInPostParams(keywords="#cdohiring")),
    LinkedInPostLink(params=LinkedInPostParams(keywords="#cdojobs")),
]


async def _get_image_urls_from_element(page: Page, element_id: str) -> list[str]:
    """
    Extract resolved image URLs from a post element, capping quality at 1080w.
    Looks for img[alt='view image'] elements with srcset or src.
    """
    return await page.evaluate(
        """
        (elementId) => {
            const el = document.getElementById(elementId);
            if (!el) return [];

            const imgs = el.querySelectorAll('img[alt="view image" i]');
            const results = [];

            for (const img of imgs) {
                const srcset = img.srcset || img.getAttribute('srcset');
                if (srcset) {
                    // Parse srcset: "url 720w, url 1080w, ..."
                    const candidates = [];
                    for (const part of srcset.split(',')) {
                        const tokens = part.trim().split(/\\s+/);
                        if (tokens.length === 2) {
                            const url = tokens[0];
                            const width = parseInt(tokens[1].toLowerCase().replace('w', ''));
                            if (!isNaN(width)) candidates.push([width, url]);
                        }
                    }
                    if (candidates.length) {
                        // Prefer 720-1080 range
                        const inRange = candidates.filter(([w]) => w >= 720 && w <= 1080);
                        if (inRange.length) {
                            const best = inRange.reduce((a, b) => a[0] > b[0] ? a : b);
                            results.push(best[1]);
                            continue;
                        }
                        // Below 720: take the max
                        const below = candidates.filter(([w]) => w < 720);
                        if (below.length) {
                            results.push(below.reduce((a, b) => a[0] > b[0] ? a : b)[1]);
                            continue;
                        }
                        // Above 1080: take the min
                        const above = candidates.filter(([w]) => w > 1080);
                        if (above.length) {
                            results.push(above.reduce((a, b) => a[0] < b[0] ? a : b)[1]);
                            continue;
                        }
                    }
                }
                // Fallback to src
                if (img.src) results.push(img.src);
            }
            return results;
        }
        """,
        element_id,
    )


async def _scroll_feed(page: Page, link: LinkedInPostLink) -> None:
    """Scroll the LinkedIn feed according to the link's scroll config."""
    print("  Scrolling feed...")
    current_scroll = 0
    while link.should_continue(current_scroll):
        await page.evaluate("""() => {
            const allDivs = document.querySelectorAll('div[id^="expanded"]');
            if (allDivs.length > 0) {
                allDivs[allDivs.length - 1].scrollIntoView({ behavior: 'smooth', block: 'end' });
            }
        }""")
        await asyncio.sleep(random.uniform(0.5, 2.5))
        current_scroll += 1
    print("  Scroll complete.")


async def _scrape_link(page: Page, db, link: LinkedInPostLink) -> None:
    url = link.get_url()
    print(f"\n{'='*60}")
    print(f"Keyword: {link.params.keywords}")
    print(f"URL: {url}")
    print("=" * 60)

    await page.goto(url, wait_until="domcontentloaded")
    await asyncio.sleep(random.uniform(3.5, 8.0))

    if "authwall" in page.url.lower() or "login" in page.url.lower():
        input("LinkedIn requires login. Please log in and press Enter to continue...")

    await _scroll_feed(page, link)

    post_elements = await page.query_selector_all('div[id^="expanded"]')
    print(f"  Found {len(post_elements)} post elements.")

    new_jobs: list[LinkedInPostJobDetails] = []

    for idx, element in enumerate(post_elements):
        element_id = await element.get_attribute("id")
        if not element_id:
            continue

        print(f"\n  [{idx + 1}/{len(post_elements)}] Processing post: #{element_id}")

        post_url: Optional[str] = None
        share_id: Optional[str] = None

        try:
            control_btn = await element.query_selector(
                'button[aria-label*="Open control menu" i]'
            )
            if not control_btn:
                print("    [skip] No control menu button found — skipping.")
                continue

            async with page.expect_response(
                lambda r: CONTROL_MENU_URL_FRAGMENT in r.url,
                timeout=15000,
            ) as resp_info:
                await control_btn.click()

            response = await resp_info.value
            response_body = await response.body()
            response_text = response_body.decode("utf-8", errors="replace")

            try:
                post_url, share_id = extract_linkedin_post_data(response_text)
                print(f"    share_id={share_id}, url={post_url}")
            except ValueError as e:
                print(f"    [warn] extract_linkedin_post_data: {e}")

            await asyncio.sleep(random.uniform(0.5, 1.5))
            await page.keyboard.press("Escape")

        except Exception as e:
            print(f"    [error] Control menu interception failed: {e}")
            await page.keyboard.press("Escape")

        if not share_id:
            print("    [skip] Could not obtain share_id — skipping.")
            await asyncio.sleep(
                random.uniform(POST_CLICK_DELAY_MIN, POST_CLICK_DELAY_MAX)
            )
            continue

        post_text = await element.evaluate("el => el.textContent") or ""
        post_text = post_text.strip()

        # TODO: Get Image Base64 directly without downloading
        image_urls = await _get_image_urls_from_element(page, element_id)
        print(f"    Images found: {len(image_urls)}")

        try:
            extraction = await extract_jobs_from_post(post_text, image_urls)
        except Exception as e:
            print(f"    [error] LLM extraction failed: {e}")
            await asyncio.sleep(
                random.uniform(POST_CLICK_DELAY_MIN, POST_CLICK_DELAY_MAX)
            )
            continue

        if not extraction.is_job_post:
            print("    [skip] LLM determined this is not a job post.")
            await asyncio.sleep(
                random.uniform(POST_CLICK_DELAY_MIN, POST_CLICK_DELAY_MAX)
            )
            continue

        print(f"    Extracted {len(extraction.jobs)} job(s).")

        for job_idx, job in enumerate(extraction.jobs):
            job_id = (
                share_id if len(extraction.jobs) == 1 else f"{share_id}_{job_idx + 1}"
            )

            if get_linkedin_post_by_job_id(db, job_id):
                print(f"    [dup] Job {job_id} already in DB — skipping.")
                continue

            record = LinkedInPostJobDetails.from_extracted(
                job=job,
                job_id=job_id,
                post_url=post_url or "",
            )
            # TODO: actually get the posted date from the post, not just the current time
            record.posted_at_utc = datetime.now(timezone.utc).isoformat()
            new_jobs.append(record)
            print(f"    + [{job_id}] {job.title} @ {job.company_name or 'Unknown'}")

        await asyncio.sleep(random.uniform(1.5, 3.0))

    if new_jobs:
        create_linkedin_post_details_bulk(db, new_jobs)
        print(f"\n  Saved {len(new_jobs)} new job record(s) to the database.")
    else:
        print("\n  No new job records to save.")


async def scrape_linkedin_posts(
    links: Optional[list[LinkedInPostLink]] = None,
    is_retry: bool = False,
) -> None:
    targets = links if links is not None else DEFAULT_LINKS
    tracker = LinkedinPostsRunTracker(links=targets, is_retry_run=is_retry)

    try:
        context = await CamoufoxSingleton.get_context()
        assert isinstance(context, BrowserContext)
        page = await context.new_page()

        with SessionLocal() as db:
            total_items = len(targets)
            for index, link in enumerate(targets):
                tracker.set_current_index(index)
                print(f"Scraping LinkedIn Posts target {index + 1} of {total_items}")
                try:
                    await _scrape_link(page, db, link)
                    tracker.record_success()
                except Exception as e:
                    if tracker.record_link_error(link=link, error=e):
                        break

                if index < total_items - 1:
                    await asyncio.sleep(random.uniform(5.0, 15.0))

                print("" + "=" * 50 + "\n")

        tracker.finalize()

    except Exception as e:
        print(f"[fatal] Scraper terminated: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(scrape_linkedin_posts())
