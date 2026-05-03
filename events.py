import os
import requests
import re

# --- Configuration ---
PROXY_URL = os.environ.get("GOOGLE_BRIDGE_URL")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def get_wiki_link(name):
    clean_name = name.replace("XP/Skill Event", "Double XP and Skill").replace("'", "").replace(" ", "_")
    return f"https://tibia.fandom.com/wiki/{clean_name}"

def scrape_strict_calendar():
    if not PROXY_URL:
        print("Error: GOOGLE_BRIDGE_URL is missing.")
        return []

    events = set()
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(PROXY_URL, headers=headers, timeout=30)
        raw_html = response.text
        
        # 1. Isolate ONLY the calendar table to ensure we ignore the rest of the website
        calendar_match = re.search(r'<table[^>]*id="eventscheduletable"[^>]*>(.*?)</table>', raw_html, re.IGNORECASE | re.DOTALL)
        
        if not calendar_match:
            print("ERROR: 'eventscheduletable' not found. The Bridge did not return the calendar HTML.")
            return []

        calendar_html = calendar_match.group(1)

        # 2. Extract the event names from the tooltip tags inside the table
        # Matches: word-break: break-word;&quot;&gt;Chyllfroest:&lt;/div&gt;
        # Also handles if the quotes are unescaped (") instead of (&quot;)
        pattern = r'word-break: break-word;(?:&quot;|")&gt;(.*?):(?:&lt;|<)/div(?:&gt;|>)'
        
        found_matches = re.findall(pattern, calendar_html, re.IGNORECASE)

        for match in found_matches:
            clean_name = match.strip()
            # Ignore empty matches
            if clean_name and len(clean_name) > 2:
                events.add(clean_name)

    except Exception as e:
        print(f"Scraper Error: {e}")
            
    return sorted(list(events))

def post_discord(events):
    if not events:
        print("Final Status: No events populated from the calendar grid.")
        return

    # Filter out generic month-long background events if you only want major ones
    # Remove this line if you want "Flower Month" and "Prank Month" included
    major_events = [e for e in events if "Month" not in e]

    active_desc = "\n".join([f"🚀 **[`[{e.upper()}]`]({get_wiki_link(e)})**\n`┕ Official Calendar`" for e in major_events])
    
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
        results = scrape_strict_calendar()
        post_discord(results)
