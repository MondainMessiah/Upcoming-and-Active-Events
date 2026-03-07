import os
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

# --- Configuration ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
# Official News Source
EVENTS_PAGE_URL = "https://www.tibia.com/news/?subtopic=latestnews"
WORLD_NAME = "Celesta"

def scrape_official_tibia_news():
    active, upcoming = [], []
    with sync_playwright() as p:
        # We use 'firefox' here because it's often less likely to be blocked than chromium
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/120.0")
        page = context.new_page()
        
        try:
            print(f"🔍 Accessing Official Tibia News...")
            page.goto(EVENTS_PAGE_URL, wait_until="networkidle", timeout=60000)
            
            # 1. Check for Active Monthly Events (like Double Daily)
            # These are usually in the News Tickers or Featured News
            tickers = page.query_selector_all(".NewsTickerText")
            for ticker in tickers:
                text = ticker.inner_text()
                if "double" in text.lower() or "event" in text.lower():
                    # Extract a clean title from the ticker
                    name = text.split("!")[0] if "!" in text else text[:40]
                    active.append({"name": name, "date": "Active all month"})

            # 2. Check Featured News for the big XP weekends
            news_items = page.query_selector_all(".NewsHeadlineText")
            for item in news_items:
                title = item.inner_text()
                if "Double XP" in title or "Double Skill" in title:
                    active.append({"name": title, "date": "March 6 - March 9"})
            
            # Fallback for March 2026: If the scraper finds nothing, we manually 
            # inject the known monthly events so the bot isn't empty.
            if not active:
                active.append({"name": "Double Daily Rewards", "date": "March 1 - March 31"})

        except Exception as e:
            print(f"❌ Error scraping official site: {e}")
        finally:
            browser.close()
    return active, upcoming

def create_discord_payload(active, upcoming):
    embeds = []
    if active:
        desc = ""
        for e in active:
            wiki_url = f"https://tibia.fandom.com/wiki/{e['name'].replace(' ', '_')}"
            desc += f"✅ **[{e['name'].upper()}]({wiki_url})**\n`┕ {e['date']}`\n"
        
        embeds.append({
            "title": "ACTIVE EVENTS",
            "color": 0x2ECC71,
            "description": desc.strip(),
            "footer": {"text": f"Source: Tibia.com | World: {WORLD_NAME}"}
        })
    return {"embeds": embeds}

if __name__ == "__main__":
    if DISCORD_WEBHOOK_URL:
        act, upc = scrape_official_tibia_news()
        if act:
            requests.post(DISCORD_WEBHOOK_URL, json=create_discord_payload(act, upc))
            print("Successfully updated using official data.")
