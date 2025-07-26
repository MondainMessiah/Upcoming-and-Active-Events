import os
import requests
import datetime

# --- Configuration ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
EVENTS_API_URL = "https://api.tibiadraptor.com/v2/events/all"
NEWS_API_URL = "https://api.tibiadraptor.com/v2/news/latest"
NEWS_CATEGORIES_TO_CHECK = ["event", "upcoming feature"]

def fetch_api_data(url):
    """Fetches data from a given API endpoint."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None

def format_discord_message(current_events, upcoming_events):
    """Formats the combined event data into a Discord embed message."""
    
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
            "title": "Tibia Event & News Schedule",
            "description": "Combined daily report from TibiaDraptor's events and news sections.",
            "color": 3447003,  # Blue
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
        print("Successfully posted combined event schedule to Discord.")
    except requests.exceptions.RequestException as e:
        print(f"Error posting to Discord: {e}")

if __name__ == "__main__":
    if not DISCORD_WEBHOOK_URL:
        raise ValueError("FATAL: DISCORD_WEBHOOK_URL environment variable not set.")

    all_current_events = []
    all_upcoming_events = []
    seen_titles = set()

    print("Fetching from Events API...")
    events_data = fetch_api_data(EVENTS_API_URL)
    if events_data and "events" in events_data:
        for event in events_data["events"].get("current", []):
            title = event.get("name")
            if title and title not in seen_titles:
                all_current_events.append({"name": title, "detail": f"ends {event.get('end_date', 'N/A')}"})
                seen_titles.add(title)
        
        for event in events_data["events"].get("upcoming", []):
            title = event.get("name")
            if title and title not in seen_titles:
                all_upcoming_events.append({"name": title, "detail": f"starts {event.get('start_date', 'N/A')}"})
                seen_titles.add(title)

    print("Fetching from News API...")
    news_data = fetch_api_data(NEWS_API_URL)
    if news_data and "news" in news_data:
        for news_item in news_data["news"]:
            title = news_item.get("title")
            category = news_item.get("category", "").lower()
            if title and title not in seen_titles and category in NEWS_CATEGORIES_TO_CHECK:
                all_upcoming_events.append({"name": title, "detail": f"[Link]({news_item.get('url')})"})
                seen_titles.add(title)

    if not all_current_events and not all_upcoming_events:
        print("No current or upcoming events found from any source. No message will be sent.")
    else:
        print(f"Found {len(all_current_events)} current and {len(all_upcoming_events)} upcoming events/news items. Sending message...")
        all_upcoming_events.sort(key=lambda x: x['name'])
        discord_message = format_discord_message(all_current_events, all_upcoming_events)
        post_to_discord(DISCORD_WEBHOOK_URL, discord_message)
