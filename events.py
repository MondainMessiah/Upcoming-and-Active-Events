import os
import requests

# --- Configuration ---
PROXY_URL = os.environ.get("GOOGLE_BRIDGE_URL")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# Keywords are shorter to avoid failing on special characters like apostrophes
KEYWORDS = {
    "double xp": "DOUBLE XP AND SKILL",
    "spring into": "SPRING INTO LIFE",
    "chyllfroest": "CHYLLFROEST",
    "lullaby": "DEMON'S LULLABY",
    "rapid respawn": "RAPID RESPAWN",
    "double loot": "DOUBLE LOOT",
    "overload": "EXALTATION OVERLOAD",
    "devovorga": "RISE OF DEVOVORGA",
    "bewitched": "BEWITCHED"
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
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(PROXY_URL, headers=headers, timeout=30)
        
        # .casefold() makes the search case-insensitive
        content = response.text.casefold()
        
        print(f"DEBUG: Scanned {len(content)} characters.")

        for key, full_name in KEYWORDS.items():
            if key.casefold() in content:
                print(f"DEBUG: Found {full_name}")
                found.append({"name": full_name, "date": "Official Event"})
                
    except Exception as e:
        print(f"Scraper Error: {e}")
            
    return found

def post_discord(events):
    if not events:
        print("No events found to post.")
        return

    # Consistent with your successful Discord layout
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
