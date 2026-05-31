"""Upwork scraper — bypasses Cloudflare, extracts window.__NUXT__ state.

Carries over the proven technique from the original project:
  - DrissionPage with anti-detection args
  - Wait loop for Cloudflare
  - window.__NUXT__ extraction for fast structured data
"""

import time
import urllib.parse
from typing import Optional

from src.scrapers.base import BaseScraper, wait_for_page, POST_RENDER_DELAY
from src.models.job import Job
from src.utils.logger import info, warn, error, debug


UPWORK_SEARCH_URL = "https://www.upwork.com/nx/search/jobs/?q={q}&sort=recency"

# Default keywords — matches the original set plus a few more
DEFAULT_KEYWORDS = [
    "python web scraping",
    "data extraction API",
    "AI automation agent",
    "LLM RAG developer",
    "FastAPI backend",
    "CrewAI",
    "n8n",
    "Local LLM",
    "web scraper python",
    "selenium puppeteer scraper",
]


class UpworkScraper(BaseScraper):
    """Scrape Upwork job listings via Nuxt.js state extraction."""

    def platform(self) -> str:
        return "upwork"

    def search_keyword(self, keyword: str) -> list[dict]:
        """Fetch raw job dicts from Upwork search for one keyword."""
        url = UPWORK_SEARCH_URL.format(q=urllib.parse.quote(keyword))
        info(f"Fetching: {url[:90]}...")

        self.page.get(url)

        # Tunggu Cloudflare
        wait_for_page(self.page)

        # Tunggu Nuxt render state
        time.sleep(POST_RENDER_DELAY)

        try:
            nuxt_data = self.page.run_js("return window.__NUXT__")
            if not nuxt_data:
                warn("window.__NUXT__ returned None — page may not have loaded fully")
                return []

            jobs = (
                nuxt_data.get("state", {})
                .get("jobsSearch", {})
                .get("jobs", [])
            )
            if not jobs:
                # Coba alternative path (sometimes the structure differs)
                jobs = (
                    nuxt_data.get("state", {})
                    .get("searchResults", {})
                    .get("jobs", [])
                )

            info(f"Found {len(jobs)} jobs for '{keyword}'")
            return jobs

        except Exception as e:
            error(f"Failed to extract __NUXT__: {e}", keyword=keyword)
            return []

    def scrape_keyword(self, keyword: str) -> list[Job]:
        """Search and convert results to Job objects."""
        raw_jobs = self.search_keyword(keyword)
        jobs: list[Job] = []
        for raw in raw_jobs:
            job = Job.from_upwork_nuxt(raw)
            if job:
                jobs.append(job)
        debug(f"Parsed {len(jobs)} valid jobs for '{keyword}'")
        return jobs

    def scrape_all(self, keywords: Optional[list[str]] = None) -> list[Job]:
        """Run scraper across all keywords."""
        keywords = keywords or DEFAULT_KEYWORDS
        all_jobs: list[Job] = []
        info(f"Upwork scraper: {len(keywords)} keywords")

        for i, kw in enumerate(keywords):
            try:
                jobs = self.scrape_keyword(kw)
                all_jobs.extend(jobs)
            except Exception as e:
                error(f"Keyword failed: '{kw}'", error=str(e))

            # Delay antar keyword
            if i < len(keywords) - 1:
                delay = max(self.delay, 10)  # min 10s antar keyword
                info(f"Waiting {delay}s before next keyword...")
                time.sleep(delay)

        return all_jobs
