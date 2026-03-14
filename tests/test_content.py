"""
Tests de contenido: verifican que las skills y agentes contienen
las instrucciones criticas que hacen funcionar el plugin.

Si un refactor rompe una instruccion clave, estos tests lo detectan.
"""
import os
import re
import unittest

PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..")


def read_file(rel_path):
    with open(os.path.join(PLUGIN_ROOT, rel_path)) as f:
        return f.read()


# ---------------------------------------------------------------------------
# Colores de agentes
# ---------------------------------------------------------------------------

class TestAgentColors(unittest.TestCase):
    """Cada agente debe tener un color distinto en el frontmatter."""

    EXPECTED_COLORS = {
        "product-owner": "blue",
        "requirement-analyst": "cyan",
        "publisher": "green",
        "sprint-planner": "amber",
        "culture-guardian": "magenta",
    }

    def test_all_agents_have_color(self):
        for agent_name, expected_color in self.EXPECTED_COLORS.items():
            files = [f for f in os.listdir(os.path.join(PLUGIN_ROOT, "agents"))
                     if f.endswith(".md")]
            found = False
            for f in files:
                content = read_file(f"agents/{f}")
                name_match = re.search(r"^name:\s*(.+)$", content, re.MULTILINE)
                if name_match and name_match.group(1).strip() == agent_name:
                    color_match = re.search(r"^color:\s*(.+)$", content, re.MULTILINE)
                    self.assertIsNotNone(color_match,
                                        f"Agente {agent_name} no tiene campo color")
                    self.assertEqual(color_match.group(1).strip(), expected_color,
                                     f"Agente {agent_name} tiene color incorrecto")
                    found = True
                    break
            self.assertTrue(found, f"Agente {agent_name} no encontrado")

    def test_no_duplicate_colors(self):
        colors = []
        for f in os.listdir(os.path.join(PLUGIN_ROOT, "agents")):
            if f.endswith(".md"):
                content = read_file(f"agents/{f}")
                color_match = re.search(r"^color:\s*(.+)$", content, re.MULTILINE)
                if color_match:
                    colors.append(color_match.group(1).strip())
        self.assertEqual(len(colors), len(set(colors)),
                         f"Colores duplicados: {colors}")


# ---------------------------------------------------------------------------
# Culture guardian invocado en las skills criticas
# ---------------------------------------------------------------------------

class TestCultureGuardianInvocation(unittest.TestCase):
    """El culture-guardian debe invocarse en generate, validate y publish."""

    def test_invoked_in_generate_stories(self):
        content = read_file("skills/generate-stories/SKILL.md")
        self.assertIn("culture-guardian", content,
                       "generate-stories no invoca a culture-guardian")

    def test_invoked_in_validate(self):
        content = read_file("skills/validate/SKILL.md")
        self.assertIn("culture-guardian", content,
                       "validate no invoca a culture-guardian")

    def test_invoked_in_publish(self):
        content = read_file("skills/publish/SKILL.md")
        self.assertIn("culture-guardian", content,
                       "publish no invoca a culture-guardian")


# ---------------------------------------------------------------------------
# Publish: 3 pasos explicitos (tarjeta + adjunto + DoD)
# ---------------------------------------------------------------------------

class TestPublishFlow(unittest.TestCase):
    """El publish debe crear tarjeta, adjuntar .md y anadir DoD."""

    def setUp(self):
        self.content = read_file("skills/publish/SKILL.md")

    def test_creates_card(self):
        self.assertIn("create-cards", self.content)

    def test_attaches_md(self):
        self.assertIn("attach-file", self.content)

    def test_adds_dod_checklist(self):
        self.assertIn("add-checklist", self.content)

    def test_single_confirmation(self):
        self.assertIn("UNA VEZ", self.content.upper() if "UNA VEZ" in self.content.upper()
                       else self.content,
                       "Publish debe pedir confirmacion una sola vez")

    def test_no_individual_confirmation(self):
        self.assertIn("NUNCA pidas confirmacion individual", self.content,
                       "Publish no prohibe confirmacion individual")

    def test_estimation_in_preview(self):
        self.assertIn("Talla", self.content,
                       "Vista previa de publish no muestra tallas")

    def test_estimation_in_card_description(self):
        self.assertIn("Estimacion", self.content,
                       "Descripcion de tarjeta no incluye estimacion")


