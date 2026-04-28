import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- Configuration ---
PROXY_URL = os.environ.get("GOOGLE_BRIDGE_URL")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# --- Event Filtering ---
# Keywords that define a "Major Event" for the main sections
MAJOR_KEYWORDS = ["DOUBLE", "RAPID", "FORGE", "OVERLOAD", "BEWITCHED", "DEVOCORGA", "LIGHTBEARER", "CHYLLFROEST", "SPRING INTO LIFE"]

# Fixed Annual Schedule for Fallback
ANNUAL_SCHEDULE = {
    4: [{"name": "Chyllfroest", "date": "Apr 1 - May 1"}, {"name": "Spring into Life", "date": "Apr 16 - May 16"}],
    5: [{"name": "Spring into Life", "date": "Until May 16"}],
    12: [{"name": "Winterlight Solstice", "date": "Dec 22 - Jan 10"}]
}

def get_wiki_link(name):
    name_up = name.upper()
    if "OVERLOAD" in name_up or "FORGE" in name_up:
        return "https://tibia.fandom.com/wiki/Exaltation_Overload_Events"
    return f"https://tibia.fandom.com/wiki/{name.replace(' ', '_')}"

def scrape_official_calendar():
    active, upcoming, minis = [], [], []
    today = datetime.now()
    
    if PROXY_URL:
        try:
            response = requests.get(PROXY_URL, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            events = soup.find_all('div', class_='EventSchedule')
            
            for event in events:
                name = event.get_text().strip()
                name_up = name.upper()
                
                # Logic to sort between Major Events and Mini World Changes
                if any(k in name_up for k in MAJOR_KEYWORDS):
                    # Simplified logic: If it's on the calendar today, it's active
                    # This can be refined further with date parsing if needed
                    active.append({"name": name, "date": "Active Now"})
                else:
                    # Everything else (Grimvale, Bank Robbery, etc.) goes to Minis
                    minis.append(name)
        except Exception as e:
            print(f"Proxy Error: {e}")
            
    # Fallback for April 28
    if not active and today.month == 4:
        active.append({"name": "Chyllfroest", "date": "Ends May 1"})
        upcoming.append({"name": "Spring into Life", "date": "Starts Apr 16"})

    return active, upcoming, minis

def post_discord(active, upcoming, minis):
    embeds = []
    
    # 1. ✅ Active Events Section
    if active:
        active_desc = "\n".join([f"🚀 **[`[{a['name'].upper()}]`]({get_wiki_link(a['name'])})**\n`┕ {a['date']}`" for a in active])
        embeds.append({"title": "✅ Active Events", "color": 0x2ECC71, "description": active_desc})

    # 2. ⏳ Upcoming Events Section
    if upcoming:
        up_desc = "\n".join([f"⏳ **[`[{u['name'].upper()}]`]({get_wiki_link(u['name'])})**\n`┕ {u['date']}`" for u in upcoming])
        embeds.append({"title": "⏳ Upcoming Events", "color": 0x3498DB, "description": up_desc})

    # 3. 🗺️ Mini World Changes (Optional compact section)
    if minis:
        mini_desc = " • ".join([f"[{m}]" for m in set(minis)])
        embeds.append({"title": "🗺️ Mini World Changes", "color": 0x95A5A6, "description": f"_{mini_desc}_"})

    if embeds:
        requests.post(DISCORD_WEBHOOK_URL, json={"embeds": embeds})

if __name__ == "__main__":
    if DISCORD_WEBHOOK_URL:
        act, up, mini = scrape_official_calendar()
        post_discord(act, up, mini)
