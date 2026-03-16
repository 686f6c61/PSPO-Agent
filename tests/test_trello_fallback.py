import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock


PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..")
FALLBACK_PATH = os.path.join(PLUGIN_ROOT, "servers", "trello-fallback.py")


def load_module():
    spec = importlib.util.spec_from_file_location("trello_fallback", FALLBACK_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestTrelloFallback(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_load_arguments_supports_file_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            story_path = os.path.join(tmpdir, "HU-01-login.md")
            with open(story_path, "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            payload = self.module._load_arguments(json.dumps({"filePath": story_path}))
            self.assertEqual(payload["fileName"], "HU-01-login.md")
            self.assertEqual(payload["content"], "# HU-01\n")

    def test_main_executes_tool_handler(self):
        module = self.module

        class FakeLauncher:
            @staticmethod
            def _load_project_env():
                return None

        class FakeMcp:
            class TrelloClient:
                def __init__(self, api_key, token):
                    self.api_key = api_key
                    self.token = token

            TOOL_MAP = {
                "verify-credentials": {
                    "handler": lambda client, args: {
                        "ok": True,
                        "apiKeySuffix": client.api_key[-4:],
                        "args": args,
                    }
                }
            }

        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.object(module, "_load_runtime_modules", return_value=(FakeLauncher, FakeMcp)):
            with mock.patch.dict(os.environ, {
                "TRELLO_API_KEY": "0123456789abcdef0123456789abcdef",
                "TRELLO_TOKEN": "ATTA1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ123456",
            }, clear=False):
                with mock.patch.object(sys, "argv", ["trello-fallback.py", "verify-credentials", "--pretty"]):
                    with mock.patch("sys.stdout", stdout), mock.patch("sys.stderr", stderr), mock.patch("sys.stdin", io.StringIO("{}")):
                        exit_code = module.main()

        self.assertEqual(exit_code, 0, stderr.getvalue())
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["apiKeySuffix"], "cdef")
        self.assertEqual(payload["args"], {})

    def test_env_status_masks_secrets(self):
        module = self.module
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.object(module, "_load_runtime_modules", return_value=(type("L", (), {"_load_project_env": staticmethod(lambda: None)}), object())):
            with mock.patch.dict(os.environ, {
                "TRELLO_API_KEY": "0123456789abcdef0123456789abcdef",
                "TRELLO_TOKEN": "ATTA1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ123456",
                "TRELLO_BOARD_ID": "board123",
            }, clear=False):
                with mock.patch.object(sys, "argv", ["trello-fallback.py", "env-status", "--pretty"]):
                    with mock.patch("sys.stdout", stdout), mock.patch("sys.stderr", stderr), mock.patch("sys.stdin", io.StringIO("")):
                        exit_code = module.main()

        self.assertEqual(exit_code, 0, stderr.getvalue())
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["hasApiKey"])
        self.assertTrue(payload["hasToken"])
        self.assertTrue(payload["hasBoardId"])
        self.assertEqual(payload["apiKeyMasked"], "****cdef")
        self.assertTrue(payload["tokenMasked"].startswith("****"))
        self.assertEqual(payload["boardId"], "board123")

    def test_save_board_id_updates_env_from_positional_arg(self):
        module = self.module
        stdout = io.StringIO()
        stderr = io.StringIO()
        content = ""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = os.path.join(tmpdir, ".env")
            with open(env_path, "w", encoding="utf-8") as handle:
                handle.write("TRELLO_API_KEY=abc123\nTRELLO_TOKEN=token456\n")
            with mock.patch.object(
                module,
                "_load_runtime_modules",
                return_value=(type("L", (), {"_load_project_env": staticmethod(lambda: None)}), object()),
            ):
                with mock.patch.object(
                    sys,
                    "argv",
                    ["trello-fallback.py", "save-board-id", "board789", "--pretty"],
                ):
                    with mock.patch("sys.stdout", stdout), mock.patch("sys.stderr", stderr), mock.patch("sys.stdin", io.StringIO("")):
                        cwd = os.getcwd()
                        try:
                            os.chdir(tmpdir)
                            exit_code = module.main()
                            with open(env_path, encoding="utf-8") as handle:
                                content = handle.read()
                        finally:
                            os.chdir(cwd)

        self.assertEqual(exit_code, 0, stderr.getvalue())
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["saved"])
        self.assertEqual(payload["boardId"], "board789")
        self.assertIn("TRELLO_BOARD_ID=board789", content)


if __name__ == "__main__":
    unittest.main()
