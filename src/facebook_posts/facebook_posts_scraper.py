import asyncio
import base64
import random
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs
import re
from typing import List, Optional

from playwright.async_api import ElementHandle, Page

from src.common.infra.browser_context import CamoufoxSingleton
from src.common.logger import format_job_log, get_logger
from src.db.database import SessionLocal
from src.facebook_posts.facebook_posts_run_tracker import FacebookPostsRunTracker
from src.facebook_posts.models.facebook_post_link import (
    FacebookLinkType,
    FacebookPostLink,
    FacebookPostParams,
)
from .db import (
    create_facebook_post_details_bulk,
    get_facebook_post_by_job_id,
)
from .llm_extractor import extract_jobs_from_post
from .models.facebook_post_job_details import FacebookPostJobDetails

logger = get_logger("facebook_posts_scraper")

POST_CLICK_DELAY_MIN: float = 0.5
POST_CLICK_DELAY_MAX: float = 1.5
MAX_EXISTING_POSTS_PER_SCROLL: int = 3
MAX_FAILED_POSTS_PER_LINK: int = 10

DEFAULT_LINKS: list[FacebookPostLink] = [
    FacebookPostLink(
        max_scrolls=3,
        params=FacebookPostParams(
            query="hiringph",
            link_type=FacebookLinkType.HASHTAG,
        ),
    ),
    FacebookPostLink(
        max_scrolls=3,
        params=FacebookPostParams(
            query="workfromhomeph",
            link_type=FacebookLinkType.HASHTAG,
        ),
    ),
    FacebookPostLink(
        max_scrolls=3,
        params=FacebookPostParams(
            query="remotejobsph",
            link_type=FacebookLinkType.HASHTAG,
        ),
    ),
    FacebookPostLink(
        max_scrolls=3,
        params=FacebookPostParams(
            query="techjobs",
            link_type=FacebookLinkType.HASHTAG,
        ),
    ),
    FacebookPostLink(
        max_scrolls=3,
        params=FacebookPostParams(
            query="developerjobs",
            link_type=FacebookLinkType.HASHTAG,
        ),
    ),
    FacebookPostLink(
        max_scrolls=3,
        params=FacebookPostParams(
            query="wearehiring",
            link_type=FacebookLinkType.HASHTAG,
        ),
    ),
    FacebookPostLink(
        max_scrolls=3,
        params=FacebookPostParams(
            query="jobsph",
            link_type=FacebookLinkType.HASHTAG,
        ),
    ),
    FacebookPostLink(
        max_scrolls=3,
        params=FacebookPostParams(
            query="cdojob",
            link_type=FacebookLinkType.HASHTAG,
        ),
    ),
    FacebookPostLink(
        max_scrolls=3,
        params=FacebookPostParams(
            query="cdojobopportunity",
            link_type=FacebookLinkType.HASHTAG,
        ),
    ),
    FacebookPostLink(
        max_scrolls=3,
        params=FacebookPostParams(
            query="cebujobs",
            link_type=FacebookLinkType.HASHTAG,
        ),
    ),
    FacebookPostLink(
        max_scrolls=3,
        params=FacebookPostParams(
            query="hiringnow",
            link_type=FacebookLinkType.HASHTAG,
        ),
    ),
    FacebookPostLink(
        max_scrolls=3,
        params=FacebookPostParams(
            query="jobsincebu",
            link_type=FacebookLinkType.HASHTAG,
        ),
    ),
    FacebookPostLink(
        max_scrolls=3,
        params=FacebookPostParams(
            query="philippinesjobs",
            link_type=FacebookLinkType.HASHTAG,
        ),
    ),
    FacebookPostLink(
        max_scrolls=3,
        params=FacebookPostParams(
            query="jobphilippines",
            link_type=FacebookLinkType.HASHTAG,
        ),
    ),
]

