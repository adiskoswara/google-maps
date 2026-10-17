import time
import re
import urllib.parse
from playwright.sync_api import sync_playwright

SOCIAL_DOMAINS = [
    'instagram.com', 'linktr.ee', 'facebook.com', 'fb.com', 'tiktok.com',
    'twitter.com', 'x.com', 'bio.link', 'beacons.ai', 'bit.ly', 'wa.me',
    'whatsapp.com', 'g.page', 'business.site', 'maps.google.com', 'youtube.com'
]

def normalize_indonesian_phone(raw_phone: str):
    """
    Normalizes Indonesian phone numbers:
    0812-3456-7890 -> 6281234567890
    +62 812 3456 7890 -> 6281234567890
    (021) 123456 -> 6221123456 (landline)
    """
    if not raw_phone:
        return "", False, ""
    
    # Strip everything except digits and '+'
    cleaned = re.sub(r'[^\d+]', '', raw_phone)
    if cleaned.startswith('+'):
        cleaned = cleaned[1:]
        
    if cleaned.startswith('08'):
        normalized = '62' + cleaned[1:]
    elif cleaned.startswith('8'):
        normalized = '62' + cleaned
    elif cleaned.startswith('62'):
        normalized = cleaned
    elif cleaned.startswith('0'):
        normalized = '62' + cleaned[1:]
    else:
        normalized = cleaned

    # Indonesian mobile numbers start with 628 and have 10-15 digits
    is_mobile = normalized.startswith('628') and 10 <= len(normalized) <= 15
    
    wa_link = f"https://wa.me/{normalized}" if is_mobile else ""
    return normalized, is_mobile, wa_link

def classify_website(url: str):
    """
    Classifies website into:
    - 'none': No website
    - 'social_only': Uses only Instagram, Linktree, Facebook, etc.
    - 'website': Genuine independent business website
    """
    if not url or url.strip() == "":
        return False, "none", "Belum Ada Website"
    
    clean_url = url.lower()
    for social in SOCIAL_DOMAINS:
        if social in clean_url:
            return False, "social_only", f"Hanya Medsos ({social})"
            
    return True, "website", "Sudah Ada Website"

