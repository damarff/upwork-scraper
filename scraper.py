import time
import urllib.parse
from DrissionPage import ChromiumPage, ChromiumOptions
from bs4 import BeautifulSoup
from database import init_db, job_exists, insert_job

def clean_html(raw_html):
    if not raw_html: return ""
    return BeautifulSoup(raw_html, "html.parser").get_text(separator=" ", strip=True)

def run_scraper(keyword="python web scraping"):
    print(f"[*] Memulai Nuxt Scraper untuk keyword: '{keyword}'")
    init_db()
    
    co = ChromiumOptions()
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.auto_port()
    
    page = ChromiumPage(addr_or_opts=co)
    url = f"https://www.upwork.com/nx/search/jobs/?q={urllib.parse.quote(keyword)}&sort=recency"
    print(f"[*] Mengunjungi: {url}")
    page.get(url)
    
    # Tunggu Cloudflare (jika ada)
    max_wait = 60
    for i in range(max_wait):
        if "Just a moment" not in page.title and "Challenge" not in page.title:
            break
        print(f"Menunggu Cloudflare... ({i}/{max_wait} detik)")
        time.sleep(1)
        
    time.sleep(5) # Tunggu Nuxt selesai render state
    
    try:
        print("[*] Mengekstrak JSON dari internal memory Upwork (window.__NUXT__)...")
        nuxt_data = page.run_js('return window.__NUXT__')
        
        jobs = nuxt_data.get('state', {}).get('jobsSearch', {}).get('jobs', [])
        print(f"[*] Ditemukan {len(jobs)} pekerjaan di state internal!")
        
        new_jobs_count = 0
        for job in jobs:
            job_id = job.get('ciphertext', job.get('uid', 'unknown'))
            if not job_id.startswith('~'):
                job_id = f"~01{job_id}" # Fallback
                
            if job_exists(job_id):
                continue
                
            title = clean_html(job.get('title', 'No Title'))
            desc = clean_html(job.get('description', ''))
            
            # Konstruksi URL pekerjaan
            job_url = f"https://www.upwork.com/jobs/{job_id}"
            
            # Ambil budget jika ada
            budget = "N/A"
            if job.get('tier'):
                budget = job.get('tier') # Entry/Intermediate/Expert
            if job.get('amount'):
                budget = f"${job.get('amount').get('amount', '')}"
            elif job.get('hourlyBudgetText'):
                budget = job.get('hourlyBudgetText')
                
            published_at = job.get('publishedOn', 'Baru saja')
            
            success = insert_job(job_id, title, job_url, budget, desc, published_at)
            if success:
                print(f"✅ [BARU] {title} | {budget}")
                new_jobs_count += 1
                
        print(f"[*] Scraping selesai! {new_jobs_count} pekerjaan baru masuk database.")
        
    except Exception as e:
        print(f"❌ Gagal mengekstrak: {e}")
        
    finally:
        time.sleep(2)
        page.quit()

if __name__ == "__main__":
    run_scraper()
