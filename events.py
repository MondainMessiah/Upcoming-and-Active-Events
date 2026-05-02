import os
import requests
from bs4 import BeautifulSoup

# --- Configuration ---
PROXY_URL = os.environ.get("GOOGLE_BRIDGE_URL")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def get_wiki_link(name):
    """Generates a functional Wiki link for any event found."""
    name_up = name.upper()
    if "OVERLOAD" in name_up or "FORGE" in name_up:
        return "https://tibia.fandom.com/wiki/Exaltation_Overload_Events"
    return f"https://tibia.fandom.com/wiki/{name.replace(' ', '_')}"

def scrape_official_calendar():
    """
    STRICT SCRAPE: Only returns official data from Tibia.com.
    Removes all manual dates and guesses.
    """
    active, upcoming = [], []
    
    if not PROXY_URL:
        return active, upcoming

    try:
        # Fetching official HTML through your proxy bridge
        response = requests.get(PROXY_URL, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Scrape every event bar found on the calendar
        events = soup.find_all('div', class_='EventSchedule')
        
        for event in events:
            name = event.get_text().strip()
            # Determine if active based on CSS (Tibia places active bars differently)
            style = event.get('style', '').lower()
            
            # Logic: If the bar is visible/solid in the 'Today' column
            if "opacity: 1" in style or "background-color" in style:
                active.append({"name": name, "date": "Official Active"})
            else:
                upcoming.append({"name": name, "date": "Official Upcoming"})
                
    except Exception as e:
        print(f"Proxy Error: {e}")
            
    return active, upcoming

def post_discord(active, upcoming):
    """Sends the scraped data to Discord using the requested formatting."""
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
