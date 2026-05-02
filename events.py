import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

[span_2](start_span)# --- Configuration ---
# Point this to the Wiki Upcoming Events page[span_2](end_span)
WIKI_URL = "https://tibia.fandom.com/wiki/Upcoming_Events"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# Keywords to match specifically against the Wiki's list
KEYWORDS = [
    "DOUBLE XP", "SPRING INTO LIFE", "CHYLLFROEST", 
    "DEMON'S LULLABY", "RAPID RESPAWN", "DOUBLE LOOT", 
    "EXALTATION OVERLOAD", "BEWITCHED", "GRIMVALE"
]

def get_wiki_link(name):
    name_up = name.upper()
    if "OVERLOAD" in name_up:
        return "https://tibia.fandom.com/wiki/Exaltation_Overload_Events"
    return f"https://tibia.fandom.com/wiki/{name.replace(' ', '_')}"

def scrape_wiki_events():
    active, upcoming = [], []
    today = datetime.now()
    
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(WIKI_URL, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        [span_3](start_span)# The Wiki lists events in clear <li> tags[span_3](end_span)
        event_elements = soup.find_all('li')
        
        for element in event_elements:
            text = element.get_text()
            text_up = text.upper()
            
            [span_4](start_span)# Check if any of our major keywords are in this list item
            for kw in KEYWORDS:
                if kw in text_up:
                    # Clean the string to get just the name and date
                    # Example text: "Demon's Lullaby will start in 6 days on May 7."[span_4](end_span)
                    event_info = text.split('.')[0] # Take the first sentence
                    
                    if "START IN" in text_up:
                        upcoming.append({"name": kw, "data": event_info})
                    else:
                        # If it doesn't say "will start", it's currently active
                        active.append({"name": kw, "data": event_info})
                    break # Found the keyword, move to next <li>

    except Exception as e:
        print(f"Wiki Scraper Error: {e}")
            
    return active, upcoming

def post_discord(active, upcoming):
    if not active and not upcoming:
        print("Final Status: No matches found on Wiki.")
        return

    embeds = []
    if active:
        active_desc = "\n".join([f"🚀 **[`[{a['name'].upper()}]`]({get_wiki_link(a['name'])})**\n`┕ {a['data']}`" for a in active])
        embeds.append({"title": "✅ Active Events", "color": 0x2ECC71, "description": active_desc})

    if upcoming:
        up_desc = "\n".join([f"⏳ **[`[{u['name'].upper()}]`]({get_wiki_link(u['name'])})**\n`┕ {u['data']}`" for u in upcoming])
        embeds.append({"title": "⏳ Upcoming Events", "color": 0x3498DB, "description": up_desc})

    requests.post(DISCORD_WEBHOOK_URL, json={"embeds": embeds})

if __name__ == "__main__":
    if DISCORD_WEBHOOK_URL:
        act, upc = scrape_wiki_events()
        post_discord(act, upc)
