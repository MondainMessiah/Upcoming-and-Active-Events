import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- Configuration ---
PROXY_URL = os.environ.get("GOOGLE_BRIDGE_URL")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def get_wiki_link(name):
    name_up = name.upper()
    if "OVERLOAD" in name_up or "FORGE" in name_up:
        return "https://tibia.fandom.com/wiki/Exaltation_Overload_Events"
    return f"https://tibia.fandom.com/wiki/{name.replace(' ', '_')}"

def scrape_official_calendar():
    """
    STRICT SCRAPER: Only returns what is found on the official website.
    No hardcoded dates or guesses.
    """
    active, upcoming = [], []
    
    if not PROXY_URL:
        print("Error: GOOGLE_BRIDGE_URL is missing.")
        return active, upcoming

    try:
        # Fetching official HTML via your Google Bridge Proxy
        response = requests.get(PROXY_URL, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Tibia.com uses 'EventSchedule' for calendar bars
        events = soup.find_all('div', class_='EventSchedule')
        
        for event in events:
            # Extract name and the color/style to determine status
            name = event.get_text().strip()
            style = event.get('style', '').lower()
            
            # Logic: If the event bar spans 'today' on the official site
            # Tibia marks active events with specific CSS positioning.
            # For simplicity, we categorize based on common scraper patterns:
            if "background-color" in style or "opacity: 1" in style:
                active.append({"name": name, "date": "Official Active"})
            else:
                upcoming.append({"name": name, "date": "Official Upcoming"})
                
    except Exception as e:
        print(f"Proxy Error: {e}")
            
    return active, upcoming

def post_discord(active, upcoming):
    embeds = []
    
    if active:
        active_desc = "\n".join([f"🚀 **[`[{a['name'].upper()}]`]({get_wiki_link(a['name'])})**\n`┕ {a['date']}`" for a in active])
        embeds.append({"title": "✅ Active Events", "color": 0x2ECC71, "description": active_desc})

    if upcoming:
        up_desc = "\n".join([f"⏳ **[`[{u['name'].upper()}]`]({get_wiki_link(u['name'])})**\n`┕ {u['date']}`" for u in upcoming])
        embeds.append({"title": "⏳ Upcoming Events", "color": 0x3498DB, "description": up_desc})

    if embeds:
        requests.post(DISCORD_WEBHOOK_URL, json={"embeds": embeds})

if __name__ == "__main__":
    if DISCORD_WEBHOOK_URL:
        act, upc = scrape_official_calendar()
        post_discord(act, upc)
