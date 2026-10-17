import base64
from playwright.async_api import ElementHandle

from src.common.logger import get_logger

logger = get_logger("linkedin_posts_scraper")


async def screenshot_and_return_base64(element: ElementHandle) -> str:
    """
    Takes a screenshot of the element specified by the selector on the given page and returns it as a base64 string.

    Args:
        element (ElementHandle): The Playwright ElementHandle of the element to screenshot.

    Returns:
        str: The base64-encoded screenshot of the element.
    """
    screenshot_bytes = await element.screenshot()
    return base64.b64encode(screenshot_bytes).decode("ascii")
