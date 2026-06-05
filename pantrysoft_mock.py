"""
pantrysoft_mock.py – Simulates a PantrySoft API call.

Returns the list of users who have opted in to Bears Share notifications.

TO REPLACE WITH REAL API:
    Swap this module's get_optin_recipients() function with an actual
    HTTP request to the PantrySoft API endpoint. The rest of the app
    (app.py, email_sender.py) does not need to change.
"""

import json
import os

MOCK_DATA_PATH = os.path.join(os.path.dirname(__file__), "mock_users.json")


def get_optin_recipients() -> list[dict]:
    """
    Returns a list of user dicts for everyone opted in to Bears Share.
    Each dict contains at minimum: 'name', 'email'.
    """
    with open(MOCK_DATA_PATH, "r") as f:
        users = json.load(f)

    opted_in = [u for u in users if u.get("bears_share_optin") is True]
    print(f"[PantrySoft] Found {len(opted_in)} opted-in recipients "
          f"out of {len(users)} total users.")
    return opted_in


def get_optin_emails() -> list[str]:
    """Convenience wrapper – returns only the email addresses."""
    return [u["email"] for u in get_optin_recipients()]
