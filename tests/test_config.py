"""Tests de validacion de configuracion del plugin."""
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..")


class TestPluginJson(unittest.TestCase):

    def setUp(self):
        with open(os.path.join(PLUGIN_ROOT, ".claude-plugin", "plugin.json")) as f:
            self.plugin = json.load(f)

    def test_all_skills_exist(self):
        for skill_path in self.plugin["skills"]:
            full_path = os.path.join(PLUGIN_ROOT, skill_path.lstrip("./"))
            self.assertTrue(os.path.exists(full_path), f"Skill no encontrada: {skill_path}")
            self.assertTrue(os.path.isdir(full_path), f"La skill debe declararse como directorio: {skill_path}")
            self.assertTrue(os.path.exists(os.path.join(full_path, "SKILL.md")),
                            f"Falta SKILL.md dentro de {skill_path}")

    def test_all_agents_exist(self):
        for agent_path in self.plugin["agents"]:
            full_path = os.path.join(PLUGIN_ROOT, agent_path.lstrip("./"))
            self.assertTrue(os.path.exists(full_path), f"Agente no encontrado: {agent_path}")

    def test_hooks_file_exists(self):
        """hooks/hooks.json se carga automaticamente, no necesita estar en plugin.json."""
        hooks_path = os.path.join(PLUGIN_ROOT, "hooks", "hooks.json")
        self.assertTrue(os.path.exists(hooks_path))

    def test_hooks_not_in_manifest(self):
        """plugin.json NO debe declarar hooks porque hooks/hooks.json se carga automaticamente."""
        self.assertNotIn("hooks", self.plugin,
                         "plugin.json no debe tener campo 'hooks' - se carga automaticamente")

    def test_required_fields(self):
        for field in ("name", "version", "skills", "agents", "mcpServers"):
            self.assertIn(field, self.plugin, f"Falta campo: {field}")

    def test_manifest_points_to_plugin_mcp_config(self):
        self.assertEqual(self.plugin["mcpServers"], "./.mcp.json",
                         "plugin.json debe apuntar al fichero .mcp.json del plugin")

    def test_start_command_registered(self):
        self.assertIn("./commands/start.md", self.plugin["commands"])

    def test_autopilot_command_registered(self):
        self.assertIn("./commands/autopilot.md", self.plugin["commands"])

    def test_assign_command_registered(self):
        self.assertIn("./commands/assign.md", self.plugin["commands"])

    def test_dependencies_command_registered(self):
        self.assertIn("./commands/dependencies.md", self.plugin["commands"])

    def test_skills_are_array(self):
        self.assertIsInstance(self.plugin["skills"], list)

    def test_agents_are_array(self):
        self.assertIsInstance(self.plugin["agents"], list)

    def test_skill_count(self):
        self.assertEqual(len(self.plugin["skills"]), 18)

    def test_skill_manifest_uses_directories_not_skill_files(self):
        for skill_path in self.plugin["skills"]:
            self.assertFalse(skill_path.endswith("SKILL.md"),
                             f"plugin.json no debe apuntar al fichero SKILL.md: {skill_path}")

    def test_agent_count(self):
        self.assertEqual(len(self.plugin["agents"]), 6)


class TestSettingsJson(unittest.TestCase):

    def setUp(self):
        with open(os.path.join(PLUGIN_ROOT, "settings.json")) as f:
            self.settings = json.load(f)
        self.defaults = self.settings["defaults"]

    def test_sprint_config_exists(self):
        self.assertIn("sprint", self.defaults)

    def test_dod_config_exists(self):
        self.assertIn("dod", self.defaults)

    def test_ai_factor_in_range(self):
        factor = self.defaults["sprint"]["ai_agent_factor"]
        lo, hi = self.defaults["sprint"]["ai_agent_factor_range"]
        self.assertGreaterEqual(factor, lo)
        self.assertLessEqual(factor, hi)

    def test_ai_factor_recommended_in_range(self):
        rec = self.defaults["sprint"]["ai_agent_factor_recommended"]
        lo, hi = self.defaults["sprint"]["ai_agent_factor_range"]
        self.assertGreaterEqual(rec, lo)
        self.assertLessEqual(rec, hi)

    def test_ai_factor_default_is_065(self):
        self.assertEqual(self.defaults["sprint"]["ai_agent_factor"], 0.65)

    def test_ai_factor_recommended_is_070(self):
        self.assertEqual(self.defaults["sprint"]["ai_agent_factor_recommended"], 0.70)

    def test_all_sections_exist(self):
        for section in ("trello", "discovery", "stories", "validation", "docs", "publish", "sprint", "autopilot", "dod"):
            self.assertIn(section, self.defaults, f"Falta seccion: {section}")

    def test_sprint_duration_is_one_week_or_less(self):
        self.assertLessEqual(self.defaults["sprint"]["duration_days"], 5)

    def test_default_lists_include_blocked_and_active_sprint(self):
        lists = self.defaults["trello"]["default_lists"]
        self.assertIn("Sprint activo", lists)
        self.assertIn("Bloqueada", lists)


