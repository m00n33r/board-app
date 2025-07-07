from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
from supabase_client import get_supabase_client

BASE_URL = "https://afisha.yandex.ru"


def parse_events():
    url = f"{BASE_URL}/kazan"
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(7)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(7)
    html = driver.page_source
    
    with open("debug.html", "w", encoding="utf-8") as f:
        f.write(html)

    driver.quit()
    soup = BeautifulSoup(html, "html.parser")
    events = []

    for card in soup.find_all("div", {"data-test-id": "eventCard.root"}):
        # Название
        try:
            title = card.find(
                "h2", {"data-test-id": "eventCard.eventInfoTitle"}
            ).text.strip()
        except AttributeError:
            title = None

        # Дата и время
        try:
            datetime = (
                card.find("ul", {"data-test-id": "eventCard.eventInfoDetails"})
                .find("li")
                .text.strip()
            )
        except AttributeError:
            datetime = None

        # Локация
        try:
            location = (
                card.find("ul", {"data-test-id": "eventCard.eventInfoDetails"})
                .find_all("li")[1]
                .text.strip()
            )
        except (AttributeError, IndexError):
            location = None

        # Цена
        try:
            price = card.find("span", {"data-test-id": "event-card-price"}).text.strip()
        except AttributeError:
            price = None

        # Ссылка на картинку
        try:
            image_url = card.find("img", class_="jYbobS")["data-src"]
        except (AttributeError, TypeError):
            image_url = None

        # Ссылка на событие
        try:
            link = card.find("a", {"data-test-id": "eventCard.link"})["href"]
            if link and link.startswith("/"):
                link = BASE_URL + link
        except (AttributeError, TypeError):
            link = None

        genre = None
        description = None

        events.append(
            {
                "event_name": title,
                "event_banner": image_url,
                "event_start_dttm": datetime,
                "event_end_dttm": None,
                "event_location": location,
                "event_description": description,
                "event_tag": genre,
                "event_link": link,
                "event_approval": None,
                "event_price_status": None,
                "event_price": price,
                "event_visibility": "public",
                "event_capacity": None,
                "event_moderation_step": None,
                "user_id": None,
            }
        )
    return events


def save_to_supabase(events):
    supabase = get_supabase_client()
    for event in events:
        supabase.table("events_raw").insert(event).execute()


if __name__ == "__main__":
    events = parse_events()
    save_to_supabase(events)
    print(f"Сохранено {len(events)} событий в Supabase.")
