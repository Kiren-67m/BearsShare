# BearsShare — Food Notification Prototype

A Flask application built as a demo for Missouri State University's Bear Pantry. Staff enter a food pickup notice; the app sends email to opted-in subscribers and records the broadcast.

## Implemented features

- Web form with required-field validation and an optional staff access code.
- Subscriber CSV import with SQLAlchemy storage: SQLite locally or PostgreSQL via `DATABASE_URL`.
- SMTP delivery of plain-text and HTML messages.
- Signed unsubscribe links, suppression across re-imports and send history.

**Scope:** This is a development prototype. Recipients come from a CSV import or bundled mock users; there is no live PantrySoft API integration. Deployment instructions do not imply an approved university production deployment.

## Architecture

```text
Staff form → Flask → subscriber DB / mock users → SMTP
                      ↓                          ↓
                   send log             signed unsubscribe link
```

## Local setup

```bash
git clone https://github.com/Kiren-67m/BearsShare.git
cd BearsShare
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set environment variables in your shell before starting the app. The code reads environment variables directly; copying `.env.example` to `.env` alone does not load them.

```bash
export SECRET_KEY="replace-with-a-local-development-secret"
export BASE_URL="http://localhost:5000"
export SMTP_SERVER="sandbox.smtp.mailtrap.io"
export SMTP_PORT="465"
export SMTP_USER="your-sandbox-username"
export SMTP_PASSWORD="your-sandbox-password"
export ACCESS_CODE="your-local-demo-access-code"
python app.py
```

Open `http://localhost:5000`. Use an email sandbox and the bundled mock recipients for a demo; configuring a real SMTP account makes the send action deliver email. No PantrySoft account is needed for the mock path.

## Where to look

| Path | Purpose |
| --- | --- |
| `app.py` | Form, CSV import, send, history and unsubscribe routes |
| `db.py` | Subscriber, suppression and send-log storage |
| `email_sender.py` | SMTP delivery and message formatting |
| `tokens.py` | Signed unsubscribe tokens |
| `pantrysoft_mock.py` | DB-backed recipients with mock fallback |
| `templates/` | Flask-rendered pages |
| `.env.example` | Configuration reference |

## Deployment considerations

The optional access code is a demo gate, not a complete identity or authorization system. Production use would require a review of authentication, CSRF protection, access to history, logging of recipient information and email-provider requirements. Keep subscriber exports, credentials and local databases out of Git.

[Detailed setup and operations guide](OPERATIONS.md) — deployment configuration, SMTP providers, route descriptions and troubleshooting. The guide preserves the project's original implementation notes.
