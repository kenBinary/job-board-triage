import asyncio
from camoufox import AsyncCamoufox
from playwright.async_api import BrowserContext

PROFILE_DIR = "./camoufox_profile"


class CamofouxProvider(AsyncCamoufox):
    def __init__(self, **launch_options):
        super().__init__(**launch_options)
        self._lock = asyncio.Lock()
        self._context = None
        self._is_primary_page_used = False

    async def get_context(self) -> BrowserContext:
        async with self._lock:
            if self._context is None:
                self._context = await self.__aenter__()
            assert isinstance(self._context, BrowserContext)
            return self._context

    async def close_context(self):
        async with self._lock:
            if self._context is not None:
                await self.__aexit__(None, None, None)
                self._context = None
                self._is_primary_page_used = False

    async def get_primary_page(self):
        context = await self.get_context()
        assert isinstance(context, BrowserContext)
        if not self._is_primary_page_used:
            self._is_primary_page_used = True
        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script("""
            Object.defineProperty(document, 'hasFocus', {
                value: () => true,
                writable: false
            });
        """)
        return page

    async def create_new_page(self):
        context = await self.get_context()
        assert isinstance(context, BrowserContext)

        if not self._is_primary_page_used:
            self._is_primary_page_used = True
            return await self.get_primary_page()
        page = await context.new_page()
        await page.add_init_script("""
            Object.defineProperty(document, 'hasFocus', {
                value: () => true,
                writable: false
            });
        """)

        return page
