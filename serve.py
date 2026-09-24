"""Local Windows-friendly server. No debug mode and no implicit database changes."""
import os
from pathlib import Path
import secrets

root = Path(__file__).resolve().parent
os.chdir(root)
env_file = root / ".env"
if not env_file.exists() and not os.environ.get("SECRET_KEY"):
    env_file.write_text("SECRET_KEY=" + secrets.token_urlsafe(48) + "\n", encoding="utf-8")

from app import create_app
from app.extensions import db
from sqlalchemy import text
from waitress import serve

app = create_app()
with app.app_context():
    try:
        revision = db.session.execute(text("SELECT version_num FROM alembic_version")).scalar()
    except Exception:
        raise SystemExit("Database not ready. Start MySQL and run: python -m flask --app run db upgrade") from None
    if revision != "000000000003":
        raise SystemExit("Database migration required: python -m flask --app run db upgrade")
    db.session.remove()

if __name__ == "__main__":
    print("SmartTicket: http://127.0.0.1:5000", flush=True)
    serve(app, host="127.0.0.1", port=5000, threads=4)
