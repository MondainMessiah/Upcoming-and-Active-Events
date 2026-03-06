import os
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

# --- Configuration ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
EVENTS_PAGE_URL = "https://tibiadraptor.com/"
WORLD_NAME = "Celesta"

# --- Fixed Wiki Search ---

def get_tibiawiki_url(event_name):
    """Reliable URL generator for TibiaWiki."""
    base_url = "https://tibia.fandom.com/wiki/"
    search_term = event_name.upper()
    
    # Precise map for events shown in your screenshots
    name_map = {
        "DOUBLE DAILY": "Daily_Reward_System",
        "DOUBLE XP": "Double_XP_and_Double_Skill",
        "ORCSOBERFEST": "Orcsoberfest",
        "COLOURS OF MAGIC": "The_Colours_of_Magic",
        "CHYLLFROEST": "Chyllfroest",
        "UNDEAD JESTERS": "Undead_Jesters"
    }

    target_page = None
    for keyword, page in name_map.items():
        if keyword in search_term:
            target_page = page
            break
    
    if not target_page:
        target_page = event_name.strip().replace(" ", "_").title()

    url = f"{base_url}{target_page}"
    
    # We must use a User-Agent or Fandom will block the request
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        resp = requests.get(url, timeout=5, headers=headers)
        if resp.status_code == 200:
            return url
    except:
        pass
    return None

# --- Data Fetching ---

def scrape_website_events():
    active, upcoming = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            page.goto(EVENTS_PAGE_URL, wait_until="networkidle", timeout=60000)
            blocks = page.query_selector_all(".events")
            for block in blocks:
                title_el = block.query_selector(".event-title")
                date_el = block.query_selector(".dateStart")
                if not title_el: continue
                
                name = title_el.inner_text().strip()
                if name.upper() in ["HAPPENING NOW", "UPCOMING EVENTS", ""]: continue
                
                date_text = date_el.inner_text().strip() if date_el else ""
                event = {"name": name, "date": date_text}

                if "LEFT" in date_text.upper():
                    if event not in active: active.append(event)
                else:
                    if event not in upcoming: upcoming.append(event)
        finally:
            browser.close()
    return active, upcoming

# --- Discord Formatting ---

def create_discord_payload(active, upcoming):
    embeds = []

    # ACTIVE EMBED
    if active:
        active_fields = []
        for e in active:
            url = get_tibiawiki_url(e['name'])
            # The [Link](URL) format is vital here
            val = f"🔗 [Wiki Link]({url})" if url else "No Wiki Link"
            time_val = f"\n`⏳ {e['date'].lower().replace('!', '')}`"
            active_fields.append({
                "name": f"✅ {e['name'].upper()}",
                "value": val + time_val,
                "inline": False
            })
        
        embeds.append({
            "title": f"⚔️ ACTIVE NOW: {WORLD_NAME}",
            "color": 0x2ECC71,
            "fields": active_fields,
            "thumbnail": {"url": "https://wiki.tibia.com/images/3/3a/Tibia_Logo.png"}
        })

    # UPCOMING EMBED
    if upcoming:
        upcoming_fields = []
        for e in upcoming:
            url = get_tibiawiki_url(e['name'])
            val = f"🔗 [Wiki Link]({url})" if url else "No Wiki Link"
            time_val = f"\n`⏳ {e['date'].lower().replace('!', '').replace('to start', 'starts in')}`"
            upcoming_fields.append({
                "name": f"🗓️ {e['name'].upper()}",
                "value": val + time_val,
                "inline": False
            })
        
        embeds.append({
            "title": f"⏳ UPCOMING: {WORLD_NAME}",
            "color": 0x3498DB,
            "fields": upcoming_fields,
            "footer": {"text": f"Last Updated: {datetime.now().strftime('%H:%M')} | {WORLD_NAME}"}
        })

    return {"embeds": embeds}

# --- Main ---

if __name__ == "__main__":
    if not DISCORD_WEBHOOK_URL:
        print("Missing Webhook URL")
    else:
        act, upc = scrape_website_events()
        if act or upc:
            payload = create_discord_payload(act, upc)
            requests.post(DISCORD_WEBHOOK_URL, json=payload)
            print("Done!")
