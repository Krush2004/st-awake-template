import asyncio
import datetime
import json
import os
import threading
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from streamlit_app import STREAMLIT_APPS


# 🔥 Increased timings (important)
BROWSER_PAGELOAD_TIMEOUT_SECONDS = 5
SITE_WAIT_SECONDS = 90
BUTTON_APPEAR_WAIT_SECONDS = 15
WAKE_INTERVAL_HOURS = float(os.getenv("WAKE_INTERVAL_HOURS", "0"))
MAX_CONCURRENT_APPS = 2

STATE_FILE = "wakeup_state.json"
LOG_FILE = "wakeup_log.txt"

CHROME_BINARY = "/usr/bin/chromium"
CHROMEDRIVER_PATH = "/usr/bin/chromedriver"

ENFORCE_WAKE_INTERVAL = False


SLEEP_TEXT_MARKERS = (
    "yes, get this app back up!",
    "this app has gone to sleep due to inactivity",
    "zzzz",
)

WAKE_BUTTON_LOCATORS = (
    (By.CSS_SELECTOR, "button[data-testid='wakeup-button-viewer']"),
    (By.CSS_SELECTOR, "button[data-testid='wakeup-button-owner']"),
    (By.CSS_SELECTOR, "button[data-testid='wakeup-button']"),
    (By.XPATH, "//button[normalize-space()='Yes, get this app back up!']"),
)

APP_CONTENT_SELECTORS = (
    "[data-testid='stAppViewContainer']",
    "[data-testid='stSidebar']",
    "main",
)

UNIQUE_STREAMLIT_APPS = list(dict.fromkeys(STREAMLIT_APPS))
LOG_LOCK = threading.Lock()


def log_message(log_file, message):
    timestamped = f"[{datetime.datetime.now()}] {message}"
    with LOG_LOCK:
        log_file.write(f"{timestamped}\n")
        log_file.flush()
        print(timestamped)


def create_driver():
    options = Options()
    options.binary_location = CHROME_BINARY

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(executable_path=CHROMEDRIVER_PATH)
    return webdriver.Chrome(service=service, options=options)


def find_wake_button(driver):
    for locator in WAKE_BUTTON_LOCATORS:
        try:
            for button in driver.find_elements(*locator):
                if button.is_displayed():
                    return button
        except:
            continue
    return None


def sleep_marker_present(driver):
    if find_wake_button(driver):
        return True

    try:
        text = driver.find_element(By.TAG_NAME, "body").text.lower()
    except:
        return False

    return any(marker in text for marker in SLEEP_TEXT_MARKERS)


def click_wake(driver):
    btn = find_wake_button(driver)
    if not btn:
        return False

    driver.execute_script("arguments[0].scrollIntoView();", btn)
    time.sleep(1)

    try:
        btn.click()
    except:
        driver.execute_script("arguments[0].click();", btn)

    return True


def app_loaded(driver):
    try:
        text = driver.find_element(By.TAG_NAME, "body").text.lower()
    except:
        return False

    if any(marker in text for marker in SLEEP_TEXT_MARKERS):
        return False

    if len(text) > 100:
        return True

    try:
        return any(driver.find_elements(By.CSS_SELECTOR, s) for s in APP_CONTENT_SELECTORS)
    except:
        return False


def check_site(url):
    driver = create_driver()

    try:
        driver.get(url)

        deadline = time.time() + SITE_WAIT_SECONDS

        while time.time() < deadline:

            # 🔴 If sleeping → wake it
            if sleep_marker_present(driver):

                if click_wake(driver):
                    time.sleep(5)
                    driver.refresh()

                    # 🔥 WAIT for real app load
                    post_deadline = time.time() + 90

                    while time.time() < post_deadline:
                        if app_loaded(driver):
                            return "woken", "app fully loaded after wake"
                        time.sleep(3)

                    return "errors", "wake clicked but app did not load"

            # ✅ Already awake
            if app_loaded(driver):
                return "awake", "app already running"

            time.sleep(2)

        return "errors", "timeout"

    finally:
        driver.quit()


async def process_site(index, total, url, log_file, sem):
    async with sem:
        log_message(log_file, f"Checking {index}/{total}: {url}")
        try:
            state, detail = await asyncio.to_thread(check_site, url)
        except Exception as e:
            state, detail = "errors", str(e)
        return url, state, detail


async def main():
    with open(LOG_FILE, "a") as log_file:

        log_message(log_file, "Execution started")

        summary = {"awake": 0, "woken": 0, "errors": 0}
        sem = asyncio.Semaphore(MAX_CONCURRENT_APPS)

        tasks = [
            asyncio.create_task(process_site(i, len(UNIQUE_STREAMLIT_APPS), url, log_file, sem))
            for i, url in enumerate(UNIQUE_STREAMLIT_APPS, 1)
        ]

        for task in asyncio.as_completed(tasks):
            url, state, detail = await task
            summary[state] += 1

            log_message(log_file, f"{state.upper()}: {url} ({detail})")

        log_message(log_file, f"Summary: {summary}")
        log_message(log_file, "Execution finished")


if __name__ == "__main__":
    asyncio.run(main())
