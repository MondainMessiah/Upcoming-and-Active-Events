import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- Configuration ---
PROXY_URL = os.environ.get("GOOGLE_BRIDGE_URL")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# --- Major Event Definitions ---
MAJOR_EVENTS = {
    "CHYLLFROEST": {"start": (4, 1), "end": (5, 1)},
    "SPRING INTO LIFE": {"start": (4, 16), "end": (5, 16)},
    "DOUBLE XP": {"is_dynamic": True},
    "DOUBLE SKILL": {"is_dynamic": True},
    "RAPID RESPAWN": {"is_dynamic": True},
    "DOUBLE LOOT": {"is_dynamic": True},
    "EXALTATION OVERLOAD": {"is_dynamic": True}
}

def get_wiki_link(name):
    name_up = name.upper()
    if "OVERLOAD" in name_up or "FORGE" in name_up:
        return "https://tibia.fandom.com/wiki/Exaltation_Overload_Events"
    return f"https://tibia.fandom.com/wiki/{name.replace(' ', '_')}"

def scrape_official_calendar():
    active, upcoming = [], []
    today = datetime.now()
    current_tuple = (today.month, today.day)
    
    found_names = set()

    if PROXY_URL:
        try:
            response = requests.get(PROXY_URL, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            events = soup.find_all('div', class_='EventSchedule')
            
            for event in events:
                name = event.get_text().strip()
                name_up = name.upper()
                found_names.add(name_up)
                
                # Check dynamic rotating bonuses from the official calendar
                if any(k in name_up for k in ["DOUBLE", "RAPID", "OVERLOAD"]):
                    # If it's on the calendar today, we'll mark it active
                    active.append({"name": name, "date": "Check Calendar"})
        except Exception as e:
            print(f"Proxy Error: {e}")

    # --- Perpetual Logic for Fixed Annual Events ---
    for event_key, info in MAJOR_EVENTS.items():
        if "is_dynamic" in info: continue
        
        start, end = info["start"], info["end"]
        
        # Check if active today
        if start <= current_tuple <= end:
            active.append({"name": event_key.title(), "date": f"Until {datetime(today.year, end[0], end[1]).strftime('%b %d')}"})
        # Check if upcoming (within next 30 days)
        elif current_tuple < start:
            upcoming.append({"name": event_key.title(), "date": f"Starts {datetime(today.year, start[0], start[1]).strftime('%b %d')}"})

    return active, upcoming

def post_discord(active, upcoming):
    embeds = []
    
    # Remove duplicates if scraper and manual logic both find an event
    unique_active = {a['name'].upper(): a for a in active}.values()
    unique_upcoming = {u['name'].upper(): u for u in upcoming if u['name'].upper() not in [a['name'].upper() for a in active]}.values()

    if unique_active:
        active_desc = "\n".join([f"🚀 **[`[{a['name'].upper()}]`]({get_wiki_link(a['name'])})**\n`┕ {a['date']}`" for a in unique_active])
        embeds.append({"title": "✅ Active Events", "color": 0x2ECC71, "description": active_desc})

    if unique_upcoming:
        up_desc = "\n".join([f"⏳ **[`[{u['name'].upper()}]`]({get_wiki_link(u['name'])})**\n`┕ {u['date']}`" for u in unique_upcoming])
        embeds.append({"title": "⏳ Upcoming Events", "color": 0x3498DB, "description": up_desc})

    if embeds:
        requests.post(DISCORD_WEBHOOK_URL, json={"embeds": embeds})

if __name__ == "__main__":
    if DISCORD_WEBHOOK_URL:
        act, upc = scrape_official_calendar()
        post_discord(act, upc)
