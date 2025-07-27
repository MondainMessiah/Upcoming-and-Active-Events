import os
import requests
import datetime
import re
from playwright.sync_api import sync_playwright, TimeoutError

# --- Configuration ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
EVENTS_PAGE_URL = "https://tibiadraptor.com/"

def get_tibiawiki_url(event_name):
    """Checks for a TibiaWiki page, trying both a base and a /Spoiler URL."""
    
    # --- NEW: Convert event name to Title Case to match wiki URL format ---
    event_name_title_case = event_name.title()
    
    base_url = "https://tibia.fandom.com/wiki/"
    # Remove special characters and replace spaces with underscores for the URL
    safe_name = re.sub(r"[^\w\s]", "", event_name_title_case)
    safe_name = safe_name.replace(" ", "_")
    
    # List of URLs to check, with the /Spoiler version first.
    urls_to_try = [
        base_url + safe_name + "/Spoiler",
        base_url + safe_name
    ]
    
    for url in urls_to_try:
        try:
            resp = requests.head(url, allow_redirects=True, timeout=5)
            if resp.status_code == 200:
                print(f"Found valid wiki link: {resp.url}")
                return resp.url
        except requests.exceptions.RequestException:
            continue
            
    print(f"No valid wiki link found for {event_name}.")
    return None

def scrape_tibia_events():
    """Launches a browser to scrape event data directly from the website."""
    current_events = []
    upcoming_events = []

    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch()
        page = browser.new_page()
        
        try:
            print(f"Navigating to {EVENTS_PAGE_URL}...")
            page.goto(EVENTS_PAGE_URL)

            print("Waiting for events container to load...")
            page.wait_for_selector("div.events-container", timeout=60000)
            print("Events container found.")
            
            main_container = page.query_selector("div.events-container")
            if main_container:
                print("Waiting for event content to appear inside container...")
                main_container.wait_for_selector(".event-title", timeout=15000)
                print("Event content appeared. Now scraping...")

                event_blocks = main_container.query_selector_all("div.events")
                print(f"Found {len(event_blocks)} event block(s).")
                
                for block in event_blocks:
                    countdown_element = block.query_selector(".dateStart")
                    title_element = block.query_selector(".event-title")
                    
                    if countdown_element and title_element:
                        name = title_element.inner_text().strip()
                        detail = countdown_element.inner_text().strip()
                        
                        print(f"Scraped Upcoming Event: {name}")
                        upcoming_events.append({"name": name, "detail": detail})
            else:
                print("Could not find the main 'events-container' on the page.")

        except TimeoutError as e:
            print(f"Timed out waiting for content: {e}")
            page.screenshot(path="debug_screenshot.png")
            
        except Exception as e:
            print(f"An error occurred during scraping: {e}")
        finally:
            print("Closing browser...")
            browser.close()

    return current_events, upcoming_events

def format_discord_message(current_events, upcoming_events):
    """Formats the scraped event data into a Discord embed message with Wiki links."""
    def format_list(events_list, default_text):
        if not events_list:
            return default_text
        
        formatted_events = []
        for event in events_list:
            wiki_url = get_tibiawiki_url(event['name'])
            if wiki_url:
                display_name = f"[{event['name']}]({wiki_url})"
            else:
                display_name = event['name']
            formatted_events.append(f"**{display_name}** ({event['detail']})")
        return "\n".join(formatted_events)
    
    current_events_text = format_list(current_events, "There are no events happening right now.")
    upcoming_events_text = format_list(upcoming_events, "There are no upcoming events scheduled.")

    fields = [
        {"name": "✅ Happening Now", "value": current_events_text, "inline": False},
        {"name": "⏳ Upcoming Events", "value": upcoming_events_text, "inline": False}
    ]
    message = {
        "embeds": [{
            "title": "Tibia Event Schedule",
            "fields": fields,
            "footer": {
                "text": f"Report generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        }]
    }
    return message

def post_to_discord(webhook_url, message):
    """Posts the formatted message to the Discord webhook."""
    try:
        response = requests.post(webhook_url, json=message)
        response.raise_for_status()
        print("Successfully posted event schedule to Discord.")
    except requests.exceptions.RequestException as e:
        print(f"Error posting to Discord: {e}")

if __name__ == "__main__":
    if not DISCORD_WEBHOOK_URL:
        raise ValueError("FATAL: DISCORD_WEBHOOK_URL environment variable not set.")

    current, upcoming = scrape_tibia_events()

    if not current and not upcoming:
        print("No events found on the webpage. No message will be sent.")
    else:
        print(f"Found {len(current)} current and {len(upcoming)} upcoming events. Sending message...")
        discord_message = format_discord_message(current, upcoming)
        post_to_discord(DISCORD_WEBHOOK_URL, discord_message)
