import json
import time
import urllib.parse
from DrissionPage import ChromiumPage, ChromiumOptions

def check_nuxt():
    co = ChromiumOptions()
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.auto_port()
    
    page = ChromiumPage(addr_or_opts=co)
    keyword = "python web scraping"
    url = f"https://www.upwork.com/nx/search/jobs/?q={urllib.parse.quote(keyword)}&sort=recency"
    
    page.get(url)
    
    # Wait for cloudflare
    max_wait = 60
    for i in range(max_wait):
        if "Just a moment" not in page.title and "Challenge" not in page.title:
            break
        time.sleep(1)
        
    time.sleep(5) # wait for render
    
    try:
        # Coba ambil state Nuxt
        nuxt_data = page.run_js('return window.__NUXT__')
        
        with open("nuxt_data.json", "w", encoding="utf-8") as f:
            json.dump(nuxt_data, f, indent=2)
            
        print("Berhasil mengekstrak window.__NUXT__ ke nuxt_data.json")
    except Exception as e:
        print("Gagal mengambil __NUXT__:", e)
        
    page.quit()

if __name__ == "__main__":
    check_nuxt()
