from datetime import datetime
from bs4 import BeautifulSoup, Tag

from src.http_client import get_client
from src.olj.models.schemas import OljJobSchema


def parse_job_card(card: Tag) -> OljJobSchema:
    # 1. Link & ID
    link_card = card.get("href")
    link = ""
    job_id = "0"
    if isinstance(link_card, str):
        link = link_card.strip()
        job_id = link_card.split("-")[-1]

    # 2. Title & Job Type
    h4 = card.select_one("h4")
    job_type = ""
    title = ""
    if h4:
        badge = h4.select_one("span.badge")
        if badge:
            job_type = badge.get_text(strip=True)
            # Remove badge text from title
            badge_text = badge.get_text()
            title = h4.get_text().replace(badge_text, "").strip()
        else:
            title = h4.get_text(strip=True)

    # 3. Author & Posted Date
    author = ""
    posted_date_str = ""

    meta_p = card.select_one("p[data-temp]")
    if meta_p:
        data_temp = meta_p.get("data-temp", "")
        if isinstance(data_temp, str):
            posted_date_str = data_temp.strip()

        meta_p_text = meta_p.get_text(strip=True).rstrip("•").strip()
        if meta_p_text:
            author = meta_p_text

    posted_date = (
        datetime.fromisoformat(posted_date_str) if posted_date_str else datetime.min
    )

    # 4. Salary
    salary_elem = card.select_one("dl dd.col")
    salary = None
    if salary_elem:
        raw_salary = salary_elem.get_text(strip=True).rstrip("🔍").strip()
        if raw_salary:
            salary = raw_salary

    # 5. Description
    desc_elem = card.select_one("div.desc")
    description = ""
    if desc_elem:
        # Clone so decomposing "See More" doesn't mutate outer tree
        desc_clone = BeautifulSoup(str(desc_elem), "html.parser")
        see_more = desc_clone.find("a")
        if see_more:
            see_more.decompose()
        description = (
            desc_clone.get_text(separator="\n", strip=True).rstrip("…").strip()
        )

    # 6. Tags
    tag_elements = card.select("div.job-tag a.badge")
    tags = [t.get_text(strip=True) for t in tag_elements if t.get_text(strip=True)]

    return OljJobSchema(
        id=job_id,
        title=title,
        job_type=job_type,
        link=link,
        author=author,
        posted_date=posted_date,
        salary=salary,
        description=description,
        tags=tags or None,
    )


def parse_job_listings(html_content: str) -> list[OljJobSchema]:
    soup = BeautifulSoup(html_content, "html.parser")
    job_cards = soup.select("a:has(div.jobpost-cat-box)")
    return [parse_job_card(card) for card in job_cards]


links = ["https://www.onlinejobs.ph/jobseekers/jobsearch?jobkeyword=developer"]

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:156.0) Gecko/20100101 Firefox/156.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


async def fetch_jobs(link: str) -> list[OljJobSchema]:
    headers = DEFAULT_HEADERS.copy()

    client = get_client()
    response = await client.get(link, headers=headers)
    response.raise_for_status()

    return parse_job_listings(response.text)
