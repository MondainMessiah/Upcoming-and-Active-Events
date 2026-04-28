import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- Configuration ---
PROXY_URL = os.environ.get("GOOGLE_BRIDGE_URL")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# OFFICIAL 2026 ANNUAL SCHEDULE
ANNUAL_SCHEDULE = {
    1: [{"name": "Tibia Anniversary", "date": "Jan 7 - Jan 10"}],
    2: [{"name": "A Piece of Cake", "date": "Feb 21 - Feb 26"}],
    3: [{"name": "Double Daily Rewards", "date": "All March"}],
    4: [{"name": "Chyllfroest", "date": "Apr 1 - May 1"}],
    5: [{"name": "Spring into Life", "date": "Apr 16 - May 16"}],
    6: [{"name": "Flower Month", "date": "All June"}, {"name": "Bewitched", "date": "June 21 - June 25"}],
    8: [{"name": "Hot Cuisine Quest", "date": "Aug 1 - Aug 31"}, {"name": "The Colours of Magic", "date": "Aug 15 - Aug 22"}],
    9: [{"name": "Rise of Devovorga", "date": "Sept 1 - Sept 7"}],
    10: [{"name": "Orcsoberfest", "date": "Oct 9 - Oct 16"}, {"name": "Halloween", "date": "Oct 31"}],
    11: [{"name": "The Lightbearer", "date": "Nov 11 - Nov 15"}],
    12: [{"name": "Winterlight Solstice", "date": "Dec 22 - Jan 10"}]
}

def get_wiki_link(name):
    name_up = name.upper()
    if "OVERLOAD" in name_up or "FORGE" in name_up:
        return "https://tibia.fandom.com/wiki/Exaltation_Overload_Events"
    return f"https://tibia.fandom.com/wiki/{name.replace(' ', '_')}"

def scrape_official_calendar():
    active, upcoming = [], []
    today = datetime.now()
    mo = today.month
    
    # 1. Add Fixed Annual Events for current and next month
    for month_index in [mo, (mo % 12) + 1]:
        if month_index in ANNUAL_SCHEDULE:
            for ev in ANNUAL_SCHEDULE[month_index]:
                # Logic to determine if it's currently Active or Upcoming
                # This is a simplified check; the scraper will refine these.
                if month_index == mo:
                    active.append(ev)
                else:
                    upcoming.append(ev)

    # 2. Scrape official calendar for dynamic bonuses (XP/Loot/Rapid)
    if PROXY_URL:
        try:
            response = requests.get(PROXY_URL, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            events = soup.find_all('div', class_='EventSchedule')
            
            for event in events:
                name = event.get_text().strip()
                name_up = name.upper()
                
                # Dynamic detection for rotating weekend bonuses
                if any(k in name_up for k in ["DOUBLE", "RAPID", "OVERLOAD"]):
                    # Avoid duplicates with the fixed schedule
                    if not any(a['name'].upper() == name_up for a in active):
                        upcoming.append({"name": name, "date": "Check Calendar"})
        except Exception as e:
            print(f"Proxy Error: {e}")
            
    return active, upcoming

def post_discord(active, upcoming):
    embeds = []
    # Active Section (Green)
    if active:
        active_desc = "\n".join([f"🚀 **[`[{a['name'].upper()}]`]({get_wiki_link(a['name'])})**\n`┕ {a['date']}`" for a in active])
        embeds.append({"title": "✅ Active Events", "color": 0x2ECC71, "description": active_desc})
    
    # Upcoming Section (Blue)
    if upcoming:
        # Filter duplicates that might appear from both logic sets
        unique_upcoming = {v['name']: v for v in upcoming}.values()
        up_desc = "\n".join([f"⏳ **[`[{u['name'].upper()}]`]({get_wiki_link(u['name'])})**\n`┕ {u['date']}`" for u in unique_upcoming])
        embeds.append({"title": "⏳ Upcoming Events", "color": 0x3498DB, "description": up_desc})
        
    if embeds:
        requests.post(DISCORD_WEBHOOK_URL, json={"embeds": embeds})

if __name__ == "__main__":
    if DISCORD_WEBHOOK_URL:
        act, upc = scrape_official_calendar()
        post_discord(act, upc)
