#!/usr/bin/env python3
"""CLI entry point for the job scraper.

Usage:
    python -m src.main upwork                         # Scrape Upwork (all keywords)
    python -m src.main freelancer                     # Scrape Freelancer
    python -m src.main all                            # Scrape both
    python -m src.main upwork "python scraping"       # Single keyword
    python -m src.main detail <url>                   # Scrape job detail
    python -m src.main jobs                           # List recent jobs
    python -m src.main stats                          # Show statistics
    python -m src.main api                            # Start API server
"""

import sys
import argparse
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import init_db, insert_job, get_recent_jobs, count_jobs
from src.config import load_config
from src.utils.logger import info, error, set_level


def cmd_upwork(args):
    from src.scrapers.upwork import UpworkScraper

    cfg = load_config()
    uw_cfg = cfg.get("upwork", {})
    keywords = args.keywords or uw_cfg.get("keywords")

    init_db()
    with UpworkScraper(
        headless=cfg.get("headless", False),
        delay=uw_cfg.get("delay", 10),
    ) as scraper:
        if len(keywords) == 1:
            jobs = scraper.scrape_keyword(keywords[0])
        else:
            jobs = scraper.scrape_all(keywords)

    new = 0
    for j in jobs:
        if insert_job(j):
            new += 1
    info(f"Upwork done: {new} new of {len(jobs)} total")


def cmd_freelancer(args):
    from src.scrapers.freelancer import FreelancerScraper

    cfg = load_config()
    fl_cfg = cfg.get("freelancer", {})
    keywords = args.keywords or fl_cfg.get("keywords")

    init_db()
    with FreelancerScraper(delay=fl_cfg.get("delay", 3)) as scraper:
        if len(keywords) == 1:
            jobs = scraper.scrape_keyword(keywords[0])
        else:
            jobs = scraper.scrape_all(keywords)

    new = 0
    for j in jobs:
        if insert_job(j):
            new += 1
    info(f"Freelancer done: {new} new of {len(jobs)} total")


def cmd_all(args):
    info("Running all scrapers...")
    cmd_upwork(args)
    cmd_freelancer(args)
    info("All scrapers finished")


def cmd_detail(args):
    from src.scrapers.job_detail import JobDetailScraper
    from src.scrapers.upwork import UpworkScraper
    from src.database import init_db, insert_job
    from src.models.job import Job
    from src.config import load_config

    cfg = load_config()
    init_db()

    with JobDetailScraper(headless=cfg.get("headless", False)) as scraper:
        detail = scraper.scrape_job_detail(args.url)

    if not detail:
        error("Failed to scrape job detail")
        return

    # Tampilkan metadata
    print(f"\n{'='*55}")
    print(f"  {detail['title']}")
    print(f"{'='*55}")
    print(f"  Budget:  {detail['budget']} ({detail['budget_type']})")
    if detail.get('hours'):
        print(f"  Hours:   {detail['hours']}")
    if detail.get('duration'):
        print(f"  Durasi:  {detail['duration']}")
    if detail.get('experience_level'):
        print(f"  Level:   {detail['experience_level']}")
    if detail.get('proposals'):
        print(f"  Proposals: {detail['proposals']}")
    if detail.get('skills'):
        print(f"  Skills:  {', '.join(detail['skills'][:5])}")
    client = detail.get('client', {})
    if client.get('rating'):
        print(f"  Client:  ⭐ {client['rating']} | {client.get('hires', '?')} hires | {client.get('country', '')}")
    if client.get('member_since'):
        print(f"  Member:  {client['member_since'][:60]}")
    print(f"{'='*55}")
    print(f"  DESCRIPTION:")
    print(f"  {detail['description'][:2000]}")
    print(f"{'='*55}")

    # Simpan ke database
    try:
        # Ekstrak job_id dari URL
        import re
        job_id_match = re.search(r'~(\d+)', args.url)
        job_id = f"~{job_id_match.group(1)}" if job_id_match else f"~detail-{hash(args.url) % 10**12}"

        job = Job(
            job_id=job_id,
            title=detail['title'] or "Unknown",
            url=args.url,
            platform="upwork",
            budget=detail.get('budget', 'N/A'),
            description=detail.get('description', '')[:5000],
            published_at=detail.get('published_at'),
        )
        if insert_job(job):
            info("Saved to database")
        else:
            info("Already in database (duplicate)")
    except Exception as e:
        warn(f"Could not save to DB: {e}")


