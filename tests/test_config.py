"""Tests de validacion de configuracion del plugin."""
import json
import os
import unittest

PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..")


class TestPluginJson(unittest.TestCase):

    def setUp(self):
        with open(os.path.join(PLUGIN_ROOT, ".claude-plugin", "plugin.json")) as f:
            self.plugin = json.load(f)

    def test_all_skills_exist(self):
        for skill_path in self.plugin["skills"]:
            full_path = os.path.join(PLUGIN_ROOT, skill_path.lstrip("./"))
            self.assertTrue(os.path.exists(full_path), f"Skill no encontrada: {skill_path}")

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

    def test_mcp_file_exists(self):
        raw = self.plugin["mcpServers"]
        # Normalizar ruta relativa: "./.mcp.json" -> ".mcp.json"
        if raw.startswith("./"):
            raw = raw[2:]
        mcp_path = os.path.join(PLUGIN_ROOT, raw)
        self.assertTrue(os.path.exists(mcp_path), f"MCP config no encontrado: {mcp_path}")

    def test_required_fields(self):
        for field in ("name", "version", "skills", "agents", "mcpServers"):
            self.assertIn(field, self.plugin, f"Falta campo: {field}")

    def test_skills_are_array(self):
        self.assertIsInstance(self.plugin["skills"], list)

    def test_agents_are_array(self):
        self.assertIsInstance(self.plugin["agents"], list)

    def test_skill_count(self):
        self.assertEqual(len(self.plugin["skills"]), 14)

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
        for section in ("trello", "discovery", "stories", "validation", "docs", "publish", "sprint", "dod"):
            self.assertIn(section, self.defaults, f"Falta seccion: {section}")


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
            self.mcp = json.load(f)

    def test_trello_client_uses_python(self):
        srv = self.mcp["mcpServers"]["trello-client"]
        self.assertEqual(srv["command"], "python3")
        self.assertIn("trello-mcp.py", srv["args"][0])

    def test_env_vars_defined(self):
        env = self.mcp["mcpServers"]["trello-client"]["env"]
        self.assertIn("TRELLO_API_KEY", env)
        self.assertIn("TRELLO_TOKEN", env)

    def test_no_nodejs_reference(self):
        raw = json.dumps(self.mcp)
        self.assertNotIn("node", raw.lower())


class TestMcpServerExists(unittest.TestCase):

    def test_trello_mcp_py_exists(self):
        path = os.path.join(PLUGIN_ROOT, "servers", "trello-mcp.py")
        self.assertTrue(os.path.exists(path))

    def test_no_typescript_legacy(self):
        legacy = os.path.join(PLUGIN_ROOT, "servers", "trello-mcp")
        self.assertFalse(os.path.isdir(legacy),
                         "El directorio TypeScript legacy no deberia existir")


if __name__ == "__main__":
    unittest.main()
