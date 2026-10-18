import asyncio
import random
import re
from typing import Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from playwright.async_api import ElementHandle, Page

from src.common.enums.job_board import JobBoardEnum
from src.common.infra.dependencies import infra_container
from src.common.logger import format_job_log, get_logger
from src.common.playwright.utils import screenshot_and_return_base64
from src.common.settings import settings
from src.db.database import SessionLocal
from src.linkedin_posts.db import (
    create_linkedin_post_details,
    get_linkedin_post_by_job_id,
)
from src.linkedin_posts.linkedin_llm_extractor import (
    DEFAULT_LINKEDIN_SYSTEM_PROMPT,
    LinkedInLLMExtractor,
)
from src.linkedin_posts.linkedin_posts_run_tracker import LinkedinPostsRunTracker
from src.linkedin_posts.models.linkedin_post_job_details import LinkedInPostJobDetails
from src.linkedin_posts.models.linkedin_post_link import LinkedInPostLink
from src.common.media_utils import base64_to_data_url, fetch_image_as_data_url

logger = get_logger("linkedin_posts_scraper")

linkedin_llm_extractor = LinkedInLLMExtractor(
    prompt_template=DEFAULT_LINKEDIN_SYSTEM_PROMPT
)

CONTROL_MENU_URL_FRAGMENT = "feedUpdateControlMenuRequest"


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


def _extract_linkedin_post_data(
    payload: str, clean_search_params: bool = True
) -> Optional[Tuple[str, str]]:
    """
    Extracts the LinkedIn post share URL and its shareId from a decoded SDUI/Flight payload.

    :param payload: The raw decoded base64 string.
    :param clean_search_params: If True, strips internal transient parameters
                                ('highlightedUpdateUrn', 'highlightedUpdateType', 'origin').
    :return: A tuple of (clean_url, share_id).
    """
    url_match = re.search(
        r'"longUrl"\s*:\s*"(https://www\.linkedin\.com/posts/[^"]+)"', payload
    )
    if not url_match:
        url_match = re.search(
            r'https://www\.linkedin\.com/posts/[^\s"\'<>\\]+', payload
        )

    if not url_match:
        return None

    url = url_match.group(1) if url_match.groups() else url_match.group(0)

    if clean_search_params:
        parsed = urlsplit(url)
        params_to_remove = {"highlightedUpdateUrn", "highlightedUpdateType", "origin"}

        filtered_query = [
            (k, v)
            for k, v in parse_qsl(parsed.query, keep_blank_values=True)
            if k not in params_to_remove
        ]

        url = urlunsplit(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                urlencode(filtered_query),
                parsed.fragment,
            )
        )

    share_id_match = re.search(r'shareId\s*[:=]\s*["\']?(\d+)["\']?', payload)
    if not share_id_match:
        return None

    share_id = share_id_match.group(1)
    if not share_id:
        return None

    return url, share_id


async def _scroll_to_last_card(page: Page) -> None:
    """Scroll the last expanded post card into view to trigger lazy loading."""
    await page.evaluate("""() => {
        const allDivs = document.querySelectorAll('div[id^="expanded"]');
        if (allDivs.length > 0) {
            allDivs[allDivs.length - 1].scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
    }""")


async def _intercept_control_menu_response(
    page: Page,
    element: ElementHandle,
) -> Optional[str]:
    control_btn = await element.query_selector(
        'button[aria-label*="Open control menu" i]'
    )
    if not control_btn:
        logger.debug("[LinkedIn Posts] [skip] No control menu button found — skipping.")
        return None

    async with page.expect_response(
        lambda r: CONTROL_MENU_URL_FRAGMENT in r.url,
        timeout=15000,
    ) as resp_info:
        await control_btn.click()

    response = await resp_info.value
    response_body = await response.body()
    response_text = response_body.decode("utf-8", errors="replace")

    await asyncio.sleep(random.uniform(1.5, 2.5))
    await page.keyboard.press("Escape")

    return response_text


async def _process_post_card(
    page: Page,
    element: ElementHandle,
    element_id: str,
    card_num: int,
) -> Optional[tuple[int, int]]:
    """
    Process a single LinkedIn post card: extract share_id, run LLM extraction,
    and immediately persist each discovered job to the database.

    Returns:
        (share_id_ok, saved_count, skipped_count)
        share_id_ok is False when share_id could not be obtained for this card.
    """
    saved_count = 0
    skipped_count = 0

    logger.debug(f"[LinkedIn Posts] [card {card_num}] Processing post: #{element_id}")

    response_text = await _intercept_control_menu_response(page, element)
    if not response_text:
        logger.debug(
            "[LinkedIn Posts] [skip] No control menu response received — skipping."
        )
        return None

    post_data = _extract_linkedin_post_data(response_text)
    if not post_data:
        logger.debug(
            "[LinkedIn Posts] [skip] Could not extract share_id from control menu response — skipping."
        )
        return None

    post_url, share_id = post_data

    with SessionLocal() as db:
        if get_linkedin_post_by_job_id(db, share_id):
            skipped_count += 1
            logger.debug(
                f"[LinkedIn Posts] [dup] Job {share_id} already in DB — skipping."
            )
            return saved_count, skipped_count

    # TODO: Get Image Base64 directly without downloading
    image_urls = await _get_image_urls_from_element(page, element_id)
    logger.debug(f"[LinkedIn Posts] Images found: {len(image_urls)}")

    image_data_urls: list[str] = []
    for url in image_urls:
        try:
            data_url = fetch_image_as_data_url(url)
            await asyncio.sleep(random.uniform(0.5, 1.0))
            if data_url:
                image_data_urls.append(data_url)
        except Exception as img_err:
            logger.warning(
                f"[LinkedIn Posts] Failed to fetch image data url for {url[:60]}: {img_err}"
            )

    post_text = (await element.evaluate("el => el.textContent") or "").strip()
    post_screenshot_base64 = await screenshot_and_return_base64(element)
    post_screenshot_data_url = base64_to_data_url(
        post_screenshot_base64, media_type="image/png"
    )
    image_data_urls.append(post_screenshot_data_url)

    try:
        extraction = await linkedin_llm_extractor.extract_jobs_from_post(
            text=post_text,
            image_data_urls=image_data_urls,
        )
    except Exception as e:
        logger.warning(f"[LinkedIn Posts] LLM extraction failed: {e}")
        return None

    if not extraction.is_job_post:
        logger.debug("[LinkedIn Posts] [skip] LLM determined this is not a job post.")
        return None

    for job_idx, job in enumerate(extraction.jobs, 1):
        job_id = share_id if len(extraction.jobs) == 1 else f"{share_id}_{job_idx}"

        record = LinkedInPostJobDetails.from_extracted(
            job=job,
            job_id=job_id,
            post_url=post_url or "",
        )

        with SessionLocal() as db:
            create_linkedin_post_details(db, record)
        saved_count += 1

        salary_str = (
            str(record.salary_min)
            + " - "
            + str(record.salary_max)
            + record.salary_currency
            if record.salary_min and record.salary_max and record.salary_currency
            else None
        )
        formatted_job = format_job_log(
            board="LinkedIn Posts",
            title=job.title or "Untitled",
            company=job.company_name,
            salary=salary_str,
            location=record.location,
            page_info=f"card {card_num}",
            item_info=f"{job_idx}/{len(extraction.jobs)}",
        )
        logger.debug(formatted_job)

    return saved_count, skipped_count


