import os
import subprocess
import json
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def init_db():
    print("Database terhubung ke Supabase Cloud (via REST Curl).")
    pass

def job_exists(job_id, platform="upwork"):
    cmd = [
        "curl", "-s",
        f"{SUPABASE_URL}/rest/v1/jobs?select=job_id&job_id=eq.{job_id}&platform=eq.{platform}",
        "-H", f"apikey: {SUPABASE_KEY}"
    ]
    try:
        res = subprocess.check_output(cmd, text=True, timeout=10)
        data = json.loads(res)
        return len(data) > 0
    except Exception:
        return False

def insert_job(job_id, title, url, budget, description, published_at, platform="upwork"):
    data = {
        "job_id": job_id,
        "title": title,
        "url": url,
        "budget": budget,
        "description": description,
        "published_at": published_at,
        "platform": platform,
        "status": "new"
    }
    cmd = [
        "curl", "-s", "-X", "POST",
        f"{SUPABASE_URL}/rest/v1/jobs",
        "-H", f"apikey: {SUPABASE_KEY}",
        "-H", f"Authorization: Bearer {SUPABASE_KEY}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(data)
    ]
    try:
        subprocess.check_output(cmd, text=True, timeout=10)
        return True
    except Exception as e:
        print(f"Failed to insert job {job_id} ({platform}): {e}")
        return False
