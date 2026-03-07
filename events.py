import os
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

# --- Configuration ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
# Reliable Source: TibiaWiki Upcoming Events
EVENTS_PAGE_URL = "https://tibia.fandom.com/wiki/Upcoming_Events"
WORLD_NAME = "Celesta"

def scrape_tibiawiki_events():
    active, upcoming = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            print(f"🔍 Visiting {EVENTS_PAGE_URL}...")
            page.goto(EVENTS_PAGE_URL, wait_until="domcontentloaded", timeout=45000)
            
            # TibiaWiki uses a specific list structure for upcoming events
            # We target the 'Upcoming Events' section specifically
            event_items = page.query_selector_all("div.mw-parser-output > ul > li")
            
            for li in event_items:
                text = li.inner_text().strip()
                # Skip navigation or category links that aren't actual events
                if "start in" not in text.lower(): continue
                
                # Format: "Event Name will start in X days on Month Day."
                # We split to get the Name and the Date
                parts = text.split(" will start in ")
                name = parts[0].strip()
                date_info = parts[1].strip() if len(parts) > 1 else "Check Wiki"
                
                url_element = li.query_selector("a")
                url = "https://tibia.fandom.com" + url_element.get_attribute("href") if url_element else f"https://tibia.fandom.com/wiki/{name.replace(' ', '_')}"
                
                event = {"name": name, "date": date_info, "url": url}
                upcoming.append(event)
                
            # Note: Active events on Wiki are usually in a separate "Active" template
            # For now, we focus on Upcoming since the 'Current' logic varies by month
        except Exception as e:
            print(f"❌ Wiki Scrape Error: {e}")
        finally:
            browser.close()
    return active, upcoming

def create_discord_payload(active, upcoming):
    embeds = []
    if upcoming:
        desc = ""
        # Limit to the next 5 events to keep it small
        for e in upcoming[:5]:
            desc += f"⏳ **[{e['name'].upper()}]({e['url']})**\n`┕ {e['date'].lower()}`\n"
        
        embeds.append({
            "title": "UPCOMING EVENTS",
            "color": 0x3498DB,
            "description": desc.strip(),
            "footer": {"text": f"Source: TibiaWiki | World: {WORLD_NAME} | {datetime.now().strftime('%H:%M')}"}
        })
    return {"embeds": embeds}

if __name__ == "__main__":
    if DISCORD_WEBHOOK_URL:
        act, upc = scrape_tibiawiki_events()
        if upc:
            requests.post(DISCORD_WEBHOOK_URL, json=create_discord_payload(act, upc))
            print("Successfully posted TibiaWiki data.")
        else:
            print("📭 No data found on TibiaWiki.")
