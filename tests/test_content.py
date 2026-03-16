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
        self.assertIn("UNA SOLA VEZ", self.content,
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

    def test_batch_processing(self):
        self.assertIn("lotes de 5", self.content,
                       "Publish no procesa en lotes de 5")

    def test_post_publish_verification(self):
        self.assertIn("Verificacion post-publicacion", self.content,
                       "Publish no tiene verificacion post-publicacion")

    def test_member_assignment(self):
        self.assertIn("get-board-members", self.content,
                       "Publish no usa get-board-members para asignar miembros")
        self.assertIn("NO la publiques todavia", self.content,
                      "Publish debe bloquear HUs sin responsable")
        self.assertIn("create-cards", self.content,
                      "Publish debe reforzar create-cards como operacion correcta")
        self.assertIn("nunca `create-card`", self.content,
                      "Publish debe prohibir create-card en singular en el contrato con publisher")
        self.assertIn("cuando `get-card` confirma `idMembers`", self.content,
                      "Publish debe exigir verificacion real de miembros asignados")

    def test_sprint_list_routing(self):
        self.assertIn("Sprint activo", self.content,
                       "Publish no envia HUs del sprint a la lista Sprint activo")

    def test_no_legacy_sprint_column_alias(self):
        self.assertNotIn('(o "Sprint actual"', self.content,
                         "Publish no debe tratar Sprint actual como alias valido")
        self.assertIn('renombrala a **"Sprint activo"**', self.content,
                      "Publish debe normalizar tableros legacy a Sprint activo")

    def test_blocked_list_routing(self):
        self.assertIn("Bloqueada", self.content,
                       "Publish no contempla la lista Bloqueada para HUs con dependencias")

    def test_dependency_checklist_sync(self):
        self.assertIn('checklist "Dependencias"', self.content,
                      "Publish no sincroniza checklist de dependencias")

    def test_incremental_sync_tools(self):
        self.assertIn("get-card", self.content,
                      "Publish no inspecciona tarjetas existentes")
        self.assertIn("update-card", self.content,
                      "Publish no sincroniza tarjetas existentes")

    def test_operational_labels(self):
        for label in ["Asignada", "Bloqueada", "Bloqueante"]:
            self.assertIn(label, self.content,
                          f"Publish no contempla la etiqueta operativa {label}")

    def test_uses_ask_user_question(self):
        self.assertIn("AskUserQuestion", self.content,
                       "Publish debe usar AskUserQuestion para opciones")
        self.assertIn("En modo autonomo o autopilot, la confirmacion ya se recibio en la gate final", self.content,
                      "Publish debe respetar la confirmacion ya dada por autopilot")

    def test_no_sn_confirmations(self):
        self.assertNotIn("(s/n)", self.content,
                          "Publish no debe usar confirmaciones (s/n)")

    def test_compatible_team_csv_supported(self):
        self.assertIn("CSV de equipo compatible", self.content,
                      "Publish debe aceptar cualquier CSV de equipo compatible")

    def test_publish_forbids_bash_fallbacks(self):
        self.assertIn("NUNCA uses Bash generico, Fetch, curl, wget, python ad hoc", self.content,
                      "Publish debe prohibir fallbacks manuales por terminal o HTTP")
        self.assertIn("`.pspo-agent/runtime/trello-fallback.sh`", self.content,
                      "Publish debe permitir solo el fallback oficial controlado")
        self.assertIn("`.pspo-agent/runtime/notion-fallback.sh`", self.content,
                      "Publish debe contemplar el fallback oficial de Notion")
        self.assertIn("puedes usar `Task` con `publisher`", self.content,
                      "Publish debe seguir documentando la via con publisher en modo interactivo")
        self.assertIn("trello-fallback.py", self.content,
                      "Publish debe documentar el fallback oficial controlado")

    def test_publish_has_provider_routing_and_notion_path(self):
        self.assertIn("Paso 0: Resolver proveedor remoto", self.content)
        self.assertIn("Ruta Notion", self.content)
        self.assertIn("resolve-user-by-email", self.content)
        self.assertIn("upload-and-attach-markdown", self.content)
        self.assertIn("NUNCA leas `.env` con `Read`", self.content)
        self.assertIn(".pspo-agent/runtime/notion-fallback.sh env-status --pretty", self.content)
        self.assertIn("ensure-dependency-relations", self.content)
        self.assertIn("find-story-page", self.content)
        self.assertIn("update-story-page", self.content)
        self.assertIn("set-story-dependencies", self.content)
        self.assertIn("Bloqueada_por", self.content)
        self.assertIn("Bloquea", self.content)


# ---------------------------------------------------------------------------
# Generate stories: pasos criticos
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Publisher agent: prohibiciones y herramientas
# ---------------------------------------------------------------------------

class TestPublisherAgent(unittest.TestCase):
    """El publisher debe prohibir bash generico y listar herramientas Trello."""

    def setUp(self):
        self.content = read_file("agents/publisher.md")

    def test_prohibits_bash(self):
        self.assertIn("NUNCA", self.content)
        self.assertIn("bash", self.content.lower())

    def test_has_official_fallback(self):
        self.assertIn("trello-fallback.py", self.content)
        self.assertIn("fallback oficial", self.content.lower())

    def test_prohibits_curl(self):
        self.assertIn("curl", self.content.lower())

    def test_lists_attach_file(self):
        self.assertIn("attach-file", self.content)

    def test_lists_add_checklist(self):
        self.assertIn("add-checklist", self.content)

    def test_lists_invite_member(self):
        self.assertIn("invite-member", self.content)

    def test_lists_get_board_members(self):
        self.assertIn("get-board-members", self.content)

    def test_batch_processing(self):
        self.assertIn("lotes de 5", self.content)

    def test_verify_before_create_lists(self):
        self.assertIn("Verificar antes de crear listas", self.content)

    def test_id_members_support(self):
        self.assertIn("idMembers", self.content)
        self.assertIn("create-card", self.content,
                      "Publisher debe documentar la compatibilidad con prompts singulares")
        self.assertIn("Verificacion obligatoria despues de crear o sincronizar", self.content,
                      "Publisher debe verificar post-publicacion")

    def test_all_trello_tools_listed(self):
        tools = ["verify-credentials", "list-boards", "get-board",
                 "create-board", "manage-lists", "manage-labels",
                 "create-cards", "search-cards", "get-card", "update-card", "add-checklist",
                 "attach-file", "get-board-members", "invite-member"]
        for tool in tools:
            self.assertIn(tool, self.content,
                          f"Publisher no lista herramienta: {tool}")

    def test_compatible_team_csv_supported(self):
        self.assertIn("CSV de equipo compatible", self.content,
                      "Publisher debe trabajar con cualquier CSV de equipo compatible")


class TestFlexibleTeamCsv(unittest.TestCase):
    """El flujo no debe depender rigidamente del nombre team.csv."""

    def test_team_skill_accepts_any_filename(self):
        content = read_file("skills/team/SKILL.md")
        self.assertIn("cuyo nombre puede ser el que el usuario quiera", content)
        self.assertIn("cualquier fichero `.csv`", content)

    def test_autopilot_detects_any_compatible_csv(self):
        content = read_file("skills/autopilot/SKILL.md")
        self.assertIn("cualquier `*.csv` compatible con equipo", content)
        self.assertIn("CSV de equipo compatible", content)

    def test_autopilot_checks_optional_files_before_reading(self):
        content = read_file("skills/autopilot/SKILL.md")
        self.assertIn("NUNCA leas rutas opcionales que no hayas confirmado que existen", content)
        self.assertIn("Si una ruta opcional no existe, continua sin ella", content)

    def test_autopilot_forbids_trello_fallbacks(self):
        content = read_file("skills/autopilot/SKILL.md")
        self.assertIn("NUNCA improvises un flujo alternativo con Bash, Fetch, curl, wget o scripts Python ad hoc contra Trello", content)
        self.assertIn("trello-fallback.py", content)

    def test_autopilot_mentions_provider_selection_runtime(self):
        content = read_file("skills/autopilot/SKILL.md")
        self.assertIn("publish-provider.json", content)
        self.assertIn("proveedores remotos configurados", content)

    def test_autopilot_forbids_direct_agent_or_task(self):
        content = read_file("skills/autopilot/SKILL.md")
        self.assertIn("NUNCA uses `Agent` ni `Task` directamente desde `autopilot`", content)

    def test_autopilot_forces_linear_execution(self):
        content = read_file("skills/autopilot/SKILL.md")
        self.assertIn("La ejecucion es **lineal**", content)
        self.assertIn('Cualquier intento de usar `Bash`, `Agent`, `Task`', content)

    def test_autopilot_starts_with_glob_not_bash(self):
        content = read_file("skills/autopilot/SKILL.md")
        self.assertIn("Lista los ficheros presentes con `Glob`, no con Bash", content)
        self.assertIn("Primer barrido: `{carpeta}/*`", content)
        self.assertIn("tras leer el", content)

    def test_autopilot_uses_explicit_skill_chain(self):
        content = read_file("skills/autopilot/SKILL.md")
        for skill_name in [
            'Skill("pspo-agent:product-phase")',
            'Skill("pspo-agent:validate")',
            'Skill("pspo-agent:assign")',
            'Skill("pspo-agent:dependencies")',
            'Skill("pspo-agent:sprint-plan")',
            'Skill("pspo-agent:publish")',
        ]:
            self.assertIn(skill_name, content,
                          f"autopilot debe usar la cadena explicita {skill_name}")

    def test_start_and_validate_use_compatible_csv_language(self):
        start = read_file("skills/start/SKILL.md")
        validate = read_file("skills/validate/SKILL.md")
        self.assertIn("CSV de equipo compatible", start)
        self.assertIn("CSV de equipo compatible", validate)

    def test_sprint_plan_reads_compatible_csv(self):
        content = read_file("skills/sprint-plan/SKILL.md")
        self.assertIn("CSV de equipo compatible", content)

    def test_prd_documents_compatible_csv(self):
        content = read_file("docs/prd.md")
        self.assertIn("CSV de equipo compatible", content)
        self.assertIn("nombre,email,rol,categoria,dedicacion,usa_agente_ia", content)


class TestAutopilotGuardrails(unittest.TestCase):
    """Autopilot debe orquestar skills y no reinventar el flujo."""

    def setUp(self):
        self.skill = read_file("skills/autopilot/SKILL.md")
        self.command = read_file("commands/autopilot.md")

    def test_uses_default_inbox_when_arguments_missing(self):
        self.assertIn("Si `$ARGUMENTS` esta vacio", self.command,
                      "El comando autopilot debe resolver el caso sin argumentos")
        self.assertIn(".pspo-agent/inbox", self.command,
                      "El comando autopilot debe usar .pspo-agent/inbox por defecto")

    def test_forbids_reading_local_settings_to_discover_input(self):
        self.assertIn("No preguntes por la ruta ni leas `.claude/settings.local.json`", self.command,
                      "El comando autopilot no debe inspeccionar settings.local para deducir la inbox")
        self.assertIn("NO leas `.claude/settings.local.json`", self.skill,
                      "La skill autopilot no debe inspeccionar settings.local")

    def test_forbids_plugin_source_inspection(self):
        self.assertIn("No inspecciones el codigo fuente del plugin", self.skill,
                      "Autopilot no debe re-leer el propio plugin para decidir el flujo")
        self.assertIn("commands/", self.skill)
        self.assertIn("skills/", self.skill)
        self.assertIn("agents/", self.skill)

    def test_forbids_bash_for_file_ops(self):
        self.assertIn("Bash esta prohibido en este flujo", self.skill,
                      "Autopilot debe prohibir Bash para operaciones locales")
        self.assertIn("`ls`, `cp`, `mkdir`,", self.skill,
                      "Autopilot debe dejar claro que Bash no se usa ni para utilidades basicas")

    def test_bootstrap_handles_csv_import_deterministically(self):
        self.assertIn("bootstrap del sistema lo detecta", self.skill)
        self.assertIn("elige uno de forma determinista", self.skill)

    def test_forbids_manual_generation_of_downstream_artifacts(self):
        self.assertIn("Esta skill **orquesta**", self.skill,
                      "Autopilot debe declararse como skill de orquestacion")
        self.assertIn("NUNCA redactes manualmente desde aqui el backlog", self.skill,
                      "Autopilot no debe generar backlog o HUs por su cuenta")
        self.assertIn("NUNCA escribas desde aqui `docs/analisis-requisitos.md`", self.skill,
                      "Autopilot no debe escribir analisis o backlog por fuera de las skills hijas")
        self.assertIn("Invoca las skills. No generes manualmente sus artefactos", self.skill,
                      "Autopilot debe encadenar skills en lugar de duplicarlas")

    def test_does_not_reinterpret_word_threshold(self):
        self.assertIn("95 palabras siguen siendo `discovery`", self.skill,
                      "Autopilot no debe reinterpretar el umbral de discovery/analyze")

    def test_does_not_read_env_during_product_phase(self):
        self.assertIn("No leas `.env` durante la fase de producto", self.skill,
                      "Autopilot no debe tocar credenciales antes de la rama publicar")

    def test_recovers_with_skill_after_hook_block(self):
        self.assertIn("Si un hook bloquea `Bash`, `Agent` o `Task`", self.skill)
        self.assertIn("volver al carril de `Skill(...)`", self.skill)

    def test_forbids_todowrite_and_side_config_inspection(self):
        self.assertIn("NUNCA uses `TodoWrite`, `ToolSearch`", self.skill)
        self.assertIn("`.pspo-agent/config*`", self.skill)
        self.assertIn("`docs/**/*.md`", self.skill)
        self.assertIn("`CLAUDE.md`", self.skill)
        self.assertIn("La **siguiente llamada de herramienta**", self.skill)

    def test_reentry_goes_directly_to_final_gate_when_product_ready(self):
        self.assertIn("Si reejecutas `/pspo-agent:autopilot`", self.skill)
        self.assertIn("siguientes pasos en texto plano", self.skill)
        self.assertIn("Paso 0: Reentrada determinista", self.skill)
        self.assertIn("Paso 5: Gate final unica", self.skill)
        self.assertIn("product-phase.status` esta en `done`", self.skill)
        self.assertIn("Paso 6: Rama revisar", self.skill)
        self.assertIn("Paso 7: Rama planificar y publicar", self.skill)


class TestAutopilotCompatibleSkills(unittest.TestCase):
    """Las skills hijas deben soportar ejecucion autonoma desde autopilot."""

    def test_analyze_supports_autopilot_mode(self):
        content = read_file("skills/analyze/SKILL.md")
        self.assertIn("## Modo autopilot", content)
        self.assertIn("NO hagas preguntas al usuario", content)
        self.assertIn("supuestos razonables", content)

    def test_product_phase_closes_with_autopilot_gate(self):
        content = read_file("skills/product-phase/SKILL.md")
        self.assertIn("100% no interactiva", content)
        self.assertIn("No hagas preguntas al usuario", content)
        self.assertIn(".pspo-agent/runtime/autopilot-context.md", content)
        self.assertIn("NUNCA releas la inbox durante `product-phase`", content)
        self.assertIn("NUNCA uses ToolSearch ni TodoWrite", content)
        self.assertIn("NUNCA uses `Task` ni `Agent`", content)
        self.assertIn('NUNCA hagas `Glob("docs/**/*")`', content)
        self.assertIn("siguiente", content)
        self.assertIn("llamada de herramienta", content,
                      "product-phase debe exigir marcar active antes de explorar docs")
        self.assertIn("3 historias maximo por ola de redaccion", content)
        self.assertIn("4 y un producto amplio puede necesitar 40", content)
        self.assertIn("no fuerces un numero minimo ni maximo", content)
        self.assertIn("HU-00 / vision", content)
        self.assertIn("docs/analisis-requisitos.md", content)
        self.assertIn("docs/backlog.md", content)
        self.assertIn("docs/auditoria-hu.md", content)
        self.assertIn("docs/historias/HU-*.md", content)
        self.assertIn("escribe inmediatamente los `docs/historias/HU-XX-*.md`", content)
        self.assertIn("no uses `mkdir`", content)
        self.assertIn("requirement-analyst", content)
        self.assertIn("product-owner", content)
        self.assertIn("criterio de `culture-guardian`", content)
        self.assertIn("criterio de `senior-auditor`", content)
        self.assertIn("varias olas de escritura", content)
        self.assertIn(".pspo-agent/runtime/final-gate.status", content)
        self.assertIn('**"Revisar historias"**', content)
        self.assertIn('**"Planificar y publicar"**', content)
        self.assertIn("La gate final no se resuelve aqui", content)
        self.assertIn('Skill("pspo-agent:validate")', content)
        self.assertIn('Skill("pspo-agent:assign")', content)
        self.assertIn('Skill("pspo-agent:publish")', content)

    def test_plan_publish_runtime_keeps_downstream_skills_in_autonomous_mode(self):
        assign = read_file("skills/assign/SKILL.md")
        dependencies = read_file("skills/dependencies/SKILL.md")
        sprint = read_file("skills/sprint-plan/SKILL.md")
        for content in [assign, dependencies, sprint]:
            self.assertIn("final-gate.status", content)
            self.assertIn("plan-publish", content)

    def test_discovery_supports_autopilot_mode(self):
        content = read_file("skills/discovery/SKILL.md")
        self.assertIn("## Modo autopilot", content)
        self.assertIn("NO hagas preguntas al usuario", content)
        self.assertIn("docs/analisis-requisitos.md", content)

    def test_generate_stories_supports_autopilot_mode(self):
        content = read_file("skills/generate-stories/SKILL.md")
        self.assertIn("## Modo autopilot", content)
        self.assertIn("NO llames desde aqui a `save-docs`, `audit` ni `validate`", content)
        self.assertIn("Asigna automaticamente `Estimacion`", content)

    def test_audit_supports_autopilot_mode(self):
        content = read_file("skills/audit/SKILL.md")
        self.assertIn("## Modo autopilot", content)
        self.assertIn("NO uses AskUserQuestion", content)
        self.assertIn("docs/auditoria-hu.md", content)


class TestUninstallScripts(unittest.TestCase):
    """La desinstalacion debe tratar cualquier CSV de equipo compatible."""

    def test_uninstall_sh_supports_compatible_csvs(self):
        content = read_file("uninstall.sh")
        self.assertIn("CSVs de equipo compatibles", content)
        self.assertIn("nombre,email,rol,categoria,dedicacion,usa_agente_ia", content)
        self.assertIn("collect_compatible_team_csvs", content)

    def test_uninstall_ps1_supports_compatible_csvs(self):
        content = read_file("uninstall.ps1")
        self.assertIn("CSVs de equipo compatibles", content)
        self.assertIn("nombre,email,rol,categoria,dedicacion,usa_agente_ia", content)
        self.assertIn("Get-CompatibleTeamCsvFiles", content)


class TestHistoricalDocsWarnings(unittest.TestCase):
    """Los documentos historicos deben marcarse como tales."""

    def test_changelog_is_marked_historical(self):
        content = read_file("CHANGELOG.md")
        self.assertIn("historial de releases", content)
        self.assertIn("fuente de verdad", content)

    def test_plan_docs_are_marked_historical(self):
        for path in [
            "docs/plans/2026-03-14-sprint-planner-design.md",
            "docs/plans/2026-03-14-fix-real-usage-issues.md",
        ]:
            content = read_file(path)
            self.assertIn("plan historico", content,
                          f"{path} debe indicar que es historico")


class TestProviderDocs(unittest.TestCase):
    """La documentación viva debe reflejar la capa de proveedores."""

    def test_documents_readme_links_notion_integration(self):
        content = read_file("Documents/README.md")
        self.assertIn("notion-integration.md", content)
        self.assertIn("publish-provider.json", content)

    def test_configuration_mentions_notion_env(self):
        content = read_file("Documents/configuration.md")
        self.assertIn("NOTION_TOKEN", content)
        self.assertIn("NOTION_PARENT_PAGE_ID", content)
        self.assertIn("publish-provider.py", content)

    def test_architecture_mentions_provider_layer(self):
        content = read_file("Documents/architecture.md")
        self.assertIn("publish-provider runtime", content)
        self.assertIn("publish-provider.json", content)

    def test_notion_integration_doc_exists_and_is_zero_template(self):
        content = read_file("Documents/notion-integration.md")
        self.assertIn("zero-template", content)
        self.assertIn("NOTION_PARENT_PAGE_ID", content)
        self.assertIn("HU-00 · Vision", content)

    def test_env_example_includes_notion_variables(self):
        content = read_file(".env.example")
        self.assertIn("NOTION_TOKEN", content)
        self.assertIn("NOTION_PARENT_PAGE_ID", content)


# ---------------------------------------------------------------------------
# Onboarding: AskUserQuestion obligatorio
# ---------------------------------------------------------------------------

class TestOnboardingAskUserQuestion(unittest.TestCase):
    """Onboarding debe usar AskUserQuestion y no (s/n)."""

    def setUp(self):
        self.content = read_file("skills/onboarding/SKILL.md")

    def test_uses_ask_user_question(self):
        self.assertIn("AskUserQuestion", self.content)

    def test_no_sn_confirmations(self):
        self.assertNotIn("(s/n)", self.content,
                          "Onboarding no debe usar confirmaciones (s/n)")

    def test_board_selection_interactive(self):
        self.assertIn("Que tablero quieres usar", self.content)

    def test_retry_on_failure_interactive(self):
        self.assertIn("Reintentar API Key", self.content)

    def test_does_not_echo_resolved_authorization_url(self):
        self.assertNotIn("URL_CONSTRUIDA_CON_LA_API_KEY", self.content,
                         "Onboarding no debe mostrar la URL resuelta con la API key")
        self.assertIn("<TU_API_KEY>", self.content,
                      "Onboarding debe mostrar una plantilla segura con placeholder")

    def test_env_is_source_of_truth_for_credentials(self):
        self.assertIn("`.env` es la fuente de verdad", self.content)
        self.assertIn(".pspo-agent/runtime/trello-fallback.sh env-status --pretty", self.content)
        self.assertIn(".pspo-agent/runtime/notion-fallback.sh env-status --pretty", self.content)
        self.assertIn("publish-provider.py", self.content)
        self.assertIn("las **primeras llamadas validas**", self.content)
        self.assertIn("allowed-tools: Write, Edit, Bash, Task, AskUserQuestion", self.content)

    def test_autopilot_board_creation_rule_exists(self):
        self.assertIn("NO hagas esta pregunta", self.content)
        self.assertIn("crear automaticamente un tablero nuevo", self.content)

    def test_onboarding_has_notion_route(self):
        self.assertIn("Ruta Notion", self.content)
        self.assertIn("NOTION_TOKEN", self.content)
        self.assertIn("NOTION_PARENT_PAGE_ID", self.content)
        self.assertIn("create-project", self.content)
        self.assertIn("crea automaticamente", self.content)
        self.assertIn("no preguntes si quieres crearla", self.content)


# ---------------------------------------------------------------------------
# Hooks: bloqueo de bash con Trello
# ---------------------------------------------------------------------------

class TestHooksConfig(unittest.TestCase):
    """hooks.json debe bloquear bash con Trello."""

    def setUp(self):
        import json
        with open(os.path.join(PLUGIN_ROOT, "hooks", "hooks.json")) as f:
            self.hooks = json.load(f)

    def test_bash_hook_exists(self):
        matchers = [h["matcher"] for h in self.hooks["hooks"]["PreToolUse"]]
        self.assertIn("Bash", matchers,
                       "No hay hook PreToolUse para Bash")

    def test_fetch_hook_exists(self):
        matchers = [h["matcher"] for h in self.hooks["hooks"]["PreToolUse"]]
        self.assertIn("Fetch", matchers,
                       "No hay hook PreToolUse para Fetch")

    def test_read_hook_exists(self):
        matchers = [h["matcher"] for h in self.hooks["hooks"]["PreToolUse"]]
        self.assertIn("Read", matchers,
                       "No hay hook PreToolUse para Read sensible")

    def test_glob_hook_exists(self):
        matchers = [h["matcher"] for h in self.hooks["hooks"]["PreToolUse"]]
        self.assertIn("Glob", matchers,
                      "No hay hook PreToolUse para Glob en autopilot")

    def test_toolsearch_hook_exists(self):
        matchers = [h["matcher"] for h in self.hooks["hooks"]["PreToolUse"]]
        self.assertIn("ToolSearch", matchers,
                      "No hay hook PreToolUse para ToolSearch en autopilot")

    def test_ask_user_question_hook_exists(self):
        matchers = [h["matcher"] for h in self.hooks["hooks"]["PreToolUse"]]
        self.assertIn("AskUserQuestion", matchers,
                      "No hay hook PreToolUse para AskUserQuestion en onboarding")

    def test_todowrite_hook_exists(self):
        matchers = [h["matcher"] for h in self.hooks["hooks"]["PreToolUse"]]
        self.assertIn("TodoWrite", matchers,
                      "No hay hook PreToolUse para TodoWrite en autopilot")

    def test_agent_hook_exists(self):
        matchers = [h["matcher"] for h in self.hooks["hooks"]["PreToolUse"]]
        self.assertIn("Agent", matchers,
                      "No hay hook PreToolUse para Agent en autopilot")

    def test_skill_hook_exists(self):
        matchers = [h["matcher"] for h in self.hooks["hooks"]["PreToolUse"]]
        self.assertIn("Skill", matchers,
                      "No hay hook PreToolUse para Skill en autopilot")

    def test_task_hook_exists(self):
        matchers = [h["matcher"] for h in self.hooks["hooks"]["PreToolUse"]]
        self.assertIn("Task", matchers,
                      "No hay hook PreToolUse para Task en autopilot")

    def test_trello_mcp_hook_exists(self):
        matchers = [h["matcher"] for h in self.hooks["hooks"]["PreToolUse"]]
        self.assertIn("mcp__trello-client__.*", matchers,
                      "No hay hook PreToolUse para MCP Trello en autopilot")

    def test_block_trello_bash_script_exists(self):
        path = os.path.join(PLUGIN_ROOT, "hooks", "scripts", "block-trello-bash.sh")
        self.assertTrue(os.path.exists(path),
                         "Script block-trello-bash.sh no existe")

    def test_warn_sensitive_read_script_exists(self):
        path = os.path.join(PLUGIN_ROOT, "hooks", "scripts", "warn-sensitive-read.sh")
        self.assertTrue(os.path.exists(path),
                        "Script warn-sensitive-read.sh no existe")

    def test_warn_sensitive_read_mentions_both_official_wrappers(self):
        content = read_file("hooks/scripts/warn-sensitive-read.sh")
        self.assertIn(".pspo-agent/runtime/trello-fallback.sh env-status --pretty", content)
        self.assertIn(".pspo-agent/runtime/notion-fallback.sh env-status --pretty", content)
        self.assertIn(".pspo-agent/runtime/publish-provider.py .", content)

    def test_block_autopilot_agent_script_exists(self):
        path = os.path.join(PLUGIN_ROOT, "hooks", "scripts", "block-autopilot-agent.sh")
        self.assertTrue(os.path.exists(path),
                        "Script block-autopilot-agent.sh no existe")

    def test_block_autopilot_drift_script_exists(self):
        path = os.path.join(PLUGIN_ROOT, "hooks", "scripts", "block-autopilot-drift.sh")
        self.assertTrue(os.path.exists(path),
                        "Script block-autopilot-drift.sh no existe")

    def test_block_autopilot_skill_script_exists(self):
        path = os.path.join(PLUGIN_ROOT, "hooks", "scripts", "block-autopilot-skill.sh")
        self.assertTrue(os.path.exists(path),
                        "Script block-autopilot-skill.sh no existe")

    def test_persist_autopilot_gate_script_exists(self):
        path = os.path.join(PLUGIN_ROOT, "hooks", "scripts", "persist-autopilot-gate.py")
        self.assertTrue(os.path.exists(path),
                        "Script persist-autopilot-gate.py no existe")

    def test_block_autopilot_trello_script_exists(self):
        path = os.path.join(PLUGIN_ROOT, "hooks", "scripts", "block-autopilot-trello.sh")
        self.assertTrue(os.path.exists(path),
                        "Script block-autopilot-trello.sh no existe")

    def test_block_secret_prompt_leak_script_exists(self):
        path = os.path.join(PLUGIN_ROOT, "hooks", "scripts", "block-secret-prompt-leak.py")
        self.assertTrue(os.path.exists(path),
                        "Script block-secret-prompt-leak.py no existe")

    def test_autopilot_guard_script_exists(self):
        path = os.path.join(PLUGIN_ROOT, "hooks", "scripts", "autopilot-guard.py")
        self.assertTrue(os.path.exists(path),
                        "Script autopilot-guard.py no existe")

    def test_autopilot_bootstrap_script_exists(self):
        path = os.path.join(PLUGIN_ROOT, "hooks", "scripts", "autopilot-bootstrap.py")
        self.assertTrue(os.path.exists(path),
                        "Script autopilot-bootstrap.py no existe")

    def test_block_scripts_emit_actionable_message(self):
        bash_hook = read_file("hooks/scripts/block-trello-bash.sh")
        agent_hook = read_file("hooks/scripts/block-autopilot-agent.sh")
        drift_hook = read_file("hooks/scripts/block-autopilot-drift.sh")
        trello_hook = read_file("hooks/scripts/block-autopilot-trello.sh")
        secret_hook = read_file("hooks/scripts/block-secret-prompt-leak.py")
        guard_script = read_file("hooks/scripts/autopilot-guard.py")
        bootstrap_script = read_file("hooks/scripts/autopilot-bootstrap.py")
        self.assertIn("emit_block", bash_hook)
        self.assertIn("emit_block", agent_hook)
        self.assertIn("emit_block", drift_hook)
        self.assertIn("emit_block", trello_hook)
        self.assertIn("Nunca copies API keys ni tokens", secret_hook)
        self.assertIn("Trello o Notion", secret_hook)
        self.assertIn("Usa Glob para listar", bash_hook)
        self.assertIn("trello-fallback.sh", bash_hook)
        self.assertIn("notion-fallback.sh", bash_hook)
        self.assertIn("publish-provider.py", bash_hook)
        self.assertIn("Skill(\\\"pspo-agent:product-phase\\\")", agent_hook)
        self.assertIn("pspo-agent:product-phase", agent_hook)
        self.assertIn("notion-fallback.sh verify-credentials", agent_hook)
        self.assertIn("no uses ToolSearch ni TodoWrite", drift_hook)
        self.assertIn("No leas docs, .claude, .env", drift_hook)
        self.assertIn(".pspo-agent/inbox", drift_hook)
        self.assertIn("Durante product-phase no inspecciones .claude, .env", drift_hook)
        self.assertIn("publish-provider.py", drift_hook)
        self.assertIn("notion-fallback.sh verify-credentials", drift_hook)
        self.assertIn("Trello va despues de la fase de producto", trello_hook)
        self.assertIn("product-phase.status", guard_script)
        self.assertIn("modo_producto", bootstrap_script)


class TestStartProviderRouting(unittest.TestCase):
    def test_start_mentions_provider_resolution(self):
        content = read_file("skills/start/SKILL.md")
        self.assertIn("Paso 0: Resolver proveedor remoto", content)
        self.assertIn("Solo local", content)
        self.assertIn("runtime/notion-fallback.sh", content)
        self.assertIn("publish-provider.py", content)

    def test_onboarding_forces_bash_first_call(self):
        content = read_file("skills/onboarding/SKILL.md")
        self.assertIn("Primera llamada obligatoria de herramienta", content)
        self.assertIn("Empieza por `Bash`, no por `Glob`", content)
        self.assertIn("publish-provider.py", content)


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
        for size in ["XS = 1", "S = 2", "M = 4", "L = 8", "XL = 16"]:
            self.assertIn(size, self.content,
                          f"Falta talla de estimacion: {size}")

    def test_clear_step_order(self):
        self.assertIn("6a.", self.content,
                       "generate-stories no tiene paso 6a (save-docs primero)")
        self.assertIn("6b.", self.content,
                       "generate-stories no tiene paso 6b (culture-guardian)")
        self.assertIn("6c.", self.content,
                       "generate-stories no tiene paso 6c (auditoria)")
        self.assertIn("6d.", self.content,
                       "generate-stories no tiene paso 6d (presentar)")
        self.assertIn("6e.", self.content,
                       "generate-stories no tiene paso 6e (validate)")


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
        self.assertEqual(sizes["XS"], 1)
        self.assertEqual(sizes["S"], 2)
        self.assertEqual(sizes["M"], 4)
        self.assertEqual(sizes["L"], 8)
        self.assertEqual(sizes["XL"], 16)

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
        self.assertIn("XS / S / M / L / XL", self.content,
                       "Plantilla HU no muestra tallas")

    def test_hu_template_has_context_narrative(self):
        self.assertIn("## Contexto narrativo", self.content,
                       "Plantilla HU debe incluir contexto narrativo amplio")

    def test_hu_template_has_mermaid(self):
        self.assertIn("## Flujo operativo", self.content)
        self.assertIn("```mermaid", self.content,
                       "Plantilla HU debe incluir un diagrama Mermaid")

    def test_hu_template_has_optional_table_section(self):
        self.assertIn("## Tabla de datos o reglas", self.content,
                       "Plantilla HU debe ofrecer una tabla explicativa")

    def test_hu_template_prefers_long_form(self):
        self.assertIn("Mejor largo y explicativo", self.content,
                       "Plantilla HU debe empujar a un contenido explicativo")

    def test_vision_template_has_mermaid_map(self):
        self.assertIn("Mapa operativo y dependencias criticas", self.content)
        self.assertIn("mermaid", self.content.lower())
        self.assertIn("Vision / HU-00", self.content,
                      "La vision debe tratarse como HU-00")

    def test_backlog_has_talla_column(self):
        self.assertIn("Talla", self.content,
                       "Backlog no tiene columna de talla")

    def test_backlog_has_horas_column(self):
        self.assertIn("Horas", self.content,
                       "Backlog no tiene columna de horas")

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

    def test_routes_to_assignments_and_dependencies(self):
        self.assertIn("/pspo-agent:assign", self.content)
        self.assertIn("/pspo-agent:dependencies", self.content)

    def test_uses_env_status_as_first_probe(self):
        self.assertIn(".pspo-agent/runtime/trello-fallback.sh env-status --pretty", self.content)
        self.assertIn("NUNCA uses `Glob(\"**/.claude/**\")`", self.content)


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

    def test_assignment_is_visible_in_summary(self):
        self.assertIn("Asignado a:", self.content)
        self.assertIn("persona asignada", self.content.lower())


# ---------------------------------------------------------------------------
# Team CSV template on web
# ---------------------------------------------------------------------------

class TestTeamTemplate(unittest.TestCase):
    """La plantilla CSV del equipo debe existir en la web."""

    def test_team_skill_references_download(self):
        content = read_file("skills/team/SKILL.md")
        self.assertIn("team-template.csv", content,
                       "Skill team no referencia la plantilla CSV descargable")


if __name__ == "__main__":
    unittest.main()
