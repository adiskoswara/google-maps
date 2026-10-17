"""
MapLeads F&B - Google Maps Intelligence & WhatsApp Lead Finder Launcher
"""
import socket
import webbrowser
import threading
import time
import uvicorn
import urllib.request
import json

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def find_available_port(start_port: int = 8000, max_attempts: int = 10) -> int:
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start_port

def is_mapleads_running(port: int = 8000) -> bool:
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/stats")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return "total" in data
    except Exception:
        return False

if __name__ == "__main__":
    target_port = 8000
    
    # Check if MapLeads server is already running on port 8000
    if is_mapleads_running(target_port):
        url = f"http://localhost:{target_port}"
        print("=" * 65)
        print("   MapLeads F&B - Google Maps Intelligence & WhatsApp Lead Finder")
        print("=" * 65)
        print(f"[!] Server MapLeads SUDAH AKTIF di latar belakang pada: {url}")
        print("[*] Membuka dashboard di browser Anda sekarang...")
        print("=" * 65)
        webbrowser.open(url)
        print("[v] Selesai. Anda dapat langsung menggunakan dashboard di browser.")
    else:
        # Check if port 8000 is taken by another app
        if is_port_in_use(target_port):
            chosen_port = find_available_port(target_port + 1)
            print(f"[i] Port {target_port} sedang dipakai, dialihkan ke port: {chosen_port}")
        else:
            chosen_port = target_port

        url = f"http://localhost:{chosen_port}"
        print("=" * 65)
        print("   MapLeads F&B - Google Maps Intelligence & WhatsApp Lead Finder")
        print("=" * 65)
        print(f"[*] Menjalankan server pada: {url}")
        print("[*] Dashboard web akan terbuka secara otomatis di browser Anda.")
        print("=" * 65)
        
        def open_browser():
            time.sleep(1.5)
            webbrowser.open(url)
            
        threading.Thread(target=open_browser, daemon=True).start()
        
        uvicorn.run("server:app", host="127.0.0.1", port=chosen_port, reload=False)
