import time
from DrissionPage import ChromiumPage, ChromiumOptions
from bs4 import BeautifulSoup

def scrape_profile():
    print("Memulai DrissionPage untuk scraping profil lengkap...")
    
    co = ChromiumOptions()
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.auto_port()
    
    page = ChromiumPage(addr_or_opts=co)
    url = "https://www.upwork.com/freelancers/damarff"
    
    page.get(url)
    print("Menunggu render Nuxt.js...")
    time.sleep(15)  # Ekstra waktu tunggu untuk rendering client-side
    
    print("Mengekstrak data profil...")
    
    try:
        html_content = page.html
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Hapus tag script dan style agar teks lebih bersih
        for script in soup(["script", "style"]):
            script.extract()
            
        text = soup.get_text(separator='\n', strip=True)
        
        with open("profile_data.txt", "w", encoding="utf-8") as f:
            f.write(text)
            
        print("✅ Profil berhasil diekstrak dengan BeautifulSoup dan disimpan ke profile_data.txt!")
        print("--- AWAL PROFIL ---")
        print(text[:1000]) 
        
    except Exception as e:
        print(f"Gagal mengekstrak: {e}")
        
    finally:
        page.quit()

if __name__ == '__main__':
    scrape_profile()
