# Wake Up Streamlit Apps

A GitHub Actions workflow and Python script to automatically wake up Streamlit apps.

## Overview

Streamlit Cloud apps go to sleep after inactivity, which can cause cold starts and slower response times.

This project automatically detects sleeping apps, wakes them using Selenium, verifies successful loading, and keeps execution logs for monitoring.

It is useful for keeping apps responsive and reducing manual wake-ups.

## How it works

1. The Python script checks whether the Streamlit app is **awake** or **sleeping**.

2. Sleep detection uses markers such as:

```text
Zzzz
This app has gone to sleep due to inactivity
Yes, get this app back up!
```

3. If sleep is detected, Selenium launches Chrome and clicks the wake button.

4. The script verifies the app loads successfully before marking it as **woken**.

5. GitHub Actions runs the workflow automatically on schedule and push events.

## New Improvements

Latest updates include:

- Automatic Chrome + ChromeDriver setup
- Wake confirmation after button click
- Retry support (`WAKE_CLICK_RETRIES`)
- Parallel processing support
- UTC timestamp logging
- State tracking with `wakeup_state.json`
- Workflow log artifact upload

Configuration:

```text
WAKE_INTERVAL_HOURS=10
ENFORCE_WAKE_INTERVAL=1
MAX_CONCURRENT_APPS=5
```

## Repository contents

* `wake_up_streamlit.py` — Main wake automation script

* `streamlit_app.py` — Streamlit app URLs

* `wakeup_log.txt` — Execution logs

* `wakeup_state.json` — Wake interval tracking

* `.github/workflows/wake_up.yml` — Workflow configuration

## Usage

1. Add app URLs to `streamlit_app.py`

2. Copy `.github/workflows/wake_up.yml`

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run:

```bash
python wake_up_streamlit.py
```

## Log file

Example:

```text
Checking app 1/3
App is already awake

Checking app 2/3
App was asleep and is now awake

Summary:
{'awake':2,'woken':1,'errors':0}
```

Logs are uploaded automatically after each workflow run.

## Schedule

Workflow runs:

- Push to `main`
- Hourly schedule
- Manual execution

```yaml
schedule:
  - cron: "0 * * * *"
```

The script enforces:

```text
ENFORCE_WAKE_INTERVAL=1
WAKE_INTERVAL_HOURS=10
```

to reduce unnecessary executions.

## License

MIT License
