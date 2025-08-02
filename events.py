import os
import requests
import re
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError

# --- Configuration ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
EVENTS_PAGE_URL = "https://tibiadraptor.com/"
# CORRECTED: Using the more reliable 'latest' news endpoint instead of the ticker
NEWS_API_URL = "https://api.tibiaapi.com/v4/news/latest" 
EVENT_KEYWORDS = ["rapid respawn", "double xp and double skill", "double loot"]

# --- Helper Functions ---

def get_tibiawiki_url(event_name):
    """Checks for a TibiaWiki page using custom title case formatting."""
    def to_title_case_custom(s):
        small_words = {'a', 'an', 'the', 'of', 'in', 'on', 'and'}
        words = s.lower().split()
        capitalized_words = [words[0].capitalize()] + \
                            [word if word in small_words else word.capitalize() for word in words[1:]]
        return " ".join(capitalized_words)

    event_name_formatted = to_title_case_custom(event_name)
    base_url = "https://tibia.fandom.com/wiki/"
    safe_name = re.sub(r"[^\w\s]", "", event_name_formatted).replace(" ", "_")
    
    urls_to_try = [f"{base_url}{safe_name}/Spoiler", f"{base_url}{safe_name}"]
    
    for url in urls_to_try:
        try:
            resp = requests.head(url, allow_redirects=True, timeout=5)
            if resp.status_code == 200:
                print(f"Found valid wiki link: {resp.url}")
                return resp.url
        except requests.exceptions.RequestException:
            continue
    print(f"No valid wiki link found for '{event_name}'.")
    return None

# --- Data Fetching Functions ---

def scrape_website_events():
    """Launches a browser to scrape event data directly from tibiadraptor.com."""
    current_events, upcoming_events = [], []
    with sync_playwright() as p:
        print("▶️ Starting website scrape...")
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            page.goto(EVENTS_PAGE_URL)
            page.wait_for_selector("div.events-container", timeout=60000)
            main_container = page.query_selector("div.events-container")
            if main_container:
                main_container.wait_for_selector(".event-title", timeout=15000)
                event_blocks = main_container.query_selector_all("div.events")
                print(f"Found {len(event_blocks)} event block(s) on website.")
                for block in event_blocks:
                    title_el = block.query_selector(".event-title")
                    countdown_el = block.query_selector(".dateStart")
                    if title_el and countdown_el:
                        name = title_el.inner_text().strip()
                        detail = countdown_el.inner_text().strip()
                        event = {"name": name, "detail": detail, "source": "Website"}
                        if "LEFT" in detail.upper():
                            current_events.append(event)
                        elif "TO START" in detail.upper():
                            upcoming_events.append(event)
        except Exception as e:
            print(f"❌ Error during website scrape: {e}")
        finally:
            browser.close()
    return current_events, upcoming_events

def fetch_api_events():
    """Fetches event announcements from the main TibiaAPI news list."""
    api_events = []
    print(f"\n▶️ Starting API fetch from: {NEWS_API_URL}")
    try:
        response = requests.get(NEWS_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and "news" in data:
            print(f"API returned {len(data['news'])} news articles. Searching for keywords...")
            for item in data["news"]:
                # Check both title and content for the event
                content_to_check = (item.get("title", "") + " " + item.get("content", "")).lower()
                matched_keyword = next((k for k in EVENT_KEYWORDS if k in content_to_check), None)
                
                if matched_keyword:
                    name = matched_keyword.title()
                    print(f"✅ Found API Event: '{name}' in news item ID {item.get('id')}")
                    api_events.append({
                        "name": name,
                        "detail": "Active this weekend!",
                        "source": "API"
                    })
                    # Stop after finding the first one to avoid duplicates from the same announcement
                    break 
        else:
            print("API response did not contain a 'news' section.")
    except Exception as e:
        print(f"❌ Error during API fetch: {e}")
    return api_events

# --- Discord Formatting and Posting ---

def format_discord_message(current_events, upcoming_events):
    """Formats the combined event data into a Discord embed message."""
    def format_list(events_list, default_text):
        if not events_list:
            return default_text
        formatted = []
        for event in events_list:
            wiki_url = get_tibiawiki_url(event['name'])
            display_name = f"[{event['name']}]({wiki_url})" if wiki_url else event['name']
            formatted.append(f"**{display_name.upper()}** ({event['detail']})")
        return "\n".join(formatted)

    fields = [
        {"name": "✅ Happening Now", "value": format_list(current_events, "No current events found."), "inline": False},
        {"name": "⏳ Upcoming Events", "value": format_list(upcoming_events, "No upcoming events scheduled."), "inline": False}
    ]
    return {
        "embeds": [{
            "title": "Tibia Event Schedule,
            "color": 3447003, # Blue
            "fields": fields,
            "footer": {"text": f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
        }]
    }

def post_to_discord(webhook_url, message):
    """Posts the formatted message to the Discord webhook."""
    try:
        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()
        print("\n✅ Successfully posted combined event schedule to Discord!")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error posting to Discord: {e}")

# --- Main Execution Block ---

if __name__ == "__main__":
    if not DISCORD_WEBHOOK_URL:
        raise ValueError("FATAL: DISCORD_WEBHOOK_URL environment variable not set.")

    scraped_current, scraped_upcoming = scrape_website_events()
    api_current = fetch_api_events()

    final_current_events = []
    final_upcoming_events = scraped_upcoming
    seen_names = set(event['name'].lower() for event in final_upcoming_events)

    for event in scraped_current:
        if event['name'].lower() not in seen_names:
            final_current_events.append(event)
            seen_names.add(event['name'].lower())
    
    for event in api_current:
        if event['name'].lower() not in seen_names:
            final_current_events.append(event)
            seen_names.add(event['name'].lower())

    if not final_current_events and not final_upcoming_events:
        print("\nNo events found from any source. No message will be sent.")
    else:
        print(f"\nFound {len(final_current_events)} current and {len(final_upcoming_events)} upcoming events. Sending message...")
        final_current_events.sort(key=lambda x: x['name'])
        discord_message = format_discord_message(final_current_events, final_upcoming_events)
        post_to_discord(DISCORD_WEBHOOK_URL, discord_message)
