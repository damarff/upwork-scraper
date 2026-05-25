import asyncio
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from scraper import run_scraper

app = FastAPI(title="Upwork Scraper API")

# Allow CORS so the Vite React app can hit this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def start_scraping_task(keyword: str):
    print(f"Background task starting scraper for keyword: {keyword}")
    try:
        run_scraper(keyword)
    except Exception as e:
        print(f"Error in background scraper: {e}")

@app.post("/api/scrape")
async def trigger_scrape(background_tasks: BackgroundTasks, keyword: str = "python web scraping"):
    """
    Triggers the Upwork scraper in the background.
    """
    background_tasks.add_task(start_scraping_task, keyword)
    return {"status": "success", "message": f"Scraper agent deployed for keyword: '{keyword}'."}

@app.get("/")
def read_root():
    return {"message": "Upwork Scraper API is running."}

if __name__ == "__main__":
    import uvicorn
    # Jalankan server di port 8000
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
