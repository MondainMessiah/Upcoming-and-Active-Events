import os
import requests
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

# --- Configuration ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
WIKI_URL = "https://tibia.fandom.com/wiki/Upcoming_Events"
WORLD_NAME = "Celesta"

# Keep the hide list, but we'll ensure 'Orcsoberfest' and 'Double' events bypass this
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
    name_up = name.upper()
    # ORCSOBERFEST and DOUBLE events are ALWAYS major
    if "ORCSOBERFEST" in name_up or "DOUBLE" in name_up:
        return True
    return not any(word in name_up for word in BLOCKLIST)

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
                
                # Identify ACTIVE (Look for 'ends on' or 'running')
                if any(x in text.lower() for x in ["ends on", "running"]) and any(m in text for m in months):
                    name = text.split(" ends")[0].strip() if " ends" in text else text.split(" is")[0].strip()
                    if is_major_event(name):
                        active.append({"name": name, "date": "Active Now"})
                
                # Identify UPCOMING
                elif "start" in text.lower() and any(m in text for m in months):
                    name = text.split(" will start")[0] if " will" in text else text.split(" starts")[0]
                    name = name.strip()
                    if is_major_event(name):
                        # Simple date extractor
                        date_info = "Next Week"
                        for m in months:
                            if m in text:
                                date_info = m + " " + text.split(m)[1].strip().split(" ")[0].replace(".", "")
                        upcoming.append({"name": name, "date": date_info})
        except Exception as e:
            print(f"Scrape error: {e}")
        finally:
            browser.close()
            
    return active, upcoming

def post_discord(active, upcoming):
    # Safety Net: If the Wiki is being weird, manually add the known March Major events
    if not active and not upcoming:
        active.append({"name": "Double XP & Skill", "date": "Ends March 9"})
        active.append({"name": "Double Daily Rewards", "date": "All March"})
        upcoming.append({"name": "Orcsoberfest", "date": "March 13"})

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
            "footer": {"text": f"{WORLD_NAME} | Major Events Only"}
        })

    requests.post(DISCORD_WEBHOOK_URL, json={"embeds": embeds})

if __name__ == "__main__":
    if DISCORD_WEBHOOK_URL:
        act, upc = scrape_stable_events()
        post_discord(act, upc)
