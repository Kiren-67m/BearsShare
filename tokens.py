"""
tokens.py – Signed unsubscribe tokens.

Each notification email carries a per-recipient unsubscribe link:
    {BASE_URL}/unsubscribe/<token>
The token is the recipient's email signed with the app SECRET_KEY, so links
can't be forged or tampered with, and no database lookup is needed to mint one.
"""

from itsdangerous import BadSignature, URLSafeSerializer

import config

_serializer = URLSafeSerializer(config.SECRET_KEY, salt="bears-share-unsubscribe")


def generate_unsubscribe_token(email: str) -> str:
    return _serializer.dumps(email.strip().lower())


def verify_unsubscribe_token(token: str) -> str | None:
    """Returns the email if the token is valid, else None."""
    try:
        return _serializer.loads(token)
    except BadSignature:
        return None


def unsubscribe_url(email: str) -> str:
    return f"{config.BASE_URL.rstrip('/')}/unsubscribe/{generate_unsubscribe_token(email)}"
