import os
import asyncio
import io
import json
import threading
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd

from database import init_db, save_lead, get_all_leads, get_stats, delete_lead, clear_all_leads
from scraper import GoogleMapsScanner
from ai_pitch import generate_ai_pitch

init_db()

app = FastAPI(
    title="Google Maps F&B Intelligence & WhatsApp Lead Finder",
    redirect_slashes=False
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global scanner state & event broadcast queue
active_scanner: Optional[GoogleMapsScanner] = None
scan_thread: Optional[threading.Thread] = None
event_subscribers = []

class ScanRequest(BaseModel):
    keyword: str = "cafe"
    city: str = "Surabaya"
    max_results: int = 20
    filter_no_website_only: bool = False

def broadcast_event(event_type: str, data: dict):
    payload = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    # Dispatch to all connected SSE clients
    for q in list(event_subscribers):
        try:
            q.put_nowait(payload)
        except Exception:
            pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

@app.get("/", response_class=HTMLResponse)
@app.get("/api", response_class=HTMLResponse)
@app.get("/api/", response_class=HTMLResponse)
@app.get("/api/index", response_class=HTMLResponse)
@app.get("/api/index.py", response_class=HTMLResponse)
async def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    with open(index_file, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/demo", response_class=HTMLResponse)
@app.get("/api/demo", response_class=HTMLResponse)
async def serve_demo():
    demo_file = os.path.join(STATIC_DIR, "demo.html")
    with open(demo_file, "r", encoding="utf-8") as f:
        return f.read()

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    path = request.url.path
    # If the user is requesting root or page route on Vercel, fallback to index.html
    if not path.startswith("/static/"):
        index_file = os.path.join(STATIC_DIR, "index.html")
        if os.path.exists(index_file):
            with open(index_file, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
    return JSONResponse(status_code=404, content={"detail": f"Route {path} not found"})

@app.get("/api/stream")
async def sse_stream(request: Request):
    """Server-Sent Events endpoint for live scan progress, logs, and new leads."""
    q = asyncio.Queue()
    event_subscribers.append(q)

    async def event_generator():
        try:
            # Send initial ping
            yield f"event: ping\ndata: {{\"status\": \"connected\"}}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(q.get(), timeout=20.0)
                    yield data
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            if q in event_subscribers:
                event_subscribers.remove(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

def run_scanner_worker(keyword, city, max_results, filter_no_website_only):
    global active_scanner
    
    def on_scanner_event(event_type, data):
        if event_type == "lead_found":
            # Save directly to database
            save_lead(data)
        broadcast_event(event_type, data)

    active_scanner = GoogleMapsScanner(on_event=on_scanner_event)
    try:
        active_scanner.scan(
            keyword=keyword,
            city=city,
            max_results=max_results,
            filter_no_website_only=filter_no_website_only
        )
    except Exception as e:
        broadcast_event("error", {"message": f"Terjadi kesalahan saat scanning: {str(e)}"})
    finally:
        active_scanner = None
        broadcast_event("status", {"message": "Pemindaian selesai.", "progress": 100})

@app.post("/api/scan")
async def start_scan(req: ScanRequest):
    global active_scanner, scan_thread
    if active_scanner is not None:
        return JSONResponse(status_code=400, content={"error": "Scanning sedang berjalan. Harap tunggu atau klik Stop."})

    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        broadcast_event("log", {"message": "⚠️ [Info Cloud Vercel] Vercel Serverless Function tidak mendukung background browser Playwright."})
        broadcast_event("log", {"message": "💡 Untuk scraping data baru dari Google Maps, jalankan di komputer lokal (python run.py) atau VPS."})
        broadcast_event("status", {"message": "Playwright butuh container aktif (Gunakan Local/VPS)", "progress": 100})
        return {"status": "cloud_preview", "message": "Playwright scraping requires a full VPS or local environment."}

    scan_thread = threading.Thread(
        target=run_scanner_worker,
        args=(req.keyword, req.city, req.max_results, req.filter_no_website_only),
        daemon=True
    )
    scan_thread.start()
    return {"status": "started", "query": f"{req.keyword} di {req.city}", "target": req.max_results}

@app.post("/api/stop")
async def stop_scan():
    global active_scanner
    if active_scanner:
        active_scanner.stop()
        broadcast_event("log", {"message": "⛔ Pemindaian dihentikan oleh pengguna."})
        broadcast_event("status", {"message": "Pemindaian dihentikan.", "progress": 0})
        return {"status": "stopped"}
    return {"status": "not_running"}

@app.get("/api/leads")
@app.get("/leads")
async def fetch_leads(
    filter_no_website: bool = Query(False),
    only_with_whatsapp: bool = Query(False),
    search: str = Query("")
):
    leads = get_all_leads(
        filter_no_website=filter_no_website,
        only_with_whatsapp=only_with_whatsapp,
        search_query=search
    )
    return {"leads": leads, "count": len(leads)}

@app.get("/api/stats")
@app.get("/stats")
async def fetch_stats():
    return get_stats()

@app.delete("/api/leads/{lead_id}")
@app.delete("/leads/{lead_id}")
async def remove_lead(lead_id: int):
    delete_lead(lead_id)
    return {"status": "deleted", "id": lead_id}

@app.post("/api/leads/clear")
@app.post("/leads/clear")
async def clear_leads():
    clear_all_leads()
    return {"status": "cleared"}

class AIPitchRequest(BaseModel):
    lead: dict
    api_key: Optional[str] = ""
    goal: Optional[str] = "website"
    linkedin_url: Optional[str] = ""
    sender_name: Optional[str] = ""

@app.post("/api/ai/pitch")
@app.post("/ai/pitch")
async def generate_pitch_endpoint(req: AIPitchRequest):
    pitch = generate_ai_pitch(
        req.lead, 
        api_key=req.api_key, 
        goal=req.goal,
        linkedin_url=req.linkedin_url or "",
        sender_name=req.sender_name or ""
    )
    return {"pitch": pitch}

@app.get("/api/export/excel")
async def export_excel(
    filter_no_website: bool = Query(False),
    only_with_whatsapp: bool = Query(False)
):
    leads = get_all_leads(
        filter_no_website=filter_no_website,
        only_with_whatsapp=only_with_whatsapp
    )
    
    # Format data for clean, professional Excel
    rows = []
    for l in leads:
        web_status = "❌ Belum Ada Website"
        if l['website_type'] == 'social_only':
            web_status = "⚠️ Hanya Medsos (Perlu Website)"
        elif l['website_type'] == 'website':
            web_status = "✅ Ada Website"

        wa_status = "WhatsApp Aktif (Mobile)" if l['is_mobile'] else ("Telp Kantor / Landline" if l['phone_raw'] else "Belum Ada Kontak")
        wa_link = f"https://wa.me/{l['whatsapp_number']}" if l['is_mobile'] else ""

        rows.append({
            "Nama Bisnis": l['name'],
            "Kategori": l['category'],
            "Status Website": web_status,
            "Website URL": l['website_url'] or "-",
            "No. WhatsApp": l['whatsapp_number'] or l['phone_raw'] or "-",
            "Status Kontak": wa_status,
            "Direct Chat WA": wa_link or "-",
            "Rating": l['rating'] or 0,
            "Total Ulasan": l['reviews_count'] or 0,
            "Alamat Lengkap": l['address'] or "-",
            "Kota": l['city'] or "-",
            "Link Google Maps": l['maps_url'] or "-",
            "Waktu Scan": l['scanned_at']
        })

    df = pd.DataFrame(rows)
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Leads F&B")
        
        # Style header
        worksheet = writer.sheets["Leads F&B"]
        for col_num in range(1, len(df.columns) + 1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.style = "Accent1"

    output.seek(0)
    filename = f"leads_fnb_google_maps_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/export/csv")
async def export_csv(
    filter_no_website: bool = Query(False),
    only_with_whatsapp: bool = Query(False)
):
    leads = get_all_leads(
        filter_no_website=filter_no_website,
        only_with_whatsapp=only_with_whatsapp
    )
    df = pd.DataFrame(leads)
    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    filename = f"leads_fnb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
