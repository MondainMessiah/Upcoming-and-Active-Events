import os
import requests
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

# --- Configuration ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
WIKI_URL = "https://tibia.fandom.com/wiki/Upcoming_Events"
WORLD_NAME = "Celesta"

# Events containing these words will be hidden
BLOCKLIST = [
    "GRIMVALE", "WAR AGAINST THE CURSE", "THAWING", "NOMADS", 
    "BANK ROBBERY", "OVERWHELMED", "COLOURS OF MAGIC", "FLOWER",
    "POACHERS", "RIVER", "HIVE", "DEEPLINGS"
]

def get_dynamic_months():
    now = datetime.now()
    next_mo = now.replace(day=28) + timedelta(days=4)
    return [now.strftime("%B"), next_mo.strftime("%B")]

def is_major_event(name):
    """Returns False if the event name is in the blocklist."""
    return not any(word in name.upper() for word in BLOCKLIST)

def scrape_stable_events():
    active, upcoming = [], []
    months = get_dynamic_months()
    
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(WIKI_URL, wait_until="domcontentloaded", timeout=45000)
            items = page.query_selector_all("div.mw-parser-output > ul > li")
            
            for li in items:
                text = li.inner_text()
                
                # Identify ACTIVE events
                if "ends on" in text.lower() and any(m in text for m in months):
                    name = text.split(" ends on")[0].strip()
                    if is_major_event(name):
                        date_info = "Ends " + text.split("on ")[1].replace(".", "")
                        active.append({"name": name, "date": date_info})
                
                # Identify UPCOMING events
                elif "start" in text.lower() and any(m in text for m in months):
                    name = text.split(" will start")[0] if " will" in text else text.split(" starts")[0]
                    name = name.strip()
                    if is_major_event(name):
                        date_part = "Found in Wiki"
                        for m in months:
                            if m in text:
                                # Extract just the date (e.g. March 15)
                                date_part = m + " " + text.split(m)[1].strip().split(" ")[0].replace(".", "")
                        upcoming.append({"name": name, "date": date_part})
        except Exception as e:
            print(f"Scrape error: {e}")
        finally:
            browser.close()
            
    return active, upcoming

def post_discord(active, upcoming):
    if not active and not upcoming:
        print("No major events found.")
        return

    embeds = []
    
    if active:
        active_desc = "\n".join([f"🚀 **[{a['name'].upper()}](https://tibia.fandom.com/wiki/{a['name'].replace(' ', '_')})**\n`┕ {a['date']}`" for a in active])
        embeds.append({"title": "ACTIVE MAJOR EVENTS", "color": 0x2ECC71, "description": active_desc})

    if upcoming:
        up_desc = "\n".join([f"⏳ **[{u['name'].upper()}](https://tibia.fandom.com/wiki/{u['name'].replace(' ', '_')})**\n`┕ {u['date']}`" for u in upcoming])
        embeds.append({
            "title": "UPCOMING MAJOR EVENTS", 
            "color": 0x3498DB, 
            "description": up_desc,
            "footer": {"text": f"{WORLD_NAME} | Filters: Major Events Only"}
        })

    requests.post(DISCORD_WEBHOOK_URL, json={"embeds": embeds})

if __name__ == "__main__":
    if DISCORD_WEBHOOK_URL:
        act, upc = scrape_stable_events()
        post_discord(act, upc)
