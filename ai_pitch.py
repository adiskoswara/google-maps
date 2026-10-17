import os
import json
import sys
import httpx

# In-memory or env-based API key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

def generate_smart_pitch_heuristic(
    lead: dict, 
    goal: str = "website", 
    linkedin_url: str = "", 
    sender_name: str = ""
) -> str:
    """
    Intelligent context-aware copywriter fallback.
    Crafts unique, highly tailored Indonesian pitch positioned as a freelance web developer
    fresh graduate in Informatics from Universitas Gunadarma working together with a partner,
    attaching LinkedIn for credibility, presenting valuable features detailed in a project plan
    to build trust rather than a direct sales pitch.
    """
    name = lead.get("name", "Bapak/Ibu")
    category = lead.get("category", "kuliner").lower()
    city = lead.get("city", "kota Anda")
    rating = lead.get("rating", 0)
    reviews_count = lead.get("reviews_count", 0)
    web_type = lead.get("website_type", "none")
    
    linkedin = (linkedin_url or "").strip() or "https://www.linkedin.com/in/username-anda"
    sender = (sender_name or "").strip()
    intro_name = f"Perkenalkan saya {sender}" if sender else "Perkenalkan saya"

    # Contextual compliments
    compliment = ""
    if reviews_count > 500:
        compliment = f"Saya perhatikan ulasan Google Maps {name} sudah mencapai {reviews_count:,} ulasan dengan reputasi yang sangat baik di {city}."
    elif rating >= 4.5:
        compliment = f"Saya melihat ulasan {name} di Google Maps sangat bagus ({rating} bintang) dan disukai banyak pelanggan di {city}."
    else:
        compliment = f"Saya menemukan profil {name} di Google Maps dan melihat konsep {category} ini sangat menarik di {city}."

    # Problem statement based on website type
    problem = ""
    if web_type == "social_only":
        problem = f"Saat ini calon pelanggan yang mencari lewat Google hanya diarahkan ke media sosial, belum ada website katalog menu resmi mandiri untuk pemesanan langsung tanpa potongan komisi aplikasi."
    else:
        problem = f"Saat ini {name} belum memiliki website profil resmi di Google Maps, padahal banyak calon pelanggan mencari info menu dan lokasi tempat makan lewat Google setiap harinya."

    if goal == "qr_menu":
        pitch = f"""Halo tim {name}, salam kenal! 👋

{intro_name}, freelance web developer fresh graduate jurusan Informatika dari Universitas Gunadarma.

{compliment}

{problem}

Projek ini saya kembangkan berdua bersama rekan partner saya. Untuk memberikan gambaran nyata dan membangun rasa percaya, kami telah merancang beberapa fitur praktis untuk operasional menu {name}, yang kami lampirkan secara terstruktur di dalam dokumen *project plan*.

Sebagai latar belakang profesional dan transparansi kredibilitas saya, Kakak dapat melihat profil LinkedIn saya di:
🔗 {linkedin}

Apakah boleh kami kirimkan draf *project plan* yang memuat rincian fitur-fitur tersebut secara gratis tanpa komitmen kak?

Jika berkenan, kami dengan senang hati mengirimkannya. Terima kasih banyak dan sukses selalu untuk {name}! 🙏"""
    else:
        pitch = f"""Halo kak, salam hangat untuk tim {name}! 👋

{intro_name}, freelance web developer fresh graduate jurusan Informatika dari Universitas Gunadarma.

{compliment}

{problem}

Projek website ini saya kembangkan berdua bersama rekan partner saya. Untuk memberikan gambaran yang jelas dan membangun rasa percaya, kami telah menyiapkan rancangan beberapa fitur yang sangat bermanfaat untuk {name}, yang kami lampirkan secara lengkap di dalam dokumen *project plan*.

Untuk melihat background pendidikan dan profesional saya agar saling percaya, Kakak bisa cek profil LinkedIn saya di:
🔗 {linkedin}

Apakah boleh kami kirimkan draf *project plan* yang memuat rincian fitur-fitur tersebut secara gratis tanpa komitmen kak?

Jika berkenan, kami bisa kirimkan ringkasannya. Terima kasih banyak dan sukses selalu untuk {name}! 🙏"""

    return pitch


