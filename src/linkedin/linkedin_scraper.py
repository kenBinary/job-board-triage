import asyncio
import random
from typing import List, Optional, Tuple, TypedDict
from playwright.async_api import Page

from src.common.infra.browser_context import CamoufoxSingleton
from src.common.logger import format_job_log, get_logger
from src.db.database import SessionLocal
from src.linkedin.db import (
    create_linkedin_details_bulk,
    get_existing_job_ids,
)
from src.linkedin.linkedin_llm_extractor import LinkedInJobLLMExtractor
from src.linkedin.linkedin_run_tracker import LinkedinRunTracker
from src.linkedin.models.job_card import JobCardRawData
from src.linkedin.models.linkedin_job_details import LinkedInJobDetails
from src.linkedin.models.linkedin_link import LinkedInLink, LinkedInParams, LocationEnum

logger = get_logger("linkedin_scraper")

linkedin_job_extractor = LinkedInJobLLMExtractor()

BASE_SEARCH_URL = "https://www.linkedin.com/jobs/search-results/"
DEFAULT_LINKS: list[LinkedInLink] = [
    LinkedInLink(
        base_url=BASE_SEARCH_URL,
        max_page=5,
        params=LinkedInParams(keywords="developer", location=LocationEnum.PHILIPPINES),
    ),
    LinkedInLink(
        base_url=BASE_SEARCH_URL,
        max_page=5,
        params=LinkedInParams(keywords="software", location=LocationEnum.PHILIPPINES),
    ),
    LinkedInLink(
        base_url=BASE_SEARCH_URL,
        max_page=5,
        params=LinkedInParams(keywords="engineer", location=LocationEnum.PHILIPPINES),
    ),
    LinkedInLink(
        base_url=BASE_SEARCH_URL,
        max_page=5,
        params=LinkedInParams(keywords="developer", location=LocationEnum.CEBU),
    ),
    LinkedInLink(
        base_url=BASE_SEARCH_URL,
        max_page=5,
        params=LinkedInParams(keywords="software", location=LocationEnum.CEBU),
    ),
    LinkedInLink(
        base_url=BASE_SEARCH_URL,
        max_page=5,
        params=LinkedInParams(keywords="engineer", location=LocationEnum.CEBU),
    ),
    LinkedInLink(
        base_url=BASE_SEARCH_URL,
        max_page=5,
        params=LinkedInParams(
            keywords="developer", location=LocationEnum.CAGAYAN_DE_ORO
        ),
    ),
    LinkedInLink(
        base_url=BASE_SEARCH_URL,
        max_page=5,
        params=LinkedInParams(
            keywords="software", location=LocationEnum.CAGAYAN_DE_ORO
        ),
    ),
    LinkedInLink(
        base_url=BASE_SEARCH_URL,
        max_page=5,
        params=LinkedInParams(keywords="c#", location=LocationEnum.PHILIPPINES),
    ),
    LinkedInLink(
        base_url=BASE_SEARCH_URL,
        max_page=5,
        params=LinkedInParams(keywords=".net", location=LocationEnum.PHILIPPINES),
    ),
    LinkedInLink(
        base_url=BASE_SEARCH_URL,
        max_page=5,
        params=LinkedInParams(keywords="asp.net", location=LocationEnum.PHILIPPINES),
    ),
    LinkedInLink(
        base_url=BASE_SEARCH_URL,
        max_page=5,
        params=LinkedInParams(keywords="react", location=LocationEnum.PHILIPPINES),
    ),
    LinkedInLink(
        base_url=BASE_SEARCH_URL,
        max_page=5,
        params=LinkedInParams(keywords="angular", location=LocationEnum.PHILIPPINES),
    ),
]


class ScrollResult(TypedDict):
    at_bottom: bool


async def _scroll_container_until_loaded(page: Page):
    """Incrementally scroll the container to trigger lazy loading until bottom is reached or card count stops increasing."""
    max_scroll_attempts = 20
    job_cards_container = page.locator('[componentkey="SearchResultsMainContent"]')

    for _ in range(max_scroll_attempts):
        result: ScrollResult = await job_cards_container.evaluate("""
            (div) => {
                const cards = document.querySelectorAll('div[componentkey^="job-card-component-ref-"]');
                const count = cards.length;

                const canScrollDown = div.scrollHeight - div.scrollTop > (div.clientHeight + 10);
                if (canScrollDown) {
                    div.scrollBy({ top: 350, behavior: 'smooth' });
                }
                
                return { atBottom: !canScrollDown };
            }
            """)

        at_bottom = result.get("atBottom", False)

        if at_bottom:
            logger.debug("Reached bottom of container; stopping scroll.")
            break

        await asyncio.sleep(random.uniform(0.0, 0.3))


async def _extract_cards_from_page(page: Page) -> List[JobCardRawData]:
    """Extract unique job cards on the page.

    Returns:
        List of JobCardRawData objects.
    """
    raw_cards = await page.evaluate("""
        () => {
            const cards = document.querySelectorAll('div[componentkey^="job-card-component-ref-"]');
            const seenKeys = new Set();
            const results = [];

            for (const card of cards) {
                const key = card.getAttribute('componentkey');
                if (!key || seenKeys.has(key)) continue;
                seenKeys.add(key);

                const match = key.match(/job-card-component-ref-(\\d+)/);
                const jobId = match ? match[1] : key.replace('job-card-component-ref-', '');

                const innerText = card.innerText || card.textContent || '';
                results.push({
                    job_id: jobId,
                    card_text: innerText.trim()
                });
            }
            return results;
        }
        """)
    return [JobCardRawData(**c) for c in raw_cards]


CONTAINER_SELECTOR = '[componentkey="SearchResultsMainContent"]'


