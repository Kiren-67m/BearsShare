# Bears Share Notification System — Demo

A local demo application built for **Missouri State University's Bear Pantry** that automates food-sharing notifications. Staff fill out a simple web form, and the system immediately emails all opted-in Bears Share subscribers with details about available catering food on campus.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Deployment](#2-deployment)
3. [How It Works](#3-how-it-works)
4. [Project Structure](#4-project-structure)
5. [File-by-File Reference](#5-file-by-file-reference)
6. [Setup & Installation](#6-setup--installation)
7. [Running the App](#7-running-the-app)
8. [Using Mailtrap (Email Testing)](#8-using-mailtrap-email-testing)
9. [Using Gmail (Alternative)](#9-using-gmail-alternative)
10. [Going to Production (MSU SMTP)](#10-going-to-production-msu-smtp)
11. [Mock Data Reference](#11-mock-data-reference)
12. [Email Format](#12-email-format)
13. [Replacing PantrySoft Mock with Real API](#13-replacing-pantrysoft-mock-with-real-api)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Project Overview

**Purpose:** When leftover catering food is available on campus, Bear Pantry staff submit a quick form. The system reads a list of students who opted in to Bears Share notifications and instantly sends them a formatted email with location, food details, and pickup deadline.

**Demo scope:** Everything runs locally. Emails are captured by Mailtrap (a free email sandbox) — no real emails are sent during testing.

**Tech stack:**

| Layer | Technology |
|-------|-----------|
| Backend | Python 3 + Flask |
| Frontend | HTML/CSS (served by Flask) |
| Email | Python `smtplib` + `email.mime` |
| User data | Mock JSON file (simulates PantrySoft API) |
| SMTP (demo) | Mailtrap sandbox or Gmail |
| SMTP (production) | MSU SMTP server |

---

## 2. Deployment

### Live Demo
This app is deployed on Render: **https://bearsshare.onrender.com**

### Environment Variables (required for production)
Set these in your Render dashboard under Environment:

| Variable | Required | Description |
|----------|----------|-------------|
| `SMTP_USER` | ✅ | Email account used to send notifications |
| `SMTP_PASSWORD` | ✅ | App Password — enter without spaces to avoid encoding issues |
| `SECRET_KEY` | ✅ | Flask session secret key + unsubscribe-token signing (any random string; changing it invalidates old unsubscribe links) |
| `BASE_URL` | ✅ | Public URL of the app (e.g. `https://bearsshare.onrender.com`) — used to build unsubscribe links |
| `DATABASE_URL` | ✅ prod | Render Postgres connection string. Without it the app uses local SQLite, which resets on every deploy |
| `FROM_EMAIL` | optional | From address if different from `SMTP_USER` |
| `ACCESS_CODE` | optional | If set, staff must enter this code to send a broadcast or import a CSV |
| `SMTP_SERVER` | optional | Default: `smtp.gmail.com` |
| `SMTP_PORT` | optional | Default: `465` (SSL). Use `587` for STARTTLS |
| `PHYSICAL_ADDRESS` | optional | Mailing address shown in email footers (CAN-SPAM); defaults to the Bear Pantry campus address |

### New in this version

- **Database (SQLAlchemy)** — SQLite locally, Postgres in production. Three tables: `subscribers`, `suppression`, `send_log`.
- **CSV subscriber import** — upload a PantrySoft CSV export at `/subscribers` (needs a header row with an `email` column). Replaces the previous list; falls back to bundled mock data until the first import.
- **Access code** — set `ACCESS_CODE` and the send form + CSV import require it.
- **One-click unsubscribe** — every email carries a signed per-recipient unsubscribe link. Unsubscribed addresses go on a permanent suppression list and stay excluded even after the subscriber list is re-imported. Email footers include the physical mailing address (CAN-SPAM).
- **Send history** — every broadcast is logged and visible at `/history`.

### Deploy to Render
1. Push code to GitHub
2. Create a new Web Service on Render, connect to this repository
3. Set Build Command: `pip install -r requirements.txt`
4. Set Start Command: `gunicorn app:app`
5. Add environment variables above in the Render dashboard
6. Deploy

### Going to Production (MSU)
When MSU IT provides SMTP credentials, update environment variables in Render — no code changes needed:
- `SMTP_USER` → `BearPantry@missouristate.edu` (FROM_EMAIL follows this automatically)
- `SMTP_PASSWORD` → MSU SMTP password
- `SMTP_SERVER` → MSU SMTP server address (if different from smtp.gmail.com)
- `SMTP_PORT` → MSU SMTP port (`465` for SSL, `587` for STARTTLS)

---

## 3. How It Works

```
Staff fills form  →  Flask /send route  →  pantrysoft_mock.py  →  mock_users.json
                                       ↓
                               email_sender.py
                                       ↓
                          SMTP (Mailtrap / Gmail / MSU)
                                       ↓
                         Opted-in students receive email
                                       ↓
                          success.html shown to staff
```

**Step by step:**

1. Staff visits `http://localhost:5000`
2. Fills in: Building Name, Room Number, Food Available (textarea), Food Available Until, and optional Additional Notes
3. Clicks **"Send Bears Share Alert"**
4. Flask calls `pantrysoft_mock.get_optin_emails()` — returns only users where `bears_share_optin: true`
5. Flask calls `email_sender.send_notification()` — connects to SMTP and sends one email per recipient
6. Terminal prints a log: how many sent, how many failed
7. Staff is redirected to a success page showing sent count, timestamp, and submission summary

---

## 4. Project Structure

```
bears_share/
├── app.py                # Flask app — 8 routes, form handling, session
├── email_sender.py       # SMTP logic, email body builder (plain + HTML)
├── db.py                 # SQLAlchemy data layer — subscribers, suppression, send_log
├── tokens.py             # Signed unsubscribe tokens (itsdangerous)
├── pantrysoft_mock.py    # Recipient source — DB if imported, else mock_users.json
├── mock_users.json       # 8 test users (5 opted in, 3 opted out) — demo fallback
├── config.py             # Config — all values from environment variables
├── requirements.txt      # Python dependencies (flask, gunicorn, SQLAlchemy, psycopg2)
├── .gitignore            # Excludes venv/, credentials, *.db, .DS_Store, etc.
├── templates/
│   ├── form.html         # Staff submission form
│   ├── success.html      # Confirmation page after sending
│   ├── subscribers.html  # Subscriber list status + CSV upload
│   ├── history.html      # Past-broadcast log
│   └── unsubscribe.html  # One-click unsubscribe / resubscribe result
├── venv/                 # Python virtual environment (created during setup)
└── README.md             # This file
```

---

## 5. File-by-File Reference

### `app.py` — Flask Application

The main entry point. Defines eight routes:

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Renders `form.html` |
| `/send` | POST | Validates access code, sends emails, logs the broadcast, redirects |
| `/success` | GET | Reads session data, renders `success.html` |
| `/subscribers` | GET/POST | Shows subscriber/suppressed counts; POST imports a PantrySoft CSV (replaces the list) |
| `/unsubscribe/<token>` | GET | One-click unsubscribe — adds the email to the permanent suppression list |
| `/resubscribe/<token>` | GET | Undo an unsubscribe — removes the email from the suppression list |
| `/history` | GET | Renders `history.html` — log of past broadcasts |

**Key behaviors:**
- Validates that all required fields (food, location, room, end_time) are non-empty; shows inline error if not
- Reads the optional `notes` field (empty string if not filled)
- Records `sent_at` timestamp using `datetime.now()` formatted as human-readable string (e.g. "June 04, 2026 at 04:35 PM")
- Passes a `summary` dict into the Flask session, then pops it on the success page (prevents data on page refresh)
- Prints a structured log block to terminal for every submission

**Session summary dict keys:**

```python
{
    "food":     str,   # food description
    "location": str,   # building name
    "room":     str,   # room number
    "end_time": str,   # datetime-local value from form
    "notes":    str,   # additional notes (may be empty)
    "sent":     int,   # number of emails successfully sent
    "failed":   int,   # number of emails that failed
    "total":    int,   # total opted-in recipients
    "sent_at":  str,   # human-readable timestamp
}
```

---

### `email_sender.py` — Email Logic

**`build_email_body(food, location, room, end_time, notes="")`**

Builds both a plain-text version and an HTML version of the email. Returns a `tuple[str, str]`.

- HTML email uses MSU Maroon (`#5E0009`) header
- The `notes` row only appears in the email if `notes` is non-empty
- Styled with inline CSS for maximum email client compatibility

**`send_notification(food, location, room, end_time, recipients, notes="")`**

- Opens one SMTP connection and reuses it for all recipients (efficient)
- Sends each email as `multipart/alternative` (plain text + HTML fallback)
- Catches per-recipient errors without stopping the entire batch
- Catches SMTP authentication errors and connection errors separately
- Returns: `{"sent": int, "failed": int, "errors": list}`

**Email subject format:**
```
🐻 Bears Share Alert: Free food at [Location], [Room] — available until [Time]
```

---

### `db.py` — Database Layer (SQLAlchemy)

Same code runs on SQLite locally (default, auto-creates `bears_share.db`) and Postgres in production (set `DATABASE_URL`). Normalizes Render's `postgres://` URLs to `postgresql://`. Three tables:

| Table | Purpose |
|-------|---------|
| `subscribers` | The opt-in mailing list, populated by CSV import |
| `suppression` | Emails that clicked unsubscribe — filtered out of **every** send, permanently, even after the subscriber list is re-imported |
| `send_log` | One row per broadcast, powering `/history` |

Key functions: `replace_subscribers()` (dedupes, replaces the whole list), `get_active_subscribers()` (subscribers minus suppression), `suppress_email()` / `unsuppress_email()`, `log_send()` / `get_send_logs()`.

---

### `tokens.py` — Signed Unsubscribe Tokens

Each email carries `{BASE_URL}/unsubscribe/<token>`, where the token is the recipient's email signed with `SECRET_KEY` (via `itsdangerous`). Links can't be forged and no DB lookup is needed to mint one.

> ⚠️ Changing `SECRET_KEY` invalidates every unsubscribe link already sent out.

---

### `pantrysoft_mock.py` — User List (Mock API)

Recipient source. If any subscribers have been imported, it returns them from the database (minus the suppression list); otherwise it falls back to `mock_users.json` so the demo still works.

**`get_optin_recipients()`** — returns a list of full user dicts for opted-in users  
**`get_optin_emails()`** — convenience wrapper, returns just the email addresses

> **To connect real PantrySoft API:** replace only this file's `get_optin_recipients()`. `app.py` and `email_sender.py` do not need any changes.

---

### `mock_users.json` — Test Users

Contains 8 simulated users. 5 have `bears_share_optin: true`, 3 have `false`.

| Name | Email | Opted In |
|------|-------|----------|
| Test User 1 | user1@example.com | ✅ Yes |
| Test User 2 | user2@example.com | ✅ Yes |
| Test User 3 | user3@example.com | ✅ Yes |
| Test User 4 | user4@example.com | ❌ No |
| Test User 5 | user5@example.com | ❌ No |
| Test User 6 | user6@example.com | ✅ Yes |
| Test User 7 | user7@example.com | ✅ Yes |
| Test User 8 | user8@example.com | ❌ No |

Every submission should result in exactly **5 emails sent** (the five opted-in test users).

---

### `config.py` — SMTP Configuration

All values are read from environment variables. Defaults are shown below:

```python
SMTP_SERVER   = os.environ.get("SMTP_SERVER",   "smtp.gmail.com")
SMTP_PORT     = int(os.environ.get("SMTP_PORT", "465"))   # 465=SSL, 587=STARTTLS
SMTP_USER     = os.environ.get("SMTP_USER",     "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")       # \xa0 auto-stripped
FROM_EMAIL    = os.environ.get("FROM_EMAIL", "") or SMTP_USER  # falls back to SMTP_USER
FROM_NAME     = "Bear Pantry – Bears Share"
SECRET_KEY    = os.environ.get("SECRET_KEY",    "dev-secret-key-change-in-production")
ACCESS_CODE   = os.environ.get("ACCESS_CODE",   "")       # optional form gate
DATABASE_URL  = os.environ.get("DATABASE_URL",  "sqlite:///bears_share.db")
BASE_URL      = os.environ.get("BASE_URL",      "http://localhost:5000")
PHYSICAL_ADDRESS = os.environ.get("PHYSICAL_ADDRESS", "Bear Pantry, MSU, ...")  # CAN-SPAM footer
```

> ⚠️ **Never commit real credentials to Git.** Set all secrets as environment variables in Render (or export them locally). `config.py` itself contains no credentials.

---

### `templates/form.html` — Submission Form

Staff-facing page. Fields:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| Building Name | text input | ✅ | e.g. "Plaster Student Union" |
| Room Number | text input | ✅ | e.g. "Room 203" |
| What food is available? | textarea | ✅ | Multi-line, resizable |
| Food Available Until | datetime-local | ✅ | Pickup deadline |
| Additional Notes | textarea | ❌ | Optional; e.g. dietary info |

- Shows an inline red error box if required fields are missing
- Submit button: **"Send Bears Share Alert"**
- Footer note: "This will notify all opted-in Bears Share subscribers immediately."

---

### `templates/success.html` — Confirmation Page

Shown after successful form submission. Displays:

- **Emails Sent** count (large stat box)
- **Opted-In Users** total count
- **Failed** count (only shown if > 0, in red)
- Full submission summary table (food, location, room, until, notes if filled, sent-at timestamp)
- Link back to submit another alert
- Contact note: `BearPantry@missouristate.edu`

---

## 6. Setup & Installation

### Prerequisites

- Python 3.9 or later (`python3 --version`)
- Internet access (to reach SMTP server)
- A Gmail account with an App Password, **or** a free [Mailtrap](https://mailtrap.io) account for sandbox testing

### Install steps

```bash
# 1. Navigate into the project folder
cd bears_share

# 2. Create a virtual environment
python3 -m venv venv

# 3. Activate it
#    macOS / Linux:
source venv/bin/activate
#    Windows:
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Set SMTP credentials as environment variables (see sections 8 or 9 below)
export SMTP_USER="your.email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export SECRET_KEY="any-random-string"
```

---

## 7. Running the App

```bash
# Make sure the virtual environment is active
source venv/bin/activate

# Start Flask
python app.py
```

Expected terminal output:
```
Bears Share running at http://localhost:5000
 * Running on http://127.0.0.1:5000
```

Open your browser to: **http://localhost:5000**

To stop the server: press `Ctrl + C`

---

## 8. Using Mailtrap (Email Testing)

Mailtrap is a free email sandbox. Emails are captured and displayed in a web inbox — nothing is delivered to real recipients. **Recommended for all demo/testing.**

### Setup

1. Sign up at [https://mailtrap.io](https://mailtrap.io) (free)
2. Go to **Email Testing → Inboxes**
3. Click your inbox → **SMTP Settings** tab
4. Select **Python** from the integration dropdown — it shows your credentials

### Environment variables for Mailtrap

Set these before running the app locally:

```bash
export SMTP_SERVER="sandbox.smtp.mailtrap.io"
export SMTP_PORT="465"          # Mailtrap supports 465 (SSL)
export SMTP_USER="your_mailtrap_username"
export SMTP_PASSWORD="your_mailtrap_password"
export SECRET_KEY="any-random-string"
```

### Verifying it works

1. Run the app and submit the form
2. Go to your Mailtrap inbox at mailtrap.io
3. You should see **5 emails** (one per opted-in test user)
4. Click any email to preview the HTML layout

---

## 9. Using Gmail (Alternative)

If you prefer to use a Gmail account instead of Mailtrap:

### Setup

1. Go to your Google Account → **Security → 2-Step Verification** (must be enabled)
2. Search for **"App Passwords"** in your Google Account settings
3. Create a new App Password for "Mail" — copy the 16-character password

### Environment variables for Gmail

```bash
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="465"                      # SSL — default; use 587 for STARTTLS
export SMTP_USER="your.email@gmail.com"     # also becomes FROM_EMAIL automatically
export SMTP_PASSWORD="xxxxxxxxxxxxxxxxxxxx" # 16-char App Password, spaces removed
export SECRET_KEY="any-random-string"
```

> **Note on port:** port `465` uses `SMTP_SSL` (default); port `587` uses `STARTTLS`. Both work with Gmail — `465` is recommended as it connects faster.

> ⚠️ With Gmail, emails go to **real inboxes**. For testing, make sure `mock_users.json` contains email addresses you control, or use Mailtrap instead.

---

## 10. Going to Production (MSU SMTP)

When ready to deploy for real, make exactly **two changes**:

### Change 1 — Update environment variables in Render (no code changes needed)

```bash
SMTP_SERVER   = "<MSU SMTP server address>"   # get from MSU IT
SMTP_PORT     = "465"                          # or 587 — confirm with MSU IT
SMTP_USER     = "BearPantry@missouristate.edu" # FROM_EMAIL follows automatically
SMTP_PASSWORD = "<MSU SMTP password>"
```

`config.py` already reads all values from env vars — no file edits required.

### Change 2 — `pantrysoft_mock.py`: call the real PantrySoft API

Replace the contents of `get_optin_recipients()` with an actual HTTP request:

```python
import requests

def get_optin_recipients() -> list[dict]:
    response = requests.get(
        "https://api.pantrysoft.com/v1/users",   # confirm real endpoint
        headers={"Authorization": "Bearer YOUR_API_KEY"}
    )
    users = response.json()
    return [u for u in users if u.get("bears_share_optin") is True]
```

Everything else — `app.py`, `email_sender.py`, both templates — stays exactly the same.

---

## 11. Mock Data Reference

To add or modify test users, edit `mock_users.json`. Each user object must have:

```json
{
  "id": "U009",
  "name": "Full Name",
  "email": "email@example.com",
  "bears_share_optin": true
}
```

- `bears_share_optin: true` → receives notifications
- `bears_share_optin: false` → silently excluded

---

## 12. Email Format

### Subject line
```
🐻 Bears Share Alert: Free food at Plaster Student Union, Room 203 — available until 2026-06-04T17:00
```

### HTML email preview

```
┌─────────────────────────────────────┐
│  🐻 Bears Share Alert!  [MSU Maroon]│
├─────────────────────────────────────┤
│ Hi there,                           │
│                                     │
│ Free food is available through      │
│ Bears Share right now:              │
│                                     │
│ ┌────────────┬──────────────────┐   │
│ │ What       │ Pizza, salad...  │   │
│ │ Where      │ PSU, Room 203    │   │
│ │ Until      │ 5:00 PM         │   │
│ │ Notes      │ Nut-free        │   │  ← only if filled
│ └────────────┴──────────────────┘   │
│                                     │
│ Stop by while it lasts!             │
│                                     │
│ — Bear Pantry Team, Missouri State  │
└─────────────────────────────────────┘
```

---

## 13. Replacing PantrySoft Mock with Real API

The codebase is designed so that **only `pantrysoft_mock.py` needs to change** when connecting to real data. The contract that file must fulfill:

```python
def get_optin_emails() -> list[str]:
    """Must return a list of email address strings for opted-in users."""
    ...
```

As long as this function returns a `list[str]`, the rest of the app works unchanged.

---

## 14. Troubleshooting

### `ModuleNotFoundError: No module named 'flask'`
The virtual environment is not active. Run:
```bash
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```

### `SMTP authentication failed`
- Double-check `SMTP_USER` and `SMTP_PASSWORD` in `config.py`
- For Gmail: make sure you're using an **App Password**, not your regular Gmail password
- For Mailtrap: copy credentials from the **SMTP Settings** tab of your inbox (not the API key)

### `Connection refused` / `Network unreachable`
- Check that the `SMTP_SERVER` and `SMTP_PORT` env vars match your provider
- Mailtrap: `sandbox.smtp.mailtrap.io` port `465` (or `2525`)
- Gmail: `smtp.gmail.com` port `465` (SSL, default) or `587` (STARTTLS)
- On Render free tier, port `587` may be blocked — use `465` instead

### Form submits but 0 emails sent
- Check the terminal — look for `[EmailSender]` log lines
- Verify `mock_users.json` has users with `"bears_share_optin": true`
- Run a quick check: `python3 -c "import pantrysoft_mock; print(pantrysoft_mock.get_optin_emails())"`

### Success page shows but no emails in Mailtrap
- Wait 10–15 seconds — Mailtrap can have a short delay
- Confirm you're looking at the correct inbox in Mailtrap (you may have multiple)
- Check the terminal for any `[EmailSender] ✗ Failed` lines

### `All fields are required` error even when fields are filled
- Check the `name` attributes on form inputs match what `app.py` reads (`food`, `location`, `room`, `end_time`)

---

## Brand & Design Notes

| Element | Value |
|---------|-------|
| Primary color | `#5E0009` — Missouri State Maroon |
| Hover color | `#8B0012` |
| Background | `#F5F5F5` |
| Text on primary | `#FFFFFF` |
| Font | Arial, sans-serif |

---

*Bears Share Notification System — Demo build for Missouri State University Bear Pantry.*  
*For questions, contact: BearPantry@missouristate.edu*
