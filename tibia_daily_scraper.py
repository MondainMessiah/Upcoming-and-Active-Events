import requests
from bs4 import BeautifulSoup
import os

# Set your Discord webhook URL here or via environment variable for security
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL") or "YOUR_WEBHOOK_URL_HERE"

def scrape_tibia_fandom():
    url = "https://tibia.fandom.com/wiki/Main_Page"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    # Boosted Boss
    boosted_boss = None
    boss_img = soup.find("img", alt=lambda x: x and "Boosted Boss" in x)
    if boss_img and boss_img.parent.name == "a":
        boosted_boss = boss_img.parent.get("title")
    if not boosted_boss:
        boss_span = soup.find("span", string=lambda x: x and "Boosted Boss" in x)
        if boss_span and boss_span.parent.find("a"):
            boosted_boss = boss_span.parent.find("a").get("title")

    # Boosted Creature
    boosted_creature = None
    creature_img = soup.find("img", alt=lambda x: x and "Boosted Creature" in x)
    if creature_img and creature_img.parent.name == "a":
        boosted_creature = creature_img.parent.get("title")
    if not boosted_creature:
        creature_span = soup.find("span", string=lambda x: x and "Boosted Creature" in x)
        if creature_span and creature_span.parent.find("a"):
            boosted_creature = creature_span.parent.find("a").get("title")

    # Rashid Location
    rashid_location = None
    rashid_section = soup.find("a", title="Rashid")
    if rashid_section:
        location_text = rashid_section.find_next("span", {"style": lambda x: x and "font-weight:bold" in x})
        if location_text:
            rashid_location = location_text.get_text(strip=True)
    if not rashid_location:
        rashid_span = soup.find("span", string=lambda x: x and "Rashid's Location" in x)
        if rashid_span:
            next_bold = rashid_span.find_next("b")
            if next_bold:
                rashid_location = next_bold.get_text(strip=True)

    return boosted_boss, boosted_creature, rashid_location

def post_to_discord(boss, creature, rashid):
    lines = []
    if boss:
        lines.append(f"🧙 **Boosted Boss**: {boss}")
    else:
        lines.append("🧙 **Boosted Boss**: Not found")
    if creature:
        lines.append(f"🐾 **Boosted Creature**: {creature}")
    else:
        lines.append("🐾 **Boosted Creature**: Not found")
    if rashid:
        lines.append(f"🧳 **Rashid's Location**: {rashid}")
    else:
        lines.append("🧳 **Rashid's Location**: Not found")

    message = "Tibia Daily Info\n" + "\n".join(lines)
    payload = {"content": message}
    resp = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if resp.status_code in [200, 204]:
        print("Posted to Discord successfully!")
    else:
        print(f"Failed to post: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    boss, creature, rashid = scrape_tibia_fandom()
    print("Boosted Boss:", boss)
    print("Boosted Creature:", creature)
    print("Rashid's Location:", rashid)
    post_to_discord(boss, creature, rashid)
