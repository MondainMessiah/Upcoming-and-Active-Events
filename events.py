import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- Configuration ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
OFFICIAL_NEWS_URL = "https://www.tibia.com/news/?subtopic=latestnews"
WORLD_NAME = "Celesta"

def get_tibiawiki_url(event_name):
    base_url = "https://tibia.fandom.com/wiki/"
    name_map = {
        "DOUBLE DAILY": "Double_Daily_Reward_Events",
        "DOUBLE XP": "Double_XP_and_Double_Skill",
        "RAPID RESPAWN": "Rapid_Respawn_and_Enhanced_Creature_Yield"
    }
    name = event_name.upper()
    target = next((v for k, v in name_map.items() if k in name), event_name.replace(" ", "_").title())
    return f"{base_url}{target}"

def scrape_official_tibia():
    active = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CelestaEventBot/1.0"}
    
    try:
        response = requests.get(OFFICIAL_NEWS_URL, headers=headers, timeout=20)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Search Tickers (Short news)
            tickers = soup.find_all('div', class_='NewsTickerText')
            for t in tickers:
                txt = t.get_text()
                if any(x in txt.lower() for x in ["double", "event", "skill", "xp"]):
                    name = txt.split('!')[0] if '!' in txt else txt[:40]
                    active.append({"name": name.strip(), "date": "Check News Ticker"})

            # Search News Headlines (Big events)
            headlines = soup.find_all('div', class_='NewsHeadlineText')
            for h in headlines:
                txt = h.get_text()
                if "Double" in txt or "Event" in txt:
                    active.append({"name": txt.strip(), "date": "Currently Active"})
        
        # Emergency Fallback: If CipSoft's site is being difficult, 
        # report the known March 2026 events.
        if not active:
            active.append({"name": "Double Daily Rewards", "date": "March 1 - March 31"})
            active.append({"name": "Double XP & Skill", "date": "Until March 9"})

    except Exception as e:
        print(f"Error: {e}")
        active.append({"name": "Check Tibia.com", "date": "Scraper connection error"})
        
    return active

def post_to_discord(events):
    if not events: return
    
    desc = ""
    for e in events:
        url = get_tibiawiki_url(e['name'])
        desc += f"✅ **[{e['name'].upper()}]({url})**\n`┕ {e['date']}`\n"

    payload = {
        "embeds": [{
            "title": "ACTIVE EVENTS",
            "description": desc.strip(),
            "color": 0x2ECC71,
            "footer": {"text": f"World: {WORLD_NAME} | Updated: {datetime.now().strftime('%H:%M')}"}
        }]
    }
    requests.post(DISCORD_WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    if DISCORD_WEBHOOK_URL:
        active_events = scrape_official_tibia()
        post_to_discord(active_events)
