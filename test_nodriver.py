import asyncio
import nodriver as uc

async def main():
    print("Memulai Nodriver (Undetected Browser)...")
    # Launch browser
    browser = await uc.start()
    
    url = "https://www.upwork.com/freelancers/damarff"
    print(f"Mengunjungi: {url}")
    
    page = await browser.get(url)
    
    # Tunggu beberapa detik untuk membiarkan Turnstile loading
    print("Menunggu halaman loading (dan bypass Cloudflare)...")
    await asyncio.sleep(10)
    
    # Ambil elemen title
    title = await page.evaluate("document.title")
    print(f"Title Halaman: {title}")
    
    if "Challenge" in title or "Access denied" in title:
        print("❌ Masih kena blokir Cloudflare Turnstile.")
    else:
        print("✅ Berhasil nembus Cloudflare!")
        body = await page.evaluate("document.body.innerText")
        print("Cuplikan Isi:")
        print(body[:500])
        
    await browser.stop()

if __name__ == '__main__':
    # Fix for asyncio on linux if needed
    uc.loop().run_until_complete(main())
