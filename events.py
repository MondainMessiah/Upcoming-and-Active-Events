import os
import re
import requests
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
TARGET_TIBIA_URL = "https://www.tibia.com/news/?subtopic=eventcalendar"

def get_wiki_link(name):
    clean_name = name.replace("XP/Skill Event", "Double XP and Skill").replace("'", "").replace(" ", "_")
    return f"https://tibia.fandom.com/wiki/{clean_name}"

def scrape_tibia_windows():
    events = set()
    try:
        print("Deploying Windows-Native Browser + Stealth to bypass Cloudflare...")
        
        with Stealth().use_sync(sync_playwright()) as p:
            # We can run headless=True on Windows because the OS fingerprint is trusted
            browser = p.chromium.launch(
                headless=True, 
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            page.goto(TARGET_TIBIA_URL, timeout=60000)
            print(f"DEBUG: Initial Page Title -> {page.title()}")
            
            print("Waiting for the calendar to render (up to 45s)...")
            page.wait_for_selector("#eventscheduletable", timeout=45000)
            print("SUCCESS! We bypassed Cloudflare!")
            
            calendar_html = page.inner_html("#eventscheduletable")
            
            bar_pattern = r'<div style="background:#[a-zA-Z0-9]+;[^>]*>\s*\*?(.*?)\s*</div>'
            found_bars = re.findall(bar_pattern, calendar_html, re.IGNORECASE)

            for match in found_bars:
                clean_name = match.strip()
                if clean_name and len(clean_name) > 2:
                    events.add(clean_name)
                    
            browser.close()

    except Exception as e:
        print(f"Scraper Error: {e}")
            
    return sorted(list(events))

def post_discord(events):
    if not events:
        print("Final Status: No colored event bars found.")
        return

    active_desc = "\n".join([f"🚀 **[`[{e.upper()}]`]({get_wiki_link(e)})**\n`┕ Official Calendar`" for e in events])
    
    payload = {
        "embeds": [{
            "title": "✅ Official Event Tracker",
            "color": 0x2ECC71,
            "description": active_desc
        }]
    }

    requests.post(DISCORD_WEBHOOK_URL, json=payload)
    print("Discord payload sent successfully.")

if __name__ == "__main__":
    if DISCORD_WEBHOOK_URL:
        results = scrape_tibia_windows()
        post_discord(results)
