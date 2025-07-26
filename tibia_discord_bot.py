import os
import requests
import datetime

# --- Configuration ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
TIBIADRAPTOR_EVENTS_API_URL = "https://api.tibiadraptor.com/v2/events/all"

def get_tibia_events():
    """Fetches current and upcoming events from the TibiaDraptor API."""
    try:
        response = requests.get(TIBIADRAPTOR_EVENTS_API_URL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching event data from TibiaDraptor: {e}")
        return None

def format_event_field(events, event_type):
    """Formats a list of events into a single string for a Discord field."""
    if not events:
        return f"There are no {event_type} events right now."
    events.sort(key=lambda x: x.get('start_date', ''))
    formatted_list = [
        f"**{event.get('name', 'Unknown Event')}** (ends {event.get('end_date', 'N/A')})"
        for event in events
    ]
    return "\n".join(formatted_list)

def format_upcoming_event_field(events):
    """Formats upcoming events, including the start date."""
    if not events:
        return "There are no upcoming events scheduled."
    events.sort(key=lambda x: x.get('start_date', ''))
    formatted_list = [
        f"**{event.get('name', 'Unknown Event')}** (starts {event.get('start_date', 'N/A')})"
        for event in events
    ]
    return "\n".join(formatted_list)

def format_discord_message(events_data):
    """Formats the event data into a Discord embed message."""
    current_events = events_data.get("events", {}).get("current", [])
    upcoming_events = events_data.get("events", {}).get("upcoming", [])

    fields = [
        {
            "name": "🔴 Happening Now",
            "value": format_event_field(current_events, "current"),
            "inline": False
        },
        {
            "name": "⏳ Upcoming Events",
            "value": format_upcoming_event_field(upcoming_events),
            "inline": False
        }
    ]

    message = {
        "embeds": [{
            "title": "Tibia Event Schedule",
            "description": "Here is the current and upcoming event schedule from TibiaDraptor.",
            "color": 5814783,
            "fields": fields,
            "footer": {
                "text": f"Report generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        }]
    }
    return message

def post_to_discord(webhook_url, message):
    """Posts the formatted message to the Discord webhook."""
    if not message:
        print("No message to post.")
        return
    try:
        response = requests.post(webhook_url, json=message)
        response.raise_for_status()
        print("Successfully posted event schedule to Discord.")
    except requests.exceptions.RequestException as e:
        print(f"Error posting to Discord: {e}")
        print(f"Response Body: {e.response.text if e.response else 'No Response'}")

# --- Main Execution Block ---
if __name__ == "__main__":
    if not DISCORD_WEBHOOK_URL:
        raise ValueError("FATAL: DISCORD_WEBHOOK_URL environment variable not set.")

    print("Fetching Tibia event schedule...")
    events_json = get_tibia_events()

    if events_json and "events" in events_json:
        current_events = events_json["events"].get("current", [])
        upcoming_events = events_json["events"].get("upcoming", [])

        # --- MODIFICATION ---
        # Only proceed if there is at least one current or upcoming event
        if not current_events and not upcoming_events:
            print("No current or upcoming events found. No message will be sent.")
        else:
            print("Events found. Formatting and sending message...")
            discord_message = format_discord_message(events_json)
            post_to_discord(DISCORD_WEBHOOK_URL, discord_message)
    else:
        print("Could not retrieve or parse events from the API.")
