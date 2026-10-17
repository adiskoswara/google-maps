# MapLeads F&B Intelligence 🚀
### Sistem Deteksi Profil Google Maps & Ekstraksi WhatsApp Bisnis Kuliner Tanpa Website

Aplikasi otomatis untuk mencari, memindai, dan mengumpulkan data restoran, kafe, kedai kopi, dan bisnis kuliner (F&B) dari **Google Maps** yang **belum mempunyai website resmi**, serta mengekstraksi **nomor WhatsApp aktif** untuk prospek penawaran jasa pembuatan website, menu online, atau optimasi digital.

---

## 🌟 Fitur Utama

1. **Deteksi Google Maps Otomatis (Tanpa Perlu API Key Berbayar)**
   - Menggunakan browser automation Chromium / Microsoft Edge terintegrasi.
   - Mendukung kata kunci fleksibel (contoh: *cafe, coffee shop, restoran, bakery, rumah makan, bistro*) dan target kota (contoh: *Jakarta Selatan, Surabaya, Bandung, Bali, Yogyakarta*).
   - Pengaturan target jumlah tempat (10, 20, 40, 60, 100+).

2. **Klasifikasi Cerdas Status Website**
   - 🔴 **Belum Ada Website**: Listing Google Maps sama sekali tidak mencantumkan website. Target paling potensial!
   - 🟡 **Hanya Medsos / Linktree**: Memiliki link Instagram, Linktree, Facebook, atau BioLink, tetapi belum memiliki website/portal resmi sendiri.
   - 🟢 **Sudah Punya Website**: Memiliki domain website resmi.

3. **Ekstraksi & Normalisasi Nomor WhatsApp Indonesia**
   - Mendeteksi nomor seluler Indonesia (`08xx` / `+62 8xx`) dan mengubahnya otomatis ke format standar internasional (`628xxx`).
   - Membedakan otomatis antara nomor HP seluler (WhatsApp Ready) dan telepon kantor/kabel (landline).

4. **✨ Fitur Baru: AI WhatsApp Pitch Studio (Didukung Google Gemini)**
   - Tersedia tombol **✨ AI Draft** di setiap profil bisnis untuk meracik draf pesan penawaran yang unik & hiper-personal.
   - AI membaca jumlah ulasan, reputasi, kategori, dan ketiadaan website dari kafe tersebut sehingga pesan tidak terkesan seperti spam atau template kaku.
   - Pilihan variasi tawaran: *Website Profil & Online Menu* atau *QR E-Menu Tanpa Potongan Fee*.
   - Mendukung integrasi API Key **Google Gemini (Gratis dari Google AI Studio)**, atau menggunakan Smart Contextual AI Engine bawaan jika tanpa API Key.

5. **1-Click WhatsApp Outreach dengan Template Kustom**
   - Tombol **Chat WA** langsung membuka WhatsApp Web / Aplikasi WhatsApp dengan pesan penawaran otomatis yang sudah disesuaikan nama tempat, kategori bisnis, dan kotanya.
   - Tersedia generator template pesan siap pakai (Penawaran Website & Menu Online, QR Digital Menu, Audit SEO Google Maps).

5. **Live Radar & Real-Time Stream**
   - Tampilan progress bar interaktif, live ticker, dan log terminal Server-Sent Events (SSE) saat proses pemindaian berjalan.

6. **Ekspor Data Lengkap**
   - **Download Excel (.xlsx)**: Spreadsheet terformat rapi dengan link WhatsApp yang dapat langsung diklik.
   - **Download CSV**: Untuk integrasi ke software CRM atau spreadsheet lain.
   - **Salin Semua No. WhatsApp**: 1 tombol untuk copy semua nomor WhatsApp prospek ke clipboard.

---

## 📁 Struktur Direktori

```
c:/google-maps/
├── database.py              # Penyimpanan SQLite & kueri deduplikasi
├── scraper.py               # Mesin ekstraksi Google Maps (Playwright)
├── server.py                # Backend REST API & Server-Sent Events (FastAPI)
├── run.py                   # Script launcher 1-klik buka server & browser
├── requirements.txt         # Daftar pustaka Python
├── static/
│   ├── index.html           # Antarmuka Dashboard (Glassmorphism Dark Theme)
│   ├── style.css            # Styling visual modern & responsif
│   └── app.js               # Logika real-time SSE, filter, & WhatsApp launcher
└── leads.db                 # Database lokal hasil pencarian
```

---

## 🚀 Cara Menjalankan Aplikasi

Aplikasi saat ini telah aktif di:
👉 **`http://127.0.0.1:8000`**

Jika Anda ingin menjalankannya kembali kapan saja, cukup jalankan perintah berikut di terminal:

```powershell
cd c:\google-maps
python run.py
```
*Browser Anda akan terbuka secara otomatis menampilkan dashboard MapLeads.*