# ---------------------------------------------------------------------------
# Generate stories: pasos criticos
# ---------------------------------------------------------------------------

class TestGenerateStoriesFlow(unittest.TestCase):
    """Generate stories debe tener edge cases, estimacion y culture-guardian."""

    def setUp(self):
        self.content = read_file("skills/generate-stories/SKILL.md")

    def test_has_edge_cases_step(self):
        self.assertIn("edge case", self.content.lower(),
                       "generate-stories no tiene paso de edge cases")

    def test_edge_cases_categories(self):
        for category in ["Limites de datos", "Concurrencia", "Estado inconsistente",
                         "Permisos", "Integraciones"]:
            self.assertIn(category, self.content,
                          f"Falta categoria de edge case: {category}")

    def test_has_estimation_step(self):
        self.assertIn("t-shirt", self.content.lower(),
                       "generate-stories no tiene paso de estimacion")

    def test_estimation_sizes(self):
        for size in ["S = 1", "M = 2", "L = 3", "XL = 5"]:
            self.assertIn(size, self.content,
                          f"Falta talla de estimacion: {size}")


# ---------------------------------------------------------------------------
# Product owner: formato enriquecido
# ---------------------------------------------------------------------------

class TestProductOwnerEnriched(unittest.TestCase):
    """El product-owner debe generar HU enriquecidas."""

    def setUp(self):
        self.content = read_file("agents/product-owner.md")

    def test_has_context_narrative(self):
        self.assertIn("Contexto narrativo", self.content)

    def test_has_mermaid_diagrams(self):
        self.assertIn("mermaid", self.content.lower())

    def test_has_data_tables(self):
        self.assertIn("Tabla de datos", self.content)

    def test_has_external_references(self):
        self.assertIn("Referencias externas", self.content)

    def test_has_implementation_notes(self):
        self.assertIn("Notas de implementacion", self.content)

    def test_has_jarvis_personality(self):
        # Verifica que tiene personalidad JARVIS (ironico, tecnico, skin in the game)
        self.assertIn("skin in the game", self.content.lower(),
                       "Product-owner no tiene personalidad JARVIS")

    def test_detailed_acceptance_criteria(self):
        self.assertIn("INCORRECTO", self.content,
                       "No tiene ejemplo de criterio incorrecto vs correcto")
        self.assertIn("CORRECTO", self.content)


# ---------------------------------------------------------------------------
# Requirement analyst
# ---------------------------------------------------------------------------

class TestRequirementAnalyst(unittest.TestCase):
    """El requirement-analyst debe tener claridad progresiva y JARVIS."""

    def setUp(self):
        self.content = read_file("agents/requirement-analyst.md")

    def test_has_clarity_indicator(self):
        self.assertIn("Claridad:", self.content)

    def test_has_8_categories(self):
        categories = ["Usuario final", "Problema", "Contexto de negocio",
                       "Alcance", "Restricciones", "Criterios de exito",
                       "Dependencias", "Fuera de alcance"]
        for cat in categories:
            self.assertIn(cat, self.content,
                          f"Falta categoria de claridad: {cat}")

    def test_80_percent_threshold(self):
        self.assertIn("80%", self.content,
                       "No tiene umbral del 80% de claridad")

    def test_has_jarvis_personality(self):
        has_jarvis = ("skin in the game" in self.content.lower()
                      or "interrogador" in self.content.lower()
                      or "humor seco" in self.content.lower())
        self.assertTrue(has_jarvis,
                        "Requirement-analyst no tiene personalidad JARVIS")


# ---------------------------------------------------------------------------
# Settings: configuracion critica
# ---------------------------------------------------------------------------

