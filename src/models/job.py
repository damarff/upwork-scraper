"""Job model — shared across scrapers and database."""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Job:
    job_id: str
    title: str
    url: str
    platform: str  # "upwork" | "freelancer"
    budget: str = "N/A"
    description: str = ""
    published_at: Optional[str] = None
    status: str = "new"
    scraped_at: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        if d["scraped_at"] is None:
            d["scraped_at"] = datetime.utcnow().isoformat()
        return d

    @staticmethod
    def from_upwork_nuxt(job: dict) -> Optional["Job"]:
        """Buat Job dari item state jobsSearch.jobs di window.__NUXT__."""
        from bs4 import BeautifulSoup

        def clean(raw):
            if not raw:
                return ""
            return BeautifulSoup(raw, "html.parser").get_text(separator=" ", strip=True)

        job_id = job.get("ciphertext") or job.get("uid")
        if not job_id:
            return None
        if not str(job_id).startswith("~"):
            job_id = f"~01{job_id}"

        title = clean(job.get("title", "No Title"))
        desc = clean(job.get("description", ""))
        url = f"https://www.upwork.com/jobs/{job_id}"

        budget = "N/A"
        if job.get("tier"):
            budget = job["tier"]
        if job.get("amount"):
            amt = job["amount"]
            if isinstance(amt, dict) and amt.get("amount"):
                budget = f"${amt['amount']}"
        elif job.get("hourlyBudgetText"):
            budget = job["hourlyBudgetText"]

        published_at = job.get("publishedOn", "Baru saja")

        return Job(
            job_id=job_id,
            title=title,
            url=url,
            platform="upwork",
            budget=budget,
            description=desc,
            published_at=published_at,
        )

    @staticmethod
    def from_freelancer_api(project: dict) -> Optional["Job"]:
        """Buat Job dari response API Freelancer.com."""
        job_id = str(project.get("id", ""))
        if not job_id:
            return None

        title = project.get("title", "No Title")
        seo_url = project.get("seo_url", "")
        url = f"https://www.freelancer.com/projects/{seo_url}" if seo_url else ""

        budget_obj = project.get("budget", {})
        currency_obj = project.get("currency", {})
        currency_code = currency_obj.get("code", "USD")
        min_budget = budget_obj.get("minimum")
        max_budget = budget_obj.get("maximum")

        budget_str = "TBD"
        if min_budget and max_budget:
            budget_str = f"{min_budget} - {max_budget} {currency_code}"
        elif min_budget:
            budget_str = f"> {min_budget} {currency_code}"

        description = project.get("preview_description", "")

        published_at = None
        ts = project.get("submitdate")
        if ts:
            published_at = datetime.fromtimestamp(ts).isoformat()

        return Job(
            job_id=job_id,
            title=title,
            url=url,
            platform="freelancer",
            budget=budget_str,
            description=description,
            published_at=published_at,
        )
