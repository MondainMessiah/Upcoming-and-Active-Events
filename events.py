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
    if "OVERLOAD" in name_up or "FORGE" in name_up:
        return "https://tibia.fandom.com/wiki/Exaltation_Overload_Events"
    
    # Standard Wiki URL formatting for all other events
    return f"https://tibia.fandom.com/wiki/{name.replace(' ', '_')}"

def scrape_official_calendar():
    """
    Scrapes the official calendar via the Google Bridge.
    Includes logic to categorize events as Active or Upcoming based on the date.
    """
    active, upcoming = [], []
    today = datetime.now()
    
    if not PROXY_URL:
        return active, upcoming

    try:
        # Fetching official HTML via your Google Bridge Proxy
        response = requests.get(PROXY_URL, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Pulling event bars from the official Tibia.com calendar
        events = soup.find_all('div', class_='EventSchedule')
        
        for event in events:
            name = event.get_text().strip()
            name_up = name.upper()
            
            # --- April 2026 Specific Logic ---
            
            # 1. Chyllfroest (Active all of April)
            if "CHYLLFROEST" in name_up:
                active.append({"name": "Chyllfroest", "date": "Until May 1"})
            
            # 2. Exaltation Overload (April 3 - April 6)
            elif "FORGE" in name_up or "OVERLOAD" in name_up:
                if 3 <= today.day <= 6 and today.month == 4:
                    active.append({"name": "Exaltation Overload", "date": "Ends April 6"})
                elif today.day < 3 and today.month == 4:
                    upcoming.append({"name": "Exaltation Overload", "date": "Starts April 3"})
            
            # 3. Catch-all for other major announcements
            elif any(word in name_up for word in ["DOUBLE", "RAPID"]):
                upcoming.append({"name": name, "date": "Check Calendar"})
                
    except Exception as e:
        print(f"Proxy Error: {e}")
    
    # --- Manual Safety Net (In case the calendar is empty) ---
    if not active and not upcoming:
        if today.month == 4:
            active.append({"name": "Chyllfroest", "date": "Until May 1"})
            if 3 <= today.day <= 6:
                active.append({"name": "Exaltation Overload", "date": "Ends April 6"})
            elif today.day < 3:
                upcoming.append({"name": "Exaltation Overload", "date": "Starts April 3"})
        
    return active, upcoming

def post_discord(active, upcoming):
    """Formats and sends the Discord Embed."""
    embeds = []
    
    # Active Section (Green)
    if active:
        active_desc = "\n".join([
            f"🚀 **[`[{a['name'].upper()}]`]({get_wiki_link(a['name'])})**\n`┕ {a['date']}`" 
            for a in active
        ])
        embeds.append({
            "title": "✅ Active Events",
            "color": 0x2ECC71,
            "description": active_desc
        })

    # Upcoming Section (Blue)
    if upcoming:
        up_desc = "\n".join([
            f"⏳ **[`[{u['name'].upper()}]`]({get_wiki_link(u['name'])})**\n`┕ {u['date']}`" 
            for u in upcoming
        ])
        embeds.append({
            "title": "⏳ Upcoming Events",
            "color": 0x3498DB,
            "description": up_desc
        })

    if embeds:
        requests.post(DISCORD_WEBHOOK_URL, json={"embeds": embeds})

if __name__ == "__main__":
    if DISCORD_WEBHOOK_URL:
        act, upc = scrape_official_calendar()
        post_discord(act, upc)
