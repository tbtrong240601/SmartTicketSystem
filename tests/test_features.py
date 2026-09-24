from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch, Mock
from flask import g
from flask_migrate import upgrade
import requests
from app import create_app
from app.extensions import db
from app.models import User, Category, Ticket, KnowledgeArticle, AuditEvent, AIRequest
from app.services.ai import answer, retrieve


class FeatureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-only", "GROQ_API_KEY": "", "AI_REQUESTS_PER_HOUR": 20,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + (Path(self.temp.name) / "test.db").as_posix()})
        self.context = self.app.app_context()
        self.context.push()
        upgrade(directory=str(Path(__file__).resolve().parents[1] / "migrations"))
        self.people = {}
        for name, role in (("admin", "Admin"), ("support", "IT Support"), ("owner", "User"), ("other", "User")):
            user = User(username=name, role=role)
            user.set_password("password123")
            db.session.add(user)
            self.people[name] = user
        db.session.flush()
        self.category = Category(name="Network")
        db.session.add(self.category)
        db.session.flush()
        self.ticket = Ticket(title="Wi-Fi disconnected", description="No network", status="Open",
            created_by_id=self.people["owner"].id, category_id=self.category.id)
        self.article = KnowledgeArticle(title="Wi-Fi network", content="Restart Wi-Fi connection and check the approved network name. Contact IT if the issue persists.",
            author_id=self.people["admin"].id, published=True, category_id=self.category.id)
        self.draft = KnowledgeArticle(title="Wi-Fi private draft", content="PRIVATE-DRAFT-CONTENT",
            author_id=self.people["support"].id, published=False)
        db.session.add_all([self.ticket, self.article, self.draft])
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.engine.dispose()
        self.context.pop()
        self.temp.cleanup()

    def login(self, name):
        g.pop("_login_user", None)
        with self.client.session_transaction() as session:
            session.clear()
            session["_user_id"] = str(self.people[name].id)
            session["_fresh"] = True

    def test_all_admin_screens_render(self):
        self.login("admin")
        for url in ("/", "/admin/", "/admin/users", "/admin/categories", "/admin/audit", "/knowledge/", "/knowledge/new", f"/knowledge/{self.article.id}", "/ai/", "/account", "/it/dashboard"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        export = self.client.get("/admin/export.csv")
        self.assertEqual(export.status_code, 200)
        self.assertIn("Wi-Fi disconnected", export.get_data(as_text=True))

    def test_role_boundaries(self):
        for name in ("owner", "support"):
            self.login(name)
            self.assertEqual(self.client.get("/admin/").status_code, 403)
            self.assertEqual(self.client.post("/admin/categories", data={"name":"Hacked"}).status_code, 403)
        self.login("owner")
        self.assertEqual(self.client.get("/knowledge/new").status_code, 403)
        self.assertEqual(self.client.get(f"/knowledge/{self.draft.id}").status_code, 404)
        self.assertNotIn(self.draft, retrieve("Wi-Fi"))
        self.login("other")
        self.assertEqual(self.client.get(f"/ai/?ticket_id={self.ticket.id}").status_code, 403)
        self.assertEqual(self.client.post(f"/tickets/{self.ticket.id}/comments", data={"content":"test"}).status_code, 403)

    def test_category_crud_and_references(self):
        self.login("admin")
        self.client.post("/admin/categories", data={"name":"Hardware", "description":"Devices"})
        category = Category.query.filter_by(name="Hardware").one()
        self.client.post(f"/admin/categories/{category.id}/edit", data={"name":"Devices", "description":"Updated"})
        self.assertEqual(category.name, "Devices")
        self.client.post(f"/admin/categories/{category.id}/delete")
        self.assertIsNone(db.session.get(Category, category.id))
        self.client.post(f"/admin/categories/{self.category.id}/delete")
        self.assertIsNotNone(db.session.get(Category, self.category.id))
        self.client.post("/admin/categories", data={"name":"Network"})
        self.assertEqual(Category.query.count(), 1)

    def test_users_create_disable_and_last_admin(self):
        self.login("admin")
        self.assertEqual(self.client.post("/admin/users", data={"username":"newuser", "password":"password123", "role":"IT Support"}).status_code, 302)
        new = User.query.filter_by(username="newuser").one()
        self.assertTrue(new.check_password("password123"))
        self.client.post(f"/admin/users/{new.id}/edit", data={"role":"User"})
        self.assertFalse(new.enabled)
        self.assertEqual(self.client.post(f"/admin/users/{self.people['admin'].id}/edit", data={"role":"User", "enabled":"on"}).status_code, 400)
        self.assertEqual(self.people["admin"].role, "Admin")

    def test_disable_assignee_with_open_work_is_blocked(self):
        self.ticket.assigned_to_id = self.people["support"].id
        db.session.commit()
        self.login("admin")
        self.assertEqual(self.client.post(f"/admin/users/{self.people['support'].id}/edit", data={"role":"IT Support"}).status_code, 400)
        self.assertTrue(self.people["support"].enabled)

    def test_knowledge_draft_publish_and_search(self):
        self.login("support")
        self.client.post("/knowledge/new", data={"title":"Printer guide", "content":"Check printer power, paper and approved print queue.", "published":"on"})
        article = KnowledgeArticle.query.filter_by(title="Printer guide").one()
        self.assertFalse(article.published)
        self.login("admin")
        self.client.post(f"/knowledge/{article.id}/edit", data={"title":article.title, "content":article.content, "published":"on"})
        self.assertTrue(article.published)
        self.login("owner")
        self.assertIn("Printer guide", self.client.get("/knowledge/?q=Printer").get_data(as_text=True))
        self.login("support")
        self.assertEqual(self.client.get(f"/knowledge/{article.id}/edit").status_code, 403)

    def test_ticket_to_knowledge_is_draft(self):
        self.ticket.status = "Closed"
        self.ticket.resolution_note = "Check the approved printer queue and retry printing."
        self.ticket.assigned_to_id = self.people["support"].id
        db.session.commit()
        self.login("support")
        self.assertEqual(self.client.post(f"/knowledge/from-ticket/{self.ticket.id}").status_code, 302)
        created = KnowledgeArticle.query.order_by(KnowledgeArticle.id.desc()).first()
        self.assertFalse(created.published)
        self.assertEqual(created.content, self.ticket.resolution_note)

    def test_ai_without_key_never_calls_provider(self):
        self.login("owner")
        with patch("app.services.ai.requests.post") as provider:
            response = self.client.post("/ai/", data={"question":"Wi-Fi not working", "external":"on"})
            self.assertEqual(response.status_code, 200)
            self.assertIn("Wi-Fi network", response.get_data(as_text=True))
            provider.assert_not_called()
        self.assertEqual(AIRequest.query.one().mode, "knowledge")

    def test_ai_mocked_success_redacts_and_does_not_mutate_ticket(self):
        self.app.config["GROQ_API_KEY"] = "test-key"
        self.login("owner")
        response = Mock()
        response.json.return_value = {"choices":[{"message":{"content":"Check Wi-Fi [KB 1]"}}]}
        with patch("app.services.ai.requests.post", return_value=response) as provider:
            result = self.client.post("/ai/", data={"question":"Wi-Fi password=secret-value test@example.com", "ticket_id":self.ticket.id, "external":"on"})
            self.assertEqual(result.status_code, 200)
            sent = str(provider.call_args.kwargs["json"])
            self.assertNotIn("secret-value", sent)
            self.assertNotIn("test@example.com", sent)
        self.assertEqual(self.ticket.status, "Open")
        self.assertEqual(AIRequest.query.one().mode, "groq")

    def test_ai_failure_falls_back_and_escapes_html(self):
        self.app.config["GROQ_API_KEY"] = "test-key"
        with patch("app.services.ai.requests.post", side_effect=requests.Timeout):
            result = answer("Wi-Fi", [self.article], True)
            self.assertEqual(result["mode"], "fallback")
        self.login("owner")
        response = Mock()
        response.json.return_value = {"choices":[{"message":{"content":"<script>alert(1)</script>"}}]}
        with patch("app.services.ai.requests.post", return_value=response):
            html = self.client.post("/ai/", data={"question":"Wi-Fi failure", "external":"on"}).get_data(as_text=True)
            self.assertIn("&lt;script&gt;", html)
            self.assertNotIn("<script>alert(1)</script>", html)

    def test_ai_malformed_provider_response(self):
        self.app.config["GROQ_API_KEY"] = "test-key"
        for payload in ({}, {"choices": []}, {"choices": [{"message": {"content": None}}]}):
            with self.subTest(payload=payload):
                response = Mock()
                response.json.return_value = payload
                with patch("app.services.ai.requests.post", return_value=response):
                    self.assertEqual(answer("Wi-Fi", [self.article], True)["mode"], "fallback")

    def test_password_change(self):
        self.login("owner")
        self.client.post("/account", data={"old_password":"wrong", "password":"replacement123"})
        self.assertTrue(self.people["owner"].check_password("password123"))
        self.client.post("/account", data={"old_password":"password123", "password":"replacement123"})
        self.assertTrue(self.people["owner"].check_password("replacement123"))

    def test_ai_requires_opt_in_and_sources(self):
        self.app.config["GROQ_API_KEY"] = "test-key"
        with patch("app.services.ai.requests.post") as provider:
            self.assertEqual(answer("Wi-Fi", [self.article], False)["mode"], "knowledge")
            self.assertEqual(answer("unknown", [], True)["mode"], "knowledge")
            provider.assert_not_called()

    def test_ai_quota(self):
        self.login("owner")
        self.app.config["AI_REQUESTS_PER_HOUR"] = 1
        self.assertEqual(self.client.post("/ai/", data={"question":"Wi-Fi failure"}).status_code, 200)
        self.assertEqual(self.client.post("/ai/", data={"question":"Wi-Fi failure"}).status_code, 429)

    def test_invalid_ticket_inputs_and_closed_comments(self):
        self.login("owner")
        self.assertEqual(self.client.post("/create-ticket", data={"title":"", "description":"x"}).status_code, 400)
        self.assertEqual(self.client.post("/create-ticket", data={"title":"Test", "description":"x", "category_id":"abc"}).status_code, 400)
        self.ticket.status = "Closed"
        db.session.commit()
        self.assertEqual(self.client.post(f"/tickets/{self.ticket.id}/comments", data={"content":"test"}).status_code, 400)
        self.login("support")
        self.assertEqual(self.client.get("/it/dashboard?category_id=abc").status_code, 400)

    def test_resolution_confirmation_and_audit(self):
        self.login("support")
        self.client.post(f"/tickets/{self.ticket.id}/accept")
        self.assertEqual(self.ticket.status, "In Progress")
        self.assertEqual(self.client.post(f"/tickets/{self.ticket.id}/status", data={"status":"Resolved"}).status_code, 400)
        self.client.post(f"/tickets/{self.ticket.id}/resolve", data={"resolution_note":"Fixed wireless network"})
        self.client.post(f"/tickets/{self.ticket.id}/status", data={"status":"Closed"})
        self.assertEqual(self.ticket.status, "Resolved")
        self.login("owner")
        self.client.post(f"/tickets/{self.ticket.id}/confirm-resolution", data={"confirmation":"not_fixed"})
        self.assertEqual(self.ticket.status, "In Progress")
        self.assertIsNone(self.ticket.resolved_at)
        self.assertGreater(AuditEvent.query.filter_by(ticket_id=self.ticket.id).count(), 0)

    def test_csrf_and_logout(self):
        self.app.config["WTF_CSRF_ENABLED"] = True
        self.assertEqual(self.client.post("/login", data={"username":"admin", "password":"password123"}).status_code, 400)
        html = self.client.get("/login").get_data(as_text=True)
        token = re.search('name="csrf_token" value="([^"]+)"', html).group(1)
        self.assertEqual(self.client.post("/login", data={"username":"admin", "password":"password123", "csrf_token":token}).status_code, 302)
        g.pop("_login_user", None)
        self.assertEqual(self.client.get("/logout").status_code, 405)
        self.assertEqual(self.client.post("/logout", data={"csrf_token":token}).status_code, 302)

    def test_login_backoff(self):
        for _ in range(10):
            self.client.post("/login", data={"username":"admin", "password":"wrong"})
        self.assertEqual(self.client.post("/login", data={"username":"admin", "password":"password123"}).status_code, 429)

    def test_csv_formula_is_neutralized(self):
        self.ticket.title = "=HYPERLINK(test)"
        db.session.commit()
        self.login("admin")
        self.assertIn("'=HYPERLINK(test)", self.client.get("/admin/export.csv").get_data(as_text=True))

    def test_disabled_login_and_registration(self):
        self.people["owner"].enabled = False
        db.session.commit()
        response = self.client.post("/login", data={"username":"owner", "password":"password123"})
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as session:
            self.assertNotIn("_user_id", session)
        self.client.post("/register", data={"username":"registered", "password":"password123", "role":"Admin"})
        self.assertEqual(User.query.filter_by(username="registered").one().role, "User")


if __name__ == "__main__":
    unittest.main()
