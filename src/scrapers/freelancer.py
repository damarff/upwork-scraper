"""Freelancer.com scraper — uses public REST API with curl_cffi.

curl_cffi impersonates real Chrome TLS fingerprint, so it bypasses
Cloudflare without needing a full browser. ~10x faster than DrissionPage.
"""

import json
import time
import urllib.parse
from typing import Optional

from curl_cffi import requests as curl_requests

from src.scrapers.base import BaseScraper
from src.models.job import Job
from src.utils.logger import info, warn, error, debug


FREELANCER_API = "https://www.freelancer.com/api/projects/0.1/projects/active/"

# Chrome version — ganti kalo curl_cffi nambah support versi lebih baru
CURL_IMPersonATE = "chrome131"

DEFAULT_KEYWORDS = [
    "python web scraping",
    "data extraction API",
    "AI automation agent",
    "LLM RAG developer",
    "FastAPI backend",
    "browser automation",
    "PDF data extraction",
    "chatbot development",
    "Excel automation Python",
    "n8n workflow automation",
    "web app MVP",
    "voice AI agent",
    "local LLM setup",
    "database migration",
    "document classification AI",
    "webhook integration",
    "social media automation",
    "data pipeline ETL",
    "screen scraper RPA",
    "SEO monitoring tool",
]

# Session global — reuse koneksi, lebih cepet
_session: Optional[curl_requests.Session] = None


def _get_session() -> curl_requests.Session:
    global _session
    if _session is None:
        _session = curl_requests.Session(impersonate=CURL_IMPersonATE)
        _session.headers.update({
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.freelancer.com/",
            "Origin": "https://www.freelancer.com",
        })
    return _session


class FreelancerScraper(BaseScraper):
    """Scrape Freelancer.com via their public API.

    Uses curl_cffi with Chrome impersonation — bypasses Cloudflare,
    no browser needed.
    """

    def platform(self) -> str:
        return "freelancer"

    def search_keyword(self, keyword: str, limit: int = 20) -> list[dict]:
        """Fetch projects from Freelancer API for one keyword."""
        params = {
            "query": keyword,
            "limit": limit,
        }
        url = f"{FREELANCER_API}?{urllib.parse.urlencode(params)}"

        info(f"Fetching Freelancer API: '{keyword}'")

        try:
            session = _get_session()
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            error(f"Freelancer API request failed: {e}", keyword=keyword)
            return []

        if data.get("status") == "success":
            projects = data.get("result", {}).get("projects", [])
            info(f"Found {len(projects)} projects for '{keyword}'")
            return projects
        else:
            warn(f"Freelancer API status not success", keyword=keyword, data=str(data)[:200])
            return []

    def scrape_keyword(self, keyword: str) -> list[Job]:
        """Search and convert results to Job objects."""
        raw_projects = self.search_keyword(keyword)
        jobs: list[Job] = []
        for raw in raw_projects:
            job = Job.from_freelancer_api(raw)
            if job:
                jobs.append(job)
        debug(f"Parsed {len(jobs)} valid jobs for '{keyword}'")
        return jobs

    def scrape_all(self, keywords: Optional[list[str]] = None) -> list[Job]:
        """Run scraper across all keywords."""
        keywords = keywords or DEFAULT_KEYWORDS
        all_jobs: list[Job] = []
        info(f"Freelancer scraper: {len(keywords)} keywords")

        for i, kw in enumerate(keywords):
            try:
                jobs = self.scrape_keyword(kw)
                all_jobs.extend(jobs)
            except Exception as e:
                error(f"Keyword failed: '{kw}'", error=str(e))

            if i < len(keywords) - 1:
                info(f"Waiting {self.delay}s before next keyword...")
                time.sleep(self.delay)

        return all_jobs
