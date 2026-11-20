import sys
import time
from DrissionPage import ChromiumPage, ChromiumOptions

def scrape_freelancer_job(url):
    print(f"Menjalankan Freelancer Scraper untuk URL: {url}")
    co = ChromiumOptions()
    co.headless()
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-gpu')
    page = ChromiumPage(co)
    try:
        page.get(url)
        # Tunggu Angular merender komponen utama
        time.sleep(5)
        
        title = page.title
        # Gunakan eksekusi JS native untuk menembus Angular Shadow DOM
        text_content = page.run_js('return document.body.innerText')
        
        with open("dump_freelancer.txt", "w", encoding="utf-8") as f:
            f.write(f"TITLE: {title}\n")
            f.write("=== CONTENT ===\n")
            f.write(text_content if text_content else "KOSONG!")
            
        print("Scraping sukses! Data disimpan di dump_freelancer.txt")
    except Exception as e:
        print(f"Gagal melakukan scraping: {e}")
    finally:
        page.quit()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        target_url = "https://www.freelancer.com/projects/data-analysis/Simple-Excel-Data-Entry-40473971/details"
    
    scrape_freelancer_job(target_url)
