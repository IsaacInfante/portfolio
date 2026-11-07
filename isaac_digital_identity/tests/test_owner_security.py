"""Stage 1: no external provider calls, real owner files or credentials needed."""
import copy
import json
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from werkzeug.security import generate_password_hash

import app as module
from owner_auth import cookie_name


class OwnerSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password = "test-only-long-password"
        cls.password_hash = generate_password_hash(cls.password, method="scrypt:32768:8:1")
        cls.base_owner = {
            "id": "student-a", "name": "Student A Test", "role": "Software",
            "short_name": "Student A", "initials": "SA", "subtitle": "Engineering",
            "email": "business@example.test", "phone": "PRIVATE_PHONE_SENTINEL",
            "objective": "COLLABORATION_OBJECTIVE_SENTINEL", "interests": ["IoT"],
            "constraints": {"max_hours_week": 3, "prohibited": ["PRIVATE_RULE_SENTINEL"]},
            "agent_config": {"secret": "PRIVATE_CONFIG_SENTINEL"},
            "extra": "UNKNOWN_PRIVATE_SENTINEL",
            "projects": [{"id": "project", "title": "Test Project", "description": "Academic",
                          "private_notes": "NESTED_PRIVATE_SENTINEL", "tags": ["Python"]}],
            "skills": [{"name": "Software", "items": ["Python"], "token": "NESTED_TOKEN_SENTINEL"}],
        }

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.a = self.build("a")
        self.client = self.a.test_client()

    def tearDown(self):
        # Windows will fail here if any request leaves SQLite handles open.
        self.tmp.cleanup()

    def build(self, name, **overrides):
        owner = copy.deepcopy(self.base_owner)
        owner["id"] = "student-" + name
        owner["name"] = "Student " + name.upper() + " Test"
        path = self.root / (name + ".json")
        if not path.exists():
            path.write_text(json.dumps(owner), encoding="utf-8")
        config = {
            "TESTING": True, "OWNER_PROFILE_PATH": path,
            "DATABASE_PATH": self.root / (name + ".db"), "INSTANCE_ID": "",
            "OWNER_PASSWORD_HASH": self.password_hash,
            "SECRET_KEY": "test-only-secret-for-instance-" + name + "-with-enough-entropy",
            "SESSION_COOKIE_SECURE": False, "PUBLIC_BASE_URL": "",
            "GEMINI_API_KEY": "", "GEMINI_MODEL": "gemini-3.5-flash-lite",
        }
        config.update(overrides)
        return module.create_app(config)

    def login(self, client=None):
        client = client or self.client
        challenge = client.get("/api/owner/session")
        self.assertEqual(challenge.status_code, 200)
        csrf = challenge.get_json()["csrf_token"]
        result = client.post("/api/owner/login", json={"password": self.password}, headers={"X-CSRF-Token": csrf})
        self.assertEqual(result.status_code, 200)
        return result.get_json()["csrf_token"]

    def guest(self, client, csrf):
        result = client.post("/api/profiles", json={
            "name": "Guest Test", "role": "Engineering", "objective": "Build academic embedded prototypes",
            "skills": ["Python", "ESP32"],
        }, headers={"X-CSRF-Token": csrf})
        self.assertEqual(result.status_code, 201)
        return result.get_json()["profile"]["id"]

    def test_independent_profiles_databases_and_stable_identity(self):
        b = self.build("b")
        cb = b.test_client()
        self.assertNotEqual(self.a.config["INSTANCE_ID"], b.config["INSTANCE_ID"])
        self.assertEqual(self.build("a").config["INSTANCE_ID"], self.a.config["INSTANCE_ID"])
        self.assertEqual(self.client.get("/api/status").get_json()["owner_id"], "student-a")
        self.assertEqual(cb.get("/api/status").get_json()["owner_id"], "student-b")
        self.assertIn(b"Student B Test", cb.get("/").data)
        self.assertNotIn(b"Isaac", cb.get("/").data)
        self.assertEqual(cb.get("/p/student-a").status_code, 404)
        csrf = self.login()
        pid = self.guest(self.client, csrf)
        self.assertEqual(self.client.get("/api/profile/" + pid).status_code, 200)
        self.assertNotIn(b"Build academic embedded prototypes", self.client.get("/api/profile/" + pid).data)
        self.assertEqual(cb.get("/api/profile/" + pid).status_code, 404)
        self.assertEqual(cb.get("/api/owner/profile").status_code, 401)
        with self.assertRaisesRegex(ValueError, "otro propietario"):
            self.build("b", DATABASE_PATH=self.a.config["DATABASE_PATH"])
        with self.assertRaisesRegex(ValueError, "no coincide"):
            self.build("a", INSTANCE_ID="00000000-0000-4000-8000-000000000001")

    def test_public_routes_exclude_private_and_unknown_nested_data(self):
        for path in ("/", "/api/profile/student-a", "/api/status", "/api/vcard/student-a"):
            with self.client.get(path) as response:
                self.assertEqual(response.status_code, 200)
                data = response.get_data(as_text=True)
                for sentinel in ("PRIVATE_PHONE", "COLLABORATION_OBJECTIVE", "PRIVATE_RULE", "PRIVATE_CONFIG",
                                 "UNKNOWN_PRIVATE", "NESTED_PRIVATE", "NESTED_TOKEN"):
                    self.assertNotIn(sentinel, data)
        profile = self.client.get("/api/profile/student-a").get_json()
        self.assertEqual(profile["projects"][0]["title"], "Test Project")
        self.assertEqual(profile["email"], "business@example.test")
        csrf = self.login()
        private = self.client.get("/api/owner/profile").get_json()
        self.assertIn("objective", private["collaboration_candidates"])
        self.assertNotIn("constraints", private["collaboration_candidates"])
        self.assertIn("prohibited", private["private_agent_config"])
        self.assertFalse(private["collaboration_authorized"])
        self.assertNotIn("SECRET_KEY", json.dumps(private))
        self.assertTrue(csrf)

    def test_contact_privacy_applies_to_vcard_and_html(self):
        owner = copy.deepcopy(self.base_owner)
        owner["privacy"] = {"public_fields": ["about", "projects", "phone", "constraints"]}
        app = self.build("hidden", OWNER=owner)
        client = app.test_client()
        for path in ("/", "/api/profile/student-a", "/api/vcard/student-a"):
            with client.get(path) as response:
                self.assertEqual(response.status_code, 200)
                self.assertNotIn(b"business@example.test", response.data)
                self.assertNotIn(b"PRIVATE_PHONE_SENTINEL", response.data)
        self.assertNotIn("constraints", client.get("/api/profile/student-a").get_json())

    def test_public_cannot_mutate_or_consume_gemini(self):
        with patch.object(module, "gemini_json") as model:
            for path in ("/api/profiles", "/api/connections", "/api/agents/negotiate", "/api/owner/logout"):
                self.assertEqual(self.client.post(path, json={}).status_code, 401)
            model.assert_not_called()
        self.assertEqual(self.client.get("/api/owner/profile").status_code, 401)

    def test_csrf_required_for_login_and_all_mutations(self):
        challenge = self.client.get("/api/owner/session").get_json()["csrf_token"]
        self.assertEqual(self.client.post("/api/owner/login", json={"password": self.password}).status_code, 403)
        self.assertEqual(self.client.post("/api/owner/login", json={"password": self.password}, headers={"X-CSRF-Token": challenge, "Origin": "https://attacker.test"}).status_code, 403)
        csrf = self.login()
        self.assertNotEqual(challenge, csrf)
        for path in ("/api/profiles", "/api/connections", "/api/agents/negotiate", "/api/owner/logout"):
            for headers in ({}, {"X-CSRF-Token": "wrong"}, {"X-CSRF-Token": csrf, "Origin": "http://localhost:5002"},
                            {"X-CSRF-Token": csrf, "Sec-Fetch-Site": "cross-site"}):
                self.assertEqual(self.client.post(path, json={}, headers=headers).status_code, 403)
        other = self.a.test_client()
        self.login(other)
        self.assertEqual(other.post("/api/profiles", json={}, headers={"X-CSRF-Token": csrf}).status_code, 403)

    def test_wrong_password_and_login_rate_limit(self):
        token = self.client.get("/api/owner/session").get_json()["csrf_token"]
        for _ in range(5):
            result = self.client.post("/api/owner/login", json={"password": "wrong"}, headers={"X-CSRF-Token": token})
            self.assertEqual(result.status_code, 401)
        self.assertEqual(self.client.post("/api/owner/login", json={"password": self.password}, headers={"X-CSRF-Token": token}).status_code, 429)

    def test_logout_revokes_cookie_replay_and_expiration(self):
        csrf = self.login()
        with self.a.app_context():
            name = cookie_name()
        stolen = self.client.get_cookie(name).value
        self.assertEqual(self.client.post("/api/owner/logout", json={}, headers={"X-CSRF-Token": csrf}).status_code, 200)
        self.client.set_cookie(name, stolen)
        self.assertEqual(self.client.get("/api/owner/profile").status_code, 401)
        self.login()
        with self.a.app_context(), module.database() as db:
            db.execute("UPDATE owner_sessions SET expires=?", (time.time() - 1,))
        self.assertEqual(self.client.get("/api/owner/profile").status_code, 401)

    def test_instances_reject_each_others_sessions(self):
        self.login()
        with self.a.app_context():
            name_a = cookie_name()
        value = self.client.get_cookie(name_a).value
        b = self.build("b")
        client = b.test_client()
        with b.app_context():
            name_b = cookie_name()
        self.assertNotEqual(name_a, name_b)
        client.set_cookie(name_b, value)
        self.assertEqual(client.get("/api/owner/profile").status_code, 401)

    def test_cookies_headers_and_disabled_configuration(self):
        app = self.build("secure", SESSION_COOKIE_SECURE=True)
        result = app.test_client().get("/api/owner/session", base_url="https://localhost")
        cookie = result.headers["Set-Cookie"]
        for flag in ("Secure", "HttpOnly", "SameSite=Strict"):
            self.assertIn(flag, cookie)
        self.assertEqual(result.headers["Cache-Control"], "no-store")
        self.assertEqual(app.test_client().get("/api/owner/session").status_code, 403)
        self.assertEqual(self.client.get("/api/owner/session", base_url="http://192.168.1.50").status_code, 403)
        self.assertEqual(self.client.get("/api/owner/session", environ_overrides={"REMOTE_ADDR": "192.168.1.50"}).status_code, 403)
        disabled = self.build("disabled", SECRET_KEY=None, OWNER_PASSWORD_HASH="").test_client()
        self.assertFalse(disabled.get("/api/owner/session").get_json()["configured"])
        self.assertEqual(disabled.post("/api/agents/negotiate", json={}).status_code, 503)
        self.assertEqual(disabled.get("/").status_code, 200)
        with self.assertRaises(ValueError):
            self.build("bad", SECRET_KEY="insecure")
        with self.assertRaises(ValueError):
            self.build("bad-hash", OWNER_PASSWORD_HASH="plaintext-not-allowed")

    def test_invalid_json_and_demo_without_owner_are_rejected(self):
        csrf = self.login()
        headers = {"X-CSRF-Token": csrf}
        for path in ("/api/profiles", "/api/connections", "/api/agents/negotiate"):
            self.assertEqual(self.client.post(path, json=[], headers=headers).status_code, 400)
            self.assertEqual(self.client.post(path, data="text", headers=headers).status_code, 415)
        p1 = self.guest(self.client, csrf)
        p2 = self.guest(self.client, csrf)
        with patch.object(module, "gemini_json") as model:
            result = self.client.post("/api/agents/negotiate", json={"a": p1, "b": p2, "demo_consent": True}, headers=headers)
            self.assertEqual(result.status_code, 403)
            model.assert_not_called()

    def test_demo_requires_explicit_consent_and_local_owner(self):
        csrf = self.login()
        pid = self.guest(self.client, csrf)
        headers = {"X-CSRF-Token": csrf}
        self.client.post("/api/connections", json={"a": "student-a", "b": pid}, headers=headers)
        with patch.object(module, "gemini_json") as model:
            response = self.client.post("/api/agents/negotiate", json={"a": "student-a", "b": pid}, headers=headers)
            self.assertEqual(response.status_code, 403)
            model.assert_not_called()
        self.assertFalse(self.client.get("/api/status").get_json()["federation_enabled"])

    def test_sqlite_closes_on_success_and_rollback(self):
        with self.a.app_context():
            with module.database() as connection:
                connection.execute("SELECT 1")
            with self.assertRaises(sqlite3.ProgrammingError):
                connection.execute("SELECT 1")
            with self.assertRaises(RuntimeError):
                with module.database() as failed:
                    failed.execute("INSERT INTO instance_metadata VALUES ('rollback-test','value')")
                    raise RuntimeError("test-only failure")
            with self.assertRaises(sqlite3.ProgrammingError):
                failed.execute("SELECT 1")
            with module.database() as db:
                self.assertIsNone(db.execute("SELECT value FROM instance_metadata WHERE key='rollback-test'").fetchone())
        # Rename immediately, without GC or sleeping: detects leaked Windows handles.
        path = self.a.config["DATABASE_PATH"]
        moved = path.with_suffix(".closed")
        path.rename(moved)
        moved.rename(path)

    def test_revocation_stops_next_model_call_in_active_demo(self):
        csrf = self.login()
        pid = self.guest(self.client, csrf)
        headers = {"X-CSRF-Token": csrf}
        self.client.post("/api/connections", json={"a": "student-a", "b": pid}, headers=headers)
        self.a.config["GEMINI_API_KEY"] = "FAKE_TEST_ONLY_NOT_SENT"
        def revoke(*args, **kwargs):
            with module.database() as db:
                db.execute("DELETE FROM owner_sessions")
            return "Test-only generated message"
        with patch.object(module, "gemini_json", side_effect=revoke) as model, self.assertLogs(self.a.logger, level="ERROR"):
            response = self.client.post("/api/agents/negotiate", json={"a": "student-a", "b": pid, "demo_consent": True}, headers=headers, buffered=True)
        self.assertEqual(model.call_count, 1)
        body = response.get_data(as_text=True)
        self.assertIn("event: error", body)
        self.assertNotIn("event: proposal", body)


if __name__ == "__main__":
    unittest.main()
