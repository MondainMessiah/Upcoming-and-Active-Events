import requests
from bs4 import BeautifulSoup

def get_boosted_boss():
    url = "https://tibia.fandom.com/wiki/Main_Page"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    # Look for the "Today's Boosted Boss" section
    boss_section = soup.find("a", title="Boosted Boss")
    if boss_section:
        # The boss name is in the next <b><a ...> tag inside a <div class="compact-box-boss">
        box = boss_section.find_next("div", class_="compact-box-boss")
        if box:
            boss_link = box.find("b").find("a")
            boss_name = boss_link.get_text(strip=True)
            boss_url = "https://tibia.fandom.com" + boss_link['href']
            boss_img_tag = box.find("img", alt=boss_name)
            boss_img_url = boss_img_tag['src'] if boss_img_tag else None
            # Optionally extract HP/EXP if needed
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

if __name__ == "__main__":
    boss = get_boosted_boss()
    if boss:
        print(f"Today's Boosted Boss: {boss['name']} ({boss['url']})")
        print(f"Image: {boss['img']}")
        print(f"HP: {boss['hp']} | EXP: {boss['exp']}")
    else:
        print("Could not find boosted boss.")
