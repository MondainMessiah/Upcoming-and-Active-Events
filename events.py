import os
import re
import cloudscraper
import requests

# --- Configuration ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
TARGET_TIBIA_URL = "https://www.tibia.com/news/?subtopic=eventcalendar"

def get_wiki_link(name):
    clean_name = name.replace("XP/Skill Event", "Double XP and Skill").replace("'", "").replace(" ", "_")
    return f"https://tibia.fandom.com/wiki/{clean_name}"

def scrape_tibia_direct():
    events = set()
    try:
        print(f"Bypassing Cloudflare and fetching: {TARGET_TIBIA_URL}")
        
        # Initialize the Cloudflare-bypassing scraper
        scraper = cloudscraper.create_scraper(browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        })
        
        response = scraper.get(TARGET_TIBIA_URL, timeout=30)
        raw_html = response.text
        
        print(f"DEBUG: Cloudscraper returned {len(raw_html)} characters.")
        
        # 1. Isolate the calendar table strictly
        calendar_match = re.search(r'<table[^>]*id="eventscheduletable"[^>]*>(.*?)</table>', raw_html, re.IGNORECASE | re.DOTALL)
        
        if not calendar_match:
            print("ERROR: 'eventscheduletable' not found. Cloudflare might still be blocking us.")
            # Print the title to confirm if we got through
            title_match = re.search(r'<title>(.*?)</title>', raw_html, re.IGNORECASE)
            if title_match:
                print(f"DEBUG: Page Title seen -> {title_match.group(1).strip()}")
            return []

        print("Successfully bypassed Cloudflare and found the calendar table!")
        calendar_html = calendar_match.group(1)

        # 2. Extract the text directly from the colored event boxes
        bar_pattern = r'<div style="background:#[a-zA-Z0-9]+;[^>]*>\s*\*?(.*?)\s*</div>'
        found_bars = re.findall(bar_pattern, calendar_html, re.IGNORECASE)

        for match in found_bars:
            clean_name = match.strip()
            if clean_name and len(clean_name) > 2:
                events.add(clean_name)

    except Exception as e:
        print(f"Scraper Error: {e}")
            
    return sorted(list(events))

def post_discord(events):
    if not events:
        print("Final Status: No colored event bars found.")
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
        results = scrape_tibia_direct()
        post_discord(results)
    else:
        print("Error: DISCORD_WEBHOOK_URL is missing from environment variables.")
