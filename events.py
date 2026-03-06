import os
import requests
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

# --- Configuration ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
EVENTS_PAGE_URL = "https://tibiadraptor.com/"

# --- Helper Functions ---

def get_tibiawiki_url(event_name):
    """Refined Wiki search with specific Tibia terminology overrides."""
    base_url = "https://tibia.fandom.com/wiki/"
    
    # Standardize the name for URL format
    clean_name = event_name.replace(" ", "_").title()
    
    # Map common Tibiadraptor names to exact TibiaWiki page titles
    overrides = {
        "Double_Xp": "Double_XP_and_Double_Skill",
        "Double_Xp_And_Double_Skill": "Double_XP_and_Double_Skill",
        "Rapid_Respawn": "Rapid_Respawn_and_Enhanced_Creature_Yield",
        "Double_Loot": "Double_Loot_Event"
    }
    
    lookup_name = overrides.get(clean_name, clean_name)
    urls_to_try = [f"{base_url}{lookup_name}", f"{base_url}{lookup_name}/Spoiler"]

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    for url in urls_to_try:
        try:
            resp = requests.get(url, timeout=5, headers=headers)
            if resp.status_code == 200:
                return url
        except:
            continue
    return None

# --- Data Fetching Function ---

def scrape_website_events():
    """Launches a browser to scrape event data directly from tibiadraptor.com."""
    current_events, upcoming_events = [], []
    
    selector_strategies = [
        {"container": "div.events-container", "blocks": "div.events", "title": ".event-title", "detail": ".dateStart"},
        {"container": "div[class*='event']", "blocks": "div[class*='event-item']", "title": "[class*='title']", "detail": "[class*='date']"}
    ]
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        try:
            page.goto(EVENTS_PAGE_URL, wait_until="networkidle", timeout=60000)
            
            for strategy in selector_strategies:
                containers = page.query_selector_all(strategy["container"])
                if not containers: continue
                
                for container in containers:
                    event_blocks = container.query_selector_all(strategy["blocks"])
                    for block in event_blocks:
                        title_el = block.query_selector(strategy["title"])
                        if not title_el: continue
                        
                        name = title_el.inner_text().strip()
                        if name.upper() == "HAPPENING NOW": continue
                        
                        detail_el = block.query_selector(strategy["detail"])
                        detail = detail_el.inner_text().strip() if detail_el else "Check website for dates"
                        
                        event = {"name": name, "detail": detail}
                        
                        # Sort into Active vs Upcoming
                        if "LEFT" in detail.upper():
                            current_events.append(event)
                        else:
                            upcoming_events.append(event)
                
                if current_events or upcoming_events:
                    break # Success, stop trying strategies
                    
        except Exception as e:
            print(f"❌ Scrape Error: {e}")
        finally:
            browser.close()
    
    return current_events, upcoming_events

# --- Discord Formatting and Posting ---

def format_discord_message(current_events, upcoming_events):
    def format_list(events_list, default_text):
        if not events_list:
            return default_text
        formatted = []
        for event in events_list:
            url = get_tibiawiki_url(event['name'])
            name_text = event['name'].upper()
            display_name = f"**[{name_text}]({url})**" if url else f"**{name_text}**"
            formatted.append(f"{display_name}\n└ *{event['detail']}*")
        return "\n".join(formatted)

    embed_color = 3066993 if current_events else 15105570

    return {
        "embeds": [{
            "title": "⚔️ Tibia Event Schedule",
            "url": EVENTS_PAGE_URL,
            "color": embed_color,
            "fields": [
                {"name": "✅ ACTIVE NOW", "value": format_list(current_events, "No active events."), "inline": False},
                {"name": "⏳ UPCOMING", "value": format_list(upcoming_events, "No scheduled events."), "inline": False}
            ],
            "footer": {"text": f"Updated: {datetime.now().strftime('%b %d, %H:%M')}"}
        }]
    }

def post_to_discord(webhook_url, message):
    try:
        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()
        print("✅ Success: Discord notified.")
    except Exception as e:
        print(f"❌ Discord Error: {e}")

# --- Main Execution ---

if __name__ == "__main__":
    if not DISCORD_WEBHOOK_URL:
        print("❌ Error: Missing DISCORD_WEBHOOK_URL env variable.")
    else:
        scraped_current, scraped_upcoming = scrape_website_events()

        if not scraped_current and not scraped_upcoming:
            print("📭 No events found.")
        else:
            # Sort for cleaner look
            scraped_current.sort(key=lambda x: x['name'])
            scraped_upcoming.sort(key=lambda x: x['name'])
            
            payload = format_discord_message(scraped_current, scraped_upcoming)
            post_to_discord(DISCORD_WEBHOOK_URL, payload)