_JS_SCROLL_FEED_BOTTOM = """\
() => {
    const feed = document.querySelector('[role="feed"]');
    if (!feed) {
        window.scrollBy({ top: 1200, behavior: 'smooth' });
        return;
    }
    const cards = feed.querySelectorAll('[data-virtualized="false"]');
    if (cards.length > 0) {
        cards[cards.length - 1].scrollIntoView({ behavior: 'smooth', block: 'end' });
    } else {
        window.scrollBy({ top: 1200, behavior: 'smooth' });
    }
}
"""


async def _check_authwall(page: Page) -> None:
    url_lower = page.url.lower()
    if "login" in url_lower or "checkpoint" in url_lower or "recover" in url_lower:
        logger.warning(
            "[Facebook Posts] Auth barrier detected. "
            "Please log in to Facebook in the browser window and press Enter to continue..."
        )
        input("  [Waiting for login] Press Enter once you are logged in: ")


async def _click_see_more_button(buttons: List[ElementHandle]) -> bool:
    for btn in buttons:
        btn_text = await btn.inner_text()
        if btn_text.strip().lower() == "see more":
            try:
                await btn.click()
                return True
            except Exception as e:
                logger.warning(f"  [card] Failed to click 'See More' button: {e}")
                return False
    return False


def _extract_post_id_from_href(href: str) -> Optional[str]:
    """Extracts the Facebook post ID or story_fbid from a URL or link string."""
    if not href:
        return None

    parsed = urlparse(href)

    if parsed.query:
        query_params = parse_qs(parsed.query)
        for param in ["story_fbid", "fbid"]:
            if param in query_params and query_params[param]:
                return query_params[param][0]

    path_match = re.search(r"/(?:posts|permalink|story)/([a-zA-Z0-9_.-]+)", parsed.path)
    if path_match:
        return path_match.group(1)

    raw_match = re.search(r"/posts/([a-zA-Z0-9_-]+)", href)
    if raw_match:
        return raw_match.group(1)

    return None


