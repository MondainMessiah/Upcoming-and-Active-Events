import os
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

# --- Configuration ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
# Backup Source: TibiaPal
EVENTS_PAGE_URL = "https://tibiapal.com/events" 
WORLD_NAME = "Celesta"

def get_tibiawiki_url(event_name):
    base_url = "https://tibia.fandom.com/wiki/"
    name = event_name.upper()
    name_map = {
        "DOUBLE DAILY": "Double_Daily_Reward_Events",
        "DOUBLE XP": "Double_XP_and_Double_Skill",
        "DOUBLE SKILL": "Double_XP_and_Double_Skill",
        "RAPID RESPAWN": "Rapid_Respawn_and_Enhanced_Creature_Yield",
        "DOUBLE LOOT": "Double_Loot_Event"
    }
    target = next((v for k, v in name_map.items() if k in name), event_name.replace(" ", "_").title())
    return f"{base_url}{target}"

def scrape_tibiapal_events():
    active, upcoming = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            print(f"🔍 Visiting {EVENTS_PAGE_URL}...")
            # We use a 45s timeout to be safe
            page.goto(EVENTS_PAGE_URL, wait_until="networkidle", timeout=45000)
            
            # TibiaPal typically uses distinct sections or cards for events
            # We target common containers like 'card' or list items
            event_elements = page.query_selector_all(".event-card, .event-item, tr") 
            
            for el in event_elements:
                text = el.inner_text().strip()
                if not text or "Boosted" in text: continue # Skip unrelated info
                
                # Split logic: Name is usually the first line, date/timer is second
                lines = text.split('\n')
                if len(lines) >= 2:
                    name = lines[0].strip()
                    date_info = lines[1].strip()
                    
                    event = {"name": name, "date": date_info}
                    
                    # Logic to sort based on current status
                    if "active" in text.lower() or "ends" in text.lower() or "left" in text.lower():
                        active.append(event)
                    else:
                        upcoming.append(event)
        except Exception as e:
            print(f"❌ Backup Error: {e}")
        finally:
            browser.close()
    return active, upcoming

def create_discord_payload(active, upcoming):
    embeds = []
    
    # Process Active
    if active:
        desc = ""
        for e in active:
            url = get_tibiawiki_url(e['name'])
            desc += f"✅ **[{e['name'].upper()}]({url})**\n`┕ {e['date'].lower()}`\n"
        embeds.append({"title": "ACTIVE EVENTS", "color": 0x2ECC71, "description": desc.strip()})

    # Process Upcoming
    if upcoming:
        desc = ""
        for e in upcoming:
            url = get_tibiawiki_url(e['name'])
            desc += f"⏳ **[{e['name'].upper()}]({url})**\n`┕ {e['date'].lower()}`\n"
        embeds.append({
            "title": "UPCOMING EVENTS", 
            "color": 0x3498DB, 
            "description": desc.strip(),
            "footer": {"text": f"Source: TibiaPal | World: {WORLD_NAME} | {datetime.now().strftime('%H:%M')}"}
        })
    return {"embeds": embeds}

if __name__ == "__main__":
    if DISCORD_WEBHOOK_URL:
        act, upc = scrape_tibiapal_events()
        if act or upc:
            requests.post(DISCORD_WEBHOOK_URL, json=create_discord_payload(act, upc))
            print("Successfully posted TibiaPal data.")
        else:
            print("📭 No data found on TibiaPal.")
