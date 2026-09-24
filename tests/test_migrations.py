"""Run with python -m unittest discover -s tests -v. Uses temporary SQLite only."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from flask import g
from flask_migrate import downgrade, upgrade
import sqlalchemy as sa

from app import create_app
from app.extensions import db
from app.models import Ticket, User
from config import Config

MIGRATIONS = str(Path(__file__).resolve().parents[1] / "migrations")


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        uri = "sqlite:///" + (Path(self.temp.name) / "test.db").as_posix()
        self.config = patch.object(Config, "SQLALCHEMY_DATABASE_URI", uri)
        self.config.start()
        self.app = create_app()
        self.app.config.update(TESTING=True, SECRET_KEY="migration-test", WTF_CSRF_ENABLED=False)
        self.context = self.app.app_context()
        self.context.push()

    def tearDown(self):
        db.session.remove()
        db.engine.dispose()
        self.context.pop()
        self.config.stop()
        self.temp.cleanup()

    def migrate(self, revision="head"):
        upgrade(directory=MIGRATIONS, revision=revision)

    def assert_schema_matches_models(self):
        with db.engine.connect() as connection:
            context = MigrationContext.configure(connection)
            self.assertEqual(compare_metadata(context, db.metadata), [])

    def seed_legacy_ticket(self):
        with db.engine.begin() as connection:
            connection.execute(sa.text(
                "INSERT INTO tickets (id, title, description, status, created_at) "
                "VALUES (1, 'Existing ticket', 'Keep this data', 'Open', '2026-09-01 10:00:00')"
            ))

    def test_empty_database_and_ticket_workflow(self):
        self.assertEqual(sa.inspect(db.engine).get_table_names(), [])
        self.migrate()
        self.assert_schema_matches_models()
        user = User(username="user", role="User")
        support = User(username="support", role="IT Support")
        user.set_password("test-password")
        support.set_password("test-password")
        db.session.add_all([user, support])
        db.session.commit()
        user_id, support_id = user.id, support.id
        client = self.app.test_client()

        def login(user_id):
            g.pop("_login_user", None)
            with client.session_transaction() as session:
                session["_user_id"] = str(user_id)
                session["_fresh"] = True

        login(user_id)
        self.assertEqual(client.post("/create-ticket", data={
            "title": "Migration test", "description": "Test issue"
        }).status_code, 302)
        ticket_id = Ticket.query.one().id
        login(support_id)
        self.assertEqual(client.get("/it/dashboard").status_code, 200)
        self.assertEqual(client.post(f"/tickets/{ticket_id}/accept").status_code, 302)
        self.assertEqual(client.post(f"/tickets/{ticket_id}/resolve", data={
            "resolution_note": "Fixed"
        }).status_code, 302)
        login(user_id)
        self.assertEqual(client.post(f"/tickets/{ticket_id}/confirm-resolution", data={
            "confirmation": "fixed"
        }).status_code, 302)
        login(support_id)
        self.assertEqual(client.post(f"/tickets/{ticket_id}/status", data={
            "status": "Closed"
        }).status_code, 302)
        db.session.expire_all()
        ticket = db.session.get(Ticket, ticket_id)
        self.assertEqual(ticket.status, "Closed")
        self.assertEqual(ticket.resolution_note, "Fixed")
        self.assertIsNotNone(ticket.updated_at)
        self.assertIsNotNone(ticket.resolved_at)
        self.assertIsNotNone(ticket.closed_at)

    def test_ticket_detail_roles_and_states(self):
        self.migrate()
        users = [User(username=name, role=role, password_hash="test-only") for name, role in (
            ("owner", "User"), ("other", "User"), ("support", "IT Support"),
            ("admin", "Admin"), ("other-support", "IT Support"),
        )]
        db.session.add_all(users)
        db.session.flush()
        owner, other, support, admin, other_support = users
        ticket = Ticket(title="<script>alert(1)</script>", description="Test issue",
                        created_by_id=owner.id, assigned_to_id=support.id)
        db.session.add(ticket)
        db.session.commit()
        client = self.app.test_client()
        url = f"/tickets/{ticket.id}"
        self.assertEqual(client.get(url).status_code, 302)
        for status, confirmed in (("Open", None), ("In Progress", None),
                                  ("Resolved", None), ("Resolved", True), ("Closed", True)):
            ticket.status, ticket.resolution_confirmed = status, confirmed
            db.session.commit()
            for user in users:
                with self.subTest(status=status, confirmed=confirmed, role=user.username):
                    g.pop("_login_user", None)
                    with client.session_transaction() as session:
                        session["_user_id"] = str(user.id)
                        session["_fresh"] = True
                    response = client.get(url)
                    self.assertEqual(response.status_code, 403 if user == other else 200)
                    if user == other:
                        continue
                    html = response.get_data(as_text=True)
                    self.assertIn("&lt;script&gt;", html)
                    self.assertNotIn("<script>alert(1)</script>", html)
                    if user.role in ("Admin", "IT Support"):
                        self.assertIn('class="it-sidebar"', html)
                        self.assertEqual(html.count("<!doctype html>"), 1)
                        if status == "In Progress":
                            self.assertEqual(f'/tickets/{ticket.id}/resolve' in html,
                                             user in (support, admin))
                        if status == "Resolved" and confirmed:
                            self.assertEqual('value="Closed"' in html, user in (support, admin))
                    else:
                        self.assertNotIn('class="it-sidebar"', html)
                    self.assertEqual(ticket.status, status)

    def test_upgrade_previous_head_preserves_rows(self):
        self.migrate("1e6b9640cdac")
        self.seed_legacy_ticket()
        self.migrate()
        self.assert_schema_matches_models()
        ticket = db.session.get(Ticket, 1)
        self.assertEqual(ticket.description, "Keep this data")
        self.assertEqual(ticket.updated_at, ticket.created_at)
        self.assertIsNone(ticket.resolved_at)
        self.assertIsNone(ticket.closed_at)
        self.migrate()
        self.assertEqual(Ticket.query.count(), 1)

    def test_upgrade_early_revision_with_data(self):
        self.migrate("650b210f5706")
        with db.engine.begin() as connection:
            connection.execute(sa.text(
                "INSERT INTO tickets (id, title, description, status) "
                "VALUES (1, 'Early ticket', 'Keep early data', 'Open')"
            ))
        self.migrate()
        self.assert_schema_matches_models()
        ticket = db.session.get(Ticket, 1)
        self.assertEqual(ticket.description, "Keep early data")
        self.assertIsNotNone(ticket.created_at)
        self.assertEqual(ticket.updated_at, ticket.created_at)

    def test_historical_foreign_keys_can_be_downgraded(self):
        self.migrate("1e6b9640cdac")
        downgrade(directory=MIGRATIONS, revision="base")
        self.assertEqual(sa.inspect(db.engine).get_table_names(), ["alembic_version"])

    def test_partial_timestamp_schema(self):
        self.migrate("1e6b9640cdac")
        self.seed_legacy_ticket()
        with db.engine.begin() as connection:
            connection.execute(sa.text("ALTER TABLE tickets ADD COLUMN resolved_at DATETIME"))
            connection.execute(sa.text("UPDATE tickets SET resolved_at = '2026-09-03 12:00:00'"))
        self.migrate()
        self.assert_schema_matches_models()
        ticket = db.session.get(Ticket, 1)
        self.assertEqual(ticket.updated_at, ticket.created_at)
        self.assertEqual(ticket.resolved_at.isoformat(), "2026-09-03T12:00:00")
        self.assertIsNone(ticket.closed_at)

    def test_preserve_preexisting_timestamp_values(self):
        self.migrate("1e6b9640cdac")
        self.seed_legacy_ticket()
        with db.engine.begin() as connection:
            connection.execute(sa.text(
                "ALTER TABLE tickets ADD COLUMN updated_at DATETIME NOT NULL "
                "DEFAULT '2026-09-02 11:00:00'"
            ))
            for column in ("resolved_at", "closed_at"):
                connection.execute(sa.text(f"ALTER TABLE tickets ADD COLUMN {column} DATETIME"))
                connection.execute(sa.text(
                    f"UPDATE tickets SET {column} = '2026-09-03 12:00:00'"
                ))
        self.migrate()
        ticket = db.session.get(Ticket, 1)
        self.assertEqual(ticket.updated_at.isoformat(), "2026-09-02T11:00:00")
        self.assertEqual(ticket.resolved_at.isoformat(), "2026-09-03T12:00:00")
        self.assertEqual(ticket.closed_at.isoformat(), "2026-09-03T12:00:00")


if __name__ == "__main__":
    unittest.main()
