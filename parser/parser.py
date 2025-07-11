from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
from supabase_client import get_supabase_client

BASE_URL = "https://afisha.yandex.ru"
SELECTION_URL = "https://afisha.yandex.ru/moscow/selections/main-show"

def click_show_more(driver, max_clicks=50):
    clicks = 0
    while clicks < max_clicks:
        try:
            btn = driver.find_element(
                By.XPATH,
                "//div[@data-test-id='eventsList.more']//a[contains(@class, 'button-more') and not(contains(@class, 'button-more_hidden_yes'))]"
            )
            if btn.is_displayed():
                driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                btn.click()
                clicks += 1
                time.sleep(2)
            else:
                break
        except (NoSuchElementException, ElementClickInterceptedException):
            break

def parse_events_from_selection(selection_url):
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # включить для headless-режима
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(selection_url)
    time.sleep(20)
    click_show_more(driver)
    html = driver.page_source
    # Сохраняем HTML для отладки
    with open("debug_main_show.html", "w", encoding="utf-8") as f:
        f.write(html)
    driver.quit()
    soup = BeautifulSoup(html, "html.parser")
    events = []
    cards = soup.find_all("div", {"data-test-id": "eventCard.root"})
    print(f"Найдено карточек: {len(cards)}")
    for card in cards:
        try:
            title = card.find("h2", {"data-test-id": "eventCard.eventInfoTitle"}).text.strip()
        except AttributeError:
            title = None
        try:
            datetime = (
                card.find("ul", {"data-test-id": "eventCard.eventInfoDetails"})
                .find("li")
                .text.strip()
            )
        except AttributeError:
            datetime = None
        try:
            location = (
                card.find("ul", {"data-test-id": "eventCard.eventInfoDetails"})
                .find_all("li")[1]
                .text.strip()
            )
        except (AttributeError, IndexError):
            location = None
        try:
            price = card.find("span", {"data-test-id": "event-card-price"}).text.strip()
        except AttributeError:
            price = None
        try:
            image_url = card.find("img", class_="jYbobS")["data-src"]
        except (AttributeError, TypeError):
            image_url = None
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
                "event_price": price,
            }
        )
    return events

def save_to_supabase(events):
    c = 0
    supabase = get_supabase_client()
    for event in events:
        existing = supabase.table("events_raw").select("id").eq("event_link", event["event_link"]).execute()
        if not existing.data:
            supabase.table("events_raw").insert(event).execute()
            c += 1
    print(f"Сохранено {c} новых событий в Supabase.")

if __name__ == "__main__":
    print(f"Парсим селекцию: {SELECTION_URL}")
    events = parse_events_from_selection(SELECTION_URL)
    print(f"Найдено событий: {len(events)}")
    save_to_supabase(events)
    print("Парсинг и сохранение завершены.")
