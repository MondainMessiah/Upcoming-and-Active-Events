import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- Configuration ---
PROXY_URL = os.environ.get("GOOGLE_BRIDGE_URL")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# Events that deserve an extra "Diamond" highlight
HIGH_PRIORITY = ["DOUBLE XP", "DOUBLE SKILL", "RAPID RESPAWN", "DOUBLE LOOT", "BEWITCHED"]

def scrape_official_calendar():
    active, upcoming = [], []
    if not PROXY_URL:
        return active, upcoming

    try:
        response = requests.get(PROXY_URL, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        events = soup.find_all('div', class_='EventSchedule')
        
        for event in events:
            name = event.get_text().strip()
            name_up = name.upper()
            
            # Apply Diamond Highlight to major power-gaming events
            display_name = f"💎 {name}" if any(hp in name_up for hp in HIGH_PRIORITY) else name

            # Official April 2026 Logic
            if "Chyllfroest" in name:
                active.append({"name": "Chyllfroest", "date": "April 1 - May 1"})
            elif "Forge" in name:
                upcoming.append({"name": display_name, "date": "April 3 - April 6"})
            elif "Double" in name or "Rapid" in name:
                upcoming.append({"name": display_name, "date": "Check Calendar"})
                
    except Exception as e:
        print(f"Proxy Error: {e}")
    
    # Accurate Fallback
    if not active and not upcoming:
        active.append({"name": "Chyllfroest", "date": "Until May 1"})
        upcoming.append({"name": "💎 Exaltation Forge Bonus", "date": "Starts April 3"})
        
    return active, upcoming

def post_discord(active, upcoming):
    embeds = []
    
    if active:
        active_desc = "\n".join([f"🚀 **[`[{a['name'].upper()}]`](https://tibia.fandom.com/wiki/{a['name'].replace(' ', '_')})**\n`┕ {a['date']}`" for a in active])
        embeds.append({"title": "✅ Active Events", "color": 0x2ECC71, "description": active_desc})

    if upcoming:
        up_desc = "\n".join([f"⏳ **[`[{u['name'].upper()}]`](https://tibia.fandom.com/wiki/{u['name'].replace(' ', '_')})**\n`┕ {u['date']}`" for u in upcoming])
        embeds.append({"title": "⏳ Upcoming Events", "color": 0x3498DB, "description": up_desc})

    if embeds:
        requests.post(DISCORD_WEBHOOK_URL, json={"embeds": embeds})

if __name__ == "__main__":
    if DISCORD_WEBHOOK_URL:
        act, upc = scrape_official_calendar()
        post_discord(act, upc)
