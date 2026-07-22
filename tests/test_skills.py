"""Tests de estructura de skills y agentes."""
import os
import re
import unittest

PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..")
SKILLS_DIR = os.path.join(PLUGIN_ROOT, "skills")
AGENTS_DIR = os.path.join(PLUGIN_ROOT, "agents")


class TestSkillStructure(unittest.TestCase):

    def _get_skill_files(self):
        skills = []
        for root, _, files in os.walk(SKILLS_DIR):
            for f in files:
                if f == "SKILL.md":
                    skills.append(os.path.join(root, f))
        return skills

    def test_all_skills_have_frontmatter(self):
        for path in self._get_skill_files():
            with open(path) as f:
                content = f.read()
            self.assertTrue(content.startswith("---"),
                            f"Falta frontmatter en {path}")
            self.assertIn("name:", content,
                          f"Falta 'name' en frontmatter de {path}")
            self.assertIn("description:", content,
                          f"Falta 'description' en frontmatter de {path}")

    def test_skill_count(self):
        skills = self._get_skill_files()
        self.assertEqual(len(skills), 18,
                         f"Se esperan 18 skills, hay {len(skills)}")

    def test_skill_names_unique(self):
        names = []
        for path in self._get_skill_files():
            with open(path) as f:
                content = f.read()
            match = re.search(r"^name:\s*(.+)$", content, re.MULTILINE)
            if match:
                names.append(match.group(1).strip())
        self.assertEqual(len(names), len(set(names)),
                         f"Nombres duplicados: {names}")

    def test_expected_skill_names(self):
        expected = {"start", "onboarding", "discovery", "generate-stories",
                    "validate", "publish", "save-docs", "update", "team",
                    "assign", "dependencies",
                    "sprint-plan", "export", "sprint-review", "analyze", "audit",
                    "autopilot", "product-phase"}
        actual = set()
        for path in self._get_skill_files():
            with open(path) as f:
                content = f.read()
            match = re.search(r"^name:\s*(.+)$", content, re.MULTILINE)
            if match:
                actual.add(match.group(1).strip())
        self.assertEqual(actual, expected)

    def test_skills_using_ask_user_question_declare_tool(self):
        for path in self._get_skill_files():
            with open(path) as f:
                content = f.read()
            if "AskUserQuestion" not in content:
                continue
            self.assertIn("allowed-tools:", content,
                          f"Falta allowed-tools en {path}")
            self.assertIn("AskUserQuestion", content.split("---", 2)[1],
                          f"{path} usa AskUserQuestion pero no lo declara")

    def test_agent_delegation_skills_declare_task_tool(self):
        required = {
            "start",
            "onboarding",
            "discovery",
            "analyze",
            "generate-stories",
            "validate",
            "publish",
            "team",
            "assign",
            "dependencies",
            "sprint-plan",
            "sprint-review",
            "audit",
        }
        for path in self._get_skill_files():
            with open(path) as f:
                content = f.read()
            match = re.search(r"^name:\s*(.+)$", content, re.MULTILINE)
            if not match:
                continue
            name = match.group(1).strip()
            if name not in required:
                continue
            self.assertIn("allowed-tools:", content,
                          f"Falta allowed-tools en {path}")
            self.assertIn("Task", content.split("---", 2)[1],
                          f"{path} delega en agentes pero no declara Task")

    def test_autopilot_does_not_declare_task_tool(self):
        path = os.path.join(SKILLS_DIR, "autopilot", "SKILL.md")
        with open(path) as f:
            content = f.read()
        self.assertIn("allowed-tools:", content)
        self.assertNotIn("Task", content.split("---", 2)[1],
                         "autopilot no debe delegar con Task; debe encadenar skills")

    def test_all_skills_share_common_voice(self):
        for path in self._get_skill_files():
            with open(path) as f:
                content = f.read()
            self.assertIn("Voz comun de PSPO Agent", content,
                          f"Falta voz comun en {path}")


