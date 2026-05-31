# Upwork Job Scraper

Multi-platform job scraper for Upwork and Freelancer.com with automatic Cloudflare bypass. Extracts job listings via browser automation (DrissionPage) and API calls (curl_cffi), stores results in SQLite.

## Features

- **Upwork scraping** — DrissionPage + Chromium, bypasses Cloudflare JS challenges, extracts `window.__NUXT__` state
- **Freelancer.com scraping** — curl_cffi with Chrome TLS fingerprint impersonation, no browser needed
- **20 keyword categories** — auto-scrapes across AI, automation, scraping, and development niches
- **SQLite storage** — deduplication, status tracking, filtering
- **CLI interface** — `python -m src.main <command>`
- **REST API** — optional FastAPI server for querying results

## Quick Start

```bash
# Install
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Configure
cp config.yaml config.yaml  # edit keywords & delay

# Scrape Freelancer.com (fast, no browser)
python -m src.main freelancer

# Scrape Upwork (needs Chromium + display)
python -m src.main upwork

# Scrape a single job detail
python -m src.main detail <url>

# View results
python -m src.main stats
python -m src.main jobs
```

## Structure

```
src/
├── main.py              # CLI entry point
├── config.py            # Config loader
├── database.py          # SQLite operations
├── job_filter.py        # Relevance filtering
├── scrapers/
│   ├── base.py          # Shared browser setup (DrissionPage)
│   ├── upwork.py        # Upwork Nuxt extraction
│   ├── freelancer.py    # Freelancer.com API (curl_cffi)
│   └── job_detail.py    # Individual job detail scrape
├── models/
│   └── job.py           # Job dataclass + parsers
└── utils/
    ├── logger.py
    └── clean.py
```

## Tech Stack

- Python 3.10+
- DrissionPage (Chromium browser automation)
- curl_cffi (Chrome TLS fingerprint impersonation)
- FastAPI (optional API server)
- SQLite
