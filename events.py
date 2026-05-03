import os
import requests
from lxml import html

# --- Configuration ---
PROXY_URL = os.environ.get("GOOGLE_BRIDGE_URL")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def get_wiki_link(name):
    return f"https://tibia.fandom.com/wiki/{name.replace(' ', '_')}"

def scrape_by_xpath():
    active, upcoming = [], []
    if not PROXY_URL:
        return active, upcoming

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(PROXY_URL, headers=headers, timeout=30)
        
        # Convert the HTML into a searchable tree
        tree = html.fromstring(response.content)
        
        # Your specific XPath location
        xpath_table = "/html/body/div[3]/div[3]/div[3]/div[5]/div/div/div[1]/div/table"
        
        # Find all event divs within that specific table
        # EventSchedule is the class name CipSoft uses for the colored bars
        events = tree.xpath(f"{xpath_table}//div[@class='EventSchedule']")

        for event in events:
            # .text_content() gets the text even if it's inside <span> tags
            name = event.text_content().strip()
            if not name: continue

            # Inspect the 'style' for 'left: 0%' to see if it's happening TODAY
            style = event.get('style', '').lower()
            
            if "left: 0%" in style or "left:0%" in style:
                active.append({"name": name, "status": "Active Now"})
            else:
                upcoming.append({"name": name, "status": "Upcoming"})

    except Exception as e:
        print(f"XPath Scraper Error: {e}")
            
    return active, upcoming

def post_discord(active, upcoming):
    if not active and not upcoming:
        print("XPath check complete: No events found at that location.")
        return

    embeds = []
    if active:
        desc = "\n".join([f"🚀 **[`[{a['name'].upper()}]`]({get_wiki_link(a['name'])})**\n`┕ {a['status']}`" for a in active])
        embeds.append({"title": "✅ Active Events", "color": 0x2ECC71, "description": desc})

    if upcoming:
        desc = "\n".join([f"⏳ **[`[{u['name'].upper()}]`]({get_wiki_link(u['name'])})**\n`┕ {u['status']}`" for u in upcoming])
        embeds.append({"title": "⏳ Upcoming Events", "color": 0x3498DB, "description": desc})

    requests.post(DISCORD_WEBHOOK_URL, json={"embeds": embeds})

if __name__ == "__main__":
    if DISCORD_WEBHOOK_URL:
        act, upc = scrape_by_xpath()
        post_discord(act, upc)
