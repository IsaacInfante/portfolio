"""Ejecutar: python -m unittest discover -s tests -v
Requiere pip install -r requirements.txt. No hace peticiones reales a Gemini.
"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

import requests

import app as app_module


class DigitalIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from werkzeug.security import generate_password_hash
        cls.password_hash = generate_password_hash("test-only-owner-password", method="scrypt:32768:8:1")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = app_module.create_app({
            "TESTING": True, "DATABASE_PATH": Path(self.tmp.name) / "test.db",
            "INSTANCE_ID": "", "SECRET_KEY": "test-only-random-secret-with-32-characters",
            "OWNER_PASSWORD_HASH": self.password_hash, "SESSION_COOKIE_SECURE": False,
            "GEMINI_API_KEY": "", "PUBLIC_BASE_URL": "",
        })
        self.client = self.app.test_client()
        token = self.client.get("/api/owner/session").get_json()["csrf_token"]
        login = self.client.post("/api/owner/login", json={"password": "test-only-owner-password"}, headers={"X-CSRF-Token": token})
        self.assertEqual(login.status_code, 200)
        self.csrf = login.get_json()["csrf_token"]
        self.context = self.app.app_context()
        self.context.push()

    def tearDown(self):
        self.context.pop()
        self.tmp.cleanup()

    def post(self, path, **kwargs):
        return self.client.post(path, headers={"X-CSRF-Token": self.csrf}, **kwargs)

    def test_owner_and_home(self):
        response = self.client.get("/p/isaac")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Portfolio", response.data)
        profile = self.client.get("/api/profile/isaac").get_json()
        self.assertEqual(profile["name"], "Isaac Infante Méndez")
        self.assertGreaterEqual(len(profile["projects"]), 3)

    def test_qr_and_vcard(self):
        qr = self.client.get("/api/qr/isaac")
        self.assertEqual(qr.status_code, 200)
        self.assertTrue(qr.data.startswith(b"\x89PNG\r\n\x1a\n"))
        vcard = self.client.get("/api/vcard/isaac")
        self.assertIn(b"BEGIN:VCARD", vcard.data)

    def test_profile_registration_connect_and_real_orchestration_contract(self):
        person = {"name": "Ana Pruebas", "role": "Desarrollo UX", "objective": "Colaborar en una app educativa de datos y experiencia de usuario",
                  "skills": ["Figma", "React", "UX research"], "hours": 3}
        registered = self.post("/api/profiles", json=person)
        self.assertEqual(registered.status_code, 201, registered.data)
        new_id = registered.get_json()["profile"]["id"]
        linked = self.post("/api/connections", json={"a": "isaac", "b": new_id})
        self.assertEqual(linked.status_code, 200)
        self.app.config["GEMINI_API_KEY"] = "TEST_VALUE_NOT_SENT"
        calls = []

        def fake_model(system_text, user_text, max_tokens=450):
            calls.append((system_text, user_text))
            return f"Respuesta artificial SOLO DEL TEST {len(calls)}"  # Nunca se usa en producción.

        with patch.object(app_module, "gemini_json", side_effect=fake_model):
            result = self.post("/api/agents/negotiate", json={"a": "isaac", "b": new_id, "demo_consent": True}, buffered=True)
            body = result.get_data(as_text=True)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(body.count("event: turn"), 6)
        self.assertEqual(body.count("event: proposal"), 1)
        self.assertEqual(len(calls), 7)
        self.assertIn("event: end", body)
        self.assertIn("Isaac Infante Méndez", calls[0][0])
        self.assertIn("Ana Pruebas", calls[1][0])
        self.assertNotIn("Ana Pruebas", calls[0][0])
        self.assertIn("Ana Pruebas", calls[0][1])

    def test_negotiate_requires_real_key(self):
        self.app.config["GEMINI_API_KEY"] = ""
        response = self.post("/api/agents/negotiate", json={"a": "isaac", "b": "anybody"})
        self.assertEqual(response.status_code, 400)  # Invalid profile; no pretend results.

    def test_gemini_request_and_thought_parts(self):
        reply = Mock()
        reply.json.return_value = {"candidates": [{"content": {"parts": [
            {"thought": True, "text": "internal"}, {"text": '{"message":"Propuesta real del proveedor"}'}
        ]}}]}
        with patch.dict(self.app.config, GEMINI_API_KEY="PRIVATE_TEST_KEY"), patch.object(app_module.requests, "post", return_value=reply) as post:
            self.assertEqual(app_module.gemini_json("reglas", "contexto"), "Propuesta real del proveedor")
            args, kwargs = post.call_args
            self.assertNotIn("PRIVATE_TEST_KEY", args[0])
            self.assertEqual(kwargs["headers"]["x-goog-api-key"], "PRIVATE_TEST_KEY")
            self.assertEqual(kwargs["json"]["generationConfig"]["responseMimeType"], "application/json")
            for path in ("/", "/api/status", "/api/profile/isaac", "/static/app.js"):
                with self.client.get(path) as public_response:
                    self.assertNotIn(b"PRIVATE_TEST_KEY", public_response.data)

    def test_provider_errors_do_not_expose_details(self):
        for code, expected in [(429, "límite de uso"), (403, "denegó"), (404, "no está disponible")]:
            reply = Mock(status_code=code, text="SECRET_PROVIDER_DETAIL")
            reply.raise_for_status.side_effect = requests.HTTPError(response=reply)
            with patch.dict(self.app.config, GEMINI_API_KEY="PRIVATE_TEST_KEY"), patch.object(app_module.requests, "post", return_value=reply):
                with self.assertRaisesRegex(RuntimeError, expected) as caught:
                    app_module.gemini_json("reglas", "contexto")
                self.assertNotIn("SECRET_PROVIDER_DETAIL", str(caught.exception))

    def test_connected_profiles_without_key_return_503(self):
        person = {"name": "Luis Pruebas", "role": "Software", "objective": "Colaborar en prototipos de sistemas embebidos", "skills": ["Python", "ESP32"]}
        pid = self.post("/api/profiles", json=person).get_json()["profile"]["id"]
        self.post("/api/connections", json={"a": "isaac", "b": pid})
        with patch.dict(self.app.config, GEMINI_API_KEY=""), patch.object(app_module.requests, "post") as post:
            response = self.post("/api/agents/negotiate", json={"a": "isaac", "b": pid, "demo_consent": True})
            self.assertEqual(response.status_code, 503)
            post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
