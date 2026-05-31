#!/bin/bash
# Quick runner — activate venv and run the scraper
# Usage: ./run.sh [command]

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Auto-create venv if missing
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Default to "all" if no args
if [ $# -eq 0 ]; then
    python -m src.main all
else
    python -m src.main "$@"
fi