class TestSettingsContent(unittest.TestCase):
    """Settings.json debe tener los valores criticos correctos."""

    def setUp(self):
        import json
        with open(os.path.join(PLUGIN_ROOT, "settings.json")) as f:
            self.settings = json.load(f)
        self.defaults = self.settings["defaults"]

    def test_date_format_spanish(self):
        self.assertEqual(self.defaults["docs"]["date_format"], "DD/MM/AAAA",
                          "Formato de fecha no es espanol")

    def test_estimation_sizes_exist(self):
        sizes = self.defaults["stories"]["estimation_sizes"]
        self.assertEqual(sizes["S"], 1)
        self.assertEqual(sizes["M"], 2)
        self.assertEqual(sizes["L"], 3)
        self.assertEqual(sizes["XL"], 5)

    def test_ai_factor(self):
        sprint = self.defaults["sprint"]
        self.assertEqual(sprint["ai_agent_factor"], 0.65)
        self.assertEqual(sprint["ai_agent_factor_recommended"], 0.70)

    def test_dod_config(self):
        self.assertIn("dod", self.defaults)
        self.assertTrue(self.defaults["dod"]["add_checklist_to_trello"])


# ---------------------------------------------------------------------------
# Templates: campos de estimacion
# ---------------------------------------------------------------------------

class TestFileTemplates(unittest.TestCase):
    """Las plantillas de ficheros deben incluir campos de estimacion."""

    def setUp(self):
        self.content = read_file("skills/save-docs/file-templates.md")

    def test_hu_template_has_estimation(self):
        self.assertIn("Estimacion", self.content,
                       "Plantilla HU no tiene campo de estimacion")

    def test_hu_template_has_talla(self):
        self.assertIn("S / M / L / XL", self.content,
                       "Plantilla HU no muestra tallas")

    def test_backlog_has_talla_column(self):
        self.assertIn("Talla", self.content,
                       "Backlog no tiene columna de talla")

    def test_backlog_has_dias_column(self):
        self.assertIn("Dias", self.content,
                       "Backlog no tiene columna de dias")

    def test_date_format_spanish(self):
        self.assertIn("DD/MM/AAAA", self.content,
                       "Plantillas no usan formato de fecha espanol")


# ---------------------------------------------------------------------------
# Start: vision de producto y opciones correctas
# ---------------------------------------------------------------------------

class TestStartFlow(unittest.TestCase):
    """Start debe pedir vision, ofrecer analyze como opcion 1."""

    def setUp(self):
        self.content = read_file("skills/start/SKILL.md")

    def test_offers_analyze_first(self):
        self.assertIn("Analizar un documento", self.content,
                       "Start no ofrece analizar documento como primera opcion")

    def test_asks_for_vision(self):
        self.assertIn("vision", self.content.lower(),
                       "Start no pide vision de producto")

    def test_vision_file_reference(self):
        self.assertIn("docs/vision.md", self.content,
                       "Start no referencia docs/vision.md")

    def test_detects_long_text_as_analyze(self):
        self.assertIn("100 palabras", self.content,
                       "Start no detecta texto largo para redirigir a analyze")


# ---------------------------------------------------------------------------
# Card format: estructura correcta
# ---------------------------------------------------------------------------

class TestCardFormat(unittest.TestCase):
    """Card format debe tener resumen + adjunto + DoD."""

    def setUp(self):
        self.content = read_file("skills/publish/card-format.md")

    def test_has_summary_format(self):
        self.assertIn("resumen", self.content.lower())

    def test_has_attachment_section(self):
        self.assertIn("Fichero adjunto", self.content)

    def test_has_dod_section(self):
        self.assertIn("Definition of Done", self.content)

    def test_estimation_in_description(self):
        self.assertIn("Estimacion", self.content)


# ---------------------------------------------------------------------------
# Team CSV template on web
# ---------------------------------------------------------------------------

class TestTeamTemplate(unittest.TestCase):
    """La plantilla CSV del equipo debe existir en la web."""

    def test_csv_exists_on_web(self):
        path = "/home/r/Escritorio/Astro-PSPO-AI/public/team-template.csv"
        if os.path.exists(path):
            with open(path) as f:
                content = f.read()
            self.assertIn("nombre,email,rol,categoria,dedicacion,usa_agente_ia",
                          content, "CSV no tiene cabecera correcta")
        # Si no existe la web local, skip
        else:
            self.skipTest("Web Astro no disponible localmente")

    def test_team_skill_references_download(self):
        content = read_file("skills/team/SKILL.md")
        self.assertIn("team-template.csv", content,
                       "Skill team no referencia la plantilla CSV descargable")


if __name__ == "__main__":
    unittest.main()
