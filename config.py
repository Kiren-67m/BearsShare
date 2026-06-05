import os

# Bears Share — SMTP Configuration
# All values are loaded from environment variables (set in Render dashboard).
# For local testing, export them in your shell or temporarily hardcode below —
# but never commit real credentials to Git.

SMTP_SERVER   = os.environ.get("SMTP_SERVER",   "smtp.gmail.com")
SMTP_PORT     = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER     = os.environ.get("SMTP_USER",     "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
FROM_EMAIL    = os.environ.get("SMTP_USER",     "")
FROM_NAME     = "Bear Pantry – Bears Share"

# Flask secret key for session management
SECRET_KEY    = os.environ.get("SECRET_KEY",    "dev-secret-key-change-in-production")

# Optional access code to restrict form submission (leave blank to disable)
ACCESS_CODE   = os.environ.get("ACCESS_CODE",   "")
