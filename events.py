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
            page.goto(EVENTS_PAGE_URL, wait_until="networkidle", timeout=60000)
            blocks = page.query_selector_all(".events")
            for block in blocks:
                title_el = block.query_selector(".event-title")
                date_el = block.query_selector(".dateStart")
                if not title_el: continue
                name = title_el.inner_text().strip()
                if name.upper() in ["HAPPENING NOW", "UPCOMING EVENTS", ""]: continue
                event = {"name": name, "date": date_el.inner_text().strip() if date_el else ""}
                if "LEFT" in event['date'].upper():
                    active.append(event)
                else:
                    upcoming.append(event)
        finally:
            browser.close()
    return active, upcoming

def create_discord_payload(active, upcoming):
    embeds = []

    # 1. ACTIVE EMBED (Green & Compact)
    if active:
        active_fields = []
        for e in active:
            url = get_tibiawiki_url(e['name'])
            # Using bold text but no headers to keep it small
            active_fields.append({
                "name": f"✅ {e['name']}",
                "value": f"[Wiki]({url}) • `{e['date'].lower()}`",
                "inline": True # Side-by-side to save space
            })
        
        embeds.append({
            "title": f"Active: {WORLD_NAME}",
            "color": 0x2ECC71,
            "fields": active_fields
        })

    # 2. UPCOMING EMBED (Blue & Compact)
    if upcoming:
        upcoming_fields = []
        for e in upcoming:
            url = get_tibiawiki_url(e['name'])
            # Cleaning up the timer text
            timer = e['date'].lower().replace("to start", "starts")
            upcoming_fields.append({
                "name": f"⏳ {e['name']}",
                "value": f"[Wiki]({url}) • `{timer}`",
                "inline": True # Side-by-side to save space
            })
        
        embeds.append({
            "title": f"Upcoming: {WORLD_NAME}",
            "color": 0x3498DB,
            "fields": upcoming_fields,
            "footer": {"text": f"Updated: {datetime.now().strftime('%H:%M')}"}
        })

    return {"embeds": embeds}

if __name__ == "__main__":
    if DISCORD_WEBHOOK_URL:
        act, upc = scrape_website_events()
        if act or upc:
            requests.post(DISCORD_WEBHOOK_URL, json=create_discord_payload(act, upc))
