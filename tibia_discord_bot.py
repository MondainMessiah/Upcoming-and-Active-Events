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
            boss_img_url = boss_img_tag['src'] if boss_img_tag else None
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
            creature_img_url = img_tag['src'] if img_tag else None
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
            city_bold = content_div.find("b")
            rashid_city = None
            rashid_city_url = None
            if city_bold and city_bold.find("a"):
                city_a = city_bold.find("a")
                rashid_city = city_a.get_text(strip=True)
                rashid_city_url = "https://tibia.fandom.com" + city_a['href']
            map_link = content_div.find("a", string="Browse Map")
            map_url = map_link['href'] if map_link else None
            return {
                "city": rashid_city,
                "city_url": rashid_city_url,
                "map_url": map_url
            }
    return None

def make_discord_message(boss, creature, rashid):
    lines = ["**Tibia Daily Info**"]
    if boss:
        boss_line = f"🧙 **Boosted Boss**: [{boss['name']}]({boss['url']})"
        if boss['img']:
            boss_line += f"\n{boss['img']}"
        if boss['hp'] and boss['exp']:
            boss_line += f"\nHP: {boss['hp']} | EXP: {boss['exp']}"
        lines.append(boss_line)
    else:
        lines.append("🧙 **Boosted Boss**: Not found")
    if creature:
        creature_line = f"🐾 **Boosted Creature**: [{creature['name']}]({creature['url']})"
        if creature['img']:
            creature_line += f"\n{creature['img']}"
        if creature['hp'] and creature['exp']:
            creature_line += f"\nHP: {creature['hp']} | EXP: {creature['exp']}"
        lines.append(creature_line)
    else:
        lines.append("🐾 **Boosted Creature**: Not found")
    if rashid and rashid['city']:
        rashid_line = f"🧳 **Rashid's Location**: [{rashid['city']}]({rashid['city_url']})"
        if rashid['map_url']:
            rashid_line += f" ([Map Link]({rashid['map_url']}))"
        lines.append(rashid_line)
    else:
        lines.append("🧳 **Rashid's Location**: Not found")
    return "\n\n".join(lines)

def post_to_discord(message):
    payload = {
        "content": message,
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
    message = make_discord_message(boss, creature, rashid)
    post_to_discord(message)

if __name__ == "__main__":
    main()
