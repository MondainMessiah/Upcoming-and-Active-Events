import os
import requests
import datetime
from playwright.sync_api import sync_playwright, TimeoutError

# --- Configuration ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
EVENTS_PAGE_URL = "https://tibiadraptor.com/"

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

            # Wait for the main events container to appear on the page
            print("Waiting for events container to load...")
            page.wait_for_selector("div.events-container", timeout=60000)
            print("Events container found. Now scraping...")
            
            # Scope our search to the main events container
            main_container = page.query_selector("div.events-container")
            if main_container:
                # Find all individual event blocks
                event_blocks = main_container.query_selector_all("div.events")
                print(f"Found {len(event_blocks)} event block(s).")
                
                for block in event_blocks:
                    # Check if it's an upcoming event by looking for the countdown timer
                    countdown_element = block.query_selector(".dateStart")
                    title_element = block.query_selector(".event-title")
                    
                    if countdown_element and title_element:
                        name = title_element.inner_text().strip()
                        detail = countdown_element.inner_text().strip()
                        
                        print(f"Scraped Upcoming Event: {name}")
                        upcoming_events.append({"name": name, "detail": detail})
            else:
                print("Could not find the main 'events-container' on the page.")

        except TimeoutError:
            print("Timed out waiting for event content. The page structure may have changed.")
            page.screenshot(path="debug_screenshot.png")
            
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
            "color": 2123412,
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
