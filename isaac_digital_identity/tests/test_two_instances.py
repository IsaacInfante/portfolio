"""Two actual Flask processes with independent synthetic config and SQLite."""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


class TwoProcessTests(unittest.TestCase):
    def test_independent_env_files_and_public_http_flows(self):
        processes = []
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            try:
                for label in ("a", "b"):
                    profile = temporary / (label + ".json")
                    profile.write_text(json.dumps({
                        "id": "student-" + label, "name": "Student Test " + label,
                        "role": "Software", "projects": [], "skills": [],
                        "constraints": {"prohibited": ["PRIVATE_TEST_RULE"]},
                    }), encoding="utf-8")
                    config = temporary / (label + ".env")
                    config.write_text(
                        f'OWNER_PROFILE_PATH="{profile.as_posix()}"\n'
                        f'DATABASE_PATH="{(temporary / (label + ".db")).as_posix()}"\n'
                        'GEMINI_API_KEY=\nSECRET_KEY=\nOWNER_PASSWORD_HASH=\n', encoding="utf-8"
                    )
                    env = os.environ.copy()
                    for key in ("OWNER_PROFILE_PATH", "DATABASE_PATH", "INSTANCE_ID", "GEMINI_API_KEY",
                                "GEMINI_MODEL", "SECRET_KEY", "OWNER_PASSWORD_HASH", "PUBLIC_BASE_URL"):
                        env.pop(key, None)
                    env["PORTFOLIO_ENV_FILE"] = str(config)
                    ready = temporary / (label + ".ready")
                    code = """
import json, sys
from pathlib import Path
from werkzeug.serving import make_server
from app import app
server = make_server('127.0.0.1', 0, app, threaded=True)
Path(sys.argv[1]).write_text(json.dumps({'port': server.server_port}), encoding='utf-8')
server.serve_forever()
"""
                    process = subprocess.Popen([sys.executable, "-c", code, str(ready)], cwd=ROOT,
                                               env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    processes.append((process, ready, label))
                identities = []
                for process, ready, label in processes:
                    deadline = time.monotonic() + 10
                    while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
                        time.sleep(.05)
                    self.assertTrue(ready.exists(), "Synthetic test server did not start")
                    port = json.loads(ready.read_text(encoding="utf-8"))["port"]
                    base = f"http://127.0.0.1:{port}"
                    with urlopen(base + "/api/status", timeout=3) as response:
                        status = json.load(response)
                    self.assertEqual(status["owner_id"], "student-" + label)
                    self.assertFalse(status["federation_enabled"])
                    self.assertFalse(status["ai_ready"])
                    identities.append(status["instance_id"])
                    with urlopen(base + "/api/profile/student-" + label, timeout=3) as response:
                        self.assertNotIn("constraints", json.load(response))
                    with urlopen(base + "/", timeout=3) as response:
                        self.assertIn(("Student Test " + label).encode(), response.read())
                    with urlopen(base + "/api/qr/student-" + label, timeout=3) as response:
                        self.assertTrue(response.read().startswith(b"\x89PNG"))
                    with urlopen(base + "/api/vcard/student-" + label, timeout=3) as response:
                        self.assertIn(b"BEGIN:VCARD", response.read())
                self.assertNotEqual(*identities)
            finally:
                for process, _, _ in processes:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
