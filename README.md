# Job Board Triage Engine

Job Board Triage Engine collects job listings and hiring posts from several Philippine job boards, stores them locally, and provides a web interface for reviewing and triaging results.

# Features

* Scrape Indeed, JobStreet, Kalibrr, LinkedIn jobs, LinkedIn posts, Mynimo, OnlineJobs.ph, and Facebook posts.
* Run all boards, one or more selected boards, or groups of fast and slow scrapers.
* Resume failed scraper runs or force a fresh run.
* Persist scraped jobs in the local SQLite database and avoid repeatedly showing jobs already marked as seen.
* Review listings in a NiceGUI dashboard with board filters, pagination, status controls, and direct application links.
* Use Gemini through LiteLLM to extract structured data from LinkedIn and Facebook posts.

# Prerequisites / Requirements

* Python 3.13 or newer.
* `uv` for installing the locked dependencies and running the project.
* A supported browser environment for Camoufox. The first run may download the required browser components.
* A Gemini API key for the LinkedIn and Facebook post extractors.
* Accounts for job boards that require authentication. A persistent Camoufox profile is used to retain login sessions.

# Installation

1. Clone the repository and change into its directory.
2. Install the dependencies:

   ```powershell
   uv sync
   ```

3. Create the runtime configuration files:

   ```powershell
   Copy-Item config.template.json config.json
   Copy-Item .env.template .env
   ```

4. Edit `config.json` with the searches you want to run and set `GEMINI_API_KEY` in `.env`.
5. If authentication is required, initialize the persistent browser profile:

   ```powershell
   uv run python profile_setup.py
   ```

   Sign in when each browser page opens, then press Enter in the terminal to save the session.

# Usage / Quick Start

Indeed, LinkedIn, and Facebook require an authenticated browser profile. Before the first scraper run, initialize the profile and sign in to each site when prompted:

```powershell
uv run python profile_setup.py
```

Keep the saved `camoufox_profile` directory so later runs can reuse these sessions. Repeat the setup whenever a site's session expires.

Run the configured scrapers:

```powershell
uv run python scraper.py
```

Run only selected boards:

```powershell
uv run python scraper.py --board indeed,jobstreet
```

Other useful options include `--fast`, `--slow`, `--retry`, `--fresh`, `--verbose`, `--write-to-file`, and `--headless`. Use `--help` to see the complete CLI help:

```powershell
uv run python scraper.py --help
```

Start the local dashboard in a second terminal:

```powershell
uv run python view.py
```

Then open [http://localhost:8080](http://localhost:8080) in a browser.

# Configuration

`config.json` contains a `scrapers` object. Each board accepts one or more search targets. Use [config.template.json](config.template.json) as the reference for the supported fields:

* `indeed`, `jobstreet`, `kalibrr`, `linkedin`, `mynimo`, and `olj` configure job searches.
* `linkedin-posts` and `facebook-posts` configure post searches and scrolling.
* `max_page` controls pagination for job-board scrapers.
* `max_scrolls` controls how far post scrapers scroll.
* Search parameters such as keywords, location, date range, and work arrangement are board-specific.

`.env` contains environment-based settings:

```dotenv
GEMINI_API_KEY="your-api-key"
MAX_CONSECUTIVE_LINK_ERRORS=3
```

The SQLite database is stored in `app.db`. Do not commit `.env`, `config.json`, browser profiles, or other local runtime data.

# Known Issues

* LinkedIn post scraping can occasionally fail to intercept a post's control menu. When that happens, the post ID and URL cannot be extracted. Let the target fail and retry the failed URLs with `--retry`.
* Facebook post scraping can similarly fail to capture a post URL and ID. Retry the failed targets.
* Indeed may occasionally display a CAPTCHA or require a new login. The built-in handling covers common cases, but a run may still need to be retried after completing the browser challenge.
* Scrapers depend on third-party websites, so changes to their markup, APIs, authentication, or rate limits can cause failures.