async def _scrape_link(
    page: Page,
    link: LinkedInPostLink,
) -> None:
    url = link.get_url()
    logger.debug(f"[LinkedIn Posts] Scraping link: {url}")

    await page.goto(url, wait_until="domcontentloaded")
    await asyncio.sleep(random.uniform(3.5, 8.0))

    if "authwall" in page.url.lower() or "login" in page.url.lower():
        input("LinkedIn requires login. Please log in and press Enter to continue...")

    seen_element_ids: set[str] = set()
    consecutive_share_id_failures = 0
    saved_count = 0
    skipped_count = 0
    processed_count = 0
    current_scroll = 0

    while True:
        post_elements = await page.query_selector_all('div[id^="expanded"]')

        new_cards: list[tuple[ElementHandle, str]] = []
        for el in post_elements:
            el_id = await el.get_attribute("id")
            if el_id and el_id not in seen_element_ids:
                seen_element_ids.add(el_id)
                new_cards.append((el, el_id))

        logger.debug(
            f"[LinkedIn Posts] Scroll {current_scroll}: "
            f"{len(new_cards)} new card(s) discovered (total seen: {len(seen_element_ids)})"
        )

        for element, element_id in new_cards:
            processed_count += 1
            await element.scroll_into_view_if_needed()

            processed_card = await _process_post_card(
                page, element, element_id, card_num=processed_count
            )
            await asyncio.sleep(random.uniform(0.5, 1.5))

            if not processed_card:
                consecutive_share_id_failures += 1
                await asyncio.sleep(random.uniform(1.5, 3.0))
                if consecutive_share_id_failures >= 3:
                    logger.warning(
                        "[LinkedIn Posts] Share ID extraction failed 3 consecutive times. "
                        "Stopping — possible LinkedIn layout change or access issue."
                    )
                    raise Exception(
                        "Share ID extraction failed 3 consecutive times. "
                        "Possible LinkedIn layout change or access issue."
                    )
            else:
                consecutive_share_id_failures = 0
                saved_count += processed_card[0]
                skipped_count += processed_card[1]

        current_scroll += 1
        if not link.should_continue(current_scroll):
            logger.debug("[LinkedIn Posts] Max scrolls reached. Stopping.")
            break

        await _scroll_to_last_card(page)
        await asyncio.sleep(random.uniform(0.5, 1.0))

    logger.info(
        f"Processed {processed_count} posts ({saved_count} saved, {skipped_count} skipped)"
    )


async def scrape_linkedin_posts(
    links: Optional[list[LinkedInPostLink]] = None,
    is_retry: bool = False,
) -> None:
    targets = (
        links
        if links is not None
        else settings.get_scraper_links(JobBoardEnum.LinkedinPosts)
    )
    tracker = LinkedinPostsRunTracker(links=targets, is_retry_run=is_retry)

    page = await infra_container.camoufox_provider.create_new_page()

    try:
        total_items = len(targets)
        logger.info(f"[LinkedIn Posts] Scraping {total_items} target keyword(s)...")
        for index, link in enumerate(targets):
            tracker.set_current_index(index)
            logger.info(
                f"[LinkedIn Posts] Target {index + 1}/{total_items}: keyword='{link.params.keywords}'"
            )
            try:
                await _scrape_link(page, link)
                tracker.record_success()
                logger.info(
                    f"[LinkedIn Posts] Target {index + 1}/{total_items} completed successfully."
                )
            except Exception as e:
                logger.error(
                    f"[LinkedIn Posts] Failed target {index + 1}/{total_items} ({link.get_url()}): {e}"
                )
                if tracker.record_link_error(link=link, error=e):
                    break

            if index < total_items - 1:
                await asyncio.sleep(random.uniform(5.0, 15.0))

        tracker.finalize()

    except Exception as e:
        logger.error(f"[LinkedIn Posts] Error occurred during scrape run: {e}")
        raise

    finally:
        await page.close()


if __name__ == "__main__":
    asyncio.run(scrape_linkedin_posts())
