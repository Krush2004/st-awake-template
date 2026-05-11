import asyncio
import datetime
import threading
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from streamlit_app import STREAMLIT_APPS


# ---------------- CONFIG ----------------

SITE_WAIT_SECONDS = 120
POST_WAKE_WAIT = 180
MAX_CONCURRENT_APPS = 2

CHROME_BINARY = "/usr/bin/chromium-browser"
CHROMEDRIVER_PATH = "/usr/bin/chromedriver"

LOG_FILE = "wakeup_log.txt"

SLEEP_TEXT_MARKERS = (
    "yes, get this app back up!",
    "this app has gone to sleep",
    "zzzz",
)

WAKE_BUTTON_LOCATORS = (
    (By.CSS_SELECTOR, "button[data-testid='wakeup-button']"),
    (By.XPATH, "//button[contains(., 'Yes')]"),
)

APP_SELECTORS = (
    "[data-testid='stAppViewContainer']",
    "section.main",
    "main",
)

LOG_LOCK = threading.Lock()


# ---------------- LOGGING ----------------

def log(log_file, msg):
    timestamp = f"[{datetime.datetime.now()}] {msg}"

    with LOG_LOCK:
        log_file.write(timestamp + "\n")
        log_file.flush()

    print(timestamp)


# ---------------- DRIVER ----------------

def create_driver():

    options = Options()

    options.binary_location = CHROME_BINARY

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    return webdriver.Chrome(
        service=Service(CHROMEDRIVER_PATH),
        options=options
    )


# ---------------- DETECTION ----------------

def find_wake_button(driver):

    for locator in WAKE_BUTTON_LOCATORS:

        try:
            buttons = driver.find_elements(*locator)

            for btn in buttons:
                if btn.is_displayed():
                    return btn

        except Exception:
            continue

    return None


def is_sleeping(driver):

    if find_wake_button(driver):
        return True

    try:
        text = driver.find_element(By.TAG_NAME, "body").text.lower()

        return any(marker in text for marker in SLEEP_TEXT_MARKERS)

    except Exception:
        return False


def is_loaded(driver):

    try:
        for selector in APP_SELECTORS:

            if driver.find_elements(By.CSS_SELECTOR, selector):
                return True

        text = driver.find_element(By.TAG_NAME, "body").text.lower()

        if "zzzz" not in text and "sleep" not in text:
            return True

    except Exception:
        return False

    return False


# ---------------- WAKE ACTION ----------------

def click_wake(driver):

    btn = find_wake_button(driver)

    if not btn:
        return False

    driver.execute_script(
        "arguments[0].scrollIntoView();",
        btn
    )

    time.sleep(1)

    try:
        btn.click()

    except Exception:
        driver.execute_script(
            "arguments[0].click();",
            btn
        )

    return True


# ---------------- CORE ----------------

def check_site(url):

    driver = create_driver()

    try:

        driver.get(url)

        deadline = time.time() + SITE_WAIT_SECONDS

        while time.time() < deadline:

            # sleeping
            if is_sleeping(driver):

                for attempt in range(2):

                    if click_wake(driver):

                        time.sleep(5)

                        driver.refresh()

                        post_deadline = time.time() + POST_WAKE_WAIT

                        while time.time() < post_deadline:

                            if is_loaded(driver):
                                return "woken", "app loaded after wake"

                            time.sleep(3)

                return "woken", "wake triggered"

            # already awake
            if is_loaded(driver):
                return "awake", "already running"

            time.sleep(2)

        return "errors", "timeout"

    except Exception as e:
        return "errors", str(e)

    finally:
        driver.quit()


# ---------------- ASYNC ----------------

async def process(index, total, url, log_file, sem):

    async with sem:

        log(log_file, f"Checking {index}/{total}: {url}")

        try:
            state, detail = await asyncio.to_thread(
                check_site,
                url
            )

        except Exception as e:
            state, detail = "errors", str(e)

        return url, state, detail


async def main():

    with open(LOG_FILE, "a", encoding="utf-8") as log_file:

        log(log_file, "Execution started")

        summary = {
            "awake": 0,
            "woken": 0,
            "errors": 0
        }

        sem = asyncio.Semaphore(MAX_CONCURRENT_APPS)

        tasks = [
            asyncio.create_task(
                process(
                    i,
                    len(STREAMLIT_APPS),
                    url,
                    log_file,
                    sem
                )
            )

            for i, url in enumerate(STREAMLIT_APPS, 1)
        ]

        for task in asyncio.as_completed(tasks):

            url, state, detail = await task

            summary[state] += 1

            log(
                log_file,
                f"{state.upper()}: {url} ({detail})"
            )

        log(log_file, f"Summary: {summary}")

        log(log_file, "Execution finished")


if __name__ == "__main__":
    asyncio.run(main())
