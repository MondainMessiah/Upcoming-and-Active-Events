import os
import requests
from bs4 import BeautifulSoup
import re

# --- Configuration ---
PROXY_URL = os.environ.get("GOOGLE_BRIDGE_URL")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def get_wiki_link(name):
    # Clean name for Wiki URL (e.g., "XP/Skill Event" -> "Double_XP_and_Skill")
    clean_name = name.replace("XP/Skill Event", "Double XP and Skill").replace("'", "").replace(" ", "_")
    return f"https://tibia.fandom.com/wiki/{clean_name}"

def scrape_tibia_table():
    active_events = set() # Use a set to avoid duplicates from different calendar days
    
    if not PROXY_URL:
        return []

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(PROXY_URL, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Find the specific events schedule table you provided
        table = soup.find('table', id='eventscheduletable')
        if not table:
            print("Table 'eventscheduletable' not found in HTML.")
            return []

        # 2. Find all 'HelperDivIndicator' spans which contain the event text
        # These are found inside the table cells <td>
        indicators = table.find_all('span', class_='HelperDivIndicator')
        
        for span in indicators:
            # The event name is often inside a div within this span
            # Or hidden in the 'onmouseover' attribute
            content = span.get_text(strip=True)
            
            # If the span has text like "XP/Skill Event", grab it
            if content and content.startswith('*'):
                active_events.add(content.replace('*', '').strip())
            elif content:
                active_events.add(content.strip())
            
            # Backup: Check the onmouseover attribute for the full name
            mouse_over = span.get('onmouseover', '')
            if "word-break: break-word;" in mouse_over:
                # Use regex to pull the title out of the Javascript string
                match = re.search(r'bold; word-break: break-word;">(.*?)[:<]', mouse_over)
                if match:
                    active_events.add(match.group(1).strip())

    except Exception as e:
        print(f"Table Scraper Error: {e}")
            
    return sorted(list(active_events))

def post_discord(events):
    if not events:
        print("No events identified in the table.")
        return

    # Filter out empty strings and generic 'Prank Month' if desired
    formatted_events = [e for e in events if e and len(e) > 3]

    active_desc = "\n".join([f"🚀 **[`[{e.upper()}]`]({get_wiki_link(e)})**\n`┕ Official Event`" for e in formatted_events])
    
    payload = {
        "embeds": [{
            "title": "✅ Official Event Tracker",
            "color": 0x2ECC71,
            "description": active_desc
        }]
    }

    requests.post(DISCORD_WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    if DISCORD_WEBHOOK_URL:
        found = scrape_tibia_table()
        post_discord(found)
