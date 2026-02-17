import os
import requests
import re
import time
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# --- Configuration ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
EVENTS_PAGE_URL = "https://tibiadraptor.com/"
EVENT_KEYWORDS = ["rapid respawn", "double xp and double skill", "double loot"]

# --- Helper Functions ---

def get_tibiawiki_url(event_name):
    """Checks for a TibiaWiki page using various formatting approaches."""
    base_url = "https://tibia.fandom.com/wiki/"

    def clean_name_for_url(name):
        return re.sub(r"[^\w\s]", "", name).replace(" ", "_")

    def to_title_case_for_wiki(s):
        small_words = {'a', 'an', 'the', 'of', 'in', 'on', 'and', 'for', 'with', 'to', 'from', 'but', 'or', 'nor', 'yet', 'so'}
        words = s.lower().split()
        if not words:
            return ""
        capitalized_words = [words[0].capitalize()] + \
                            [word if word in small_words else word.capitalize() for word in words[1:]]
        return " ".join(capitalized_words)

    name_variations = [
        event_name,
        to_title_case_for_wiki(event_name),
        event_name.lower()
    ]

    safe_name_variations = list(set(clean_name_for_url(nv) for nv in name_variations))

    urls_to_try = []
    for safe_name in safe_name_variations:
        urls_to_try.append(f"{base_url}{safe_name}/Spoiler")
        urls_to_try.append(f"{base_url}{safe_name}")

    urls_to_try = list(dict.fromkeys(urls_to_try))

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
    
    # Define multiple selector strategies to handle website structure changes
    selector_strategies = [
        # Strategy 1: Original selectors
        {
            "container": "div.events-container",
            "blocks": "div.events",
            "title": ".event-title",
            "detail": ".dateStart",
            "name": "Original Selectors"
        },
        # Strategy 2: Alternative selectors
        {
            "container": "div[class*='event']",
            "blocks": "div[class*='event-item']",
            "title": "[class*='title']",
            "detail": "[class*='date']",
            "name": "Alternative Selectors (v1)"
        },
        # Strategy 3: Simpler approach
        {
            "container": "main, article, [role='main']",
            "blocks": "div[class*='event'], li[class*='event']",
            "title": "h2, h3, h4, [class*='title']",
            "detail": "[class*='date'], [class*='time'], span",
            "name": "Flexible Selectors (v2)"
        }
    ]
    
    with sync_playwright() as p:
        print("▶️ Starting website scrape...")
        browser = p.chromium.launch()
        page = browser.new_page()
        
        try:
            print(f"Loading {EVENTS_PAGE_URL}...")
            page.goto(EVENTS_PAGE_URL, wait_until="domcontentloaded", timeout=60000)
            
            # Wait for page to be interactive
            page.wait_for_load_state("networkidle", timeout=30000)
            
            success = False
            
            for strategy in selector_strategies:
                if success:
                    break
                    
                print(f"\n📋 Trying {strategy['name']}...")
                try:
                    # Try to find container
                    containers = page.query_selector_all(strategy["container"])
                    
                    if not containers:
                        print(f"   ❌ No containers found with '{strategy['container']}'")
                        continue
                    
                    print(f"   ✓ Found {len(containers)} container(s)")
                    
                    # Look for event blocks
                    for container in containers:
                        try:
                            # Wait for blocks to appear
                            container.wait_for_selector(strategy["blocks"], timeout=10000)
                            event_blocks = container.query_selector_all(strategy["blocks"])
                            
                            if event_blocks:
                                print(f"   ✓ Found {len(event_blocks)} event block(s)")
                                
                                for block in event_blocks:
                                    try:
                                        # Try to extract title
                                        title_el = block.query_selector(strategy["title"])
                                        if not title_el:
                                            continue
                                        
                                        name = title_el.inner_text().strip()
                                        
                                        # Try to extract detail
                                        detail = ""
                                        detail_el = block.query_selector(strategy["detail"])
                                        if detail_el:
                                            detail = detail_el.inner_text().strip()
                                        
                                        if name:  # Only add if we have at least a name
                                            event = {"name": name, "detail": detail or "Event details unavailable", "source": "Website"}
                                            
                                            # Categorize by keywords
                                            if detail:
                                                if "LEFT" in detail.upper():
                                                    current_events.append(event)
                                                elif "TO START" in detail.upper() or "START" in detail.upper():
                                                    upcoming_events.append(event)
                                                else:
                                                    # If detail doesn't have clear indicator, default to upcoming
                                                    upcoming_events.append(event)
                                            else:
                                                # Default to upcoming if no detail
                                                upcoming_events.append(event)
                                                
                                            print(f"   ✓ Found event: {name} ({detail[:30]}...)")
                                    
                                    except Exception as e:
                                        print(f"   ⚠️  Error extracting from block: {str(e)[:60]}")
                                        continue
                                
                                if current_events or upcoming_events:
                                    success = True
                                    break
                        
                        except Exception as e:
                            print(f"   ⚠️  Container processing error: {str(e)[:60]}")
                            continue
                
                except Exception as e:
                    print(f"   ❌ Strategy failed: {str(e)[:60]}")
                    continue
            
            if not success:
                print("\n⚠️  No events found with standard selectors. Saving page screenshot for debugging...")
                try:
                    page.screenshot(path="debug_screenshot.png")
                    print("   Saved: debug_screenshot.png")
                except Exception as e:
                    print(f"   Could not save screenshot: {e}")
                
                # Fallback: try to find ANY text that looks like an event
                print("\n🔍 Attempting fallback text search...")
                page_text = page.content()
                if "double xp" in page_text.lower() or "rapid respawn" in page_text.lower() or "double loot" in page_text.lower():
                    print("   ✓ Found event keywords in page content!")
                    # You might want to extract these, but for now just note they exist
        
        except Exception as e:
            print(f"❌ Error during website scrape: {e}")
            try:
                page.screenshot(path="debug_screenshot.png")
            except:
                pass
        
        finally:
            browser.close()
    
    return current_events, upcoming_events