class TestAgentStructure(unittest.TestCase):

    def _get_agent_files(self):
        return [os.path.join(AGENTS_DIR, f)
                for f in os.listdir(AGENTS_DIR)
                if f.endswith(".md")]

    def test_all_agents_have_frontmatter(self):
        for path in self._get_agent_files():
            with open(path) as f:
                content = f.read()
            self.assertTrue(content.startswith("---"),
                            f"Falta frontmatter en {path}")
            self.assertIn("name:", content,
                          f"Falta 'name' en frontmatter de {path}")
            self.assertIn("description:", content,
                          f"Falta 'description' en frontmatter de {path}")

    def test_agent_count(self):
        agents = self._get_agent_files()
        self.assertEqual(len(agents), 6,
                         f"Se esperan 6 agentes, hay {len(agents)}")

    def test_expected_agent_names(self):
        expected = {"product-owner", "publisher", "sprint-planner", "culture-guardian", "requirement-analyst", "senior-auditor"}
        actual = set()
        for path in self._get_agent_files():
            with open(path) as f:
                content = f.read()
            match = re.search(r"^name:\s*(.+)$", content, re.MULTILINE)
            if match:
                actual.add(match.group(1).strip())
        self.assertEqual(actual, expected)

    def test_agents_have_tools(self):
        """Los agentes restringen tools salvo el publisher, que hereda todas
        para poder usar las tools MCP de trello-client."""
        for path in self._get_agent_files():
            if os.path.basename(path) == "publisher.md":
                continue
            with open(path) as f:
                content = f.read()
            self.assertIn("tools:", content,
                          f"Falta 'tools' en frontmatter de {path}")

    def test_agents_using_ask_user_question_declare_tool(self):
        for path in self._get_agent_files():
            with open(path) as f:
                content = f.read()
            if "AskUserQuestion" not in content:
                continue
            self.assertIn("AskUserQuestion", content.split("---", 2)[1],
                          f"{path} usa AskUserQuestion pero no lo declara")

    def test_all_agents_share_common_voice(self):
        for path in self._get_agent_files():
            with open(path) as f:
                content = f.read()
            self.assertIn("Voz comun de PSPO Agent", content,
                          f"Falta voz comun en {path}")


class TestHooksStructure(unittest.TestCase):

    def test_hooks_json_exists(self):
        path = os.path.join(PLUGIN_ROOT, "hooks", "hooks.json")
        self.assertTrue(os.path.exists(path))

    def test_hook_scripts_exist(self):
        scripts_dir = os.path.join(PLUGIN_ROOT, "hooks", "scripts")
        if not os.path.exists(scripts_dir):
            self.skipTest("hooks/scripts/ no existe")
        sh_files = [f for f in os.listdir(scripts_dir) if f.endswith(".sh")]
        self.assertGreater(len(sh_files), 0, "No hay scripts de hooks")

    def test_hook_scripts_are_executable(self):
        scripts_dir = os.path.join(PLUGIN_ROOT, "hooks", "scripts")
        if not os.path.exists(scripts_dir):
            self.skipTest("hooks/scripts/ no existe")
        for f in os.listdir(scripts_dir):
            if f.endswith(".sh"):
                path = os.path.join(scripts_dir, f)
                self.assertTrue(os.access(path, os.X_OK),
                                f"Script no ejecutable: {path}")

    def test_hook_commands_quote_plugin_root(self):
        path = os.path.join(PLUGIN_ROOT, "hooks", "hooks.json")
        with open(path, encoding="utf-8") as handle:
            content = handle.read()
        # Contrato del envoltorio poliglota: la ruta de run-hook.cmd va entre
        # comillas (protege espacios en Windows) y el script pasa como argumento.
        self.assertIn("\\\"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd\\\" autopilot-stop.py", content)
        # Ya no se invoca python3 ni los .sh directamente desde hooks.json.
        self.assertNotIn("python3 ", content)
        self.assertNotIn("/hooks/scripts/", content)

    def test_run_hook_wrapper_exists_and_executable(self):
        wrapper = os.path.join(PLUGIN_ROOT, "hooks", "run-hook.cmd")
        self.assertTrue(os.path.exists(wrapper), "Falta hooks/run-hook.cmd")
        self.assertTrue(os.access(wrapper, os.X_OK),
                        "hooks/run-hook.cmd no es ejecutable")


class TestDocumentation(unittest.TestCase):

    def test_readme_exists(self):
        self.assertTrue(os.path.exists(os.path.join(PLUGIN_ROOT, "README.md")))

    def test_env_example_exists(self):
        self.assertTrue(os.path.exists(os.path.join(PLUGIN_ROOT, ".env.example")))

    def test_prd_exists(self):
        self.assertTrue(os.path.exists(os.path.join(PLUGIN_ROOT, "Documents", "prd.md")),
                        "Falta Documents/prd.md")


if __name__ == "__main__":
    unittest.main()
