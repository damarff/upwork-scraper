from curl_cffi import requests

def test_bypass():
    url = "https://www.upwork.com/freelancers/damarff"
    print(f"Mencoba menembus Cloudflare untuk URL: {url}...")
    
    try:
        # Menggunakan impersonate="chrome" agar TLS handshake persis seperti Chrome asli
        response = requests.get(url, impersonate="chrome")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ BERHASIL TEMBUS CLOUDFLARE!")
            # Ekstrak judul halaman dengan BeautifulSoup nanti, sementara print cuplikan
            print("Cuplikan HTML:")
            print(response.text[:500])
        else:
            print("❌ MASIH TERBLOKIR.")
            print(response.text[:500])
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_bypass()
