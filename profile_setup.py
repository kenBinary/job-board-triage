from camoufox.sync_api import Camoufox

PROFILE_DIR = "./camoufox_profile"

with Camoufox(
    headless=False,
    persistent_context=True,
    user_data_dir=PROFILE_DIR,
    humanize=True,
) as context:
    page = context.new_page()

    # --- Site 1 ---
    page.goto("https://gmail.com/")
    input("1. Log into Gmail in the browser window, then press Enter here...")

    # --- Site 2 ---
    page.goto("https://ph.indeed.com/")
    input("2. Log into Indeed in the browser window, then press Enter here...")

    # --- Site 3 ---
    page.goto("https://www.linkedin.com/login")
    input("3. Log into LinkedIn in the browser window, then press Enter here...")

    # --- Site 4 ---
    page.goto("https://www.facebook.com")
    input("3. Log into LinkedIn in the browser window, then press Enter here...")

    print("All sessions have been saved into the profile!")
    print("Session saved successfully!")