async def _scrape_link(
    page: Page,
    db,
    link: FacebookPostLink,
    target_idx: int,
    total_targets: int,
) -> None:
    url = link.get_url()
    logger.debug(f"[Facebook Posts] Scraping link: {url}")

    await page.goto(url, wait_until="domcontentloaded")
    await asyncio.sleep(random.uniform(3.5, 5.0))

    await _check_authwall(page)

    saved_count = 0
    skipped_count = 0
    total_cards_processed = 0
    seen_post_ids: set[str] = set()
    failed_posts_count = 0
    current_card_index = 0

    for scroll_idx in range(link.max_scrolls):
        existing_posts_in_scroll = 0
        logger.debug(
            f"[Facebook Posts] Scroll {scroll_idx + 1}/{link.max_scrolls} — extracting cards..."
        )

        post_cards = await page.query_selector_all(
            '[role="feed"] [data-virtualized="false"]'
        )
        post_cards_length = len(post_cards)
        post_cards = post_cards[current_card_index:]
        logger.debug(f"  [scroll] Found {len(post_cards)} new card(s) in this scroll.")

        for card in post_cards:
            await card.scroll_into_view_if_needed()
            logger.debug(
                f"  [card] Processing card {current_card_index + 1}/{post_cards_length} in scroll {scroll_idx + 1}/{link.max_scrolls}..."
            )
            if current_card_index + 1 == post_cards_length:
                await card.evaluate("el => el.style.border = '2px solid red'")
            else:
                await card.evaluate("el => el.style.border = '2px solid green'")

            new_jobs: list[FacebookPostJobDetails] = []

            anchor_tags = (await card.query_selector_all("a"))[2:6]
            # * Hovering over the anchor tags because the link with /posts/<post_id> is sometimes hidden until you hover over the card. This is a workaround for that.
            try:
                for a in reversed(anchor_tags):
                    box = await a.bounding_box()
                    if box:
                        await page.mouse.move(
                            box["x"] + box["width"] / 2,
                            box["y"] + box["height"] / 2,
                            steps=1,
                        )
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                    await page.mouse.move(-1000, -1000)
            except Exception as e:
                logger.warning(f"  [card] Failed to hover over anchor tags: {e}")
                # TODO: Consider whether to continue or raise an exception here. For now, we log the warning and continue.
                continue

            post_url = None
            anchor_tags_v2 = await card.query_selector_all("a")
            for a in anchor_tags_v2:
                try:
                    # TODO: this includes tracking links, which may not be the actual post URL. Consider filtering out tracking links if necessary.
                    href = await a.get_attribute("href")
                    if not href:
                        continue

                    if "/posts/" in href or "/permalink" in href:
                        post_url = href
                        break
                except Exception as e:
                    logger.warning(f"  [card] Failed to get href from anchor: {e}")

            if not post_url:
                logger.debug(
                    "[Facebook Posts] [skip] No post permalink found — skipping card."
                )
                current_card_index += 1
                # TODO: Consider whether to raise an exception here instead of skipping, as this might indicate a change in Facebook's DOM structure.
                continue

            post_id = _extract_post_id_from_href(post_url) if post_url else None
            logger.debug(f"  [card] Extracted post_id: {post_id} from link: {post_url}")
            if not post_id:
                logger.debug(
                    "[Facebook Posts] [skip] No post permalink found — skipping card."
                )
                current_card_index += 1
                # TODO: Consider whether to raise an exception here instead of skipping, as this might indicate a change in Facebook's DOM structure.
                continue

            if post_id in seen_post_ids:
                logger.debug(
                    f"[Facebook Posts] [skip] post_id={post_id} already processed in this run — skipping."
                )
                current_card_index += 1
                continue

            if get_facebook_post_by_job_id(db, post_id):
                skipped_count += 1
                existing_posts_in_scroll += 1
                logger.debug(
                    f"[Facebook Posts] [dup] post_id={post_id} already in DB — skipping."
                )
                if existing_posts_in_scroll > MAX_EXISTING_POSTS_PER_SCROLL:
                    logger.debug(
                        f"[Facebook Posts] More than "
                        f"{MAX_EXISTING_POSTS_PER_SCROLL} existing posts found in "
                        f"scroll {scroll_idx + 1}; skipping the rest of this scroll."
                    )
                    break
                current_card_index += 1
                continue

            image_tags = await card.query_selector_all("img")
            image_urls = []
            for img in image_tags:
                img_src = await img.get_attribute("src")
                if img_src and img_src.startswith("https://scontent"):
                    image_urls.append(img_src)
            logger.debug(f"  [card] Found {len(image_urls)} image(s) in card.")
            logger.debug(f"  [card] Extracted image URLs: {image_urls}")

            buttons = await card.query_selector_all('[role="button"]')
            see_more_clicked = await _click_see_more_button(buttons)
            card_screenshot: Optional[str] = None
            if see_more_clicked:
                await asyncio.sleep(random.uniform(0.2, 0.5))
                screenshot_bytes = await card.screenshot(type="png")
                card_screenshot = base64.b64encode(screenshot_bytes).decode("ascii")

            logger.debug(
                f"[Facebook Posts] Processing card post_id={post_id} "
                f"images={len(image_urls)} screenshot={see_more_clicked}"
            )

            text_content = await card.inner_text()
            logger.debug(
                f"  [card] Extracted text content (first 100 chars): {text_content[:100]}"
            )

            try:
                extraction = await extract_jobs_from_post(
                    text_content,
                    image_urls,
                    additional_image_context=(
                        [card_screenshot] if card_screenshot else None
                    ),
                )
                logger.debug(
                    f"  [LLM] post_id={post_id} is_job_post={extraction.is_job_post} "
                    f"jobs={len(extraction.jobs)}"
                )
            except Exception as e:
                failed_posts_count += 1
                logger.warning(
                    f"[Facebook Posts] LLM extraction failed for post {post_id}: {e}"
                )
                if failed_posts_count > MAX_FAILED_POSTS_PER_LINK:
                    raise RuntimeError(
                        f"More than {MAX_FAILED_POSTS_PER_LINK} posts failed while "
                        f"scraping {url}"
                    ) from e
                await asyncio.sleep(
                    random.uniform(POST_CLICK_DELAY_MIN, POST_CLICK_DELAY_MAX)
                )
                raise Exception(
                    f"LLM extraction failed for post {post_id} in card "
                    f"{current_card_index + 1}/{post_cards_length} in scroll "
                    f"{scroll_idx + 1}/{link.max_scrolls}: {e}"
                ) from e

            if not extraction.is_job_post:
                logger.debug(
                    f"[Facebook Posts] [skip] post_id={post_id} — LLM says not a job post."
                )
                await asyncio.sleep(
                    random.uniform(POST_CLICK_DELAY_MIN, POST_CLICK_DELAY_MAX)
                )
                current_card_index += 1
                continue

            for job_idx, job in enumerate(extraction.jobs, 1):
                job_id = (
                    post_id if len(extraction.jobs) == 1 else f"{post_id}_{job_idx}"
                )

                if get_facebook_post_by_job_id(db, job_id):
                    skipped_count += 1
                    logger.debug(
                        f"[Facebook Posts] [dup] job_id={job_id} already in DB — skipping."
                    )
                    continue

                record = FacebookPostJobDetails.from_extracted(
                    job=job,
                    job_id=job_id,
                    post_url=post_url or "",
                )
                if not record.posted_at_utc:
                    record.posted_at_utc = datetime.now(timezone.utc).isoformat()
                new_jobs.append(record)
                saved_count += 1

                salary_str: Optional[str] = (
                    str(record.salary_min)
                    + " - "
                    + str(record.salary_max)
                    + (record.salary_currency or "")
                    if record.salary_min and record.salary_max
                    else None
                )
                formatted_job = format_job_log(
                    board="Facebook Posts",
                    title=job.title or "Untitled",
                    company=job.company_name,
                    salary=salary_str,
                    location=record.location,
                    page_info=f"scroll {scroll_idx + 1}/{link.max_scrolls}",
                    item_info=f"{job_idx}/{len(extraction.jobs)}",
                )
                logger.debug(formatted_job)

            if new_jobs and len(new_jobs) > 0:
                create_facebook_post_details_bulk(db, new_jobs)

            seen_post_ids.add(post_id)
            total_cards_processed += 1
            current_card_index += 1
            failed_posts_count = 0

        if scroll_idx < link.max_scrolls - 1:
            await page.evaluate(_JS_SCROLL_FEED_BOTTOM)
            await asyncio.sleep(random.uniform(1.0, 1.5))

    logger.info(
        f"[Facebook Posts] Target {target_idx}/{total_targets}: "
        f"Processed {total_cards_processed} cards "
        f"({saved_count} saved, {skipped_count} skipped)"
    )


