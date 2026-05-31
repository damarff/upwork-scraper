"""
Joplin Sync Helper.
Menyimpan hasil filter & analisis ke Joplin via direct SQLite.

PENTING: Joplin harus dimatiin pas nulis ke DB biar aman.
"""

import hashlib
import sqlite3
import time
from datetime import datetime
from pathlib import Path

JOPLIN_DB = Path.home() / ".config" / "joplin" / "database.sqlite"
FOLDER_NAME = "Freelance Jobs"
PARENT_FOLDER_ID = "42d05b2be813427d9eda1c8e6f838e4f"  # 02 PROJECT


def _connect():
    """Koneksi ke Joplin database."""
    if not JOPLIN_DB.exists():
        return None
    conn = sqlite3.connect(str(JOPLIN_DB))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _note_id(title: str) -> str:
    """Buat deterministic note ID dari title (MD5)."""
    return hashlib.md5(title.encode()).hexdigest()


def _timestamp() -> int:
    """Millisecond timestamp buat Joplin."""
    return int(datetime.now().timestamp() * 1000)


def ensure_folder() -> str | None:
    """Bikin folder 'Freelance Jobs' kalo belum ada, return ID-nya."""
    conn = _connect()
    if not conn:
        return None
    
    cur = conn.cursor()
    
    # Cek apakah folder udah ada
    row = cur.execute(
        "SELECT id FROM folders WHERE title = ?", (FOLDER_NAME,)
    ).fetchone()
    
    if row:
        folder_id = row[0]
    else:
        # Generate deterministic ID
        folder_id = hashlib.md5(FOLDER_NAME.encode()).hexdigest()
        now = _timestamp()
        cur.execute(
            "INSERT INTO folders (id, title, created_time, updated_time, "
            "user_created_time, user_updated_time, parent_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (folder_id, FOLDER_NAME, now, now, now, now, PARENT_FOLDER_ID)
        )
        conn.commit()
    
    conn.close()
    return folder_id


def save_note(title: str, body: str, tags: str = "") -> bool:
    """Simpan/update note di Joplin.
    
    Args:
        title: Judul note (juga dipake buat ID deterministic)
        body: Isi note (Markdown)
        tags: Tags dipisah koma (opsional)
    
    Returns:
        True kalo berhasil
    """
    conn = _connect()
    if not conn:
        return False
    
    try:
        folder_id = ensure_folder()
        if not folder_id:
            return False
        
        note_id = _note_id(title)
        now = _timestamp()
        cur = conn.cursor()
        
        # Cek apakah note udah ada
        existing = cur.execute(
            "SELECT id FROM notes WHERE id = ?", (note_id,)
        ).fetchone()
        
        if existing:
            # Update
            cur.execute(
                "UPDATE notes SET title = ?, body = ?, updated_time = ?, "
                "user_updated_time = ? WHERE id = ?",
                (title, body, now, now, note_id)
            )
        else:
            # Insert
            cur.execute(
                "INSERT INTO notes (id, parent_id, title, body, created_time, "
                "updated_time, user_created_time, user_updated_time, "
                "is_todo, markup_language) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 1)",
                (note_id, folder_id, title, body, now, now, now, now)
            )
        
        conn.commit()
        return True
    except Exception as e:
        print(f"[!] Joplin sync failed: {e}")
        return False
    finally:
        conn.close()


def save_filtered_jobs(potensial: list) -> bool:
    """Simpan daftar filtered jobs ke 1 note di Joplin."""
    lines = ["# Filtered Jobs\n"]
    lines.append(f"*Auto-generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
    
    for job in potensial:
        budget_display = job.get('_budget_display', job.get('budget', 'N/A')[:20])
        lines.append(f"## {job['title']}")
        lines.append(f"- **Budget:** {budget_display} | **Score:** {job['_score']}/20")
        lines.append(f"- **Platform:** {job.get('platform', '?')}")
        lines.append(f"- **URL:** {job.get('url', '')}")
        lines.append("")
    
    body = "\n".join(lines)
    return save_note("📋 Filtered Jobs", body)
