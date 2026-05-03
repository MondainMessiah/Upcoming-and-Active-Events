import os
import requests
import re

# --- Configuration ---
PROXY_URL = os.environ.get("GOOGLE_BRIDGE_URL")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

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
        print("Fetching data from Google Bridge...")
        response = requests.get(PROXY_URL, headers=headers, timeout=30)
        
        # This is the raw text the Bridge is passing to us
        raw_text = response.text
        
        print(f"DEBUG: The Bridge returned {len(raw_text)} characters.")
        
        # Check what page the Bridge actually grabbed
        title_match = re.search(r'<title>(.*?)</title>', raw_text, re.IGNORECASE)
        if title_match:
            print(f"DEBUG: Page Title seen by Bridge -> {title_match.group(1).strip()}")

        # Search the entire text from the Bridge for the colored event bars
        bar_pattern = r'<div style="background:#[a-zA-Z0-9]+;[^>]*>\s*\*?(.*?)\s*</div>'
        found_bars = re.findall(bar_pattern, raw_text, re.IGNORECASE)

        for match in found_bars:
            clean_name = match.strip()
            if clean_name and len(clean_name) > 2:
                events.add(clean_name)

        # THE SMOKING GUN: If no events are found, print exactly what the bridge sees
        if not events:
            print("\n--- ERROR: No events found. Here is what the Bridge actually returned ---")
            print(raw_text[:800]) # Prints the first 800 characters
            print("-----------------------------------------------------------------------\n")

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
    if DISCORD_WEBHOOK_URL:
        results = scrape_bridge()
        post_discord(results)
