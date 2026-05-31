"""
Job Filter + Ntfy Notifier.

Hybrid approach:
1. Rule-based filter — cepet, jalan tiap cron
2. Flag job potensial → notif ke HP
3. AI analysis jalan kalo lo minta (lewat chat)

Cara pake:
    python -m src.job_filter              # Filter semua job baru + kirim notif
    python -m src.job_filter --notify     # Kirim notif aja tanpa filter ulang
"""

import json
import os
import re
import sqlite3
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "jobs.db"
NTFY_TOPIC = "Infojobdmrf"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

# ── Keywords buat detect skill match ──
# Dict: keyword -> weight (2 = core skill, 1 = related)
MATCH_KEYWORDS = {
    "web scraping": 2,
    "python": 2,
    "selenium": 2,
    "puppeteer": 2,
    "playwright": 2,
    "beautifulsoup": 2,
    "data extraction": 2,
    "data scraping": 2,
    "data pipeline": 2,
    "llm": 2,
    "rag": 2,
    "langchain": 2,
    "crewai": 2,
    "n8n": 2,
    "fastapi": 2,
    "ai agent": 2,
    "browser automation": 2,
    "api integration": 2,
    # Related (1 point)
    "automation": 1,
    "scraper": 1,
    "crawler": 1,
    "bot": 1,
    "python developer": 1,
    "data mining": 1,
    "data collection": 1,
    "openai": 1,
    "claude": 1,
    "gpt": 1,
    "deepseek": 1,
    "api": 1,
    "backend": 1,
    "flask": 1,
    "django": 1,
    "rest api": 1,
    "drissionpage": 1,
}

# ── Negative keywords ──
SKIP_KEYWORDS = [
    "expert in everything", "equity", "deferred payment",
    "unpaid", "exposure", "pro bono",
    "full stack developer", "full-stack developer",
    # False positive keywords — sering muncul di job non-teknis
    "graphic design", "logo design", "photoshop", "illustrator",
    "social media", "content writer", "copywriting",
    "video editor", "video editing", "voice over",
    "civil engineering", "mechanical engineering",
    "3d modeling", "3d model", "blender",
]

# ── Budget filter ──
MIN_FIXED_BUDGET = 50  # $50 minimum fixed price
MIN_HOURLY_RATE = 10   # $10/hr minimum


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def parse_budget(budget_str: str) -> tuple:
    """Parse budget string jadi (amount_in_usd, type). Returns (0, 'unknown') kalo gagal."""
    if not budget_str or budget_str == "N/A":
        return (0, "unknown")
    
    # Currency conversion (approximate)
    CURRENCY_TO_USD = {
        "INR": 0.012, "IDR": 0.000062, "PHP": 0.018,
        "EUR": 1.08, "GBP": 1.27, "CAD": 0.73,
        "AUD": 0.66, "SGD": 0.74, "MYR": 0.21,
        "THB": 0.028, "VND": 0.000041, "KRW": 0.00075,
        "JPY": 0.0067, "CNY": 0.14, "BRL": 0.19,
        "MXN": 0.055, "NGN": 0.00067,
    }
    
    budget_str_clean = budget_str.replace(",", "")
    
    # Deteksi currency
    detected_currency = "USD"
    for code in CURRENCY_TO_USD:
        if code in budget_str_clean.upper():
            detected_currency = code
            break
    
    usd_rate = CURRENCY_TO_USD.get(detected_currency, 1.0)
    
    # Cek hourly
    if "/hr" in budget_str.lower():
        nums = re.findall(r'[\d.]+', budget_str_clean)
        if nums:
            amount = float(nums[0]) * usd_rate
            return (amount, "hourly")
        return (0, "hourly")
    
    # Cek range "min - max CURRENCY" — ambil yang pertama (min)
    range_match = re.search(r'([\d,.]+)\s*-\s*([\d,.]+)', budget_str)
    if range_match:
        amount = float(range_match.group(1).replace(",", "")) * usd_rate
        return (amount, "fixed")
    
    # Cek angka tunggal
    nums = re.findall(r'[\d.]+', budget_str_clean)
    if nums:
        amount = float(nums[0]) * usd_rate
        return (amount, "fixed")
    
    return (0, "unknown")


