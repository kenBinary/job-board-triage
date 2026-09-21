# from src.http_client import get_client

# url = "https://ph.indeed.com/jobs"
# params = {
#     "q": "developer",
#     "l": "Philippines",
#     "sort": "date",
#     "fromage": "7",
# }
# headers = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:156.0) Gecko/20100101 Firefox/156.0",
#     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#     "Accept-Language": "en-US,en;q=0.9",
#     "mode": "cors",
# }


# async def fetch_jobs():
#     client = get_client()
#     response = await client.get(url, params=params, headers=headers)
#     print(response.status_code)
#     print(response.text)


import asyncio
from camoufox.async_api import AsyncCamoufox

PROFILE_DIR = "./camoufox_profile"


async def fetch_jobs():

    async with AsyncCamoufox(
        headless=True, persistent_context=True, user_data_dir=PROFILE_DIR
    ) as browser:
        # page = await browser.new_page()

        # --- Site 1 ---
        # await page.goto("https://gmail.com/")
        # input("1. Log into Site 1 in the browser window, then press Enter here...")

        # # --- Site 2 ---
        # await page.goto("https://ph.indeed.com/")
        # input("2. Log into Site 2 in the browser window, then press Enter here...")

        # print("Both sessions have been saved into the profile!")

        # print("Session saved successfully!")
        page = await browser.new_page()
        await page.goto(
            "https://ph.indeed.com/jobs?q=developer&l=Philippines&sort=date&fromage=7",
            wait_until="domcontentloaded",
        )

        await page.wait_for_selector("script#mosaic-data", state="attached")

        my_data = await page.evaluate(
            "() => window.mosaic?.providerData?.['mosaic-provider-jobcards']"
        )

        print(type(my_data))  # <class 'dict'>
        print(my_data)

        print("Page title:", await page.title())


# asyncio.run(fetch_jobs())
