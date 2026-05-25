import time
import random
import uuid
import datetime
from database import insert_job

dummy_jobs = [
    ("Python Backend Developer for AI Scraper", "$1,500 - $3,000", "Looking for an expert Python developer to build a scalable web scraping infrastructure using Supabase and Playwright..."),
    ("React + Vite Frontend Engineer (Apple Aesthetic)", "$40/hr", "Need a frontend wizard to build a beautiful glassmorphism dashboard connected to real-time Supabase endpoints..."),
    ("Data Engineer for PDF OCR Pipeline", "$2,000", "We have thousands of financial PDFs. We need a robust OCR pipeline using LLMs and deterministic rules..."),
    ("Autonomous AI Agent Developer", "$5,000", "Build a multi-agent system that bids on Upwork jobs automatically based on our agency's criteria..."),
    ("Supabase & PostgreSQL Expert", "$60/hr", "Need help migrating our messy SQLite database to a structured Supabase cloud instance with Realtime enabled...")
]

print("Menjalankan Simulasi Radar Upwork (Mengirim 1 dummy job setiap 5 detik)...")
print("Silakan buka Web Portofolio di browser untuk melihat efek Real-time nya!")

for job in dummy_jobs:
    time.sleep(5) # Jeda 5 detik antar job biar radar kelihatan kerjanya
    job_id = str(uuid.uuid4())[:8]
    title, budget, desc = job
    published_at = datetime.datetime.utcnow().isoformat()
    
    success = insert_job(job_id, title, f"https://upwork.com/jobs/~{job_id}", budget, desc, published_at)
    if success:
        print(f"[+] INFILTRATED: {title} ({budget})")
    else:
        print(f"[-] FAILED: {title}")

print("Simulasi selesai.")
