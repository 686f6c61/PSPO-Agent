import json
import os
import subprocess
import tempfile
import unittest


PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..")
DRIFT_HOOK = os.path.join(PLUGIN_ROOT, "hooks", "scripts", "block-autopilot-drift.sh")
BASH_HOOK = os.path.join(PLUGIN_ROOT, "hooks", "scripts", "block-trello-bash.sh")
SKILL_HOOK = os.path.join(PLUGIN_ROOT, "hooks", "scripts", "block-autopilot-skill.sh")
AGENT_HOOK = os.path.join(PLUGIN_ROOT, "hooks", "scripts", "block-autopilot-agent.sh")
ASK_HOOK = os.path.join(
    PLUGIN_ROOT, "hooks", "scripts", "block-onboarding-credential-reask.py"
)
SECRET_AGENT_HOOK = os.path.join(
    PLUGIN_ROOT, "hooks", "scripts", "block-secret-prompt-leak.py"
)
WARN_READ_HOOK = os.path.join(
    PLUGIN_ROOT, "hooks", "scripts", "warn-sensitive-read.sh"
)
PERSIST_SKILL_HOOK = os.path.join(
    PLUGIN_ROOT, "hooks", "scripts", "persist-active-skill.py"
)


class TestAutopilotHooksRuntime(unittest.TestCase):
    def _run_drift_hook(self, workspace, tool_name, tool_input):
        payload = json.dumps({
            "tool_name": tool_name,
            "cwd": workspace,
            "tool_input": tool_input,
        })
        return subprocess.run(
            [DRIFT_HOOK],
            input=payload,
            text=True,
            capture_output=True,
            check=False,
        )

    def _run_bash_hook(self, workspace, tool_name, tool_input):
        payload = json.dumps({
            "tool_name": tool_name,
            "cwd": workspace,
            "tool_input": tool_input,
        })
        return subprocess.run(
            [BASH_HOOK],
            input=payload,
            text=True,
            capture_output=True,
            check=False,
        )

    def _run_skill_hook(self, workspace, skill_name):
        payload = json.dumps({
            "tool_name": "Skill",
            "cwd": workspace,
            "tool_input": {"skill": skill_name},
        })
        return subprocess.run(
            [SKILL_HOOK],
            input=payload,
            text=True,
            capture_output=True,
            check=False,
        )

    def _run_persist_skill_hook(self, workspace, skill_name):
        payload = json.dumps({
            "tool_name": "Skill",
            "cwd": workspace,
            "tool_input": {"skill": skill_name},
        })
        env = os.environ.copy()
        env["CLAUDE_PLUGIN_ROOT"] = os.path.abspath(PLUGIN_ROOT)
        return subprocess.run(
            ["python3", PERSIST_SKILL_HOOK],
            input=payload,
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )

    def _run_ask_hook(self, workspace, question, header="Trello"):
        payload = json.dumps({
            "tool_name": "AskUserQuestion",
            "cwd": workspace,
            "tool_input": {
                "questions": [
                    {
                        "question": question,
                        "header": header,
                        "options": [
                            {"label": "Si", "description": "Continuar"},
                            {"label": "No", "description": "Cancelar"},
                        ],
                        "multiSelect": False,
                    }
                ]
            },
        })
        return subprocess.run(
            ["python3", ASK_HOOK],
            input=payload,
            text=True,
            capture_output=True,
            check=False,
        )

    def _run_agent_hook(self, workspace, tool_name, tool_input):
        payload = json.dumps({
            "tool_name": tool_name,
            "cwd": workspace,
            "tool_input": tool_input,
        })
        return subprocess.run(
            [AGENT_HOOK],
            input=payload,
            text=True,
            capture_output=True,
            check=False,
        )

    def _run_secret_agent_hook(self, workspace, tool_name, tool_input):
        payload = json.dumps({
            "tool_name": tool_name,
            "cwd": workspace,
            "tool_input": tool_input,
        })
        return subprocess.run(
            ["python3", SECRET_AGENT_HOOK],
            input=payload,
            text=True,
            capture_output=True,
            check=False,
        )

    def _run_warn_read_hook(self, workspace, tool_name, tool_input):
        payload = json.dumps({
            "tool_name": tool_name,
            "cwd": workspace,
            "tool_input": tool_input,
        })
        return subprocess.run(
            [WARN_READ_HOOK],
            input=payload,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_prepare_context_allows_inbox_glob(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            inbox_dir = os.path.join(tmpdir, ".pspo-agent", "inbox")
            os.makedirs(inbox_dir)
            with open(os.path.join(inbox_dir, "brief.md"), "w", encoding="utf-8") as handle:
                handle.write("MVP pequeno con login y recuperacion de contrasena.\n")
            result = self._run_drift_hook(
                tmpdir,
                "Glob",
                {"pattern": ".pspo-agent/inbox/**/*", "path": tmpdir},
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(os.path.isdir(os.path.join(tmpdir, ".pspo-agent", "runtime")))
            self.assertTrue(os.path.isdir(os.path.join(tmpdir, "docs", "historias")))
            self.assertTrue(
                os.path.isfile(os.path.join(tmpdir, ".pspo-agent", "runtime", "autopilot-context.md"))
            )

    def test_start_blocks_all_reads_before_env_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            os.makedirs(runtime_dir)
            self._run_persist_skill_hook(tmpdir, "pspo-agent:start")
            result = self._run_drift_hook(
                tmpdir,
                "Glob",
                {"pattern": ".env*", "path": tmpdir},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("Primera accion valida", result.stdout)
            self.assertIn("env-status", result.stdout)

    def test_persist_skill_creates_runtime_wrapper(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self._run_persist_skill_hook(tmpdir, "pspo-agent:start")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            wrapper = os.path.join(tmpdir, ".pspo-agent", "runtime", "trello-fallback.sh")
            self.assertTrue(os.path.isfile(wrapper))
            with open(wrapper, encoding="utf-8") as handle:
                content = handle.read()
            self.assertIn("trello-fallback.py", content)
            notion_wrapper = os.path.join(tmpdir, ".pspo-agent", "runtime", "notion-fallback.sh")
            self.assertTrue(os.path.isfile(notion_wrapper))
            with open(notion_wrapper, encoding="utf-8") as handle:
                notion_content = handle.read()
            self.assertIn("notion-fallback.py", notion_content)
            github_wrapper = os.path.join(tmpdir, ".pspo-agent", "runtime", "github-fallback.sh")
            self.assertTrue(os.path.isfile(github_wrapper))
            with open(github_wrapper, encoding="utf-8") as handle:
                github_content = handle.read()
            self.assertIn("github-fallback.py", github_content)
            provider_wrapper = os.path.join(tmpdir, ".pspo-agent", "runtime", "publish-provider.py")
            self.assertTrue(os.path.isfile(provider_wrapper))
            with open(provider_wrapper, encoding="utf-8") as handle:
                provider_content = handle.read()
            self.assertIn("publish-provider.py", provider_content)

    def test_start_env_status_marks_bootstrap_done(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            os.makedirs(runtime_dir)
            self._run_persist_skill_hook(tmpdir, "pspo-agent:start")
            result = self._run_bash_hook(
                tmpdir,
                "Bash",
                {"command": ".pspo-agent/runtime/trello-fallback.sh env-status --pretty"},
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            marker = os.path.join(runtime_dir, "start-bootstrap.status")
            with open(marker, encoding="utf-8") as handle:
                self.assertEqual(handle.read().strip(), "done")

    def test_onboarding_allows_quoted_runtime_wrapper(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            os.makedirs(runtime_dir)
            self._run_persist_skill_hook(tmpdir, "pspo-agent:onboarding")
            wrapper = os.path.join(runtime_dir, "notion-fallback.sh")
            result = self._run_bash_hook(
                tmpdir,
                "Bash",
                {"command": f"bash -lc '{wrapper} env-status --pretty'"},
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            marker = os.path.join(runtime_dir, "onboarding-bootstrap.status")
            with open(marker, encoding="utf-8") as handle:
                self.assertEqual(handle.read().strip(), "done")

    def test_onboarding_allows_publish_provider_with_absolute_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._run_persist_skill_hook(tmpdir, "pspo-agent:onboarding")
            result = self._run_bash_hook(
                tmpdir,
                "Bash",
                {
                    "command": (
                        "python3 "
                        f"'{os.path.join(os.path.abspath(PLUGIN_ROOT), 'hooks', 'scripts', 'publish-provider.py')}' "
                        f"'{tmpdir}'"
                    )
                },
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_onboarding_allows_runtime_publish_provider_wrapper(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._run_persist_skill_hook(tmpdir, "pspo-agent:onboarding")
            result = self._run_bash_hook(
                tmpdir,
                "Bash",
                {"command": ".pspo-agent/runtime/publish-provider.py ."},
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_onboarding_blocks_generic_bash_after_bootstrap(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            os.makedirs(runtime_dir)
            self._run_persist_skill_hook(tmpdir, "pspo-agent:onboarding")
            with open(os.path.join(runtime_dir, "onboarding-bootstrap.status"), "w", encoding="utf-8") as handle:
                handle.write("done\n")
            result = self._run_bash_hook(
                tmpdir,
                "Bash",
                {"command": f"find '{PLUGIN_ROOT}' -name 'onboarding*' -type f"},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("no uses Bash ni Fetch genericos", result.stdout)

    def test_start_blocks_generic_bash_before_env_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._run_persist_skill_hook(tmpdir, "pspo-agent:start")
            result = self._run_bash_hook(
                tmpdir,
                "Bash",
                {"command": "ls -la"},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("primera accion valida", result.stdout.lower())
            self.assertIn("trello-fallback.sh env-status", result.stdout)

    def test_wrapper_command_must_be_isolated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._run_persist_skill_hook(tmpdir, "pspo-agent:onboarding")
            with open(os.path.join(tmpdir, ".pspo-agent", "runtime", "onboarding-bootstrap.status"), "w", encoding="utf-8") as handle:
                handle.write("done\n")
            result = self._run_bash_hook(
                tmpdir,
                "Bash",
                {
                    "command": ".pspo-agent/runtime/trello-fallback.sh list-boards || curl -s https://api.trello.com/1/members/me/boards",
                },
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("comando limpio y aislado", result.stdout)

    def test_start_blocks_toolsearch_after_bootstrap(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            os.makedirs(runtime_dir)
            self._run_persist_skill_hook(tmpdir, "pspo-agent:start")
            with open(os.path.join(runtime_dir, "start-bootstrap.status"), "w", encoding="utf-8") as handle:
                handle.write("done\n")
            result = self._run_drift_hook(
                tmpdir,
                "ToolSearch",
                {"query": "select:AskUserQuestion"},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("no uses ToolSearch", result.stdout)

    def test_publish_blocks_claude_local_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._run_persist_skill_hook(tmpdir, "pspo-agent:publish")
            result = self._run_drift_hook(
                tmpdir,
                "Glob",
                {"pattern": "**/*.local.md"},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("no uses .claude", result.stdout.lower())

    def test_onboarding_blocks_reads_before_env_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            os.makedirs(runtime_dir)
            self._run_persist_skill_hook(tmpdir, "pspo-agent:onboarding")
            result = self._run_drift_hook(
                tmpdir,
                "Read",
                {"file_path": os.path.join(tmpdir, ".env.example")},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("/pspo-agent:onboarding", result.stdout)
            self.assertIn("env-status", result.stdout)

    def test_direct_onboarding_blocks_generic_agent_for_notion(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, ".env"), "w", encoding="utf-8") as handle:
                handle.write(
                    "NOTION_TOKEN=ntn_example_token\n"
                    "NOTION_PARENT_PAGE_ID=325b0a8fa25480599971f0c19b43e43c\n"
                )
            self._run_persist_skill_hook(tmpdir, "pspo-agent:onboarding")
            result = self._run_agent_hook(
                tmpdir,
                "Agent",
                {"subagent_type": "Explore", "description": "Explorar workspace"},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("/pspo-agent:onboarding", result.stdout)
            self.assertIn("notion-fallback", result.stdout)

    def test_direct_onboarding_blocks_notion_structure_choice_question(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, ".env"), "w", encoding="utf-8") as handle:
                handle.write(
                    "NOTION_TOKEN=ntn_example_token\n"
                    "NOTION_PARENT_PAGE_ID=325b0a8fa25480599971f0c19b43e43c\n"
                )
            self._run_persist_skill_hook(tmpdir, "pspo-agent:onboarding")
            result = self._run_ask_hook(
                tmpdir,
                "Prefieres que cree automaticamente la estructura en Notion o usar solo la pagina padre?",
                header="Notion",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("no preguntes", result.stdout.lower())
            self.assertIn("create-project", result.stdout)
            self.assertIn("save-project-targets", result.stdout)

    def test_prepare_context_blocks_docs_glob(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".pspo-agent", "inbox"))
            result = self._run_drift_hook(
                tmpdir,
                "Glob",
                {"pattern": "docs/**/*", "path": tmpdir},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("No leas docs, .claude, .env", result.stdout)

    def test_delegate_phase_blocks_any_extra_glob(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            os.makedirs(runtime_dir)
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            result = self._run_drift_hook(
                tmpdir,
                "Glob",
                {"pattern": ".pspo-agent/**/*.json", "path": tmpdir},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("La siguiente accion debe ser Skill", result.stdout)

    def test_delegate_phase_allows_runtime_context_read(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            os.makedirs(runtime_dir)
            context_path = os.path.join(runtime_dir, "autopilot-context.md")
            with open(context_path, "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            result = self._run_drift_hook(
                tmpdir,
                "Read",
                {"file_path": context_path},
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_product_phase_active_blocks_claude_config_reads(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            os.makedirs(runtime_dir)
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("active")
            result = self._run_drift_hook(
                tmpdir,
                "Glob",
                {"pattern": ".claude/**/*", "path": tmpdir},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("Durante product-phase", result.stdout)

    def test_delegate_product_phase_allows_specific_docs_reads_when_skill_is_active(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            os.makedirs(runtime_dir)
            os.makedirs(docs_dir)
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            with open(os.path.join(runtime_dir, "active-skill.status"), "w", encoding="utf-8") as handle:
                handle.write("pspo-agent:product-phase\n")
            backlog_path = os.path.join(docs_dir, "backlog.md")
            with open(backlog_path, "w", encoding="utf-8") as handle:
                handle.write("# Backlog\n")
            result = self._run_drift_hook(
                tmpdir,
                "Read",
                {"file_path": backlog_path},
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_product_phase_active_blocks_inbox_reads(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            inbox_dir = os.path.join(tmpdir, ".pspo-agent", "inbox")
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            os.makedirs(inbox_dir)
            os.makedirs(runtime_dir)
            brief_path = os.path.join(inbox_dir, "brief.md")
            with open(brief_path, "w", encoding="utf-8") as handle:
                handle.write("Brief de ejemplo\n")
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("active")
            result = self._run_drift_hook(
                tmpdir,
                "Read",
                {"file_path": brief_path},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertNotIn("Permission denied", result.stdout + result.stderr)
            self.assertIn("no vuelvas a leer la inbox", result.stdout)

    def test_product_phase_active_blocks_wildcard_docs_glob(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            os.makedirs(runtime_dir)
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("active")
            result = self._run_drift_hook(
                tmpdir,
                "Glob",
                {"pattern": "docs/**/*", "path": tmpdir},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertNotIn("Permission denied", result.stdout + result.stderr)
            self.assertIn("no hagas barridos amplios de docs/", result.stdout)

    def test_product_phase_active_blocks_toolsearch_with_specific_message(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            os.makedirs(runtime_dir)
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("active")
            result = self._run_drift_hook(
                tmpdir,
                "ToolSearch",
                {"query": "TodoWrite"},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("Durante product-phase no uses ToolSearch", result.stdout)

    def test_prepare_context_blocks_generic_bash(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".pspo-agent", "inbox"))
            result = self._run_bash_hook(
                tmpdir,
                "Bash",
                {"command": "pwd"},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("no uses Bash durante el bootstrap", result.stdout)

    def test_product_ready_allows_generic_bash(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            historias_dir = os.path.join(docs_dir, "historias")
            os.makedirs(runtime_dir)
            os.makedirs(historias_dir)
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done")
            for name in ("analisis-requisitos.md", "backlog.md", "auditoria-hu.md"):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            result = self._run_bash_hook(
                tmpdir,
                "Bash",
                {"command": "pwd"},
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_product_ready_blocks_reopening_inbox_before_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            inbox_dir = os.path.join(tmpdir, ".pspo-agent", "inbox")
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            historias_dir = os.path.join(docs_dir, "historias")
            os.makedirs(inbox_dir)
            os.makedirs(runtime_dir)
            os.makedirs(historias_dir)
            brief_path = os.path.join(inbox_dir, "brief.md")
            with open(brief_path, "w", encoding="utf-8") as handle:
                handle.write("Brief de ejemplo\n")
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done")
            for name in ("analisis-requisitos.md", "backlog.md", "auditoria-hu.md"):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            result = self._run_drift_hook(
                tmpdir,
                "Read",
                {"file_path": brief_path},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("AskUserQuestion", result.stdout)

    def test_autopilot_reentry_with_branch_selected_blocks_inbox_glob(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            inbox_dir = os.path.join(tmpdir, ".pspo-agent", "inbox")
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            historias_dir = os.path.join(docs_dir, "historias")
            os.makedirs(inbox_dir)
            os.makedirs(runtime_dir)
            os.makedirs(historias_dir)
            with open(os.path.join(inbox_dir, "brief.md"), "w", encoding="utf-8") as handle:
                handle.write("Brief de ejemplo\n")
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done")
            with open(os.path.join(runtime_dir, "final-gate.status"), "w", encoding="utf-8") as handle:
                handle.write("plan-publish")
            with open(os.path.join(runtime_dir, "autopilot-branch-skill.status"), "w", encoding="utf-8") as handle:
                handle.write("pspo-agent:onboarding")
            with open(os.path.join(runtime_dir, "active-skill.status"), "w", encoding="utf-8") as handle:
                handle.write("pspo-agent:autopilot")
            for name in ("analisis-requisitos.md", "backlog.md", "auditoria-hu.md"):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            result = self._run_drift_hook(
                tmpdir,
                "Glob",
                {"pattern": ".pspo-agent/inbox/*", "path": tmpdir},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn('Skill("pspo-agent:onboarding")', result.stdout)

    def test_product_ready_allows_toolsearch_for_ask_user_question_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            historias_dir = os.path.join(docs_dir, "historias")
            os.makedirs(runtime_dir)
            os.makedirs(historias_dir)
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done")
            for name in ("analisis-requisitos.md", "backlog.md", "auditoria-hu.md"):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            result = self._run_drift_hook(
                tmpdir,
                "ToolSearch",
                {"query": "select:AskUserQuestion"},
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_product_ready_blocks_reads_while_gate_is_pending(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            inbox_dir = os.path.join(tmpdir, ".pspo-agent", "inbox")
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            historias_dir = os.path.join(docs_dir, "historias")
            os.makedirs(inbox_dir)
            os.makedirs(runtime_dir)
            os.makedirs(historias_dir)
            brief_path = os.path.join(inbox_dir, "brief.md")
            with open(brief_path, "w", encoding="utf-8") as handle:
                handle.write("Brief de ejemplo\n")
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done")
            with open(os.path.join(runtime_dir, "final-gate.status"), "w", encoding="utf-8") as handle:
                handle.write("pending")
            for name in ("analisis-requisitos.md", "backlog.md", "auditoria-hu.md"):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            result = self._run_drift_hook(
                tmpdir,
                "Read",
                {"file_path": brief_path},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("AskUserQuestion", result.stdout)

    def test_product_ready_allows_reads_once_gate_branch_is_selected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            inbox_dir = os.path.join(tmpdir, ".pspo-agent", "inbox")
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            historias_dir = os.path.join(docs_dir, "historias")
            os.makedirs(inbox_dir)
            os.makedirs(runtime_dir)
            os.makedirs(historias_dir)
            brief_path = os.path.join(inbox_dir, "brief.md")
            with open(brief_path, "w", encoding="utf-8") as handle:
                handle.write("Brief de ejemplo\n")
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done")
            with open(os.path.join(runtime_dir, "final-gate.status"), "w", encoding="utf-8") as handle:
                handle.write("review")
            with open(os.path.join(runtime_dir, "autopilot-branch-skill.status"), "w", encoding="utf-8") as handle:
                handle.write("pspo-agent:validate")
            with open(os.path.join(runtime_dir, "active-skill.status"), "w", encoding="utf-8") as handle:
                handle.write("pspo-agent:validate")
            for name in ("analisis-requisitos.md", "backlog.md", "auditoria-hu.md"):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            result = self._run_drift_hook(
                tmpdir,
                "Read",
                {"file_path": brief_path},
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_review_gate_blocks_root_reads_until_validate_starts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            inbox_dir = os.path.join(tmpdir, ".pspo-agent", "inbox")
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            historias_dir = os.path.join(docs_dir, "historias")
            os.makedirs(inbox_dir)
            os.makedirs(runtime_dir)
            os.makedirs(historias_dir)
            brief_path = os.path.join(inbox_dir, "brief.md")
            with open(brief_path, "w", encoding="utf-8") as handle:
                handle.write("Brief de ejemplo\n")
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done")
            with open(os.path.join(runtime_dir, "final-gate.status"), "w", encoding="utf-8") as handle:
                handle.write("review")
            for name in ("analisis-requisitos.md", "backlog.md", "auditoria-hu.md"):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            result = self._run_drift_hook(
                tmpdir,
                "Glob",
                {"pattern": ".pspo-agent/inbox/*"},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn('Skill("pspo-agent:validate")', result.stdout)

    def test_plan_publish_gate_blocks_root_reads_until_downstream_skill_starts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            historias_dir = os.path.join(docs_dir, "historias")
            os.makedirs(runtime_dir)
            os.makedirs(historias_dir)
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done")
            with open(os.path.join(runtime_dir, "final-gate.status"), "w", encoding="utf-8") as handle:
                handle.write("plan-publish")
            for name in ("analisis-requisitos.md", "backlog.md", "auditoria-hu.md"):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            result = self._run_drift_hook(
                tmpdir,
                "Glob",
                {"pattern": ".pspo-agent/inbox/*"},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn('Skill("pspo-agent:team")', result.stdout)

    def test_onboarding_branch_blocks_env_read_and_points_to_env_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = os.path.join(tmpdir, ".env")
            with open(env_path, "w", encoding="utf-8") as handle:
                handle.write("TRELLO_API_KEY=0123456789abcdef0123456789abcdef\n")
            result = self._run_warn_read_hook(
                tmpdir,
                "Read",
                {"file_path": env_path},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("trello-fallback.sh", result.stdout)

    def test_direct_onboarding_blocks_ask_user_question_when_notion_targets_exist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, ".env"), "w", encoding="utf-8") as handle:
                handle.write(
                    "NOTION_TOKEN=ntn_example_token\n"
                    "NOTION_PARENT_PAGE_ID=325b0a8fa25480599971f0c19b43e43c\n"
                    "NOTION_PROJECT_PAGE_ID=325b0a8fa254811d9d61cd6286cd22f0\n"
                )
            self._run_persist_skill_hook(tmpdir, "pspo-agent:onboarding")
            result = self._run_ask_hook(
                tmpdir,
                "¿Quieres que cree la estructura de Notion o use la pagina padre?",
                header="Notion",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("no preguntes de nuevo", payload["hookSpecificOutput"]["permissionDecisionReason"].lower())
            self.assertIn("notion-fallback.sh verify-credentials", payload["hookSpecificOutput"]["permissionDecisionReason"])

    def test_onboarding_branch_blocks_global_claude_glob(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            historias_dir = os.path.join(docs_dir, "historias")
            os.makedirs(runtime_dir)
            os.makedirs(historias_dir)
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done")
            with open(os.path.join(runtime_dir, "final-gate.status"), "w", encoding="utf-8") as handle:
                handle.write("plan-publish")
            with open(os.path.join(runtime_dir, "autopilot-branch-skill.status"), "w", encoding="utf-8") as handle:
                handle.write("pspo-agent:onboarding")
            for name in ("analisis-requisitos.md", "backlog.md", "auditoria-hu.md"):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            result = self._run_drift_hook(
                tmpdir,
                "Glob",
                {"pattern": "/Users/00b/.claude/**/*"},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertTrue(
                "Durante onboarding desde autopilot" in result.stdout
                or "Autopilot ya tiene la rama 'Planificar y publicar' seleccionada" in result.stdout
            )

    def test_onboarding_branch_blocks_generic_explore_agent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            historias_dir = os.path.join(docs_dir, "historias")
            os.makedirs(runtime_dir)
            os.makedirs(historias_dir)
            with open(os.path.join(tmpdir, ".env"), "w", encoding="utf-8") as handle:
                handle.write(
                    "TRELLO_API_KEY=0123456789abcdef0123456789abcdef\n"
                    "TRELLO_TOKEN=ATTA1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ123456\n"
                )
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done")
            with open(os.path.join(runtime_dir, "final-gate.status"), "w", encoding="utf-8") as handle:
                handle.write("plan-publish")
            with open(os.path.join(runtime_dir, "autopilot-branch-skill.status"), "w", encoding="utf-8") as handle:
                handle.write("pspo-agent:onboarding")
            for name in ("analisis-requisitos.md", "backlog.md", "auditoria-hu.md"):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            result = self._run_agent_hook(
                tmpdir,
                "Agent",
                {"subagent_type": "Explore", "description": "Explorar plugin"},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("La unica delegacion valida es el agente publisher", result.stdout)

    def test_onboarding_branch_allows_publisher_agent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            historias_dir = os.path.join(docs_dir, "historias")
            os.makedirs(runtime_dir)
            os.makedirs(historias_dir)
            with open(os.path.join(tmpdir, ".env"), "w", encoding="utf-8") as handle:
                handle.write(
                    "TRELLO_API_KEY=0123456789abcdef0123456789abcdef\n"
                    "TRELLO_TOKEN=ATTA1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ123456\n"
                )
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done")
            with open(os.path.join(runtime_dir, "final-gate.status"), "w", encoding="utf-8") as handle:
                handle.write("plan-publish")
            with open(os.path.join(runtime_dir, "autopilot-branch-skill.status"), "w", encoding="utf-8") as handle:
                handle.write("pspo-agent:onboarding")
            for name in ("analisis-requisitos.md", "backlog.md", "auditoria-hu.md"):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            result = self._run_agent_hook(
                tmpdir,
                "Agent",
                {"subagent_type": "pspo-agent:publisher", "description": "Publicar en Trello"},
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_onboarding_branch_blocks_agent_for_notion_provider(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            historias_dir = os.path.join(docs_dir, "historias")
            os.makedirs(runtime_dir)
            os.makedirs(historias_dir)
            with open(os.path.join(tmpdir, ".env"), "w", encoding="utf-8") as handle:
                handle.write(
                    "NOTION_TOKEN=ntn_example_token\n"
                    "NOTION_PARENT_PAGE_ID=325b0a8fa25480599971f0c19b43e43c\n"
                )
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done")
            with open(os.path.join(runtime_dir, "final-gate.status"), "w", encoding="utf-8") as handle:
                handle.write("plan-publish")
            with open(os.path.join(runtime_dir, "autopilot-branch-skill.status"), "w", encoding="utf-8") as handle:
                handle.write("pspo-agent:onboarding")
            for name in ("analisis-requisitos.md", "backlog.md", "auditoria-hu.md"):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            result = self._run_agent_hook(
                tmpdir,
                "Agent",
                {"subagent_type": "pspo-agent:publisher", "description": "Publicar en Notion"},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("onboarding Notion", result.stdout)
            self.assertIn("notion-fallback.sh", result.stdout)

    def test_product_phase_active_blocks_agent_delegation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            os.makedirs(runtime_dir)
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("active")
            result = self._run_agent_hook(
                tmpdir,
                "Agent",
                {"subagent_type": "pspo-agent:requirement-analyst", "description": "Analizar brief"},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("Durante product-phase no uses Agent", result.stdout)
            self.assertIn("Write/Edit", result.stdout)

    def test_onboarding_branch_blocks_publisher_list_boards_in_autopilot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            historias_dir = os.path.join(docs_dir, "historias")
            os.makedirs(runtime_dir)
            os.makedirs(historias_dir)
            with open(os.path.join(tmpdir, ".env"), "w", encoding="utf-8") as handle:
                handle.write(
                    "TRELLO_API_KEY=0123456789abcdef0123456789abcdef\n"
                    "TRELLO_TOKEN=ATTA1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ123456\n"
                )
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done")
            with open(os.path.join(runtime_dir, "final-gate.status"), "w", encoding="utf-8") as handle:
                handle.write("plan-publish")
            with open(os.path.join(runtime_dir, "autopilot-branch-skill.status"), "w", encoding="utf-8") as handle:
                handle.write("pspo-agent:onboarding")
            for name in ("analisis-requisitos.md", "backlog.md", "auditoria-hu.md"):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            result = self._run_agent_hook(
                tmpdir,
                "Agent",
                {
                    "subagent_type": "pspo-agent:publisher",
                    "description": "Listar tableros de Trello",
                    "prompt": "Usa list-boards para mostrar todos los tableros disponibles.",
                },
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("no listes tableros", result.stdout.lower())
            self.assertIn("create-board", result.stdout)

    def test_onboarding_branch_blocks_fallback_list_boards_in_autopilot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            historias_dir = os.path.join(docs_dir, "historias")
            os.makedirs(runtime_dir)
            os.makedirs(historias_dir)
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done")
            with open(os.path.join(runtime_dir, "final-gate.status"), "w", encoding="utf-8") as handle:
                handle.write("plan-publish")
            with open(os.path.join(runtime_dir, "autopilot-branch-skill.status"), "w", encoding="utf-8") as handle:
                handle.write("pspo-agent:onboarding")
            for name in ("analisis-requisitos.md", "backlog.md", "auditoria-hu.md"):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            result = self._run_bash_hook(
                tmpdir,
                "Bash",
                {"command": ".pspo-agent/runtime/trello-fallback.sh list-boards"},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("no ejecutes list-boards", result.stdout.lower())
            self.assertIn("create-board", result.stdout)

    def test_secret_agent_hook_blocks_literal_trello_credentials(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self._run_secret_agent_hook(
                tmpdir,
                "Agent",
                {
                    "subagent_type": "pspo-agent:publisher",
                    "prompt": (
                        "Credenciales:\n"
                        "TRELLO_API_KEY=0123456789abcdef0123456789abcdef\n"
                        "TRELLO_TOKEN=ATTA1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ123456\n"
                    ),
                },
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("Nunca copies API keys ni tokens", result.stdout)

    def test_secret_agent_hook_allows_env_path_without_literals(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self._run_secret_agent_hook(
                tmpdir,
                "Agent",
                {
                    "subagent_type": "pspo-agent:publisher",
                    "prompt": (
                        "Verifica credenciales con trello-client usando el entorno ya cargado desde "
                        f"{tmpdir}/.env. No leas secretos ni los repitas."
                    ),
                },
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_onboarding_branch_blocks_generic_bash(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            historias_dir = os.path.join(docs_dir, "historias")
            os.makedirs(runtime_dir)
            os.makedirs(historias_dir)
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done")
            with open(os.path.join(runtime_dir, "final-gate.status"), "w", encoding="utf-8") as handle:
                handle.write("plan-publish")
            with open(os.path.join(runtime_dir, "autopilot-branch-skill.status"), "w", encoding="utf-8") as handle:
                handle.write("pspo-agent:onboarding")
            for name in ("analisis-requisitos.md", "backlog.md", "auditoria-hu.md"):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            result = self._run_bash_hook(
                tmpdir,
                "Bash",
                {"command": "ls -la"},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("Durante onboarding desde autopilot", result.stdout)

    def test_product_phase_branch_blocks_mkdir_with_write_guidance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            os.makedirs(runtime_dir)
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            self._run_persist_skill_hook(tmpdir, "pspo-agent:product-phase")
            result = self._run_bash_hook(
                tmpdir,
                "Bash",
                {"command": "mkdir -p docs/historias"},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("tampoco para mkdir", result.stdout.lower())
            self.assertIn("Write/Edit", result.stdout)

    def test_onboarding_branch_allows_official_trello_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            historias_dir = os.path.join(docs_dir, "historias")
            os.makedirs(runtime_dir)
            os.makedirs(historias_dir)
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done")
            with open(os.path.join(runtime_dir, "final-gate.status"), "w", encoding="utf-8") as handle:
                handle.write("plan-publish")
            with open(os.path.join(runtime_dir, "autopilot-branch-skill.status"), "w", encoding="utf-8") as handle:
                handle.write("pspo-agent:onboarding")
            for name in ("analisis-requisitos.md", "backlog.md", "auditoria-hu.md"):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            result = self._run_bash_hook(
                tmpdir,
                "Bash",
                {"command": ".pspo-agent/runtime/trello-fallback.sh verify-credentials"},
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_delegate_phase_allows_only_product_phase_skill(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            os.makedirs(runtime_dir)
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            allowed = self._run_skill_hook(tmpdir, "pspo-agent:product-phase")
            blocked = self._run_skill_hook(tmpdir, "pspo-agent:validate")
            self.assertEqual(allowed.returncode, 0, allowed.stdout + allowed.stderr)
            self.assertEqual(blocked.returncode, 2, blocked.stdout + blocked.stderr)
            self.assertIn('Skill("pspo-agent:product-phase")', blocked.stdout)

    def test_product_ready_blocks_skill_until_gate_is_resolved(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            historias_dir = os.path.join(docs_dir, "historias")
            os.makedirs(runtime_dir)
            os.makedirs(historias_dir)
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done")
            with open(os.path.join(runtime_dir, "final-gate.status"), "w", encoding="utf-8") as handle:
                handle.write("pending")
            for name in ("analisis-requisitos.md", "backlog.md", "auditoria-hu.md"):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            result = self._run_skill_hook(tmpdir, "pspo-agent:validate")
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("AskUserQuestion", result.stdout)

    def test_review_gate_blocks_product_phase_reentry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            historias_dir = os.path.join(docs_dir, "historias")
            os.makedirs(runtime_dir)
            os.makedirs(historias_dir)
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done")
            with open(os.path.join(runtime_dir, "final-gate.status"), "w", encoding="utf-8") as handle:
                handle.write("review")
            for name in ("analisis-requisitos.md", "backlog.md", "auditoria-hu.md"):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            allowed = self._run_skill_hook(tmpdir, "pspo-agent:validate")
            blocked = self._run_skill_hook(tmpdir, "pspo-agent:product-phase")
            self.assertEqual(allowed.returncode, 0, allowed.stdout + allowed.stderr)
            self.assertEqual(blocked.returncode, 2, blocked.stdout + blocked.stderr)
            self.assertIn("Revisar historias", blocked.stdout)
            resumed = self._run_skill_hook(tmpdir, "pspo-agent:autopilot")
            self.assertEqual(resumed.returncode, 0, resumed.stdout + resumed.stderr)

    def test_plan_publish_gate_allows_operational_chain_and_blocks_validate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            historias_dir = os.path.join(docs_dir, "historias")
            os.makedirs(runtime_dir)
            os.makedirs(historias_dir)
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done")
            with open(os.path.join(runtime_dir, "final-gate.status"), "w", encoding="utf-8") as handle:
                handle.write("plan-publish")
            for name in ("analisis-requisitos.md", "backlog.md", "auditoria-hu.md"):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            allowed = self._run_skill_hook(tmpdir, "pspo-agent:assign")
            blocked = self._run_skill_hook(tmpdir, "pspo-agent:validate")
            self.assertEqual(allowed.returncode, 0, allowed.stdout + allowed.stderr)
            self.assertEqual(blocked.returncode, 2, blocked.stdout + blocked.stderr)
            self.assertIn("Planificar y publicar", blocked.stdout)
            resumed = self._run_skill_hook(tmpdir, "pspo-agent:autopilot")
            self.assertEqual(resumed.returncode, 0, resumed.stdout + resumed.stderr)

    def test_onboarding_credential_reask_is_blocked_when_env_has_key_and_token(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, ".env"), "w", encoding="utf-8") as handle:
                handle.write("TRELLO_API_KEY=0123456789abcdef0123456789abcdef\n")
                handle.write("TRELLO_TOKEN=ATTA1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ123456\n")
            result = self._run_ask_hook(
                tmpdir,
                "Necesito configurar las credenciales de Trello. Tienes ya las credenciales de Trello (API Key y Token)?",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("No vuelvas a pedir API Key ni Token", payload["hookSpecificOutput"]["permissionDecisionReason"])

    def test_onboarding_credential_reask_is_allowed_when_env_is_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self._run_ask_hook(
                tmpdir,
                "Necesito configurar las credenciales de Trello. Tienes ya las credenciales de Trello (API Key y Token)?",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_onboarding_board_choice_is_blocked_in_autopilot_branch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            os.makedirs(runtime_dir)
            with open(os.path.join(tmpdir, ".env"), "w", encoding="utf-8") as handle:
                handle.write("TRELLO_API_KEY=0123456789abcdef0123456789abcdef\n")
                handle.write("TRELLO_TOKEN=ATTA1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ123456\n")
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            with open(os.path.join(runtime_dir, "autopilot-branch-skill.status"), "w", encoding="utf-8") as handle:
                handle.write("pspo-agent:onboarding")
            result = self._run_ask_hook(
                tmpdir,
                "¿Quieres que use un tablero de Trello existente o prefieres que cree uno nuevo para este proyecto?",
                header="Tablero",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("Crea automaticamente un tablero nuevo", payload["hookSpecificOutput"]["permissionDecisionReason"])

    def test_autopilot_reentry_without_context_blocks_inbox_glob(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            historias_dir = os.path.join(docs_dir, "historias")
            os.makedirs(runtime_dir)
            os.makedirs(historias_dir)
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done\n")
            with open(os.path.join(runtime_dir, "final-gate.status"), "w", encoding="utf-8") as handle:
                handle.write("plan-publish\n")
            with open(
                os.path.join(runtime_dir, "autopilot-branch-skill.status"),
                "w",
                encoding="utf-8",
            ) as handle:
                handle.write("pspo-agent:onboarding\n")
            for name in ("analisis-requisitos.md", "backlog.md", "auditoria-hu.md"):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            result = self._run_drift_hook(
                tmpdir,
                "Glob",
                {"pattern": ".pspo-agent/inbox/*", "path": tmpdir},
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("Planificar y publicar", result.stdout)
            self.assertIn('Skill("pspo-agent:onboarding")', result.stdout)

    def test_autopilot_board_question_is_blocked_with_broader_wording(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            os.makedirs(runtime_dir)
            with open(os.path.join(tmpdir, ".env"), "w", encoding="utf-8") as handle:
                handle.write("TRELLO_API_KEY=0123456789abcdef0123456789abcdef\n")
                handle.write("TRELLO_TOKEN=ATTA1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ123456\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done\n")
            with open(os.path.join(runtime_dir, "final-gate.status"), "w", encoding="utf-8") as handle:
                handle.write("plan-publish\n")
            with open(
                os.path.join(runtime_dir, "autopilot-branch-skill.status"),
                "w",
                encoding="utf-8",
            ) as handle:
                handle.write("pspo-agent:onboarding\n")
            result = self._run_ask_hook(
                tmpdir,
                "¿Qué tablero de Trello quieres usar para publicar las historias de usuario?",
                header="Tablero",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("Crea automaticamente un tablero nuevo", payload["hookSpecificOutput"]["permissionDecisionReason"])
