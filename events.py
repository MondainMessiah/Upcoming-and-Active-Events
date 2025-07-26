import os
import requests
import datetime
from playwright.sync_api import sync_playwright

# --- Configuration ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
EVENTS_PAGE_URL = "https://www.tibiadraptor.com/events"

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
            page.goto(EVENTS_PAGE_URL, wait_until="domcontentloaded")

            # Scrape "Happening Now" events
            print("Scraping 'Happening Now' events...")
            happening_now_section = page.query_selector("#happening-now")
            if happening_now_section:
                events = happening_now_section.query_selector_all(".event-entry")
                for event in events:
                    name = event.query_selector("h4").inner_text()
                    current_events.append({"name": name, "detail": "Active Now"})

            # Scrape "Upcoming Events"
            print("Scraping 'Upcoming Events'...")
            upcoming_events_section = page.query_selector("#upcoming-events")
            if upcoming_events_section:
                events = upcoming_events_section.query_selector_all(".event-entry")
                for event in events:
                    name = event.query_selector("h4").inner_text()
                    countdown = event.query_selector(".text-bright").inner_text()
                    upcoming_events.append({"name": name, "detail": countdown})

        except Exception as e:
            print(f"An error occurred during scraping: {e}")
        finally:
            print("Closing browser...")
            browser.close()

    return current_events, upcoming_events

def format_discord_message(current_events, upcoming_events):
    """Formats the scraped event data into a Discord embed message."""
    def format_list(events_list, default_text):
        if not events_list:
            return default_text
        return "\n".join([f"**{event['name']}** ({event['detail']})" for event in events_list])

    current_events_text = format_list(current_events, "There are no events happening right now.")
    upcoming_events_text = format_list(upcoming_events, "There are no upcoming events scheduled.")

    fields = [
        {"name": "🔴 Happening Now", "value": current_events_text, "inline": False},
        {"name": "⏳ Upcoming Events", "value": upcoming_events_text, "inline": False}
    ]
    message = {
        "embeds": [{
            "title": "Tibia Event Schedule (Scraped)",
            "description": "Daily event report scraped directly from TibiaDraptor.com.",
            "color": 2123412,  # Green
            "fields": fields,
            "footer": {"text": f"Report generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
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