def generate_ai_pitch(
    lead: dict, 
    api_key: str = "", 
    goal: str = "website", 
    linkedin_url: str = "", 
    sender_name: str = ""
) -> str:
    """
    Generates personalized pitch using Google Gemini Flash API if API key is provided,
    otherwise uses the Smart Heuristic Copywriter engine.
    Positioned as a freelance fresh graduate in Informatics from Universitas Gunadarma
    developing the website together with a partner, attaching LinkedIn for credibility,
    and building trust by presenting valuable features detailed in a project plan.
    """
    key = api_key or GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
    linkedin = (linkedin_url or "").strip() or "https://www.linkedin.com/in/username-anda"
    sender = (sender_name or "").strip()
    
    if not key:
        return generate_smart_pitch_heuristic(lead, goal, linkedin_url=linkedin, sender_name=sender)
        
    sender_intro = f"nama saya {sender}, " if sender else ""
    prompt = f"""
Anda adalah seorang freelance web developer di Indonesia ({sender_intro}fresh graduate jurusan Informatika dari Universitas Gunadarma).
Dalam mengerjakan projek website ini, Anda mengembangkannya berdua bersama partner/rekan developer Anda.
Karakter Anda: santun, rendah hati, tidak muluk-muluk (grounded), bersahabat, profesional, jujur, dan berorientasi pada membangun kepercayaan (trust) dengan pemilik bisnis.

Tuliskan 1 draf pesan WhatsApp penawaran singkat, sopan, natural, dan tidak terkesan spam (maksimal 3-4 paragraf pendek terstruktur rapi) yang ditujukan kepada pemilik/pengelola bisnis F&B berikut:

Data Bisnis dari Google Maps:
- Nama Bisnis: {lead.get('name')}
- Kategori: {lead.get('category')}
- Kota: {lead.get('city')}
- Alamat: {lead.get('address')}
- Rating: {lead.get('rating')} bintang
- Total Ulasan: {lead.get('reviews_count')} ulasan
- Status Website: {lead.get('website_type')} (Keterangan: {lead.get('website_status')})

Profil Pengirim:
- Posisi: Freelance Web Developer
- Kolaborasi: Projek dikembangkan berdua bersama rekan/partner
- Latar Belakang: Fresh Graduate jurusan Informatika dari Universitas Gunadarma
- Link LinkedIn Pengirim: {linkedin}

Tujuan Penawaran:
Membangun rasa percaya (trust) dengan menyampaikan bahwa Anda bersama partner telah merancang beberapa fitur yang bagus dan bermanfaat untuk kebutuhan {lead.get('name')}, yang seluruh rinciannya dilampirkan secara transparan di dalam dokumen project plan.

Aturan Penulisan Wajib:
1. Sapaan ramah dan sopan (contoh: 'Halo kak, salam hangat untuk tim {lead.get('name')}!').
2. Perkenalkan diri secara jujur bahwa Anda adalah freelance web developer fresh graduate Informatika dari Universitas Gunadarma, dan sampaikan bahwa website ini Anda kembangkan berdua bersama rekan/partner Anda.
3. Sebutkan kelebihan mereka dari data Google Maps (misal rating/ulasan positif) agar pesan terasa personal dan otentik.
4. JANGAN gunakan kata 'modern'. Hindari kesan hard-selling (seperti langsung menawarkan jasa pembuatan website). Sebagai gantinya, sampaikan dengan meyakinkan bahwa Anda dan partner telah menyiapkan rancangan beberapa fitur yang bagus/bermanfaat untuk {lead.get('name')}, yang nanti dilampirkan dan dijelaskan lengkap di dalam dokumen project plan agar memberikan gambaran jelas dan membangun rasa percaya.
5. Soroti secara halus kebutuhan website mandiri / katalog menu online yang belum mereka miliki.
6. Lampirkan link profil LinkedIn pengirim ({linkedin}) dengan sopan sebagai background profesional untuk membangun trust dan kredibilitas.
7. Call-to-Action (CTA): tawarkan untuk mengirimkan draf project plan yang memuat rincian fitur-fitur tersebut secara gratis tanpa komitmen (JANGAN tawarkan link preview demo).
8. Format rapi untuk WhatsApp (gunakan baris baru secukupnya, emoji secukupnya).
9. Hanya keluarkan teks pesan WhatsApp yang siap kirim, tanpa tanda kutip di awal/akhir atau pengantar lainnya.
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 450
        }
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return text
            else:
                print(f"Gemini API returned status {resp.status_code}: {resp.text}")
                return generate_smart_pitch_heuristic(lead, goal, linkedin_url=linkedin, sender_name=sender)
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return generate_smart_pitch_heuristic(lead, goal, linkedin_url=linkedin, sender_name=sender)

if __name__ == "__main__":
    sample_lead = {
        "name": "Historica Coffee & Kitchen",
        "category": "Kafe & Restoran",
        "city": "Surabaya",
        "rating": 4.4,
        "reviews_count": 2066,
        "website_type": "social_only",
        "website_status": "Hanya Medsos (Instagram)"
    }
    # Ensure stdout handles UTF-8 on Windows
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    print("--- Test Smart AI Pitch (Project Plan Features Persona) ---")
    print(generate_ai_pitch(sample_lead, linkedin_url="https://www.linkedin.com/in/freshgrad-gunadarma", sender_name="Dimas"))
