# Wake Up Streamlit Apps

A GitHub Actions workflow and Python automation tool to keep Streamlit Cloud apps awake automatically.

## Overview

This repository provides a Python + Selenium based wake-up utility for Streamlit apps deployed on Streamlit Cloud.

The project automatically detects sleeping apps, clicks the **“Yes, get this app back up!”** button, verifies that the application actually loads, and uploads execution logs after each workflow run.

This helps reduce cold starts and keeps apps responsive.

---

## Features

✅ Automatic Streamlit sleep detection

✅ Wake button interaction using Selenium

✅ Wake confirmation after button click

✅ Hourly GitHub Actions schedule

✅ Configurable wake interval enforcement

✅ Parallel processing for multiple apps

✅ Chrome + ChromeDriver automatic setup

✅ Workflow log artifact upload

✅ Retry support for wake actions

✅ UTC timestamp logging

---

## How it works

### Step 1: Detect app state

The script first checks whether the app is:

- Already awake
- Sleeping
- Loading / waking up

Sleep detection uses:

```text
Zzzz
This app has gone to sleep due to inactivity
Yes, get this app back up!
```

If a sleep marker is found, Selenium starts.

---

### Step 2: Wake app

The script:

1. Opens app using Selenium
2. Finds wake button
3. Clicks wake button
4. Waits for app content to load
5. Confirms wake success

Apps are marked **WOKEN** only after successful loading.

---

### Step 3: Write logs

Logs include:

```text
Execution started
Checking app 1/3
App is already awake
App was asleep and is now awake
Summary
Execution finished
```

Logs are uploaded automatically as workflow artifacts.

---

## Repository Structure

```text
.
├── wake_up_streamlit.py
├── streamlit_app.py
├── wakeup_log.txt
├── wakeup_state.json
└── .github/
    └── workflows/
        └── wake_up.yml
```

Files:

- `wake_up_streamlit.py` → main wake automation logic
- `streamlit_app.py` → Streamlit app URL list
- `wakeup_log.txt` → execution logs
- `wakeup_state.json` → interval tracking state
- `wake_up.yml` → GitHub Actions workflow

---

## Configuration

Add apps:

```python
STREAMLIT_APPS = [
    "https://app1.streamlit.app",
    "https://app2.streamlit.app",
    "https://app3.streamlit.app",
]
```

---

## Workflow Configuration

Workflow:

```yaml
schedule:
  - cron: "0 * * * *"
```

Runs every hour.

The script prevents unnecessary wake attempts using:

```yaml
WAKE_INTERVAL_HOURS=10
ENFORCE_WAKE_INTERVAL=1
```

Result:

- Workflow executes hourly
- Real wake process happens once every ~10 hours
- Safety buffer before Streamlit sleep threshold

---

## Environment Variables

```text
WAKE_INTERVAL_HOURS=10
ENFORCE_WAKE_INTERVAL=1
WAKE_CONFIRM_WAIT_SECONDS=120
WAKE_CLICK_RETRIES=3
MAX_CONCURRENT_APPS=5
```

---

## Browser Setup

GitHub Actions installs browser automatically:

```yaml
- name: Setup Chrome
  uses: browser-actions/setup-chrome@v2.1.2
```

Features:

- Google Chrome installation
- ChromeDriver installation
- Browser verification
- CI compatibility

No Chromium Snap dependency required.

---

## Logs

Example:

```text
[UTC] Execution started

Checking app 1/3
App is already awake

Checking app 2/3
Sleep marker found
Wake button clicked
App was asleep and is now awake

Summary:
{'awake': 2, 'woken': 1, 'errors': 0}

Execution finished
```

Artifact upload:

```yaml
- uses: actions/upload-artifact@v6
```

Logs remain available after workflow completion.

---

## Installation

Clone repository:

```bash
git clone <repo-url>
cd repo
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run locally:

```bash
python wake_up_streamlit.py
```

---

## Schedule Behavior

### Local execution

```text
ENFORCE_WAKE_INTERVAL=0
```

Runs every execution.

### CI execution

```text
ENFORCE_WAKE_INTERVAL=1
WAKE_INTERVAL_HOURS=10
```

Skips unnecessary executions.

---

## Result States

| State | Meaning |
|--------|----------|
| awake | App already running |
| woken | Sleeping app recovered |
| errors | Wake failed / timeout |

---

## License

MIT License