async def scrape_facebook_posts(
    links: Optional[list[FacebookPostLink]] = None,
    is_retry: bool = False,
) -> None:
    targets = links if links is not None else DEFAULT_LINKS
    tracker = FacebookPostsRunTracker(links=targets, is_retry_run=is_retry)

    page = await CamoufoxSingleton.create_new_page()

    try:
        with SessionLocal() as db:
            total_items = len(targets)
            logger.info(f"[Facebook Posts] Scraping {total_items} target(s)...")
            for index, link in enumerate(targets):
                tracker.set_current_index(index)
                logger.info(
                    f"[Facebook Posts] Target {index + 1}/{total_items}: "
                    f"type='{link.params.link_type}' query='{link.params.query}'"
                )
                try:
                    await _scrape_link(
                        page, db, link, target_idx=index + 1, total_targets=total_items
                    )
                    tracker.record_success()
                except Exception as e:
                    logger.error(
                        f"[Facebook Posts] Failed target {index + 1}/{total_items} "
                        f"({link.get_url()}): {e}"
                    )
                    if tracker.record_link_error(link=link, error=e):
                        break

                if index < total_items - 1:
                    await asyncio.sleep(random.uniform(2.0, 5.0))

        tracker.finalize()

    except Exception as e:
        logger.error(f"[Facebook Posts] Error occurred during scrape run: {e}")
        raise

    finally:
        await page.close()


if __name__ == "__main__":
    asyncio.run(scrape_facebook_posts())
