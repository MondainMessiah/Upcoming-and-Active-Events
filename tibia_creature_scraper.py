import requests
from bs4 import BeautifulSoup

def get_boosted_creature():
    url = "https://tibia.fandom.com/wiki/Main_Page"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    # Find the first <div class="compact-box"> that is likely the Boosted Creature
    creature_box = soup.find("div", class_="compact-box")
    if creature_box:
        # Creature name and URL
        name_link = creature_box.find("b").find("a")
        creature_name = name_link.get_text(strip=True)
        creature_url = "https://tibia.fandom.com" + name_link['href']
        # Creature image
        img_tag = creature_box.find("img", alt=creature_name)
        creature_img_url = img_tag['src'] if img_tag else None
        # HP
        hp_tag = creature_box.find("span", class_="creature-stats-hp")
        hp = hp_tag.get_text(strip=True) if hp_tag else None
        # EXP (boosted)
        exp_tag = creature_box.find("span", class_="creature-stats-exp")
        exp = exp_tag.get_text(strip=True) if exp_tag else None
        return {
            "name": creature_name,
            "url": creature_url,
            "img": creature_img_url,
            "hp": hp,
            "exp": exp
        }
    return None

if __name__ == "__main__":
    creature = get_boosted_creature()
    if creature:
        print(f"Today's Boosted Creature: {creature['name']} ({creature['url']})")
        print(f"Image: {creature['img']}")
        print(f"HP: {creature['hp']} | EXP: {creature['exp']}")
    else:
        print("Could not find boosted creature.")
