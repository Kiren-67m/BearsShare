# Bears Share Notification System — Demo

A local demo application built for **Missouri State University's Bear Pantry** that automates food-sharing notifications. Staff fill out a simple web form, and the system immediately emails all opted-in Bears Share subscribers with details about available catering food on campus.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [How It Works](#2-how-it-works)
3. [Project Structure](#3-project-structure)
4. [File-by-File Reference](#4-file-by-file-reference)
5. [Setup & Installation](#5-setup--installation)
6. [Running the App](#6-running-the-app)
7. [Using Mailtrap (Email Testing)](#7-using-mailtrap-email-testing)
8. [Using Gmail (Alternative)](#8-using-gmail-alternative)
9. [Going to Production (MSU SMTP)](#9-going-to-production-msu-smtp)
10. [Mock Data Reference](#10-mock-data-reference)
11. [Email Format](#11-email-format)
12. [Replacing PantrySoft Mock with Real API](#12-replacing-pantrysoft-mock-with-real-api)
13. [Troubleshooting](#13-troubleshooting)

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

## 2. How It Works

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

## 3. Project Structure

```
bears_share/
├── app.py                # Flask app — routes, form handling, session
├── email_sender.py       # SMTP logic, email body builder (plain + HTML)
├── pantrysoft_mock.py    # Simulates PantrySoft API — reads mock_users.json
├── mock_users.json       # 8 test users (5 opted in, 3 opted out)
├── config.py             # SMTP credentials and sender info
├── templates/
│   ├── form.html         # Staff submission form
│   └── success.html      # Confirmation page after sending
├── venv/                 # Python virtual environment (created during setup)
└── README.md             # This file
```

---

## 4. File-by-File Reference

### `app.py` — Flask Application

The main entry point. Defines three routes:

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Renders `form.html` |
| `/send` | POST | Processes form, sends emails, stores result in session, redirects |
| `/success` | GET | Reads session data, renders `success.html` |

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

### `pantrysoft_mock.py` — User List (Mock API)

Simulates a call to the PantrySoft API.

**`get_optin_recipients()`** — returns a list of full user dicts for opted-in users  
**`get_optin_emails()`** — convenience wrapper, returns just the email addresses

> **To connect real PantrySoft API:** replace only this file. `app.py` and `email_sender.py` do not need any changes.

---

### `mock_users.json` — Test Users

Contains 8 simulated users. 5 have `bears_share_optin: true`, 3 have `false`.

| Name | Email | Opted In |
|------|-------|----------|
| Alice Johnson | alice@example.com | ✅ Yes |
| Bob Martinez | bob@example.com | ✅ Yes |
| Carol White | carol@example.com | ❌ No |
| David Lee | david@example.com | ✅ Yes |
| Emma Chen | emma@example.com | ❌ No |
| Frank Rivera | frank@example.com | ✅ Yes |
| Grace Kim | grace@example.com | ✅ Yes |
| Henry Davis | henry@example.com | ❌ No |

Every submission should result in exactly **5 emails sent** (to Alice, Bob, David, Frank, Grace).

---

### `config.py` — SMTP Configuration

```python
SMTP_SERVER   = "sandbox.smtp.mailtrap.io"   # or smtp.gmail.com
SMTP_PORT     = 2525                          # Mailtrap; Gmail uses 587
SMTP_USER     = "your_username"
SMTP_PASSWORD = "your_password"
FROM_EMAIL    = "bearpantry-demo@example.com"
FROM_NAME     = "Bear Pantry – Bears Share"
```

> ⚠️ **Never commit real credentials to Git.** Add `config.py` to `.gitignore` when moving to production.

---

### `templates/form.html` — Submission Form

Staff-facing page. Fields:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| Building Name | text input | ✅ | e.g. "Plaster Student Union" |
| Room Number | text input | ✅ | e.g. "Room 203" |
| What food is available? | textarea | ✅ | Multi-line, resizable |
| Food Available Until | datetime-local | ✅ | Hint: students have 20 min after |
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

## 5. Setup & Installation

### Prerequisites

- Python 3.9 or later (`python3 --version`)
- Internet access (to reach SMTP server)
- A free [Mailtrap](https://mailtrap.io) account (for demo email testing)

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

# 4. Install Flask (only dependency)
pip install flask

# 5. Configure SMTP credentials (see sections 7 or 8 below)
#    Open config.py and fill in your SMTP_USER and SMTP_PASSWORD
```

---

## 6. Running the App

```bash
# Make sure the virtual environment is active
source venv/bin/activate

# Start Flask
python app.py
```

Expected terminal output:
```
Bears Share Demo running at http://localhost:5000
 * Running on http://127.0.0.1:5000
```

Open your browser to: **http://localhost:5000**

To stop the server: press `Ctrl + C`

---

## 7. Using Mailtrap (Email Testing)

Mailtrap is a free email sandbox. Emails are captured and displayed in a web inbox — nothing is delivered to real recipients. **Recommended for all demo/testing.**

### Setup

1. Sign up at [https://mailtrap.io](https://mailtrap.io) (free)
2. Go to **Email Testing → Inboxes**
3. Click your inbox → **SMTP Settings** tab
4. Select **Python** from the integration dropdown — it shows your credentials

### config.py settings

```python
SMTP_SERVER   = "sandbox.smtp.mailtrap.io"
SMTP_PORT     = 2525
SMTP_USER     = "your_mailtrap_username"   # from Mailtrap dashboard
SMTP_PASSWORD = "your_mailtrap_password"   # from Mailtrap dashboard
FROM_EMAIL    = "bearpantry-demo@example.com"
FROM_NAME     = "Bear Pantry – Bears Share"
```

### Verifying it works

1. Run the app and submit the form
2. Go to your Mailtrap inbox at mailtrap.io
3. You should see **5 emails** (one per opted-in test user)
4. Click any email to preview the HTML layout

---

## 8. Using Gmail (Alternative)

If you prefer to use a Gmail account instead of Mailtrap:

### Setup

1. Go to your Google Account → **Security → 2-Step Verification** (must be enabled)
2. Search for **"App Passwords"** in your Google Account settings
3. Create a new App Password for "Mail" — copy the 16-character password

### config.py settings

```python
SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USER     = "your.email@gmail.com"
SMTP_PASSWORD = "xxxx xxxx xxxx xxxx"   # 16-char App Password (spaces OK)
FROM_EMAIL    = "your.email@gmail.com"
FROM_NAME     = "Bear Pantry – Bears Share"
```

> ⚠️ With Gmail, emails go to **real inboxes**. For testing, make sure `mock_users.json` contains email addresses you control, or use Mailtrap instead.

---

## 9. Going to Production (MSU SMTP)

When ready to deploy for real, make exactly **two changes**:

### Change 1 — `config.py`: switch to MSU SMTP

```python
SMTP_SERVER   = "<MSU SMTP server address>"   # get from MSU IT
SMTP_PORT     = 587                            # confirm with MSU IT
SMTP_USER     = "<MSU email account>"
SMTP_PASSWORD = "<MSU email password>"
FROM_EMAIL    = "BearPantry@missouristate.edu"
FROM_NAME     = "Bear Pantry – Bears Share"
```

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

## 10. Mock Data Reference

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

## 11. Email Format

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

## 12. Replacing PantrySoft Mock with Real API

The codebase is designed so that **only `pantrysoft_mock.py` needs to change** when connecting to real data. The contract that file must fulfill:

```python
def get_optin_emails() -> list[str]:
    """Must return a list of email address strings for opted-in users."""
    ...
```

As long as this function returns a `list[str]`, the rest of the app works unchanged.

---

## 13. Troubleshooting

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
- Check that `SMTP_SERVER` and `SMTP_PORT` in `config.py` match your provider
- Mailtrap: `sandbox.smtp.mailtrap.io` port `2525`
- Gmail: `smtp.gmail.com` port `587`

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