# --- Discord Formatting and Posting ---

def format_discord_message(current_events, upcoming_events):
    """Formats the combined event data into a Discord embed message."""
    def format_list(events_list, default_text):
        if not events_list:
            return default_text
        formatted = []
        for event in events_list:
            wiki_url = get_tibiawiki_url(event['name'])
            display_text = event['name']
            display_name = f"[{display_text.upper()}]({wiki_url})" if wiki_url else display_text.upper()
            formatted.append(f"**{display_name}** ({event['detail']})")
        return "\n".join(formatted)

    fields = [
        {"name": "✅ Active Now", "value": format_list(current_events, "No current events found."), "inline": False},
        {"name": "⏳ Upcoming Events", "value": format_list(upcoming_events, "No upcoming events scheduled."), "inline": False}
    ]
    return {
        "embeds": [{
            "title": "Tibia Events",
            "color": 3447003,
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

    print("=" * 60)
    print("TIBIA EVENTS SCRAPER")
    print("=" * 60)
    
    scraped_current, scraped_upcoming = scrape_website_events()

    final_current_events = scraped_current
    final_upcoming_events = scraped_upcoming
    seen_names = set(event['name'].lower() for event in final_upcoming_events)

    for event in scraped_current:
        if event['name'].lower() not in seen_names:
            final_current_events.append(event)
            seen_names.add(event['name'].lower())

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Current Events Found: {len(final_current_events)}")
    print(f"Upcoming Events Found: {len(final_upcoming_events)}")
    print("=" * 60)

    if not final_current_events and not final_upcoming_events:
        print("\n⚠️  No events found from any source. No message will be sent.")
    else:
        print(f"\nFound {len(final_current_events)} current and {len(final_upcoming_events)} upcoming events. Sending message...")
        final_current_events.sort(key=lambda x: x['name'])
        discord_message = format_discord_message(final_current_events, final_upcoming_events)
        post_to_discord(DISCORD_WEBHOOK_URL, discord_message)