def skill_match(text: str) -> tuple:
    """Cocokin teks sama keywords. Returns (score, matched_keywords).
    
    Score minimal 2 untuk lolos filter (setidaknya 1 core skill).
    Score 0-20, capped.
    """
    text_lower = text.lower()
    total = 0
    matched = []
    
    for kw, weight in MATCH_KEYWORDS.items():
        if kw.lower() in text_lower:
            total += weight
            matched.append(kw)
    
    # Dibutuhkan minimal 1 core skill (weight 2) untuk lolos
    has_core = any(MATCH_KEYWORDS[kw] >= 2 for kw in matched)
    
    if not has_core:
        return (0, matched)
    
    score = min(total, 20)
    return (score, matched)


def has_negative_keywords(text: str) -> list:
    """Cek apakah ada negative keywords."""
    text_lower = text.lower()
    found = []
    for kw in SKIP_KEYWORDS:
        if kw.lower() in text_lower:
            found.append(kw)
    return found


def filter_jobs() -> list[dict]:
    """Filter semua job di DB dan return yang potensial.
    
    Cuma proses job dari 24 jam terakhir biar gak numpuk.
    """
    conn = _get_db()
    
    # Ambil job yang diposting dalam 48 jam (kalo ada published_at)
    # atau baru discrape dalam 12 jam (kalo published_at nggak ada)
    rows = conn.execute(
        "SELECT * FROM jobs WHERE status = 'new' AND ("
        "  (published_at IS NOT NULL AND published_at != '' "
        "   AND published_at >= datetime('now', '-2 days'))"
        "  OR "
        "  (published_at IS NULL OR published_at = '' "
        "   AND scraped_at >= datetime('now', '-12 hours'))"
        ") ORDER BY COALESCE(published_at, scraped_at) DESC"
    ).fetchall()
    
    potensial = []
    skipped_budget = 0
    skipped_hourly = 0
    skipped_skill = 0
    skipped_negative = 0
    
    for row in rows:
        job = dict(row)
        
        # ── Budget check ──
        amount, btype = parse_budget(job.get("budget", ""))
        
        # Skip kalo budget nggak jelas
        if btype == "unknown":
            skipped_budget += 1
            continue
        if btype == "fixed" and amount < MIN_FIXED_BUDGET:
            skipped_budget += 1
            continue
        if btype == "hourly" and amount < MIN_HOURLY_RATE:
            skipped_hourly += 1
            continue
        
        # ── Skill match ──
        search_text = f"{job.get('title', '')} {job.get('description', '')}"
        score, matched_kw = skill_match(search_text)
        
        if score < 1:
            skipped_skill += 1
            continue
        
        # ── Negative check ──
        bad_kw = has_negative_keywords(search_text)
        if bad_kw:
            skipped_negative += 1
            continue
        
        # Flags
        job["_score"] = score
        job["_keywords"] = matched_kw
        job["_budget_amount"] = amount
        job["_budget_type"] = btype
        # Display: USD equivalent (kalo bukan USD asli, kasih konversi)
        orig = job.get("budget", "")
        if orig and ("INR" in orig or "EUR" in orig or "GBP" in orig or "CAD" in orig):
            job["_budget_display"] = f"~${amount:.0f} USD"
        else:
            job["_budget_display"] = orig[:25]
        
        potensial.append(job)
        
        # Tandai sebagai 'filtered'
        conn.execute(
            "UPDATE jobs SET status = 'filtered' WHERE job_id = ?",
            (job["job_id"],)
        )
    
    conn.commit()
    conn.close()
    
    print(f"[*] Filter: {len(potensial)} potensial, {skipped_budget} skip budget, "
          f"{skipped_skill} skip skill, {skipped_negative} skip negative")
    
    return potensial


def send_ntfy(message: str, title: str = "Job Match", click_url: str = ""):
    """Kirim notif ke ntfy.sh pake headers (bukan JSON body)."""
    data = message.encode("utf-8")
    
    headers = {
        "Title": title,
        "Tags": "briefcase",
        "Priority": "4",
    }
    if click_url:
        headers["Click"] = click_url
    
    req = urllib.request.Request(NTFY_URL, data=data, headers=headers)
    
    try:
        urllib.request.urlopen(req, timeout=5)
        return True
    except Exception as e:
        print(f"[!] Ntfy failed: {e}", file=sys.stderr)
        return False


