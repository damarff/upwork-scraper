#!/bin/bash
# Hermes-triggered upwork scraper — runs via SSH from VPS
# This script is called by the VPS cron job

DIR="$HOME/freelance/work/upwork-scraper"
cd "$DIR" || exit 1

source venv/bin/activate 2>/dev/null

# Run scraper on all keywords
python -m src.main upwork 2>&1

# Get new job count
NEW_JOBS=$(python -c "
from src.database import count_jobs
print(count_jobs(since_hours=24))
" 2>/dev/null)

echo "New jobs in 24h: $NEW_JOBS"
