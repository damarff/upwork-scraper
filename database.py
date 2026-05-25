import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def init_db():
    print("Database terhubung ke Supabase Cloud.")
    pass # Supabase doesn't need local initialization

def job_exists(job_id):
    # Query Supabase untuk mengecek apakah job_id sudah ada
    response = supabase.table('jobs').select('job_id').eq('job_id', job_id).execute()
    return len(response.data) > 0

def insert_job(job_id, title, url, budget, description, published_at):
    try:
        data = {
            "job_id": job_id,
            "title": title,
            "url": url,
            "budget": budget,
            "description": description,
            "published_at": published_at,
            "status": "new"
        }
        supabase.table('jobs').insert(data).execute()
        return True
    except Exception as e:
        # Menangkap error duplikasi (biasanya memunculkan exception jika primary key sudah ada)
        print(f"Failed to insert job {job_id}: {e}")
        return False
