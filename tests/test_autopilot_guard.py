import importlib.util
import os
import tempfile
import unittest


PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..")
MODULE_PATH = os.path.join(
    PLUGIN_ROOT, "hooks", "scripts", "autopilot-guard.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("autopilot_guard", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestAutopilotGuard(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_inactive_without_inbox_or_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = self.module.compute_state(tmpdir)
            self.assertEqual(state["phase"], "inactive")
            self.assertFalse(state["autopilot_active"])

    def test_prepare_context_with_inbox_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".pspo-agent", "inbox"))
            state = self.module.compute_state(tmpdir)
            self.assertEqual(state["phase"], "prepare-context")
            self.assertTrue(state["autopilot_active"])
            self.assertEqual(state["next_action"], 'Glob(".pspo-agent/inbox/*")')

    def test_ensure_scaffold_creates_runtime_and_docs_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".pspo-agent", "inbox"))
            state = self.module.compute_state(tmpdir, ensure_scaffold=True)
            self.assertEqual(state["phase"], "prepare-context")
            self.assertTrue(os.path.isdir(os.path.join(tmpdir, ".pspo-agent", "runtime")))
            self.assertTrue(os.path.isdir(os.path.join(tmpdir, "docs")))
            self.assertTrue(os.path.isdir(os.path.join(tmpdir, "docs", "historias")))

    def test_delegate_product_phase_with_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            os.makedirs(runtime_dir)
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("modo: analyze\n")
            state = self.module.compute_state(tmpdir)
            self.assertEqual(state["phase"], "delegate-product-phase")
            self.assertEqual(state["next_action"], 'Skill("pspo-agent:product-phase")')

    def test_runtime_reentry_is_active_without_context_file(self):
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
            state = self.module.compute_state(tmpdir)
            self.assertTrue(state["autopilot_active"])
            self.assertEqual(state["phase"], "product-ready")
            self.assertEqual(state["gate_status"], "plan-publish")
            self.assertEqual(state["branch_skill"], "pspo-agent:onboarding")

    def test_product_phase_active_marker_wins(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            os.makedirs(runtime_dir)
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("modo: analyze\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("active")
            state = self.module.compute_state(tmpdir)
            self.assertEqual(state["phase"], "product-phase-active")

    def test_product_ready_requires_analysis_backlog_audit_and_hu(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            historias_dir = os.path.join(docs_dir, "historias")
            os.makedirs(runtime_dir)
            os.makedirs(historias_dir)
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("modo: analyze\n")
            for name in ("analisis-requisitos.md", "backlog.md", "auditoria-hu.md"):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done")
            state = self.module.compute_state(tmpdir)
            self.assertEqual(state["phase"], "product-ready")
            self.assertTrue(state["product_ready"])
            self.assertEqual(state["story_count"], 1)
            self.assertEqual(
                state["next_action"],
                'AskUserQuestion("Revisar historias" | "Planificar y publicar")',
            )
            self.assertEqual(state["gate_status"], "")
            self.assertEqual(state["branch_skill"], "")
            self.assertEqual(state["next_review_skill"], "pspo-agent:validate")
            self.assertEqual(state["next_plan_publish_skill"], "pspo-agent:team")
            self.assertFalse(state["trello_credentials_ready"])

    def test_product_ready_exposes_pending_gate_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            historias_dir = os.path.join(docs_dir, "historias")
            os.makedirs(runtime_dir)
            os.makedirs(historias_dir)
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("modo: analyze\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done")
            with open(os.path.join(runtime_dir, "final-gate.status"), "w", encoding="utf-8") as handle:
                handle.write("pending")
            for name in ("analisis-requisitos.md", "backlog.md", "auditoria-hu.md"):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            state = self.module.compute_state(tmpdir)
            self.assertEqual(state["phase"], "product-ready")
            self.assertEqual(state["gate_status"], "pending")
            self.assertEqual(state["branch_skill"], "")

    def test_trello_credentials_ready_without_board_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, ".env"), "w", encoding="utf-8") as handle:
                handle.write(
                    "TRELLO_API_KEY=0123456789abcdef0123456789abcdef\n"
                    "TRELLO_TOKEN=ATTA1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ123456\n"
                )
            state = self.module.compute_state(tmpdir)
            self.assertTrue(state["trello_credentials_ready"])
            self.assertFalse(state["trello_ready"])
            self.assertEqual(state["publish_provider"], "trello")
            self.assertEqual(state["publish_provider_source"], "auto-configured")

    def test_multiple_ready_providers_require_choice_before_plan_publish(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            historias_dir = os.path.join(docs_dir, "historias")
            os.makedirs(runtime_dir)
            os.makedirs(historias_dir)
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("modo: analyze\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done")
            with open(os.path.join(tmpdir, ".env"), "w", encoding="utf-8") as handle:
                handle.write(
                    "TRELLO_API_KEY=0123456789abcdef0123456789abcdef\n"
                    "TRELLO_TOKEN=ATTA1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ123456\n"
                    "TRELLO_BOARD_ID=0123456789abcdef01234567\n"
                    "NOTION_TOKEN=secret_notion_token\n"
                    "NOTION_PARENT_PAGE_ID=9f8c1256-4f4d-4eef-8dc9-6a72c53da111\n"
                )
            for name in ("analisis-requisitos.md", "backlog.md", "auditoria-hu.md"):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            state = self.module.compute_state(tmpdir)
            self.assertTrue(state["publish_provider_needs_choice"])
            self.assertEqual(state["next_plan_publish_skill"], "pspo-agent:onboarding")
            self.assertEqual(set(state["configured_publish_providers"]), {"trello", "notion"})

    def test_next_plan_publish_skill_moves_to_publish_when_all_artifacts_and_board_exist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            docs_dir = os.path.join(tmpdir, "docs")
            historias_dir = os.path.join(docs_dir, "historias")
            os.makedirs(runtime_dir)
            os.makedirs(historias_dir)
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("modo: analyze\n")
            with open(os.path.join(runtime_dir, "product-phase.status"), "w", encoding="utf-8") as handle:
                handle.write("done")
            with open(os.path.join(tmpdir, ".env"), "w", encoding="utf-8") as handle:
                handle.write(
                    "TRELLO_API_KEY=abc123\n"
                    "TRELLO_TOKEN=token456\n"
                    "TRELLO_BOARD_ID=board789\n"
                )
            with open(os.path.join(tmpdir, "equipo-core.csv"), "w", encoding="utf-8") as handle:
                handle.write(
                    "nombre,email,rol,categoria,dedicacion,usa_agente_ia\n"
                    "Ana,ana@example.com,TL,senior,60,si\n"
                )
            for name in (
                "analisis-requisitos.md",
                "backlog.md",
                "auditoria-hu.md",
                "asignaciones.md",
                "dependencias.md",
                "sprint-plan.md",
            ):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            state = self.module.compute_state(tmpdir)
            self.assertTrue(state["trello_ready"])
            self.assertTrue(state["has_team_csv"])
            self.assertTrue(state["assignments_ready"])
            self.assertTrue(state["dependencies_ready"])
            self.assertTrue(state["sprint_plan_ready"])
            self.assertEqual(state["next_plan_publish_skill"], "pspo-agent:publish")