class GoogleMapsScanner:
    def __init__(self, on_event=None):
        self.on_event = on_event
        self.is_running = True

    def stop(self):
        self.is_running = False

    def emit(self, event_type: str, data: dict):
        if self.on_event:
            self.on_event(event_type, data)

    def scan(self, keyword="cafe", city="Surabaya", max_results=20, filter_no_website_only=False):
        """
        Scrapes Google Maps for F&B businesses:
        1. Collects places from Google Maps search feed with auto-scrolling
        2. Inspects each place profile directly to extract Phone/WhatsApp and Website status
        """
        search_query = f"{keyword} di {city}" if city else keyword
        self.emit("log", {"message": f"Memulai pencarian Google Maps: '{search_query}' (Target: {max_results} tempat)..."})
        
        collected_leads = []
        
        with sync_playwright() as p:
            # Launch MS Edge (or fallback to Chromium)
            try:
                browser = p.chromium.launch(channel="msedge", headless=True)
            except Exception:
                try:
                    browser = p.chromium.launch(channel="chrome", headless=True)
                except Exception:
                    browser = p.chromium.launch(headless=True)

            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="id-ID"
            )
            
            search_page = context.new_page()
            maps_url = f"https://www.google.com/maps/search/{urllib.parse.quote_plus(search_query)}"
            self.emit("log", {"message": "Membuka Google Maps..."})
            
            try:
                search_page.goto(maps_url, wait_until="commit", timeout=30000)
                search_page.wait_for_selector('a.hfpxzc, div[role="feed"]', timeout=25000)
            except Exception as e:
                self.emit("error", {"message": f"Gagal memuat Google Maps: {str(e)}"})
                browser.close()
                return collected_leads

            search_page.wait_for_timeout(2000)
            self.emit("log", {"message": "Google Maps siap. Mengumpulkan daftar tempat F&B..."})

            # Phase 1: Collect place URLs from feed
            places_to_visit = []
            seen_urls = set()
            scroll_attempts = 0
            max_scroll_attempts = 35

            while self.is_running and len(places_to_visit) < (max_results * 2) and scroll_attempts < max_scroll_attempts:
                cards = search_page.locator('a.hfpxzc')
                count = cards.count()
                
                for i in range(count):
                    card = cards.nth(i)
                    href = card.get_attribute("href") or ""
                    name = card.get_attribute("aria-label") or "Tanpa Nama"
                    
                    if href and href not in seen_urls:
                        seen_urls.add(href)
                        places_to_visit.append({"name": name, "url": href})
                        
                    if len(places_to_visit) >= (max_results * 2):
                        break

                scroll_attempts += 1
                try:
                    feed = search_page.locator('div[role="feed"]')
                    if feed.count() > 0:
                        feed.first.evaluate("el => el.scrollBy(0, 1000)")
                    search_page.wait_for_timeout(1500)
                except Exception:
                    break

            self.emit("log", {"message": f"Ditemukan {len(places_to_visit)} kandidat bisnis. Memulai ekstraksi profil & WhatsApp..."})

            # Phase 2: Open dedicated detail page to extract Phone, Website, and Address
            detail_page = context.new_page()
            
            for idx, item in enumerate(places_to_visit):
                if not self.is_running or len(collected_leads) >= max_results:
                    break
                    
                name = item["name"]
                url = item["url"]
                
                progress_pct = int(((idx + 1) / min(len(places_to_visit), max_results)) * 100)
                self.emit("status", {
                    "message": f"Menganalisis ({len(collected_leads)+1}/{max_results}): {name}",
                    "progress": min(progress_pct, 99)
                })

                try:
                    detail_page.goto(url, wait_until="commit", timeout=25000)
                    detail_page.wait_for_selector('h1', timeout=15000)
                    detail_page.wait_for_timeout(1500)
                except Exception:
                    continue

                # Phone extraction
                phone_el = detail_page.locator('button[data-item-id*="phone:tel:"]')
                raw_phone = ""
                if phone_el.count() > 0:
                    raw_id = phone_el.first.get_attribute("data-item-id") or ""
                    raw_phone = raw_id.replace("phone:tel:", "").strip()
                    if not raw_phone:
                        raw_phone = phone_el.first.inner_text().strip()

                wa_num, is_mobile, wa_link = normalize_indonesian_phone(raw_phone)

                # Website extraction
                website_el = detail_page.locator('a[data-item-id="authority"]')
                website_url = ""
                if website_el.count() > 0:
                    website_url = website_el.first.get_attribute("href") or ""

                has_web, web_type, web_status_label = classify_website(website_url)

                # Address extraction
                address_el = detail_page.locator('button[data-item-id="address"]')
                address = ""
                if address_el.count() > 0:
                    aria = address_el.first.get_attribute("aria-label") or ""
                    address = aria.replace("Alamat:", "").replace("Address:", "").strip()

                # Rating & reviews
                rating_val = 0.0
                reviews_val = 0
                try:
                    rating_el = detail_page.locator('div[role="main"] span[aria-hidden="true"]').first
                    if rating_el.count() > 0:
                        rating_txt = rating_el.inner_text().replace(',', '.').strip()
                        if re.match(r'^\d+(\.\d+)?$', rating_txt):
                            rating_val = float(rating_txt)
                except Exception:
                    pass

                try:
                    review_el = detail_page.locator('div[role="main"] span[aria-label*="ulasan"], div[role="main"] span[aria-label*="reviews"]')
                    if review_el.count() > 0:
                        rev_aria = review_el.first.get_attribute("aria-label") or ""
                        rev_digits = re.findall(r'\d+', rev_aria.replace('.', '').replace(',', ''))
                        if rev_digits:
                            reviews_val = int(rev_digits[0])
                except Exception:
                    pass

                # Category extraction
                category = "F&B"
                try:
                    cat_el = detail_page.locator('button[jsaction*="category"]')
                    if cat_el.count() > 0:
                        category = cat_el.first.inner_text().strip()
                except Exception:
                    pass

                lead_item = {
                    "name": name,
                    "category": category,
                    "address": address,
                    "city": city,
                    "phone_raw": raw_phone,
                    "whatsapp_number": wa_num,
                    "is_mobile": is_mobile,
                    "whatsapp_link": wa_link,
                    "has_website": has_web,
                    "website_url": website_url,
                    "website_type": web_type,
                    "website_status": web_status_label,
                    "rating": rating_val,
                    "reviews_count": reviews_val,
                    "maps_url": url,
                    "is_prospect": (web_type in ['none', 'social_only'])
                }

                # Filter condition: if user only wants leads without official websites
                if filter_no_website_only and has_web:
                    self.emit("log", {"message": f"[Dilewati] {name} (Sudah memiliki website)"})
                    continue

                collected_leads.append(lead_item)
                self.emit("lead_found", lead_item)
                
                wa_str = f"WA: {wa_num}" if is_mobile else (f"Tel: {raw_phone}" if raw_phone else "Belum ada no telp")
                self.emit("log", {
                    "message": f"[{web_status_label}] {name} | {wa_str}"
                })

            detail_page.close()
            search_page.close()
            browser.close()
            
        self.emit("completed", {
            "total_found": len(collected_leads),
            "no_website_count": sum(1 for x in collected_leads if x['website_type'] in ['none', 'social_only']),
            "with_wa_count": sum(1 for x in collected_leads if x['is_mobile'])
        })
        return collected_leads

if __name__ == "__main__":
    def print_event(event_type, data):
        msg = data.get('message', '') if isinstance(data, dict) else str(data)
        safe_msg = msg.encode('ascii', errors='replace').decode('ascii')
        print(f"[{event_type.upper()}] {safe_msg}")
    
    scanner = GoogleMapsScanner(on_event=print_event)
    scanner.scan(keyword="cafe", city="Surabaya", max_results=3)
