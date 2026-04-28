import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# --- Configuration ---
PROXY_URL = os.environ.get("GOOGLE_BRIDGE_URL")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# --- 2026 MAJOR EVENT DATABASE ---
# Format: "Event Name": {"start": (month, day), "end": (month, day)}
MAJOR_EVENTS = {
    "CHYLLFROEST": {"start": (4, 1), "end": (5, 1)},
    "SPRING INTO LIFE": {"start": (4, 16), "end": (5, 16)},
    "DOUBLE XP AND SKILL": {"start": (5, 1), "end": (5, 4)},
    "RAPID RESPAWN WEEKEND": {"start": (5, 15), "end": (5, 18)},
    "BEWITCHED": {"start": (6, 21), "end": (6, 25)},
    "DOUBLE LOOT WEEKEND": {"start": (7, 3), "end": (7, 6)},
    "HOT CUISINE": {"start": (8, 1), "end": (8, 31)},
    "RISE OF DEVOVORGA": {"start": (9, 1), "end": (9, 7)},
    "ORCSOBERFEST": {"start": (10, 9), "end": (10, 16)},
    "THE LIGHTBEARER": {"start": (11, 11), "end": (11, 15)},
    "WINTERLIGHT SOLSTICE": {"start": (12, 22), "end": (1, 10)}
}

def get_wiki_link(name):
    name_up = name.upper()
    if "OVERLOAD" in name_up or "FORGE" in name_up:
        return "https://tibia.fandom.com/wiki/Exaltation_Overload_Events"
    # Special handling for Winterlight Solstice link
    if "SOLSTICE" in name_up:
        return "https://tibia.fandom.com/wiki/Winterlight_Solstice"
    return f"https://tibia.fandom.com/wiki/{name.replace(' ', '_')}"

def scrape_official_calendar():
    active, upcoming = [], []
    today = datetime.now()
    current_tuple = (today.month, today.day)
    
    # 1. Scrape for rotating/unannounced bonuses (via Proxy)
    if PROXY_URL:
        try:
            response = requests.get(PROXY_URL, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            events = soup.find_all('div', class_='EventSchedule')
            for event in events:
                name = event.get_text().strip()
                # If the scraper finds something not in our manual list, add it
                if not any(k in name.upper() for k in MAJOR_EVENTS.keys()):
                    active.append({"name": name, "date": "Official Event"})
        except Exception as e:
            print(f"Proxy Error: {e}")

    # 2. Perpetual Logic for Major Events
    for event_key, info in MAJOR_EVENTS.items():
        start, end = info["start"], info["end"]
        
        # Logic for current Active events
        # Note: Handles year-wrap for Winterlight Solstice (Dec-Jan)
        is_active = False
        if start[0] <= end[0]: # Normal event (same month or consecutive)
            if start <= current_tuple <= end:
                is_active = True
        else: # Wrap-around event (Dec to Jan)
            if current_tuple >= start or current_tuple <= end:
                is_active = True

        if is_active:
            active.append({
                "name": event_key.title(), 
                "date": f"Until {datetime(today.year if current_tuple <= end else today.year - 1, end[0], end[1]).strftime('%b %d')}"
            })
        
        # Logic for Upcoming events (Looks 14 days ahead)
        else:
            event_start_date = datetime(today.year, start[0], start[1])
            if start[0] < today.month: 
                event_start_date = datetime(today.year + 1, start[0], start[1])
                
            if today < event_start_date <= (today + timedelta(days=14)):
                upcoming.append({
                    "name": event_key.title(), 
                    "date": f"Starts {event_start_date.strftime('%b %d')}"
                })

    return active, upcoming

def post_discord(active, upcoming):
    embeds = []
    
    # Deduplicate and sort
    unique_active = {a['name'].upper(): a for a in active}.values()
    active_names = [a['name'].upper() for a in unique_active]
    unique_upcoming = {u['name'].upper(): u for u in upcoming if u['name'].upper() not in active_names}.values()

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
