import json
import os
import subprocess
import tempfile
import unittest


PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..")
HOOK = os.path.join(
    PLUGIN_ROOT, "hooks", "scripts", "persist-autopilot-gate.py"
)


class TestAutopilotGatePersistence(unittest.TestCase):
    def _workspace(self):
        tmpdir = tempfile.TemporaryDirectory()
        runtime_dir = os.path.join(tmpdir.name, ".pspo-agent", "runtime")
        docs_dir = os.path.join(tmpdir.name, "docs")
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
        return tmpdir

    def _run_hook(self, workspace, answer):
        question = "Autopilot ha terminado la fase de producto. Que quieres hacer ahora?"
        payload = json.dumps({
            "tool_name": "AskUserQuestion",
            "cwd": workspace,
            "tool_input": {
                "questions": [
                    {
                        "question": question,
                        "header": "Autopilot",
                        "options": [
                            {
                                "label": "Revisar historias",
                                "description": "Abrir validacion antes de planificar o publicar.",
                            },
                            {
                                "label": "Planificar y publicar",
                                "description": "Usar CSV compatible si existe, planificar sprint y publicar en Trello con resumen + adjunto .md.",
                            },
                        ],
                        "multiSelect": False,
                    }
                ]
            },
            "toolUseResult": {
                "questions": [
                    {
                        "question": question,
                        "header": "Autopilot",
                        "options": [],
                        "multiSelect": False,
                    }
                ],
                "answers": {
                    question: answer,
                },
            },
        })
        return subprocess.run(
            ["python3", HOOK],
            input=payload,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_persists_review_branch(self):
        with self._workspace() as workspace:
            result = self._run_hook(workspace, "Revisar historias")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            with open(
                os.path.join(workspace, ".pspo-agent", "runtime", "final-gate.status"),
                encoding="utf-8",
            ) as handle:
                self.assertEqual(handle.read().strip(), "review")

    def test_persists_plan_publish_branch(self):
        with self._workspace() as workspace:
            result = self._run_hook(workspace, "Planificar y publicar")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            with open(
                os.path.join(workspace, ".pspo-agent", "runtime", "final-gate.status"),
                encoding="utf-8",
            ) as handle:
                self.assertEqual(handle.read().strip(), "plan-publish")

    def test_ignores_other_questions(self):
        with self._workspace() as workspace:
            payload = json.dumps({
                "tool_name": "AskUserQuestion",
                "cwd": workspace,
                "tool_input": {
                    "questions": [
                        {
                            "question": "Como quieres validar las historias?",
                            "header": "Validacion",
                            "options": [],
                            "multiSelect": False,
                        }
                    ]
                },
                "toolUseResult": {
                    "answers": {
                        "Como quieres validar las historias?": "Aprobar en bloque",
                    },
                },
            })
            result = subprocess.run(
                ["python3", HOOK],
                input=payload,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            with open(
                os.path.join(workspace, ".pspo-agent", "runtime", "final-gate.status"),
                encoding="utf-8",
            ) as handle:
                self.assertEqual(handle.read().strip(), "pending")
