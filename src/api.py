"""FastAPI wrapper — trigger scrapers via HTTP.

Usage:
    python -m src.api
    # POST /api/scrape?keyword=python%20web%20scraping
    # POST /api/scrape/all
    # GET  /api/jobs?limit=10
"""

import asyncio
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from src.database import init_db, get_recent_jobs, count_jobs
from src.utils.logger import info, error

app = FastAPI(title="Job Scraper API", on_startup=[init_db])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _run_upwork(keyword: str):
    from src.scrapers.upwork import UpworkScraper
    from src.database import init_db, insert_job
    from src.config import load_config

    cfg = load_config()
    init_db()

    with UpworkScraper(headless=cfg.get("headless", False)) as scraper:
        jobs = scraper.scrape_keyword(keyword)
        new = 0
        for j in jobs:
            if insert_job(j):
                new += 1
        info(f"Upwork '{keyword}': {new} new of {len(jobs)} total")


@app.post("/api/scrape")
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    keyword: str = "python web scraping",
):
    """Scrape one keyword from Upwork in the background."""
    background_tasks.add_task(_run_upwork, keyword)
    return {
        "status": "success",
        "message": f"Scraping started for keyword: '{keyword}'",
    }


def _run_all():
    from src.scrapers.upwork import UpworkScraper
    from src.scrapers.freelancer import FreelancerScraper
    from src.database import init_db, insert_job
    from src.config import load_config

    cfg = load_config()
    init_db()

    total = 0

    # Upwork
    uw_cfg = cfg.get("upwork", {})
    with UpworkScraper(
        headless=cfg.get("headless", False),
        delay=uw_cfg.get("delay", 10),
    ) as scraper:
        jobs = scraper.scrape_all(uw_cfg.get("keywords"))
        for j in jobs:
            if insert_job(j):
                total += 1

    # Freelancer
    fl_cfg = cfg.get("freelancer", {})
    with FreelancerScraper(delay=fl_cfg.get("delay", 3)) as scraper:
        jobs = scraper.scrape_all(fl_cfg.get("keywords"))
        for j in jobs:
            if insert_job(j):
                total += 1

    info(f"Total new jobs: {total}")


@app.post("/api/scrape/all")
async def trigger_scrape_all(background_tasks: BackgroundTasks):
    """Run all scrapers (Upwork + Freelancer) in background."""
    background_tasks.add_task(_run_all)
    return {"status": "success", "message": "All scrapers started"}


@app.get("/api/jobs")
async def list_jobs(limit: int = 10, platform: str = ""):
    """Get recent jobs from the database."""
    p = platform if platform else None
    return {"jobs": get_recent_jobs(limit=limit, platform=p)}


@app.get("/api/stats")
async def stats():
    """Get job counts."""
    return {
        "total": count_jobs(),
        "upwork": count_jobs("upwork"),
        "freelancer": count_jobs("freelancer"),
    }


@app.get("/")
async def root():
    return {"message": "Job Scraper API is running", "endpoints": [
        "POST /api/scrape?keyword=...",
        "POST /api/scrape/all",
        "GET /api/jobs?limit=10&platform=upwork",
        "GET /api/stats",
    ]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=True)
