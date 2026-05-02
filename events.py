import os
import requests
from bs4 import BeautifulSoup

# --- Configuration ---
PROXY_URL = os.environ.get("GOOGLE_BRIDGE_URL")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def get_wiki_link(name):
    name_up = name.upper()
    if "OVERLOAD" in name_up or "FORGE" in name_up:
        return "https://tibia.fandom.com/wiki/Exaltation_Overload_Events"
    return f"https://tibia.fandom.com/wiki/{name.replace(' ', '_')}"

def scrape_official_calendar():
    active, upcoming = [], []
    if not PROXY_URL:
        return active, upcoming

    try:
        # Reverting to the logic that worked in the beginning
        response = requests.get(PROXY_URL, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the specific div class Tibia uses for the calendar bars
        events = soup.find_all('div', class_='EventSchedule')
        
        for event in events:
            name = event.get_text().strip()
            # If the name is empty or just whitespace, skip it
            if not name:
                continue
                
            style = event.get('style', '').lower()
            
            # Reverting status logic: 
            # If it has a background color or is positioned at the start, it's active.
            if "background-color" in style or "left:0%" in style or "left: 0%" in style:
                active.append({"name": name, "date": "Active Now"})
            else:
                upcoming.append({"name": name, "date": "Starts Soon"})
                
    except Exception as e:
        print(f"Proxy Error: {e}")
            
    return active, upcoming

def post_discord(active, upcoming):
    embeds = []
    
    # Strictly only post what was found in the scrape
    if active:
        active_desc = "\n".join([f"🚀 **[`[{a['name'].upper()}]`]({get_wiki_link(a['name'])})**\n`┕ {a['date']}`" for a in active])
        embeds.append({"title": "✅ Active Events", "color": 0x2ECC71, "description": active_desc})

    if upcoming:
        up_desc = "\n".join([f"⏳ **[`[{u['name'].upper()}]`]({get_wiki_link(u['name'])})**\n`┕ {u['date']}`" for u in upcoming])
        embeds.append({"title": "⏳ Upcoming Events", "color": 0x3498DB, "description": up_desc})

    if embeds:
        requests.post(DISCORD_WEBHOOK_URL, json={"embeds": embeds})
    else:
        print("No events found on the page to post.")

if __name__ == "__main__":
    if DISCORD_WEBHOOK_URL:
        act, upc = scrape_official_calendar()
        post_discord(act, upc)
