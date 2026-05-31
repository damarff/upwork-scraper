"""Base scraper — shared browser setup for DrissionPage."""

import time
from abc import ABC, abstractmethod
from typing import Optional

from DrissionPage import ChromiumPage, ChromiumOptions
from src.utils.logger import info, warn, error


CLOUDFLARE_WAIT = 60
POST_RENDER_DELAY = 5


def create_page(headless: bool = False) -> ChromiumPage:
    """Create a DrissionPage ChromiumPage with anti-detection settings."""
    co = ChromiumOptions()
    co.set_argument("--disable-blink-features=AutomationControlled")
    co.auto_port()

    if headless:
        co.headless()
        co.set_argument("--no-sandbox")
        co.set_argument("--disable-gpu")

    return ChromiumPage(addr_or_opts=co)


def wait_for_page(page: ChromiumPage, timeout: int = CLOUDFLARE_WAIT) -> bool:
    """Wait until Cloudflare challenge passes (or timeout)."""
    for i in range(timeout):
        title = page.title
        if "Just a moment" not in title and "Challenge" not in title:
            if i > 0:
                info(f"Cloudflare bypassed after {i}s")
            return True
        if i % 10 == 0 and i > 0:
            info(f"Waiting for Cloudflare... ({i}s)")
        time.sleep(1)
    warn("Cloudflare wait timed out — proceeding anyway")
    return False


class BaseScraper(ABC):
    """Base class for job scrapers."""

    def __init__(self, headless: bool = False, delay: int = 2):
        self.headless = headless
        self.delay = delay  # seconds between requests
        self._page: Optional[ChromiumPage] = None

    @property
    def page(self) -> ChromiumPage:
        if self._page is None:
            self._page = create_page(self.headless)
        return self._page

    @abstractmethod
    def platform(self) -> str:
        """Return platform identifier, e.g. 'upwork', 'freelancer'."""

    @abstractmethod
    def search_keyword(self, keyword: str) -> list[dict]:
        """Search jobs for a keyword. Returns list of raw job dicts."""

    def cleanup(self):
        """Close the browser page if open."""
        if self._page:
            try:
                self._page.quit()
            except Exception:
                pass
            self._page = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cleanup()
