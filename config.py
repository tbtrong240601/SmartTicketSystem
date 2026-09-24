import os


class Config:
    # Development fallback only; set SECRET_KEY in deployed environments.
    SECRET_KEY = os.environ.get("SECRET_KEY") or "smart-ticket-dev-only-key"

    # Preserve the existing local MySQL setup when no override is provided.
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("SQLALCHEMY_DATABASE_URI")
        or os.environ.get("DATABASE_URL")
        or "mysql+pymysql://root:@localhost/smart_ticket_db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
