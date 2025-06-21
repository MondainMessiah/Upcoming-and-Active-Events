import requests
from bs4 import BeautifulSoup
import os

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL") or "YOUR_WEBHOOK_URL_HERE"
WIKI_URL = "https://tibia.fandom.com/wiki/Main_Page"

def get_boosted_boss(soup):
    boss_section = soup.find("a", title="Boosted Boss")
    if boss_section:
        box = boss_section.find_next("div", class_="compact-box-boss")
        if box:
            boss_link = box.find("b").find("a")
            boss_name = boss_link.get_text(strip=True)
            boss_url = "https://tibia.fandom.com" + boss_link['href']
            boss_img_tag = box.find("img", alt=boss_name)
            boss_img_url = None
            if boss_img_tag:
                boss_img_url = boss_img_tag.get("data-src") or boss_img_tag.get("src")
            hp_tag = box.find("span", class_="creature-stats-hp")
            exp_tag = box.find("span", class_="creature-stats-exp")
            hp = hp_tag.get_text(strip=True) if hp_tag else None
            exp = exp_tag.get_text(strip=True) if exp_tag else None
            return {
                "name": boss_name,
                "url": boss_url,
                "img": boss_img_url,
                "hp": hp,
                "exp": exp
            }
    return None

def get_boosted_creature(soup):
    creature_boxes = soup.find_all("div", class_="compact-box")
    for box in creature_boxes:
        if not box.find_parent("div", class_="compact-box-boss"):
            name_link = box.find("b").find("a")
            creature_name = name_link.get_text(strip=True)
            creature_url = "https://tibia.fandom.com" + name_link['href']
            img_tag = box.find("img", alt=creature_name)
            creature_img_url = None
            if img_tag:
                creature_img_url = img_tag.get("data-src") or img_tag.get("src")
            hp_tag = box.find("span", class_="creature-stats-hp")
            exp_tag = box.find("span", class_="creature-stats-exp")
            hp = hp_tag.get_text(strip=True) if hp_tag else None
            exp = exp_tag.get_text(strip=True) if exp_tag else None
            return {
                "name": creature_name,
                "url": creature_url,
                "img": creature_img_url,
                "hp": hp,
                "exp": exp
            }
    return None

def get_rashid_location(soup):
    rashid_headline = soup.find("span", id="Rashid")
    if rashid_headline:
        portal_div = rashid_headline.find_parent("div", class_="mp-portal")
        if portal_div:
            content_div = portal_div.find("div", class_="mp-portal-content")
            if content_div:
                # Find the city link in the sentence about Rashid's location
                rashid_span = content_div.find("span")
                rashid_city, rashid_city_url = None, None
                if rashid_span:
                    # Look for <b><a> inside the span
                    bolds = rashid_span.find_all("b")
                    for b in bolds:
                        city_a = b.find("a")
                        if city_a and city_a.get("href", "").startswith("/wiki/"):
                            rashid_city = city_a.get_text(strip=True)
                            rashid_city_url = "https://tibia.fandom.com" + city_a['href']
                            break
                # Get map image thumbnail (the second <img> after Rashid's gif)
                map_img_tag = None
                imgs = content_div.find_all("img")
                if len(imgs) > 1:
                    # The first is Rashid's face, the second is the minimap
                    map_img_tag = imgs[1]
                map_img_url = map_img_tag['src'] if map_img_tag else None
                # Get map link
                map_a = content_div.find("a", string="Browse Map")
                map_url = map_a['href'] if map_a else None
                return {
                    "city": rashid_city,
                    "city_url": rashid_city_url,
                    "map_url": map_url,
                    "map_img": map_img_url
                }
    return None

def post_to_discord_with_embeds(boss, creature, rashid):
    embeds = []

    if boss:
        boss_embed = {
            "title": f"Boosted Boss: {boss['name']}",
            "url": boss["url"],
            "description": f"HP: {boss['hp']} | EXP: {boss['exp']}",
        }
        if boss["img"]:
            boss_embed["thumbnail"] = {"url": boss["img"]}
        embeds.append(boss_embed)

    if creature:
        creature_embed = {
            "title": f"Boosted Creature: {creature['name']}",
            "url": creature["url"],
            "description": f"HP: {creature['hp']} | EXP: {creature['exp']}",
        }
        if creature["img"]:
            creature_embed["thumbnail"] = {"url": creature["img"]}
        embeds.append(creature_embed)

    if rashid and rashid.get("city"):
        description = f"Rashid's Location: [{rashid['city']}]({rashid['city_url']})"
        if rashid.get("map_url"):
            description += f" ([Map Link]({rashid['map_url']}))"
        rashid_embed = {
            "description": description,
        }
        if rashid.get("map_img"):
            rashid_embed["thumbnail"] = {"url": rashid["map_img"]}
        embeds.append(rashid_embed)
    else:
        embeds.append({"description": "Rashid's Location: Not found"})

    payload = {
        "content": "**Tibia Daily Info**",
        "embeds": embeds,
        "allowed_mentions": {"parse": []}
    }

    resp = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if resp.status_code in [200, 204]:
        print("Posted to Discord successfully!")
    else:
        print(f"Failed to post: {resp.status_code} {resp.text}")

def main():
    resp = requests.get(WIKI_URL)
    if resp.status_code != 200:
        print(f"Failed to fetch wiki page: {resp.status_code}")
        return
    soup = BeautifulSoup(resp.text, "html.parser")
    boss = get_boosted_boss(soup)
    creature = get_boosted_creature(soup)
    rashid = get_rashid_location(soup)
    print("Boss:", boss)
    print("Creature:", creature)
    print("Rashid:", rashid)
    post_to_discord_with_embeds(boss, creature, rashid)

if __name__ == "__main__":
    main()
