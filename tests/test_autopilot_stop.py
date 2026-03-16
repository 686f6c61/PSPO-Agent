import json
import os
import subprocess
import tempfile
import unittest


PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..")
STOP_HOOK = os.path.join(PLUGIN_ROOT, "hooks", "scripts", "autopilot-stop.py")


class TestAutopilotStopHook(unittest.TestCase):
    def _run_hook(self, workspace):
        payload = json.dumps({"cwd": workspace})
        return subprocess.run(
            ["python3", STOP_HOOK],
            input=payload,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_allows_stop_when_inactive(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self._run_hook(tmpdir)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")

    def test_blocks_stop_during_prepare_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".pspo-agent", "inbox"))
            result = self._run_hook(tmpdir)
            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "block")
            self.assertIn('Glob(".pspo-agent/inbox/*")', payload["reason"])

    def test_blocks_stop_during_delegate_phase(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_dir = os.path.join(tmpdir, ".pspo-agent", "runtime")
            os.makedirs(runtime_dir)
            with open(os.path.join(runtime_dir, "autopilot-context.md"), "w", encoding="utf-8") as handle:
                handle.write("# Contexto\n")
            result = self._run_hook(tmpdir)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "block")
            self.assertIn('Skill("pspo-agent:product-phase")', payload["reason"])

    def test_blocks_stop_when_product_ready_but_gate_not_opened(self):
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
            result = self._run_hook(tmpdir)
            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "block")
            self.assertIn("Revisar historias", payload["reason"])
            self.assertIn("Planificar y publicar", payload["reason"])

    def test_blocks_stop_when_product_ready_and_gate_pending(self):
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
            result = self._run_hook(tmpdir)
            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "block")
            self.assertIn("AskUserQuestion", payload["reason"])

    def test_allows_stop_when_product_ready_and_gate_review_selected(self):
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
            with open(
                os.path.join(runtime_dir, "autopilot-branch-skill.status"),
                "w",
                encoding="utf-8",
            ) as handle:
                handle.write("pspo-agent:validate")
            for name in ("analisis-requisitos.md", "backlog.md", "auditoria-hu.md"):
                with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as handle:
                    handle.write("# ok\n")
            with open(os.path.join(historias_dir, "HU-01-login.md"), "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            result = self._run_hook(tmpdir)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")

    def test_blocks_stop_when_review_selected_but_validate_not_started(self):
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
            result = self._run_hook(tmpdir)
            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "block")
            self.assertIn('Skill("pspo-agent:validate")', payload["reason"])

    def test_blocks_stop_when_plan_publish_selected_but_next_skill_not_started(self):
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
            result = self._run_hook(tmpdir)
            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "block")
            self.assertIn('Skill("pspo-agent:team")', payload["reason"])
