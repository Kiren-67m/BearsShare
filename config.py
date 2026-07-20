import os

# Bears Share — Configuration
# All values are loaded from environment variables (set in Render dashboard).
# For local testing, export them in your shell or temporarily hardcode below —
# but never commit real credentials to Git.

SMTP_SERVER   = os.environ.get("SMTP_SERVER",   "smtp.gmail.com")
SMTP_PORT     = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER     = os.environ.get("SMTP_USER",     "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "").replace('\xa0', ' ').strip()
FROM_EMAIL    = os.environ.get("FROM_EMAIL",    "") or SMTP_USER
FROM_NAME     = "Bear Pantry – Bears Share"

# Flask secret key for session management and unsubscribe-token signing
SECRET_KEY    = os.environ.get("SECRET_KEY",    "dev-secret-key-change-in-production")

# Access code required to send a broadcast (leave blank to disable the check)
ACCESS_CODE   = os.environ.get("ACCESS_CODE",   "")

# Database: SQLite locally, set DATABASE_URL to Render's Postgres in production
DATABASE_URL  = os.environ.get(
    "DATABASE_URL",
    "sqlite:///" + os.path.join(os.path.dirname(__file__), "bears_share.db"),
)

# Public base URL of the deployed app — used to build unsubscribe links
BASE_URL      = os.environ.get("BASE_URL", "http://localhost:5000")

# Physical mailing address shown in every email footer (CAN-SPAM requirement)
PHYSICAL_ADDRESS = os.environ.get(
    "PHYSICAL_ADDRESS",
    "Bear Pantry, Missouri State University, 901 S. National Ave, Springfield, MO 65897",
)
