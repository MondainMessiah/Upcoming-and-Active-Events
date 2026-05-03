import os
import re
import requests
from playwright.sync_api import sync_playwright

# --- Configuration ---
# You can try using the Bridge URL, but because Playwright acts like a real browser,
# you might be able to change your GitHub Secret to point directly to:
# https://www.tibia.com/news/?subtopic=eventcalendar
TARGET_URL = os.environ.get("GOOGLE_BRIDGE_URL")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def get_wiki_link(name):
    clean_name = name.replace("XP/Skill Event", "Double XP and Skill").replace("'", "").replace(" ", "_")
    return f"https://tibia.fandom.com/wiki/{clean_name}"

def scrape_with_playwright():
    if not TARGET_URL:
        print("Error: TARGET_URL is missing.")
        return []

    events = set()
    try:
        with sync_playwright() as p:
            # Launch a hidden Chromium browser
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            print(f"Navigating to URL...")
            page.goto(TARGET_URL, timeout=60000)
            
            # This is the magic step: Wait for the JavaScript to render the table!
            print("Waiting for the calendar table to render...")
            page.wait_for_selector("#eventscheduletable", timeout=30000)
            
            # Grab the HTML of the table AFTER it has been fully built
            calendar_html = page.inner_html("#eventscheduletable")
            
            # Apply our targeted Regex for the colored bars
            bar_pattern = r'<div style="background:#[a-zA-Z0-9]+;[^>]*>\s*\*?(.*?)\s*</div>'
            found_bars = re.findall(bar_pattern, calendar_html, re.IGNORECASE)

            for match in found_bars:
                clean_name = match.strip()
                if clean_name and len(clean_name) > 2:
                    events.add(clean_name)
                    
            browser.close()
            
    except Exception as e:
        print(f"Playwright Scraper Error: {e}")
            
    return sorted(list(events))

def post_discord(events):
    if not events:
        print("Final Status: No colored event bars found in the calendar.")
        return

    active_desc = "\n".join([f"🚀 **[`[{e.upper()}]`]({get_wiki_link(e)})**\n`┕ Official Calendar`" for e in events])
    
    payload = {
        "embeds": [{
            "title": "✅ Official Event Tracker",
            "color": 0x2ECC71,
            "description": active_desc
        }]
    }

    resp = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    print(f"Discord Response: {resp.status_code}")

if __name__ == "__main__":
    if DISCORD_WEBHOOK_URL:
        results = scrape_with_playwright()
        post_discord(results)
