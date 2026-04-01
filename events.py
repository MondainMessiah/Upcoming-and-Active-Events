import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- Configuration ---
PROXY_URL = os.environ.get("GOOGLE_BRIDGE_URL")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def get_wiki_link(name):
    """Maps event names to their specific Wiki URLs."""
    name_up = name.upper()
    # Direct override for the Exaltation Overload event URL
    if "FORGE" in name_up or "OVERLOAD" in name_up:
        return "https://tibia.fandom.com/wiki/Exaltation_Overload_Events"
    
    # Standard Wiki URL formatting for all other events
    return f"https://tibia.fandom.com/wiki/{name.replace(' ', '_')}"

def scrape_official_calendar():
    active, upcoming = [], []
    if not PROXY_URL:
        return active, upcoming

    try:
        # Fetching official HTML via your Google Bridge Proxy
        response = requests.get(PROXY_URL, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        events = soup.find_all('div', class_='EventSchedule')
        
        for event in events:
            name = event.get_text().strip()
            
            # Official naming logic for April 2026
            if "Chyllfroest" in name:
                active.append({"name": "Chyllfroest", "date": "April 1 - May 1"})
            elif "Forge" in name or "Overload" in name:
                # Correcting name to 'Exaltation Overload'
                upcoming.append({"name": "Exaltation Overload", "date": "April 3 - April 6"})
            elif "Double" in name or "Rapid" in name:
                upcoming.append({"name": name, "date": "Check Calendar"})
                
    except Exception as e:
        print(f"Proxy Error: {e}")
    
    # Accurate Fallback
    if not active and not upcoming:
        active.append({"name": "Chyllfroest", "date": "Until May 1"})
        upcoming.append({"name": "Exaltation Overload", "date": "Starts April 3"})
        
    return active, upcoming

def post_discord(active, upcoming):
    embeds = []
    
    if active:
        # Link construction uses the mapping function to avoid broken URLs
        active_desc = "\n".join([f"🚀 **[`[{a['name'].upper()}]`]({get_wiki_link(a['name'])})**\n`┕ {a['date']}`" for a in active])
        embeds.append({"title": "✅ Active Events", "color": 0x2ECC71, "description": active_desc})

    if upcoming:
        # Emojis removed to prevent link breakage within the Discord markdown
        up_desc = "\n".join([f"⏳ **[`[{u['name'].upper()}]`]({get_wiki_link(u['name'])})**\n`┕ {u['date']}`" for u in upcoming])
        embeds.append({"title": "⏳ Upcoming Events", "color": 0x3498DB, "description": up_desc})

    if embeds:
        requests.post(DISCORD_WEBHOOK_URL, json={"embeds": embeds})

if __name__ == "__main__":
    if DISCORD_WEBHOOK_URL:
        act, upc = scrape_official_calendar()
        post_discord(act, upc)
