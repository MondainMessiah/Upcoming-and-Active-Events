import os
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

# --- Configuration ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
EVENTS_PAGE_URL = "https://tibiadraptor.com/"
WORLD_NAME = "Celesta"
# Add your Role ID here (e.g., "<@&123456789>") if you want a ping
ROLE_PING = "" 

# --- Improved Wiki Search ---

def get_tibiawiki_url(event_name):
    base_url = "https://tibia.fandom.com/wiki/"
    search_term = event_name.upper()
    
    name_map = {
        "DOUBLE XP": "Double_XP_and_Double_Skill",
        "DOUBLE SKILL": "Double_XP_and_Double_Skill",
        "RAPID RESPAWN": "Rapid_Respawn_and_Enhanced_Creature_Yield",
        "DOUBLE LOOT": "Double_Loot_Event",
        "DOUBLE DAILY": "Daily_Reward_System",
        "BEWDITCHED": "Bewitched",
        "PIE": "Annual_Autumn_Vintage"
    }

    target_page = None
    for keyword, page in name_map.items():
        if keyword in search_term:
            target_page = page
            break
    
    if not target_page:
        target_page = event_name.strip().replace(" ", "_").title()

    url = f"{base_url}{target_page}"
    try:
        resp = requests.head(url, allow_redirects=True, timeout=3, headers={'User-Agent': 'Mozilla/5.0'})
        return url if resp.status_code == 200 else None
    except:
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
                
                date_text = date_el.inner_text().strip() if date_el else "Dates TBD"
                event = {"name": name, "date": date_text}

                if "LEFT" in date_text.upper():
                    if event not in active: active.append(event)
                else:
                    if event not in upcoming: upcoming.append(event)
        finally:
            browser.close()
    return active, upcoming

# --- Discord Formatting ---

def create_event_embeds(active, upcoming):
    embeds = []

    # 1. ACTIVE EVENTS EMBED (Green)
    if active:
        active_text = ""
        for e in active:
            url = get_tibiawiki_url(e['name'])
            title = f"**[{e['name'].upper()}]({url})**" if url else f"**{e['name'].upper()}**"
            timer = e['date'].lower().replace("!", "")
            active_text += f"✅ {title}\n`⏳ Ends in: {timer}`\n\n"
        
        embeds.append({
            "title": f"⚔️ ACTIVE NOW ON {WORLD_NAME.upper()}",
            "description": active_text.strip(),
            "color": 0x2ECC71, # Emerald Green
            "thumbnail": {"url": "https://wiki.tibia.com/images/3/3a/Tibia_Logo.png"}
        })

    # 2. UPCOMING EVENTS EMBED (Blue/Gold)
    if upcoming:
        upcoming_text = ""
        for e in upcoming:
            url = get_tibiawiki_url(e['name'])
            title = f"**[{e['name'].upper()}]({url})**" if url else f"**{e['name'].upper()}**"
            timer = e['date'].lower().replace("!", "").replace("to start", "starts in")
            upcoming_text += f"🗓️ {title}\n`⏳ {timer}`\n\n"
        
        embeds.append({
            "title": f"⏳ UPCOMING FOR {WORLD_NAME.upper()}",
            "description": upcoming_text.strip(),
            "color": 0x3498DB, # Bright Blue
            "footer": {"text": f"Last Updated: {datetime.now().strftime('%H:%M')} | Celesta", "icon_url": "https://wiki.tibia.com/images/1/1a/Globe.gif"}
        })

    return embeds

# --- Execution ---

if __name__ == "__main__":
    if not DISCORD_WEBHOOK_URL:
        print("Missing Webhook URL")
    else:
        act, upc = scrape_website_events()
        
        if act or upc:
            event_embeds = create_event_embeds(act, upc)
            payload = {
                "content": ROLE_PING if act else "", # Pings only if there are active events
                "embeds": event_embeds
            }
            requests.post(DISCORD_WEBHOOK_URL, json=payload)
            print("Posted separate embeds to Discord.")
