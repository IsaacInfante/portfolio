"""Configuration checks use disposable files and never read the real .env."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ConfigurationTests(unittest.TestCase):
    def check_configuration(self, encoding="utf-8", inherited=False):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            project = base / "project"
            project.mkdir()
            (project / "data").mkdir()
            for module in ("app.py", "settings.py", "owner_auth.py", "profile_privacy.py"):
                shutil.copyfile(ROOT / module, project / module)
            shutil.copyfile(ROOT / "data" / "isaac.json", project / "data" / "isaac.json")
            # Deliberately fake values, isolated from the user's configuration.
            (project / ".env").write_text(
                "GEMINI_API_KEY=FAKE_FILE_VALUE_FOR_TEST_ONLY\n"
                "GEMINI_MODEL=configuration-test-model\n", encoding=encoding
            )
            elsewhere = base / "different-working-directory"
            elsewhere.mkdir()
            env = os.environ.copy()
            for name in ("GEMINI_API_KEY", "GEMINI_MODEL", "PYTHON_DOTENV_DISABLED", "PORTFOLIO_ENV_FILE", "OWNER_PROFILE_PATH", "INSTANCE_ID", "SECRET_KEY", "OWNER_PASSWORD_HASH", "PUBLIC_BASE_URL"):
                env.pop(name, None)
            env["DATABASE_PATH"] = str(base / "test.db")
            if inherited:
                env["GEMINI_API_KEY"] = "FAKE_PROCESS_VALUE_FOR_TEST_ONLY"
            code = """
import json, runpy, sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]).parent))
app = runpy.run_path(sys.argv[1])
expected = ('FAKE_PROCESS_VALUE_FOR_TEST_ONLY' if sys.argv[2] == 'True'
            else 'FAKE_FILE_VALUE_FOR_TEST_ONLY')
response = app['app'].test_client().get('/api/status')
print(json.dumps({
    'loaded': bool(app['GEMINI_API_KEY']),
    'correct_source': app['GEMINI_API_KEY'] == expected,
    'model_loaded': app['GEMINI_MODEL'] == 'configuration-test-model',
    'frontend_ready': response.get_json()['ai_ready'],
    'no_cache': response.headers.get('Cache-Control') == 'no-store',
    'secret_absent': expected not in response.get_data(as_text=True),
}))
"""
            result = subprocess.run(
                [sys.executable, "-c", code, str(project / "app.py"), str(inherited)],
                cwd=elsewhere, env=env, capture_output=True, text=True, timeout=20,
            )
            # Do not echo subprocess output on failure: keep diagnostics secret-safe.
            self.assertEqual(result.returncode, 0, "Configuration subprocess failed")
            checks = json.loads(result.stdout)
            for name, passed in checks.items():
                self.assertTrue(passed, name)

    def test_env_loads_beside_app_from_different_directory(self):
        self.check_configuration()

    def test_windows_utf8_bom_is_supported(self):
        self.check_configuration(encoding="utf-8-sig")

    def test_process_environment_has_priority(self):
        self.check_configuration(inherited=True)


if __name__ == "__main__":
    unittest.main()
