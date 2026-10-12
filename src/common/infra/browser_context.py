import asyncio
import random
from camoufox import AsyncCamoufox
from playwright.async_api import BrowserContext, Page

PROFILE_DIR = "./camoufox_profile"


class CamoufoxSingleton:
    _context = None
    _cm = None
    _lock = asyncio.Lock()
    _is_primary_page_used = False

    @classmethod
    async def get_context(cls, user_data_dir: str = PROFILE_DIR):
        async with cls._lock:
            if cls._context is None:
                cls._cm = AsyncCamoufox(
                    headless=False,
                    persistent_context=True,
                    user_data_dir=user_data_dir,
                    humanize=True,
                    firefox_user_prefs={
                        "widget.windows.window_occlusion_tracking.enabled": False,
                        "dom.timeout.enable_budget_timer_throttling": False,
                    },
                )
                cls._context = await cls._cm.__aenter__()
            return cls._context

    @classmethod
    async def close(cls):
        async with cls._lock:
            if cls._cm is not None:
                await cls._cm.__aexit__(None, None, None)
                cls._context = None
                cls._cm = None

    @classmethod
    async def get_primary_page(cls) -> Page:
        context = await cls.get_context()
        assert isinstance(context, BrowserContext)
        if not cls._is_primary_page_used:
            cls._is_primary_page_used = True
        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script("""
            Object.defineProperty(document, 'hasFocus', {
                value: () => true,
                writable: false
            });
        """)
        return page

    @classmethod
    async def create_new_page(cls) -> Page:
        context = await cls.get_context()
        assert isinstance(context, BrowserContext)

        if not cls._is_primary_page_used:
            cls._is_primary_page_used = True
            return await cls.get_primary_page()

        page = await context.new_page()
        await page.add_init_script("""
            Object.defineProperty(document, 'hasFocus', {
                value: () => true,
                writable: false
            });
        """)
        await asyncio.sleep(random.uniform(1.0, 2.5))
        return page
