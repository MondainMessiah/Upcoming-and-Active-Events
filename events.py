import os
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

# --- Configuration ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
WIKI_EVENTS_URL = "https://tibia.fandom.com/wiki/Upcoming_Events"
WORLD_NAME = "Celesta"

def scrape_dynamic_events():
    active, upcoming = [], []
    
    # Static logic for March-long events
    active.append({"name": "Double Daily Rewards", "date": "Until March 31"})

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(WIKI_EVENTS_URL, wait_until="domcontentloaded", timeout=45000)
            items = page.query_selector_all("div.mw-parser-output > ul > li")
            
            for li in items:
                text = li.inner_text()
                # Check for the big XP weekend ending soon
                if "Double XP" in text and "March 9" in text:
                    active.append({"name": "Double XP & Skill", "date": "Ends March 9!"})
                
                # Scrape upcoming specifically for the next 10 days
                elif "March" in text and "start in" in text:
                    name = text.split(" will start")[0]
                    date = "March " + text.split("on March ")[1].replace(".", "")
                    upcoming.append({"name": name, "date": date})
        except:
            pass
        finally:
            browser.close()
    return active, upcoming

def post_discord(active, upcoming):
    embeds = []
    
    if active:
        desc = "\n".join([f"✅ **[{a['name'].upper()}](https://tibia.fandom.com/wiki/{a['name'].replace(' ', '_')})**\n`┕ {a['date']}`" for a in active])
        embeds.append({"title": "ACTIVE EVENTS", "color": 0x2ECC71, "description": desc})

    if upcoming:
        # Show only the next 3 events to keep the post small
        desc = "\n".join([f"⏳ **[{u['name'].upper()}](https://tibia.fandom.com/wiki/{u['name'].replace(' ', '_')})**\n`┕ {u['date']}`" for u in upcoming[:3]])
        embeds.append({
            "title": "UPCOMING EVENTS", 
            "color": 0x3498DB, 
            "description": desc,
            "footer": {"text": f"Celesta • Updated {datetime.now().strftime('%H:%M')}"}
        })

    requests.post(DISCORD_WEBHOOK_URL, json={"embeds": embeds})

if __name__ == "__main__":
    act, upc = scrape_dynamic_events()
    post_discord(act, upc)
