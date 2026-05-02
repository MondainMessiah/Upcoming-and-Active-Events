import os
import requests

# --- Configuration ---
PROXY_URL = os.environ.get("GOOGLE_BRIDGE_URL")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# Official event names to look for in the raw HTML
OFFICIAL_KEYWORDS = [
    "DOUBLE XP AND SKILL", "SPRING INTO LIFE", "CHYLLFROEST", 
    "DEMON'S LULLABY", "RAPID RESPAWN", "DOUBLE LOOT", "BEWITCHED",
    "EXALTATION OVERLOAD", "RISE OF DEVOVORGA"
]

def get_wiki_link(name):
    name_up = name.upper()
    if "OVERLOAD" in name_up or "FORGE" in name_up:
        return "https://tibia.fandom.com/wiki/Exaltation_Overload_Events"
    return f"https://tibia.fandom.com/wiki/{name.replace(' ', '_')}"

def scrape_official_calendar():
    """
    Switches to a text-scan method to bypass fragile HTML structures.
    """
    active = []
    if not PROXY_URL:
        return active

    try:
        response = requests.get(PROXY_URL, timeout=30)
        # Scan the entire text of the page for our keywords
        raw_html = response.text.upper()
        
        for kw in OFFICIAL_KEYWORDS:
            if kw in raw_html:
                # If found, it exists on the official calendar today
                active.append({"name": kw.title(), "date": "Official Event"})
                
    except Exception as e:
        print(f"Proxy Error: {e}")
            
    return active

def post_discord(active):
    if not active:
        # This will now show in your GitHub log if the text scan fails
        print("Scraper found 0 keywords in the raw HTML.")
        return

    embeds = []
    # All found keywords are officially on the calendar
    active_desc = "\n".join([f"🚀 **[`[{a['name'].upper()}]`]({get_wiki_link(a['name'])})**\n`┕ {a['date']}`" for a in active])
    embeds.append({"title": "✅ Official Events", "color": 0x2ECC71, "description": active_desc})

    requests.post(DISCORD_WEBHOOK_URL, json={"embeds": embeds})

if __name__ == "__main__":
    if DISCORD_WEBHOOK_URL:
        found_events = scrape_official_calendar()
        post_discord(found_events)
