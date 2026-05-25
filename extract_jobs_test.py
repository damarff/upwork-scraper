import time
from DrissionPage import ChromiumPage, ChromiumOptions
from bs4 import BeautifulSoup
import urllib.parse

def test_search():
    print("Memulai pencarian lowongan...")
    co = ChromiumOptions()
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.auto_port()
    
    page = ChromiumPage(addr_or_opts=co)
    keyword = "python web scraping"
    url = f"https://www.upwork.com/nx/search/jobs/?q={urllib.parse.quote(keyword)}"
    
    print(f"Mengunjungi: {url}")
    page.get(url)
    
    print("Menunggu loading data pekerjaan...")
    time.sleep(10)
    
    # Simpan html mentah untuk diinspeksi
    with open("search_results.html", "w", encoding="utf-8") as f:
        f.write(page.html)
        
    print("✅ Hasil pencarian disimpan di search_results.html!")
    page.quit()

if __name__ == '__main__':
    test_search()
