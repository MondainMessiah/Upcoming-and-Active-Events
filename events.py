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
    """Refined Wiki search for Tibia events."""
    base_url = "https://tibia.fandom.com/wiki/"
    
    # Clean the name: Title Case and underscores are what Fandom likes
    # Example: "double xp" -> "Double_XP_and_Double_Skill"
    clean_name = event_name.replace(" ", "_").title()
    
    # TibiaWiki specific overrides for common event naming mismatches
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
            # We use GET instead of HEAD because Fandom sometimes behaves better with it
            resp = requests.get(url, timeout=5, headers=headers)
            if resp.status_code == 200:
                return url
        except:
            continue
    return None

# --- Discord Formatting and Posting ---

def format_discord_message(current_events, upcoming_events):
    def format_list(events_list, default_text):
        if not events_list:
            return default_text
        formatted = []
        for event in events_list:
            url = get_tibiawiki_url(event['name'])
            # Markdown link format: [TEXT](URL)
            name_text = event['name'].upper()
            display_name = f"**[{name_text}]({url})**" if url else f"**{name_text}**"
            formatted.append(f"{display_name}\n└ *{event['detail']}*")
        return "\n".join(formatted)

    # Green (3066993) if active events exist, otherwise Gold (15105570)
    embed_color = 3066993 if current_events else 15105570

    return {
        "embeds": [{
            "title": "⚔️ Tibia Event Schedule",
            "url": EVENTS_PAGE_URL,
            "color": embed_color,
            "fields": [
                {"name": "✅ HAPPENING NOW", "value": format_list(current_events, "No active events."), "inline": False},
                {"name": "⏳ UPCOMING", "value": format_list(upcoming_events, "No scheduled events."), "inline": False}
            ],
            "footer": {"text": f"Updated: {datetime.now().strftime('%b %d, %H:%M')}"}
        }]
    }

def post_to_discord(webhook_url, message):
    try:
        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()
        print("✅ Message sent to Discord!")
    except Exception as e:
        print(f"❌ Failed to post: {e}")

# --- Main Execution Block ---

if __name__ == "__main__":
    if not DISCORD_WEBHOOK_URL:
        print("❌ Error: Set DISCORD_WEBHOOK_URL environment variable.")
        exit(1)

    # 1. Scrape the data
    # (Assuming your scrape_website_events() function remains the same)
    scraped_current, scraped_upcoming = scrape_website_events()

    # 2. Prevent the double-post bug by using the lists directly
    # No more manual appending or 'seen_names' loops needed here
    if not scraped_current and not scraped_upcoming:
        print("📭 No events found to report.")
    else:
        # 3. Format and Post
        payload = format_discord_message(scraped_current, scraped_upcoming)
        post_to_discord(DISCORD_WEBHOOK_URL, payload)
