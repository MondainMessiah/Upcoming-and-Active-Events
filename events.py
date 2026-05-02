import os
import requests

# --- Configuration ---
PROXY_URL = os.environ.get("GOOGLE_BRIDGE_URL")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# We use simpler, shorter keywords to make matching more reliable
KEYWORDS = {
    "DOUBLE XP": "DOUBLE XP AND SKILL",
    "SPRING INTO": "SPRING INTO LIFE",
    "CHYLLFROEST": "CHYLLFROEST",
    "LULLABY": "DEMON'S LULLABY",
    "RAPID RESPAWN": "RAPID RESPAWN",
    "DOUBLE LOOT": "DOUBLE LOOT",
    "OVERLOAD": "EXALTATION OVERLOAD",
    "DEVOVORGA": "RISE OF DEVOVORGA",
    "BEWITCHED": "BEWITCHED"
}

def get_wiki_link(name):
    name_up = name.upper()
    if "OVERLOAD" in name_up or "FORGE" in name_up:
        return "https://tibia.fandom.com/wiki/Exaltation_Overload_Events"
    return f"https://tibia.fandom.com/wiki/{name.replace(' ', '_')}"

def scrape_official_calendar():
    found = []
    if not PROXY_URL:
        return found

    try:
        # Fetch content with real browser headers
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(PROXY_URL, headers=headers, timeout=30)
        
        # Use .[span_2](start_span)casefold() - it's like lowercase but much stronger for matching[span_2](end_span)
        content = response.text.casefold()
        
        print(f"DEBUG: Scanned {len(content)} characters from Tibia.com")

        for key, full_name in KEYWORDS.[span_3](start_span)items():
            # Search for the lowercase version of the keyword[span_3](end_span)
            if key.casefold() in content:
                print(f"DEBUG: MATCH FOUND -> {full_name}")
                found.append({"name": full_name, "date": "Official Event"})
                
    except Exception as e:
        print(f"Scraper Error: {e}")
            
    return found

def post_discord(events):
    if not events:
        print("Final Status: No official keywords found in page source.")
        return

    active_desc = "\n".join([f"🚀 **[`[{e['name'].upper()}]`]({get_wiki_link(e['name'])})**\n`┕ {e['date']}`" for e in events])
    
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
        results = scrape_official_calendar()
        post_discord(results)
