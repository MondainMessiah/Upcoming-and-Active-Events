import os
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

# --- Configuration ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
EVENTS_PAGE_URL = "https://tibiadraptor.com/"
WORLD_NAME = "Celesta"

# --- Improved Wiki Search ---

def get_tibiawiki_url(event_name):
    base_url = "https://tibia.fandom.com/wiki/"
    search_term = event_name.upper()
    
    # Precise map based on your link
    name_map = {
        "DOUBLE DAILY": "Double_Daily_Reward_Events",
        "DOUBLE XP": "Double_XP_and_Double_Skill",
        "DOUBLE SKILL": "Double_XP_and_Double_Skill",
        "RAPID RESPAWN": "Rapid_Respawn_and_Enhanced_Creature_Yield",
        "DOUBLE LOOT": "Double_Loot_Event",
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

    return f"{base_url}{target_page}"

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
        active_desc = ""
        for e in active:
            url = get_tibiawiki_url(e['name'])
            # Creating a clean clickable header
            active_desc += f"### ✅ [{e['name'].upper()}]({url})\n"
            active_desc += f"┕ `⏳ Ends in: {e['date'].lower().replace('!', '')}`\n\n"
        
        embeds.append({
            "title": f"🛡️ ACTIVE ON {WORLD_NAME.upper()}",
            "description": active_desc,
            "color": 0x2ECC71,
            "thumbnail": {"url": "https://wiki.tibia.com/images/3/3a/Tibia_Logo.png"}
        })

    # UPCOMING EMBED
    if upcoming:
        upcoming_desc = ""
        for e in upcoming:
            url = get_tibiawiki_url(event_name=e['name'])
            upcoming_desc += f"### ⏳ [{e['name'].upper()}]({url})\n"
            upcoming_desc += f"┕ `🗓️ {e['date'].lower().replace('!', '').replace('to start', 'starts in')}`\n\n"
        
        embeds.append({
            "title": f"🗓️ UPCOMING FOR {WORLD_NAME.upper()}",
            "description": upcoming_desc,
            "color": 0x3498DB,
            "footer": {"text": f"Last Updated: {datetime.now().strftime('%H:%M')} | {WORLD_NAME}"}
        })

    # Adding a button/link at the bottom via "content" since webhooks can't do real buttons easily
    return {
        "content": f"🔗 **Full Schedule:** <{EVENTS_PAGE_URL}>",
        "embeds": embeds
    }

# --- Main ---

if __name__ == "__main__":
    if not DISCORD_WEBHOOK_URL:
        print("Missing Webhook URL")
    else:
        act, upc = scrape_website_events()
        if act or upc:
            payload = create_discord_payload(act, upc)
            requests.post(DISCORD_WEBHOOK_URL, json=payload)
            print("Successfully updated Celesta event board.")