async def _scrape_page(
    page: Page,
    page_url: str,
    page_num: int,
) -> Tuple[int, int]:
    """Scrape a single search result page.

    Returns:
        (saved_count, skipped_count)
    """
    logger.debug(f"[LinkedIn] Navigating to page {page_num}: {page_url}")
    await page.goto(page_url, wait_until="domcontentloaded")
    await asyncio.sleep(random.uniform(3.0, 4.0))

    if "authwall" in page.url.lower() or "login" in page.url.lower():
        input("LinkedIn requires login. Please log in and press Enter to continue...")

    try:
        await page.wait_for_selector(CONTAINER_SELECTOR, timeout=8000)
    except Exception:
        logger.debug(
            f"[LinkedIn] Container {CONTAINER_SELECTOR} not immediately found, scrolling fallback..."
        )

    await _scroll_container_until_loaded(page)

    raw_cards = await _extract_cards_from_page(page)
    logger.debug(f"[LinkedIn] Discovered {len(raw_cards)} card(s) on page {page_num}")
    logger.debug(f"[LinkedIn] Raw cards: {raw_cards}")

    if not raw_cards:
        return 0, 0

    all_job_ids = [card.job_id for card in raw_cards]
    with SessionLocal() as db:
        existing_ids = get_existing_job_ids(db, all_job_ids)
    new_cards = [card for card in raw_cards if card.job_id not in existing_ids]

    skipped_count = len(existing_ids)
    saved_count = 0

    if not new_cards:
        logger.debug(
            f"[LinkedIn] Page {page_num}: All {len(new_cards)} jobs already saved in DB. Skipping LLM extraction."
        )
        return 0, skipped_count

    logger.debug(
        f"[LinkedIn] Page {page_num}: Extracting {len(new_cards)} new job(s) via LLM ({skipped_count} already in DB)..."
    )

    card_text_map: dict[str, str] = {card.job_id: card.card_text for card in new_cards}

    try:
        extraction = await linkedin_job_extractor.extract_batch(cards=new_cards)
    except Exception as e:
        logger.error(f"[LinkedIn] Batch LLM extraction failed on page {page_num}: {e}")
        return 0, skipped_count

    extracted_records: List[LinkedInJobDetails] = []

    for idx, extracted_job in enumerate(extraction.jobs, 1):
        raw_text = card_text_map.get(extracted_job.job_id, "")
        record = LinkedInJobDetails.from_extracted(
            job=extracted_job,
            card_raw_text=raw_text,
        )
        extracted_records.append(record)

        salary_str = (
            f"{record.salary_min} - {record.salary_max} {record.salary_currency}"
            if record.salary_min and record.salary_max and record.salary_currency
            else None
        )
        formatted_job = format_job_log(
            board="LinkedIn",
            title=record.title or "Untitled",
            company=record.company_name,
            salary=salary_str,
            location=record.location,
            page_info=f"page {page_num}",
            item_info=f"{idx}/{len(extraction.jobs)}",
        )
        logger.debug(formatted_job)

    if extracted_records:
        with SessionLocal() as db:
            create_linkedin_details_bulk(db, extracted_records)
        saved_count = len(extracted_records)
        logger.info(
            f"[LinkedIn] Page {page_num}: Successfully persisted {saved_count} job(s) to DB."
        )

    return saved_count, skipped_count


async def _scrape_link(
    page: Page,
    link: LinkedInLink,
    target_idx: int,
    total_targets: int,
) -> None:
    total_saved = 0
    total_skipped = 0

    for page_num in range(1, link.max_page + 1):
        next_button = page.locator(
            '[data-testid="pagination-controls-next-button-visible"]'
        )
        if page_num > 1 and not await next_button.count() == 0:
            logger.info(
                f"[LinkedIn] Target {target_idx}/{total_targets} ('{link.params.keywords}'): "
                f"Page {page_num} not found. Stopping further scraping for this target."
            )
            break
        page_url = link.get_next_page(page_num)
        saved, skipped = await _scrape_page(page, page_url, page_num)
        total_saved += saved
        total_skipped += skipped

        if page_num < link.max_page:
            await asyncio.sleep(random.uniform(3.0, 4.5))

    logger.info(
        f"[LinkedIn] Target {target_idx}/{total_targets} ('{link.params.keywords}'): "
        f"Completed {link.max_page} page(s) -> {total_saved} saved, {total_skipped} skipped."
    )


async def scrape_linkedin(
    links: Optional[list[LinkedInLink]] = None,
    is_retry: bool = False,
) -> None:
    targets = links if links is not None else DEFAULT_LINKS
    tracker = LinkedinRunTracker(links=targets, is_retry_run=is_retry)

    page = await CamoufoxSingleton.create_new_page()

    try:
        total_items = len(targets)
        logger.info(f"[LinkedIn] Scraping {total_items} search target(s)...")

        for index, link in enumerate(targets):
            tracker.set_current_index(index)
            logger.info(
                f"[LinkedIn] Target {index + 1}/{total_items}: keywords='{link.params.keywords}'"
            )
            try:
                await _scrape_link(
                    page, link, target_idx=index + 1, total_targets=total_items
                )
                tracker.record_success()
            except Exception as e:
                logger.error(
                    f"[LinkedIn] Failed target {index + 1}/{total_items} ({link.params.keywords}): {e}"
                )
                if tracker.record_link_error(link=link, error=e):
                    break

            if index < total_items - 1:
                await asyncio.sleep(random.uniform(4.0, 6.0))

        tracker.finalize()

    except Exception as e:
        logger.error(f"[LinkedIn] Error occurred during scraper run: {e}")
        raise

    finally:
        await page.close()


if __name__ == "__main__":
    asyncio.run(scrape_linkedin())
