from bs4 import BeautifulSoup
import json

def parse_jobs():
    with open("search_results.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, 'html.parser')
    
    # Upwork biasanya menggunakan <article> untuk setiap job card
    jobs = soup.find_all('article')
    print(f"Ditemukan {len(jobs)} tag <article>.")
    
    if len(jobs) == 0:
        # Coba cari tag dengan kelas tertentu (misal up-card-section)
        jobs = soup.find_all('section', class_=lambda c: c and 'up-card-section' in c)
        print(f"Ditemukan {len(jobs)} tag section up-card-section.")
        
    extracted = []
    for job in jobs[:3]: # Ambil 3 pertama saja
        title_tag = job.find(['h2', 'h3', 'h4', 'a'])
        title = title_tag.get_text(strip=True) if title_tag else "No Title"
        
        link_tag = job.find('a', href=lambda h: h and '~01' in h)
        link = link_tag['href'] if link_tag else "No Link"
        
        desc_tag = job.find('span', {'data-test': 'job-description-text'})
        if not desc_tag:
            desc_tag = job.find('div', class_=lambda c: c and 'description' in c.lower())
        desc = desc_tag.get_text(strip=True)[:100] if desc_tag else "No Desc"
        
        extracted.append({
            'title': title,
            'link': link,
            'desc': desc
        })
        
    print(json.dumps(extracted, indent=2))

if __name__ == "__main__":
    parse_jobs()
