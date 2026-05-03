import os
import requests
import re

PROXY_URL = os.environ.get("GOOGLE_BRIDGE_URL")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
TARGET_TIBIA_URL = "https://www.tibia.com/news/?subtopic=eventcalendar"

def get_wiki_link(name):
    clean_name = name.replace("XP/Skill Event", "Double XP and Skill").replace("'", "").replace(" ", "_")
    return f"https://tibia.fandom.com/wiki/{clean_name}"

def scrape_bridge():
    if not PROXY_URL:
        print("Error: GOOGLE_BRIDGE_URL is missing.")
        return []

    events = set()
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        print(f"Asking Google Bridge to fetch: {TARGET_TIBIA_URL}")
        
        response = requests.get(PROXY_URL, params={"url": TARGET_TIBIA_URL}, headers=headers, timeout=30)
        raw_html = response.text
        
        print(f"DEBUG: The Bridge returned {len(raw_html)} characters.")
        
        # 1. Isolate the calendar table strictly
        calendar_match = re.search(r'<table[^>]*id="eventscheduletable"[^>]*>(.*?)</table>', raw_html, re.IGNORECASE | re.DOTALL)
        
        if not calendar_match:
            print("ERROR: 'eventscheduletable' not found. Bridge did not return the calendar.")
            print("\n--- HERE IS WHAT THE BRIDGE ACTUALLY SAW (Top & Bottom) ---")
            print(raw_html[:800]) # Prints the top of the blocked page
            print("\n...\n")
            if len(raw_html) > 800:
                print(raw_html[-800:]) # Prints the bottom of the blocked page
            print("-----------------------------------------------------------\n")
            return []

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
        print("Final Status: No colored event bars found via the Bridge.")
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
    results = scrape_bridge()
    post_discord(results)
