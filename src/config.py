"""Configuration — loads from config.yaml or defaults."""

import os
from pathlib import Path
from typing import Optional

from src.utils.logger import warn

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"

# Default keywords
UPWORK_KEYWORDS = [
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

FREELANCER_KEYWORDS = [
    "python web scraping",
    "data extraction",
    "fastapi",
    "rag llm",
    "ai agent",
    "automation",
    "bot",
    "web scraper",
    "selenium",
]

# Delay settings
UPWORK_DELAY = 10   # seconds between Upwork keywords
FREELANCER_DELAY = 3  # seconds between Freelancer keywords


def load_config() -> dict:
    """Load config from YAML file if exists, else return defaults."""
    if not CONFIG_PATH.exists():
        return {
            "upwork": {
                "keywords": UPWORK_KEYWORDS,
                "delay": UPWORK_DELAY,
            },
            "freelancer": {
                "keywords": FREELANCER_KEYWORDS,
                "delay": FREELANCER_DELAY,
            },
            "headless": False,
            "log_level": "INFO",
        }

    try:
        import yaml
        with open(CONFIG_PATH) as f:
            cfg = yaml.safe_load(f) or {}
        return cfg
    except ImportError:
        warn("PyYAML not installed — using defaults")
    except Exception as e:
        warn(f"Config load failed ({e}) — using defaults")

    return {
        "upwork": {"keywords": UPWORK_KEYWORDS, "delay": UPWORK_DELAY},
        "freelancer": {"keywords": FREELANCER_KEYWORDS, "delay": FREELANCER_DELAY},
        "headless": False,
        "log_level": "INFO",
    }
