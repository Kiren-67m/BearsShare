"""
pantrysoft_mock.py – Data source for the opt-in recipient list.

The recipient list now comes from the database, populated by uploading a
PantrySoft CSV export on the /subscribers page. If no CSV has been imported
yet, it falls back to the bundled mock_users.json so the demo still works.

Either way, anyone on the suppression list (clicked unsubscribe) is filtered
out permanently — even after the subscriber list is re-imported.

TO REPLACE WITH THE REAL PANTRYSOFT API:
    Only this module's get_optin_recipients() needs to change. The rest of
    the app (app.py, email_sender.py) does not need to change. Example:

        import requests
        def get_optin_recipients() -> list[dict]:
            resp = requests.get(
                "https://api.pantrysoft.com/v1/clients",
                headers={"Authorization": f"Bearer {config.PANTRYSOFT_API_KEY}"},
                params={"optin": "bears_share"},
                timeout=15,
            )
            resp.raise_for_status()
            users = [{"name": u["name"], "email": u["email"]}
                     for u in resp.json()["clients"]]
            return [u for u in users if not db.is_suppressed(u["email"])]
"""

import json
import os

import db

MOCK_DATA_PATH = os.path.join(os.path.dirname(__file__), "mock_users.json")


def get_optin_recipients() -> list[dict]:
    """
    Returns a list of user dicts for everyone opted in to Bears Share.
    Each dict contains at minimum: 'name', 'email'.
    """
    if db.subscriber_count() > 0:
        recipients = db.get_active_subscribers()
        print(f"[Subscribers] {len(recipients)} active recipients from database "
              f"({db.suppressed_count()} suppressed).")
        return recipients

    # Fallback: no CSV imported yet — use bundled mock data (demo mode)
    with open(MOCK_DATA_PATH, "r") as f:
        users = json.load(f)
    opted_in = [
        u for u in users
        if u.get("bears_share_optin") is True and not db.is_suppressed(u["email"])
    ]
    print(f"[Subscribers] Database empty — falling back to mock data: "
          f"{len(opted_in)} opted-in recipients out of {len(users)} total users.")
    return opted_in


def get_optin_emails() -> list[str]:
    """Convenience wrapper – returns only the email addresses."""
    return [u["email"] for u in get_optin_recipients()]
