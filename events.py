import os
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

# --- Configuration ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
EVENTS_PAGE_URL = "https://tibiadraptor.com/"
WORLD_NAME = "Celesta"
THUMBNAIL_URL = "https://wiki.tibia.com/images/3/3a/Tibia_Logo.png"

# --- Smarter Wiki Search ---

def get_tibiawiki_url(event_name):
    base_url = "https://tibia.fandom.com/wiki/"
    search_term = event_name.upper()
    
    # Mapping table for the most common TibiaDraptor terms
    name_map = {
        "DOUBLE XP": "Double_XP_and_Double_Skill",
        "DOUBLE SKILL": "Double_XP_and_Double_Skill",
        "RAPID RESPAWN": "Rapid_Respawn_and_Enhanced_Creature_Yield",
        "DOUBLE LOOT": "Double_Loot_Event",
        "DOUBLE DAILY": "Daily_Reward_System",
        "ORCSOBERFEST": "Orcsoberfest",
        "COLOURS OF MAGIC": "The_Colours_of_Magic",
        "CHYLLFROEST": "Chyllfroest",
        "UNDEAD JESTERS": "Undead_Jesters",
        "BEWDITCHED": "Bewitched",
        "ANNIVERSARY": "Tibia_Anniversary"
    }

    target_page = None
    for keyword, page in name_map.items():
        if keyword in search_term:
            target_page = page
            break
    
    if not target_page:
        # Fallback: Convert "Double XP" to "Double_XP"
        target_page = event_name.strip().replace(" ", "_").title()

    url = f"{base_url}{target_page}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        # Verify the page actually exists before linking it
        resp = requests.head(url, allow_redirects=True, timeout=3, headers=headers)
        if resp.status_code == 200:
            return url
    except:
        pass
    return None

# --- Data Fetching ---

def scrape_website_events():
    active, upcoming = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            page.goto(EVENTS_PAGE_URL, wait_until="networkidle", timeout=60000)
            
            # Scrape individual event blocks
            blocks = page.query_selector_all(".events")
            for block in blocks:
                title_el = block.query_selector(".event-title")
                date_el = block.query_selector(".dateStart")
                
                if not title_el: continue
                
                name = title_el.inner_text().strip()
                # Clean out generic headers
                if name.upper() in ["HAPPENING NOW", "UPCOMING EVENTS", ""]: continue
                
                date_text = date_el.inner_text().strip() if date_el else "Dates TBD"
                event = {"name": name, "date": date_text}

                # Sort into columns based on timer status
                if "LEFT" in date_text.upper():
                    if event not in active: active.append(event)
                else:
                    if event not in upcoming: upcoming.append(event)
        finally:
            browser.close()
    return active, upcoming

# --- Discord Formatting ---

def format_discord_message(active, upcoming):
    def create_list(events):
        if not events: return "_None right now_"
        lines = []
        for e in events:
            url = get_tibiawiki_url(e['name'])
            # Formatting the Hyperlink
            title = f"🔗 [{e['name'].upper()}]({url})" if url else f"🔹 **{e['name'].upper()}**"
            # Cleaning up the timer text for better readability
            timer = e['date'].lower().replace("!", "").replace("to start", "starts in")
            lines.append(f"{title}\n`⏳ {timer}`")
        
        # Use a divider to reduce congestion
        return "\n────────────\n".join(lines)

    # Use a clean Tibia-themed color (Emerald Green for active, Gold for upcoming)
    embed_color = 0x2ECC71 if active else 0xF1C40F

    return {
        "embeds": [{
            "title": f"🛡️ World Events: {WORLD_NAME}",
            "description": f"Current schedule for players on **{WORLD_NAME}**.",
            "url": EVENTS_PAGE_URL,
            "color": embed_color,
            "thumbnail": {"url": THUMBNAIL_URL},
            "fields": [
                {"name": "✅ ACTIVE NOW", "value": create_list(active), "inline": True},
                {"name": "⏳ UPCOMING", "value": create_list(upcoming), "inline": True}
            ],
            "footer": {
                "text": f"Updated: {datetime.now().strftime('%d %b, %H:%M')} | TibiaDraptor",
                "icon_url": "https://wiki.tibia.com/images/1/1a/Globe.gif"
            }
        }]
    }

# --- Main Execution ---

if __name__ == "__main__":
    if not DISCORD_WEBHOOK_URL:
        print("Error: Missing DISCORD_WEBHOOK_URL.")
    else:
        print(f"Scraping events for {WORLD_NAME}...")
        act, upc = scrape_website_events()
        
        if not act and not upc:
            print("No event data found.")
        else:
            payload = format_discord_message(act, upc)
            requests.post(DISCORD_WEBHOOK_URL, json=payload)
            print(f"Successfully posted {len(act) + len(upc)} events to Discord.")
