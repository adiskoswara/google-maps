import sqlite3
import os
import json
from datetime import datetime

import tempfile
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Vercel / AWS Lambda has a read-only filesystem except temp directory
if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    DB_FILE = os.path.join(tempfile.gettempdir(), "leads.db")
    # Copy seed leads.db to temp directory if it exists in repository
    source_db = os.path.join(BASE_DIR, "leads.db")
    if os.path.exists(source_db) and not os.path.exists(DB_FILE):
        try:
            shutil.copy2(source_db, DB_FILE)
        except Exception:
            pass
else:
    DB_FILE = os.path.join(BASE_DIR, "leads.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            address TEXT,
            city TEXT,
            phone_raw TEXT,
            whatsapp_number TEXT,
            is_mobile BOOLEAN DEFAULT 0,
            has_website BOOLEAN DEFAULT 0,
            website_url TEXT,
            website_type TEXT, -- 'none', 'social_only', 'website'
            rating REAL,
            reviews_count INTEGER DEFAULT 0,
            maps_url TEXT UNIQUE,
            scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_lead(lead_data: dict) -> bool:
    """Save or update a lead in the database. Returns True if inserted, False if updated/skipped."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO leads (
                name, category, address, city, phone_raw, whatsapp_number, 
                is_mobile, has_website, website_url, website_type, rating, 
                reviews_count, maps_url, scanned_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(maps_url) DO UPDATE SET
                name=excluded.name,
                category=excluded.category,
                address=excluded.address,
                city=excluded.city,
                phone_raw=excluded.phone_raw,
                whatsapp_number=excluded.whatsapp_number,
                is_mobile=excluded.is_mobile,
                has_website=excluded.has_website,
                website_url=excluded.website_url,
                website_type=excluded.website_type,
                rating=excluded.rating,
                reviews_count=excluded.reviews_count,
                scanned_at=excluded.scanned_at
        """, (
            lead_data.get('name', 'Tanpa Nama'),
            lead_data.get('category', 'F&B'),
            lead_data.get('address', ''),
            lead_data.get('city', ''),
            lead_data.get('phone_raw', ''),
            lead_data.get('whatsapp_number', ''),
            1 if lead_data.get('is_mobile') else 0,
            1 if lead_data.get('has_website') else 0,
            lead_data.get('website_url', ''),
            lead_data.get('website_type', 'none'),
            lead_data.get('rating', 0.0),
            lead_data.get('reviews_count', 0),
            lead_data.get('maps_url', ''),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving lead: {e}")
        return False
    finally:
        conn.close()

def get_all_leads(filter_no_website=False, only_with_whatsapp=False, search_query=""):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM leads WHERE 1=1"
    params = []
    
    if filter_no_website:
        query += " AND website_type IN ('none', 'social_only')"
        
    if only_with_whatsapp:
        query += " AND whatsapp_number != '' AND whatsapp_number IS NOT NULL AND is_mobile = 1"
        
    if search_query:
        query += " AND (name LIKE ? OR address LIKE ? OR category LIKE ?)"
        term = f"%{search_query}%"
        params.extend([term, term, term])
        
    query += " ORDER BY id DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    leads = [dict(row) for row in rows]
    conn.close()
    return leads

def get_stats():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM leads")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE website_type = 'none'")
    no_website = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE website_type = 'social_only'")
    social_only = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE whatsapp_number != '' AND whatsapp_number IS NOT NULL AND is_mobile = 1")
    with_wa = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE (website_type = 'none' OR website_type = 'social_only') AND is_mobile = 1")
    prime_targets = cursor.fetchone()[0]
    
    conn.close()
    return {
        "total": total,
        "no_website": no_website,
        "social_only": social_only,
        "total_prospects": no_website + social_only,
        "with_whatsapp": with_wa,
        "prime_targets": prime_targets
    }

def delete_lead(lead_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
    conn.commit()
    conn.close()

def clear_all_leads():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM leads")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
