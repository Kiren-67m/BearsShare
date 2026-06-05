import os

# Bears Share — SMTP Configuration
# Credentials are loaded from environment variables (set in Render dashboard)
# For local testing, you can temporarily hardcode values here — but never commit real credentials to Git

SMTP_SERVER   = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USER     = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
FROM_EMAIL    = os.environ.get("SMTP_USER", "")
FROM_NAME     = "Bear Pantry – Bears Share"

# Flask secret key for session management
SECRET_KEY    = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