def cmd_jobs(args):
    init_db()
    jobs = get_recent_jobs(limit=args.limit, platform=args.platform)
    if not jobs:
        print("No jobs found.")
        return
    for j in jobs:
        print(f"\n{'─'*50}")
        print(f"  {j['title'][:70]}")
        print(f"  Platform: {j['platform']} | Budget: {j['budget']} | Status: {j['status']}")
        print(f"  URL: {j['url']}")
    print(f"\nTotal shown: {len(jobs)}")


def cmd_stats(args):
    init_db()
    print(f"Total jobs:     {count_jobs()}")
    print(f"  Upwork:       {count_jobs('upwork')}")
    print(f"  Freelancer:   {count_jobs('freelancer')}")


def cmd_joplin_sync(args):
    """Sync analysis file ke Joplin."""
    from src.joplin_sync import save_note
    
    path = Path(args.file)
    if not path.exists():
        error(f"File not found: {args.file}")
        return
    
    body = path.read_text(encoding="utf-8")
    if save_note(args.title, body):
        info(f"Synced to Joplin: {args.title}")
    else:
        warn("Joplin sync failed (app might be open)")


def cmd_api(args):
    info("Starting API server on port 8000...")
    import uvicorn
    uvicorn.run("src.api:app", host="0.0.0.0", port=args.port or 8000, reload=args.reload)


def main():
    parser = argparse.ArgumentParser(description="Job Scraper CLI")
    parser.add_argument("--log-level", default=None, help="DEBUG, INFO, WARN, ERROR")
    sub = parser.add_subparsers(dest="command", required=True)

    p_up = sub.add_parser("upwork", help="Scrape Upwork")
    p_up.add_argument("keywords", nargs="*", help="One or more keywords (default: from config)")

    p_fl = sub.add_parser("freelancer", help="Scrape Freelancer")
    p_fl.add_argument("keywords", nargs="*", help="One or more keywords (default: from config)")

    p_all = sub.add_parser("all", help="Scrape both Upwork and Freelancer")
    p_all.add_argument("keywords", nargs="*", help="Keywords (applied to both)")

    p_det = sub.add_parser("detail", help="Scrape job detail page")
    p_det.add_argument("url", help="Upwork job URL")

    p_jobs = sub.add_parser("jobs", help="List recent jobs")
    p_jobs.add_argument("--limit", type=int, default=10, help="Number of jobs")
    p_jobs.add_argument("--platform", default=None, help="Filter by platform")

    p_st = sub.add_parser("stats", help="Show job statistics")

    p_api = sub.add_parser("api", help="Start API server")
    p_api.add_argument("--port", type=int, default=8000)
    p_api.add_argument("--reload", action="store_true", help="Auto-reload on changes")

    p_js = sub.add_parser("joplin-sync", help="Sync analysis file ke Joplin")
    p_js.add_argument("title", help="Judul note")
    p_js.add_argument("file", help="Path ke file markdown")

    args = parser.parse_args()

    # Set log level if specified
    if args.log_level:
        set_level(args.log_level)

    # Dispatch
    cmds = {
        "upwork": cmd_upwork,
        "freelancer": cmd_freelancer,
        "all": cmd_all,
        "detail": cmd_detail,
        "jobs": cmd_jobs,
        "stats": cmd_stats,
        "api": cmd_api,
        "joplin-sync": cmd_joplin_sync,
    }
    cmds[args.command](args)


if __name__ == "__main__":
    main()