class TestMarketplaceJson(unittest.TestCase):

    def setUp(self):
        with open(os.path.join(PLUGIN_ROOT, ".claude-plugin", "marketplace.json")) as f:
            self.marketplace = json.load(f)

    def test_has_plugins_array(self):
        self.assertIsInstance(self.marketplace["plugins"], list)
        self.assertGreater(len(self.marketplace["plugins"]), 0)

    def test_plugin_name_matches(self):
        self.assertEqual(self.marketplace["plugins"][0]["name"], "pspo-agent")


class TestMcpJson(unittest.TestCase):

    def setUp(self):
        with open(os.path.join(PLUGIN_ROOT, ".mcp.json")) as f:
            self.mcp = json.load(f)["mcpServers"]

    def test_trello_client_uses_python(self):
        srv = self.mcp["trello-client"]
        self.assertEqual(srv["command"], "python3")
        self.assertIn("trello-mcp-launcher.py", srv["args"][0])

    def test_plugin_mcp_file_exists(self):
        path = os.path.join(PLUGIN_ROOT, ".mcp.json")
        self.assertTrue(os.path.exists(path), "Falta .mcp.json")

    def test_no_plugin_scoped_mcp_duplicate(self):
        plugin_scoped = os.path.join(PLUGIN_ROOT, ".claude-plugin", "mcp.json")
        self.assertFalse(os.path.exists(plugin_scoped),
                         "No debe existir .claude-plugin/mcp.json para evitar configuraciones MCP duplicadas")

    def test_no_inline_env_placeholders(self):
        srv = self.mcp["trello-client"]
        self.assertNotIn("env", srv,
                         ".mcp.json no debe inyectar placeholders; el launcher carga .env")

    def test_no_nodejs_reference(self):
        raw = json.dumps(self.mcp)
        self.assertNotIn("node", raw.lower())


class TestMcpServerExists(unittest.TestCase):

    def test_trello_mcp_py_exists(self):
        path = os.path.join(PLUGIN_ROOT, "servers", "trello-mcp.py")
        self.assertTrue(os.path.exists(path))

    def test_trello_mcp_launcher_exists(self):
        path = os.path.join(PLUGIN_ROOT, "servers", "trello-mcp-launcher.py")
        self.assertTrue(os.path.exists(path))

    def test_trello_fallback_exists(self):
        path = os.path.join(PLUGIN_ROOT, "servers", "trello-fallback.py")
        self.assertTrue(os.path.exists(path))

    def test_persist_active_skill_hook_exists(self):
        path = os.path.join(PLUGIN_ROOT, "hooks", "scripts", "persist-active-skill.py")
        self.assertTrue(os.path.exists(path))

    def test_no_typescript_legacy(self):
        legacy = os.path.join(PLUGIN_ROOT, "servers", "trello-mcp")
        self.assertFalse(os.path.isdir(legacy),
                         "El directorio TypeScript legacy no deberia existir")


class TestTrelloMcpLauncher(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        launcher_path = os.path.join(PLUGIN_ROOT, "servers", "trello-mcp-launcher.py")
        spec = importlib.util.spec_from_file_location("trello_mcp_launcher", launcher_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.launcher = module

    def test_placeholder_env_values_are_overridden_from_dotenv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text(
                "TRELLO_API_KEY=abc123\n"
                "TRELLO_TOKEN=token456\n"
                "TRELLO_BOARD_ID=board789\n",
                encoding="utf-8",
            )
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                with mock.patch.dict(os.environ, {
                    "TRELLO_API_KEY": "${TRELLO_API_KEY}",
                    "TRELLO_TOKEN": "${TRELLO_TOKEN}",
                    "TRELLO_BOARD_ID": "${TRELLO_BOARD_ID}",
                }, clear=False):
                    self.launcher._load_project_env()
                    self.assertEqual(os.environ["TRELLO_API_KEY"], "abc123")
                    self.assertEqual(os.environ["TRELLO_TOKEN"], "token456")
                    self.assertEqual(os.environ["TRELLO_BOARD_ID"], "board789")
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()
