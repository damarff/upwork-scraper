import json

def analyze_nuxt():
    try:
        with open("nuxt_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Cari kata kunci "jobs" atau "results" di dalam struktur
        def find_jobs(d, path=""):
            if isinstance(d, dict):
                for k, v in d.items():
                    if k in ['jobs', 'results', 'searchResults', 'edges', 'nodes']:
                        if isinstance(v, list) and len(v) > 0:
                            print(f"Kemungkinan daftar pekerjaan ditemukan di path: {path}->{k} (Jumlah: {len(v)})")
                            # Print sampel pertama
                            print("Sampel item pertama:")
                            print(json.dumps(v[0], indent=2)[:500])
                            print("-" * 50)
                    find_jobs(v, f"{path}->{k}")
            elif isinstance(d, list):
                for i, item in enumerate(d):
                    find_jobs(item, f"{path}[{i}]")
                    
        print("Menganalisis struktur nuxt_data.json...")
        find_jobs(data, "root")
        print("Selesai.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_nuxt()
