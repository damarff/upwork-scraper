# Upwork Scraper & Autonomous Bidder

## Stack
- Python, DrissionPage (Cloudflare Bypass), FastAPI, SQLite / Supabase

## Arsitektur Singkat
- `scraper.py` — Engine utama untuk bypass Cloudflare dan scraping state internal Upwork.
- `api.py` — FastAPI wrapper untuk men-trigger scraper via HTTP (port 8000).
- `simulate_radar.py` — Script dummy untuk testing UI Realtime.

## Konvensi Multi-Agent (Orkestrasi)
Proyek ini di-maintain oleh skuad AI berikut:
1. **`lysta`** (Analyst/Writer): Bertugas membaca hasil scraping dan menulis proposal Upwork. [MODEL_TIER_FAST]
2. **`codi`** (Backend/Scraper): Bertugas mengatur logika bypass Cloudflare dan routing API. [MODEL_TIER_ADVANCED]
3. **`archie`** (Architect): Merancang skema database (Supabase SQL) dan struktur sistem. [MODEL_TIER_ADVANCED]
4. **`qatsy`** (QA/Testing): Menjalankan script test dan menulis dokumentasi ini. [MODEL_TIER_FAST]

*Note: Jangan mengubah konfigurasi model `agent.json` tanpa persetujuan, agar token cost tetap efisien!*
