import os
import requests
import re

# --- Configuration ---
PROXY_URL = os.environ.get("GOOGLE_BRIDGE_URL")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def get_wiki_link(name):
    clean_name = name.replace("XP/Skill Event", "Double XP and Skill").replace("'", "").replace(" ", "_")
    return f"https://tibia.fandom.com/wiki/{clean_name}"

def scrape_colored_bars():
    if not PROXY_URL:
        print("Error: GOOGLE_BRIDGE_URL is missing.")
        return []

    events = set()
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(PROXY_URL, headers=headers, timeout=30)
        raw_html = response.text

        # 1. Isolate the calendar table
        calendar_match = re.search(r'<table[^>]*id="eventscheduletable"[^>]*>(.*?)</table>', raw_html, re.IGNORECASE | re.DOTALL)
        
        if not calendar_match:
            print("ERROR: 'eventscheduletable' not found in the HTML.")
            return []

        calendar_html = calendar_match.group(1)

        # 2. Look EXACTLY for the colored divs you pasted
        # It matches: <div style="background:#24657b; ... ">*XP/Skill Event</div>
        # And it automatically strips out the '*' character
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
        results = scrape_colored_bars()
        post_discord(results)
