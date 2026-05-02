import os
import requests

# --- Configuration ---
PROXY_URL = os.environ.get("GOOGLE_BRIDGE_URL")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# These are the official names we want to find
# We use partial names to ensure matches even if HTML tags are in the way
EVENT_KEYWORDS = {
    "DOUBLE XP": "DOUBLE XP AND SKILL",
    "SPRING INTO": "SPRING INTO LIFE",
    "CHYLLFROEST": "CHYLLFROEST",
    "LULLABY": "DEMON'S LULLABY",
    "RAPID RESPAWN": "RAPID RESPAWN",
    "DOUBLE LOOT": "DOUBLE LOOT",
    "OVERLOAD": "EXALTATION OVERLOAD",
    "BEWITCHED": "BEWITCHED"
}

def get_wiki_link(name):
    name_up = name.upper()
    if "OVERLOAD" in name_up:
        return "https://tibia.fandom.com/wiki/Exaltation_Overload_Events"
    return f"https://tibia.fandom.com/wiki/{name.replace(' ', '_')}"

def scrape_broad_search():
    found = []
    if not PROXY_URL:
        return found

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(PROXY_URL, headers=headers, timeout=30)
        
        # Convert the entire HTML source to Uppercase for easier matching
        content = response.text.upper()
        
        print(f"DEBUG: Scanned {len(content)} characters.")

        for key, full_name in EVENT_KEYWORDS.items():
            if key in content:
                print(f"DEBUG: Found {full_name}")
                found.append({"name": full_name, "date": "Official Event"})
                
    except Exception as e:
        print(f"Scraper Error: {e}")
            
    return found

def post_discord(events):
    if not events:
        print("Final Status: No events found in HTML content.")
        return

    # Using your preferred formatting
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
        results = scrape_broad_search()
        post_discord(results)