def save_analysis(job: dict):
    """Simpan analisis singkat ke file."""
    jobs_dir = Path.home() / "freelance" / "jobs"
    jobs_dir.mkdir(exist_ok=True)
    
    # Buat folder nama job
    safe_name = re.sub(r'[^a-zA-Z0-9]+', '-', job["title"])[:50].strip("-").lower()
    job_dir = jobs_dir / safe_name
    # Kalo udah ada, tambahin timestamp
    if job_dir.exists():
        job_dir = jobs_dir / f"{safe_name}-{datetime.now().strftime('%H%M%S')}"
    job_dir.mkdir(exist_ok=True)
    
    analysis = f"""# Analisis: {job['title']}

**Sumber:** {job.get('platform', 'upwork')}
**Budget:** {job.get('budget', 'N/A')}
**Skill match:** {job['_score']}/20
**Keywords matched:** {', '.join(job['_keywords'][:8])}

**URL:** {job.get('url', '')}

**Deskripsi:**
{job.get('description', '')[:1000]}

---

*Auto-filtered at {datetime.now().isoformat()}*
*Verdict sementara: ⏳ PERLU CEK MANUAL*
"""
    
    analysis_path = job_dir / "analisis.md"
    analysis_path.write_text(analysis)
    return analysis_path


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Job Filter + Notifier")
    parser.add_argument("--notify", action="store_true", help="Kirim notif aja")
    args = parser.parse_args()
    
    if args.notify:
        # Baca filtered jobs yang belum di-notify
        conn = _get_db()
        rows = conn.execute(
            "SELECT * FROM jobs WHERE status = 'filtered' ORDER BY scraped_at DESC LIMIT 5"
        ).fetchall()
        conn.close()
        
        if not rows:
            send_ntfy("Tidak ada job baru yang cocok.", "No Matches Today")
            return
        
        msg_lines = []
        best_url = ""
        for row in rows[:5]:
            j = dict(row)
            msg_lines.append(f"• {j['title'][:50]}\n  {j.get('_budget_display', j.get('budget', 'N/A')[:20])}")
            if not best_url:
                best_url = j.get('url', '')
        
        msg = "\n".join(msg_lines)
        send_ntfy(
            f"{len(rows)} job cocok:\n{msg}",
            f"{len(rows)} Job Match",
            click_url=best_url,
        )
        return
    
    # ── Filter baru ──
    potensial = filter_jobs()
    
    if not potensial:
        print("[*] Tidak ada job baru yang cocok.")
        send_ntfy("Scraping selesai. 0 job cocok dari hasil filter.", "No Matches Today")
        return
    
    # Simpan ke 1 file (overwrite tiap cron)
    filtered_path = Path.home() / "freelance" / "jobs" / "filtered.md"
    lines = ["# Filtered Jobs", f"*Auto-generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n"]
    for job in potensial:
        budget_display = job.get('_budget_display', job.get('budget', 'N/A')[:20])
        lines.append(f"## {job['title']}")
        lines.append(f"- **Budget:** {budget_display} | **Score:** {job['_score']}/20")
        lines.append(f"- **Platform:** {job.get('platform', '?')}")
        lines.append(f"- **URL:** {job.get('url', '')}")
        lines.append("")
    filtered_path.write_text("\n".join(lines))
    print(f"[*] Saved: {filtered_path}")
    
    # Sync ke Joplin
    try:
        from src.joplin_sync import save_filtered_jobs
        if save_filtered_jobs(potensial):
            print(f"[*] Synced to Joplin")
        else:
            print("[!] Joplin sync skipped (app might be open)")
    except Exception as e:
        print(f"[!] Joplin sync error: {e}")
    
    # Sync ke Obsidian vault
    import subprocess
    subprocess.Popen(
        ["bash", str(Path.home() / "freelance" / "tools" / "obsidian_sync.sh")],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    
    # Kirim notif
    msg_lines = []
    best_url = ""
    best_score = 0
    for job in potensial[:5]:
        budget_display = job.get('_budget_display', job.get('budget', 'N/A')[:20])
        job_url = job.get('url', '')
        msg_lines.append(
            f"• {job['title'][:50]}\n"
            f"  {budget_display} | {job['_score']}/20"
        )
        if job['_score'] > best_score and job_url:
            best_score = job['_score']
            best_url = job_url
    
    msg = "\n".join(msg_lines)
    more = f"\n+{len(potensial)-5} lainnya" if len(potensial) > 5 else ""
    send_ntfy(
        f"{len(potensial)} job cocok:\n{msg}\n{more}\nChat opencode: analisis [judul]",
        f"{len(potensial)} Job Match",
        click_url=best_url,
    )
    
    print(f"[✓] {len(potensial)} job potensial. Notif terkirim.")


if __name__ == "__main__":
    main()
