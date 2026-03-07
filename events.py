import os
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

# --- Configuration ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
EVENTS_PAGE_URL = "https://tibiadraptor.com/"
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

def scrape_website_events():
    active, upcoming = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            print(f"🔍 Visiting {EVENTS_PAGE_URL}...")
            page.goto(EVENTS_PAGE_URL, wait_until="networkidle", timeout=60000)
            
            blocks = page.query_selector_all(".events")
            print(f"📊 Found {len(blocks)} potential event blocks.")
            
            for block in blocks:
                title_el = block.query_selector(".event-title")
                date_el = block.query_selector(".dateStart")
                if not title_el: continue
                
                name = title_el.inner_text().strip()
                if name.upper() in ["HAPPENING NOW", "UPCOMING EVENTS", ""]: continue
                
                event = {"name": name, "date": date_el.inner_text().strip() if date_el else "No Date"}
                print(f"📍 Found Event: {name} ({event['date']})")
                
                if "LEFT" in event['date'].upper():
                    active.append(event)
                else:
                    upcoming.append(event)
        except Exception as e:
            print(f"❌ Scraping error: {e}")
        finally:
            browser.close()
    return active, upcoming

def create_discord_payload(active, upcoming):
    embeds = []
    if active:
        active_list = "\n".join([f"✅ **[{e['name'].upper()}]({get_tibiawiki_url(e['name'])})**\n`┕ {e['date'].lower()}`" for e in active])
        embeds.append({"title": "ACTIVE EVENTS", "color": 0x2ECC71, "description": active_list})

    if upcoming:
        upcoming_list = "\n".join([f"⏳ **[{e['name'].upper()}]({get_tibiawiki_url(e['name'])})**\n`┕ {e['date'].lower().replace('to start', 'starts')}`" for e in upcoming])
        embeds.append({
            "title": "UPCOMING EVENTS", 
            "color": 0x3498DB, 
            "description": upcoming_list,
            "footer": {"text": f"World: {WORLD_NAME} | Updated: {datetime.now().strftime('%H:%M')}"}
        })
    return {"embeds": embeds}

if __name__ == "__main__":
    if not DISCORD_WEBHOOK_URL:
        print("❌ Webhook URL is missing!")
    else:
        act, upc = scrape_website_events()
        if not act and not upc:
            print("📭 The website is currently empty. Nothing to post.")
        else:
            payload = create_discord_payload(act, upc)
            resp = requests.post(DISCORD_WEBHOOK_URL, json=payload)
            print(f"🚀 Discord response: {resp.status_code}")
