import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


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

    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    AI_REQUESTS_PER_HOUR = 20
    MAX_CONTENT_LENGTH = 128 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"
    WTF_CSRF_TIME_LIMIT = 3600
