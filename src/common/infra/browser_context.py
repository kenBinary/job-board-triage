import asyncio
from camoufox import AsyncCamoufox
from playwright.async_api import BrowserContext, Page

PROFILE_DIR = "./camoufox_profile"


class CamoufoxSingleton:
    _context = None
    _cm = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_context(cls, user_data_dir: str = PROFILE_DIR):
        async with cls._lock:
            if cls._context is None:
                cls._cm = AsyncCamoufox(
                    headless=False,
                    persistent_context=True,
                    user_data_dir=user_data_dir,
                    humanize=True,
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
        return context.pages[0] if context.pages else await context.new_page()

    @classmethod
    async def create_tab(cls) -> Page:
        context = await cls.get_context()
        assert isinstance(context, BrowserContext)
        return await context.new_page()
