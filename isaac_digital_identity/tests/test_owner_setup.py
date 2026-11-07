import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from dotenv import dotenv_values
from werkzeug.security import check_password_hash

import configure_owner


class SetupTests(unittest.TestCase):
    def test_setup_creates_separate_secrets_without_overwriting_files(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            profile = base / "owner.json"
            profile.write_text(json.dumps({"id": "test", "name": "Test Owner", "role": "Software"}))
            config = base / ".env.owner-test"
            original = base / ".env"
            original.write_text("TEST_SENTINEL_DO_NOT_CHANGE=1\n")
            password = "test-only-owner-password"
            argv = ["configure_owner.py", "--output", str(config), "--profile", str(profile),
                    "--database", str(base / "owner.db"), "--port", "5001", "--local-http"]
            stdout = io.StringIO()
            with patch("sys.argv", argv), patch("getpass.getpass", side_effect=[password, password]), redirect_stdout(stdout):
                configure_owner.main()
            values = dotenv_values(config, interpolate=False)
            self.assertTrue(check_password_hash(values["OWNER_PASSWORD_HASH"], password))
            self.assertGreaterEqual(len(values["SECRET_KEY"]), 32)
            self.assertEqual(values["GEMINI_API_KEY"], "")
            self.assertNotIn(password, stdout.getvalue())
            self.assertNotIn(values["SECRET_KEY"], stdout.getvalue())
            self.assertEqual(original.read_text(), "TEST_SENTINEL_DO_NOT_CHANGE=1\n")
            previous = config.read_bytes()
            with patch("sys.argv", argv), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                configure_owner.main()
            self.assertEqual(config.read_bytes(), previous)
