import importlib.util
import json
import os
import tempfile
import unittest
from unittest import mock


PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..")
MODULE_PATH = os.path.join(
    PLUGIN_ROOT, "hooks", "scripts", "publish-provider.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("publish_provider", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestPublishProvider(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_defaults_to_local_when_no_remote_provider_is_configured(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = self.module.compute_state(tmpdir)
            self.assertEqual(state["publish_provider"], "local")
            self.assertEqual(state["publish_provider_source"], "auto-local")
            self.assertEqual(state["configured_providers"], [])
            self.assertFalse(state["publish_provider_needs_choice"])

    def test_auto_selects_trello_when_it_is_the_only_provider(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, ".env"), "w", encoding="utf-8") as handle:
                handle.write(
                    "TRELLO_API_KEY=0123456789abcdef0123456789abcdef\n"
                    "TRELLO_TOKEN=ATTA1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ123456\n"
                    "TRELLO_BOARD_ID=0123456789abcdef01234567\n"
                )
            state = self.module.compute_state(tmpdir)
            self.assertEqual(state["publish_provider"], "trello")
            self.assertEqual(state["publish_provider_source"], "auto-ready")
            self.assertEqual(state["configured_providers"], ["trello"])
            self.assertEqual(state["ready_providers"], ["trello"])

    def test_auto_selects_notion_when_it_is_the_only_provider(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, ".env"), "w", encoding="utf-8") as handle:
                handle.write(
                    "NOTION_TOKEN=secret_notion_token\n"
                    "NOTION_PARENT_PAGE_ID=9f8c1256-4f4d-4eef-8dc9-6a72c53da111\n"
                )
            with mock.patch.dict(os.environ, {}, clear=True):
                state = self.module.compute_state(tmpdir)
            self.assertEqual(state["publish_provider"], "notion")
            self.assertEqual(state["publish_provider_source"], "auto-ready")
            self.assertEqual(state["configured_providers"], ["notion"])
            self.assertEqual(state["ready_providers"], ["notion"])
            self.assertFalse(state["notion_targets_ready"])

    def test_marks_notion_targets_ready_when_project_or_database_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, ".env"), "w", encoding="utf-8") as handle:
                handle.write(
                    "NOTION_TOKEN=secret_notion_token\n"
                    "NOTION_PARENT_PAGE_ID=9f8c1256-4f4d-4eef-8dc9-6a72c53da111\n"
                    "NOTION_PROJECT_PAGE_ID=325b0a8fa254811d9d61cd6286cd22f0\n"
                )
            with mock.patch.dict(os.environ, {}, clear=True):
                state = self.module.compute_state(tmpdir)
            self.assertTrue(state["notion_targets_ready"])

    def test_requires_user_choice_when_both_remote_providers_are_configured(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, ".env"), "w", encoding="utf-8") as handle:
                handle.write(
                    "TRELLO_API_KEY=0123456789abcdef0123456789abcdef\n"
                    "TRELLO_TOKEN=ATTA1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ123456\n"
                    "TRELLO_BOARD_ID=0123456789abcdef01234567\n"
                    "NOTION_TOKEN=secret_notion_token\n"
                    "NOTION_PARENT_PAGE_ID=9f8c1256-4f4d-4eef-8dc9-6a72c53da111\n"
                )
            state = self.module.compute_state(tmpdir)
            self.assertEqual(set(state["configured_providers"]), {"trello", "notion"})
            self.assertTrue(state["publish_provider_needs_choice"])
            self.assertEqual(state["publish_provider"], "")

    def test_runtime_selection_persists_provider_choice(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, ".env"), "w", encoding="utf-8") as handle:
                handle.write(
                    "TRELLO_API_KEY=0123456789abcdef0123456789abcdef\n"
                    "TRELLO_TOKEN=ATTA1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ123456\n"
                    "TRELLO_BOARD_ID=0123456789abcdef01234567\n"
                    "NOTION_TOKEN=secret_notion_token\n"
                    "NOTION_PARENT_PAGE_ID=9f8c1256-4f4d-4eef-8dc9-6a72c53da111\n"
                )
            path = self.module.save_selection(tmpdir, "notion", source="user")
            self.assertTrue(os.path.isfile(path))
            with open(path, encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["provider"], "notion")
            state = self.module.compute_state(tmpdir)
            self.assertEqual(state["selected_provider"], "notion")
            self.assertEqual(state["publish_provider"], "notion")
            self.assertEqual(state["publish_provider_source"], "user")
            self.assertFalse(state["publish_provider_needs_choice"])
