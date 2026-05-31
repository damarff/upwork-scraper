"""Database layer — SQLite lokal + optional Supabase sync.

SQLite selalu dipakai sebagai primary store (offline-first).
Supabase dipakai mirror opsional kalau dikonfigurasi.
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from src.models.job import Job
from src.utils.logger import info, warn, error, debug

load_dotenv()

DB_PATH = Path(__file__).resolve().parent.parent / "jobs.db"

# Supabase config (optional)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Cached supabase client
_supabase = None


def _get_supabase():
    """Lazy-init supabase SDK client."""
    global _supabase
    if _supabase is None and SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            info("Supabase client initialized")
        except Exception as e:
            warn(f"Supabase init failed: {e}")
    return _supabase


# ── SQLite ─────────────────────────────────────────────────────────────


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = _get_conn()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                platform TEXT NOT NULL DEFAULT 'upwork',
                budget TEXT DEFAULT 'N/A',
                description TEXT DEFAULT '',
                published_at TEXT,
                status TEXT DEFAULT 'new',
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_jobs_platform ON jobs(platform);
            CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
            CREATE INDEX IF NOT EXISTS idx_jobs_scraped_at ON jobs(scraped_at DESC);
        """)
        conn.commit()
        info(f"Database ready: {DB_PATH}")
    finally:
        conn.close()


def job_exists(job_id: str, platform: str = "upwork") -> bool:
    """Check if a job already exists in SQLite."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT 1 FROM jobs WHERE job_id = ? AND platform = ?",
            (job_id, platform),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def insert_job(job: Job) -> bool:
    """Insert job into SQLite. Returns True if new, False if duplicate."""
    if job_exists(job.job_id, job.platform):
        debug(f"Duplicate (local): {job.job_id}", platform=job.platform)
        return False

    conn = _get_conn()
    try:
        conn.execute(
            """INSERT OR IGNORE INTO jobs
               (job_id, title, url, platform, budget, description, published_at, status, scraped_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                job.job_id,
                job.title,
                job.url,
                job.platform,
                job.budget,
                job.description,
                job.published_at,
                job.status,
                job.scraped_at or datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        info(f"Saved (local): {job.title[:50]}", platform=job.platform, budget=job.budget)

        # ── Sync ke Supabase kalau ada (best-effort) ──
        _sync_to_supabase(job)

        return True
    except sqlite3.IntegrityError:
        debug(f"Duplicate (local, race): {job.job_id}")
        return False
    finally:
        conn.close()


def _sync_to_supabase(job: Job):
    """Insert job ke Supabase sebagai mirror."""
    client = _get_supabase()
    if not client:
        return

    try:
        # Check dulu biar ga duplicate
        existing = (
            client.table("jobs")
            .select("job_id")
            .eq("job_id", job.job_id)
            .eq("platform", job.platform)
            .execute()
        )
        if existing.data:
            return

        client.table("jobs").insert(job.to_dict()).execute()
        debug(f"Synced to Supabase: {job.job_id}")
    except Exception as e:
        warn(f"Supabase sync failed: {e}", job_id=job.job_id)


def get_recent_jobs(limit: int = 10, platform: Optional[str] = None) -> list[dict]:
    """Get most recent jobs from SQLite."""
    conn = _get_conn()
    try:
        if platform:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE platform = ? ORDER BY scraped_at DESC LIMIT ?",
                (platform, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM jobs ORDER BY scraped_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def count_jobs(platform: Optional[str] = None) -> int:
    """Count jobs in SQLite."""
    conn = _get_conn()
    try:
        if platform:
            row = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE platform = ?", (platform,)
            ).fetchone()
        else:
            row = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()
        return row[0]
    finally:
        conn.close()
