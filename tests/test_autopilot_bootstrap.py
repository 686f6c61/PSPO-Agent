import importlib.util
import os
import tempfile
import unittest


PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..")
MODULE_PATH = os.path.join(
    PLUGIN_ROOT, "hooks", "scripts", "autopilot-bootstrap.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("autopilot_bootstrap", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestAutopilotBootstrap(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_bootstrap_creates_runtime_context_from_inbox(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            inbox_dir = os.path.join(tmpdir, ".pspo-agent", "inbox")
            os.makedirs(inbox_dir)
            with open(os.path.join(inbox_dir, "brief.md"), "w", encoding="utf-8") as handle:
                handle.write("Login simple con recuperacion de contrasena.\n")
            with open(os.path.join(inbox_dir, "vision.md"), "w", encoding="utf-8") as handle:
                handle.write("Vision enfocada en validar el MVP con equipo pequeno.\n")
            with open(os.path.join(inbox_dir, "equipo-core.csv"), "w", encoding="utf-8") as handle:
                handle.write(
                    "nombre,email,rol,categoria,dedicacion,usa_agente_ia\n"
                    "Ana,ana@example.com,Tech Lead,senior,60,si\n"
                )

            result = self.module.bootstrap_context(tmpdir)

            self.assertTrue(result["created"])
            self.assertEqual(result["document_path"], ".pspo-agent/inbox/brief.md")
            self.assertEqual(result["vision_path"], ".pspo-agent/inbox/vision.md")
            self.assertEqual(result["csv_path"], ".pspo-agent/inbox/equipo-core.csv")
            self.assertEqual(result["product_mode"], "discovery")
            context_path = os.path.join(tmpdir, ".pspo-agent", "runtime", "autopilot-context.md")
            self.assertTrue(os.path.isfile(context_path))
            with open(context_path, encoding="utf-8") as handle:
                content = handle.read()
            self.assertIn("modo_producto: discovery", content)
            self.assertIn("Documento principal detectado", content)
            self.assertIn("# Vision de entrada", content)
            self.assertIn("Vision enfocada en validar el MVP", content)

    def test_bootstrap_is_noop_without_main_document(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".pspo-agent", "inbox"))
            result = self.module.bootstrap_context(tmpdir)
            self.assertFalse(result["created"])
            self.assertFalse(
                os.path.exists(
                    os.path.join(tmpdir, ".pspo-agent", "runtime", "autopilot-context.md")
                )
            )
