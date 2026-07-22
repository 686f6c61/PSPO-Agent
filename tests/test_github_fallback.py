import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock


PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..")
FALLBACK_PATH = os.path.join(PLUGIN_ROOT, "servers", "github-fallback.py")


def load_module():
    spec = importlib.util.spec_from_file_location("github_fallback", FALLBACK_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def full_schema():
    """Esquema completo del proyecto para tests de mapeo campo a campo."""
    return {
        "status": {
            "fieldId": "F_status",
            "dataType": "SINGLE_SELECT",
            "options": {
                "backlog": "st_backlog",
                "sprint activo": "st_sprint",
                "bloqueada": "st_blocked",
                "en progreso": "st_prog",
                "en revision": "st_rev",
                "hecho": "st_done",
            },
            "optionsFull": [],
        },
        "prioridad": {
            "fieldId": "F_prio",
            "dataType": "SINGLE_SELECT",
            "options": {"critica": "p_c", "alta": "p_a", "media": "p_m", "baja": "p_b"},
            "optionsFull": [],
        },
        "talla": {
            "fieldId": "F_talla",
            "dataType": "SINGLE_SELECT",
            "options": {"xs": "t_xs", "s": "t_s", "m": "t_m", "l": "t_l", "xl": "t_xl"},
            "optionsFull": [],
        },
        "horas": {"fieldId": "F_horas", "dataType": "NUMBER", "options": {}, "optionsFull": []},
        "sprint": {
            "fieldId": "F_sprint",
            "dataType": "SINGLE_SELECT",
            "options": {"sprint 1": "sp_1"},
            "optionsFull": [{"id": "sp_1", "name": "Sprint 1", "color": "BLUE", "description": ""}],
        },
        "responsable": {"fieldId": "F_resp", "dataType": "TEXT", "options": {}, "optionsFull": []},
    }


class TestGithubFallback(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    # -- env-status ---------------------------------------------------------

    def test_env_status_masks_token_and_reports_auth(self):
        module = self.module
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.dict(os.environ, {
            "GITHUB_TOKEN": "ghp_super_secret_token_value",
        }, clear=False):
            with mock.patch.object(sys, "argv", ["github-fallback.py", "env-status", "--pretty"]):
                with mock.patch("sys.stdout", stdout), mock.patch("sys.stderr", stderr), \
                        mock.patch("sys.stdin", io.StringIO("")):
                    exit_code = module.main()
        self.assertEqual(exit_code, 0, stderr.getvalue())
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["hasGithubToken"])
        self.assertEqual(payload["authMethod"], "token")
        self.assertTrue(payload["tokenMasked"].startswith("****"))

    def test_env_status_reports_project_targets(self):
        module = self.module
        with mock.patch.dict(os.environ, {
            "GITHUB_PROJECT_ID": "PVT_kwABCD",
            "GITHUB_PROJECT_NUMBER": "7",
            "GITHUB_PROJECT_OWNER": "octocat",
        }, clear=False):
            status = module._env_status()
        self.assertTrue(status["hasProjectId"])
        self.assertTrue(status["hasProjectNumber"])
        self.assertEqual(status["projectOwner"], "octocat")

    # -- help ---------------------------------------------------------------

    def test_help_lists_supported_tools_and_project_fields(self):
        module = self.module
        payload = module.help_info({})
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["provider"], "github")
        for tool in ("create-project", "save-project-targets", "sync-story-from-markdown",
                     "sync-stories-from-folder", "parse-story-markdown", "list-tools"):
            self.assertIn(tool, payload["supportedTools"])
        for field in ("Status", "Prioridad", "Talla", "Horas", "Sprint", "Responsable"):
            self.assertIn(field, payload["projectFields"])

    # -- parse story + estimation ------------------------------------------

    def test_parse_story_markdown_maps_metadata_fields(self):
        module = self.module
        markdown = """# HU-02 · Cerrar sesion

| Campo | Valor |
| --- | --- |
| ID | HU-02 |
| Prioridad | Media |
| Estimacion | M (4h) |
| Sprint | Sprint 1 |
| Estado | En progreso |
| Asignado a | Ana Garcia (ana@example.com) |
| Dependencias | HU-01, HU-03 |

## Resumen

Como persona usuaria quiero cerrar sesion para salir de la zona privada.
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "HU-02-cerrar-sesion.md")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(markdown)
            payload = module.parse_story_markdown({"filePath": path})
        self.assertEqual(payload["storyId"], "HU-02")
        self.assertEqual(payload["priority"], "Media")
        self.assertEqual(payload["size"], "M")
        self.assertEqual(payload["hours"], 4.0)
        self.assertEqual(payload["sprint"], "Sprint 1")
        self.assertEqual(payload["state"], "En progreso")
        self.assertEqual(payload["assignedRaw"], "Ana Garcia (ana@example.com)")
        self.assertEqual(payload["assignedEmail"], "ana@example.com")
        self.assertEqual(payload["dependencyStoryIds"], ["HU-01", "HU-03"])

    def test_parse_estimation_size_and_hours(self):
        module = self.module
        self.assertEqual(module._parse_estimation("M"), ("M", 4.0))
        self.assertEqual(module._parse_estimation("4h"), ("M", 4.0))
        self.assertEqual(module._parse_estimation("XL (16h)"), ("XL", 16.0))
        # 3h es equidistante entre S(2) y M(4): el desempate elige la talla menor.
        self.assertEqual(module._parse_estimation("3"), ("S", 3.0))
        self.assertEqual(module._parse_estimation("8h"), ("L", 8.0))
        self.assertEqual(module._parse_estimation(""), ("", None))

    def test_resolve_status_prefers_state_then_sprint(self):
        module = self.module
        self.assertEqual(module._resolve_status({"state": "Hecho", "sprint": "Sprint 1"}), "Hecho")
        self.assertEqual(module._resolve_status({"state": "", "sprint": "Sprint 1"}), "Sprint activo")
        self.assertEqual(module._resolve_status({"state": "", "sprint": ""}), "Backlog")
        self.assertEqual(module._resolve_status({"state": "x", "sprint": ""}, "En revision"), "En revision")

    # -- README del proyecto ------------------------------------------------

    def test_project_readme_documents_states_and_views(self):
        module = self.module
        readme = module._project_readme("Demo")
        self.assertIn("Estados del kanban", readme)
        self.assertIn("Sprint activo", readme)
        self.assertIn("Glosario de campos", readme)
        self.assertIn("Vistas recomendadas", readme)
        self.assertIn("Tablero por Status", readme)
        self.assertIn("Tabla por Sprint", readme)
        short = module._project_short_description("Demo")
        self.assertIn("Demo", short)

    # -- verify credentials -------------------------------------------------

    def test_verify_credentials_reports_missing_project_scope(self):
        module = self.module
        with mock.patch.object(module, "_graphql", return_value={"viewer": {"id": "U_1", "login": "octocat"}}):
            with mock.patch.object(module, "_oauth_scopes", return_value=["repo", "read:org"]):
                with mock.patch.object(module, "_gh_available", return_value=True):
                    result = module.verify_credentials({})
        self.assertFalse(result["hasProjectScope"])
        self.assertIn("gh auth refresh -s project", result["warning"])

    def test_verify_credentials_accepts_project_scope(self):
        module = self.module
        with mock.patch.object(module, "_graphql", return_value={"viewer": {"id": "U_1", "login": "octocat"}}):
            with mock.patch.object(module, "_oauth_scopes", return_value=["repo", "project"]):
                result = module.verify_credentials({})
        self.assertTrue(result["hasProjectScope"])
        self.assertNotIn("warning", result)

    # -- create project + schema -------------------------------------------

    def test_create_project_creates_private_project_and_schema(self):
        module = self.module
        graphql_responses = [
            {"viewer": {"id": "U_owner", "login": "octocat"}},
            {"createProjectV2": {"projectV2": {
                "id": "PVT_1", "number": 7, "title": "PSPO · Demo",
                "url": "https://github.com/users/octocat/projects/7",
            }}},
            {"updateProjectV2": {"projectV2": {"id": "PVT_1"}}},
        ]
        schema = full_schema()
        schema["_meta"] = {"statusUpdated": True, "createdFields": ["Prioridad", "Talla", "Horas", "Responsable"]}
        with mock.patch.object(module, "_graphql", side_effect=graphql_responses) as graphql:
            with mock.patch.object(module, "_ensure_project_schema", return_value=schema) as ensure:
                result = module.create_project({"projectName": "Demo"})
        self.assertTrue(result["ok"])
        self.assertEqual(result["projectId"], "PVT_1")
        self.assertEqual(result["projectOwner"], "octocat")
        self.assertTrue(result["statusUpdated"])
        self.assertIn("Prioridad", result["createdFields"])
        ensure.assert_called_once_with("PVT_1")
        # 3 llamadas graphql: viewer, create, updateMeta.
        self.assertEqual(graphql.call_count, 3)
        create_vars = graphql.call_args_list[1].args[1]
        self.assertTrue(create_vars["title"].startswith("PSPO · "))
        meta_vars = graphql.call_args_list[2].args[1]
        self.assertIn("readme", meta_vars)
        self.assertIn("Vistas recomendadas", meta_vars["readme"])

    def test_ensure_status_field_updates_native_options(self):
        module = self.module
        schema = {"status": {
            "fieldId": "F_status",
            "dataType": "SINGLE_SELECT",
            "options": {"todo": "o1", "done": "o2"},
            "optionsFull": [],
        }}
        updated = {"updateProjectV2Field": {"projectV2Field": {
            "id": "F_status", "name": "Status",
            "options": [{"id": f"o{i}", "name": name, "color": c, "description": d}
                        for i, (name, c, d) in enumerate(module.STATUS_OPTIONS)],
        }}}
        with mock.patch.object(module, "_graphql", return_value=updated) as graphql:
            result = module._ensure_status_field("PVT_1", schema)
        self.assertTrue(result["updated"])
        graphql.assert_called_once()
        self.assertIn("sprint activo", schema["status"]["options"])

    def test_ensure_status_field_skips_when_options_present(self):
        module = self.module
        schema = full_schema()
        with mock.patch.object(module, "_graphql") as graphql:
            result = module._ensure_status_field("PVT_1", schema)
        self.assertFalse(result["updated"])
        graphql.assert_not_called()

    def test_build_schema_maps_fields_by_name(self):
        module = self.module
        fields = [
            {"id": "F_status", "name": "Status", "dataType": "SINGLE_SELECT",
             "options": [{"id": "o1", "name": "Backlog", "color": "GRAY", "description": ""}]},
            {"id": "F_horas", "name": "Horas", "dataType": "NUMBER"},
            {"id": "F_other", "name": "Otro", "dataType": "TEXT"},
        ]
        schema = module._build_schema(fields)
        self.assertIn("status", schema)
        self.assertIn("horas", schema)
        self.assertNotIn("otro", schema)
        self.assertEqual(schema["status"]["options"]["backlog"], "o1")

    # -- find story item / dedupe ------------------------------------------

    def test_find_story_item_dedupes_by_story_id(self):
        module = self.module
        items = [
            {"id": "PVTI_1", "content": {"id": "DI_1", "title": "HU-00 · Vision"}},
            {"id": "PVTI_2", "content": {"id": "DI_2", "title": "HU-01 · Login"}},
        ]
        with mock.patch.object(module, "_list_project_items", return_value=items):
            result = module.find_story_item({"projectId": "PVT_1", "storyId": "HU-01"})
        self.assertTrue(result["ok"])
        self.assertEqual(result["itemId"], "PVTI_2")

    # -- sync story: mapeo campo a campo -----------------------------------

    def test_sync_story_maps_each_field_to_its_own_field(self):
        module = self.module
        parsed = {
            "ok": True, "filePath": "/tmp/HU-01.md", "markdown": "# HU-01 · Login\n\nDetalle",
            "storyId": "HU-01", "title": "Login", "fullTitle": "HU-01 · Login",
            "priority": "Alta", "estimation": "M (4h)", "size": "M", "hours": 4.0,
            "sprint": "Sprint 1", "state": "", "assignedRaw": "Ana Garcia (ana@example.com)",
            "assignedEmail": "ana@example.com", "dependenciesText": "", "dependencyStoryIds": [],
        }
        calls: list[tuple] = []

        def record_field(project_id, item_id, field_id, value):
            calls.append((field_id, value))

        with mock.patch.object(module, "parse_story_markdown", return_value=parsed):
            with mock.patch.object(module, "find_story_item", return_value={"ok": False, "itemId": "", "draftIssueId": ""}):
                with mock.patch.object(module, "_create_draft_item", return_value={"itemId": "PVTI_9", "draftIssueId": "DI_9"}):
                    with mock.patch.object(module, "_resolve_user_id", return_value=""):
                        with mock.patch.object(module, "_set_item_field", side_effect=record_field):
                            result = module.sync_story_from_markdown({
                                "projectId": "PVT_1",
                                "filePath": "/tmp/HU-01.md",
                                "schema": full_schema(),
                            })
        fm = result["fieldMapping"]
        self.assertEqual(fm["Status"], "Sprint activo")
        self.assertEqual(fm["Prioridad"], "Alta")
        self.assertEqual(fm["Talla"], "M")
        self.assertEqual(fm["Horas"], 4.0)
        self.assertEqual(fm["Sprint"], "Sprint 1")
        self.assertEqual(fm["Responsable"], "Ana Garcia (ana@example.com)")
        # Cada campo se fija con su propio fieldId.
        field_ids = {c[0] for c in calls}
        self.assertEqual(field_ids, {"F_status", "F_prio", "F_talla", "F_horas", "F_sprint", "F_resp"})
        by_field = {c[0]: c[1] for c in calls}
        self.assertEqual(by_field["F_resp"], {"text": "Ana Garcia (ana@example.com)"})
        self.assertEqual(by_field["F_horas"], {"number": 4.0})
        self.assertEqual(result["assignment"]["status"], "unresolved")

    def test_sync_story_resolves_real_assignee_when_github_login_available(self):
        module = self.module
        parsed = {
            "ok": True, "filePath": "/tmp/HU-01.md", "markdown": "# HU-01\n\nDetalle",
            "storyId": "HU-01", "title": "Login", "fullTitle": "HU-01 · Login",
            "priority": "", "estimation": "", "size": "", "hours": None,
            "sprint": "", "state": "", "assignedRaw": "Ana (ana@example.com)",
            "assignedEmail": "ana@example.com", "dependenciesText": "", "dependencyStoryIds": [],
        }
        with mock.patch.object(module, "parse_story_markdown", return_value=parsed):
            with mock.patch.object(module, "find_story_item", return_value={"ok": False, "itemId": "", "draftIssueId": ""}):
                with mock.patch.object(module, "_resolve_user_id", return_value="MDQ6VXNlcjE="):
                    with mock.patch.object(module, "_create_draft_item", return_value={"itemId": "PVTI_9", "draftIssueId": "DI_9"}) as create:
                        with mock.patch.object(module, "_apply_story_fields", return_value={}):
                            result = module.sync_story_from_markdown({
                                "projectId": "PVT_1", "filePath": "/tmp/HU-01.md", "schema": full_schema(),
                                "assignedGithub": "ana-gh",
                            })
        self.assertEqual(result["assignment"]["status"], "resolved")
        self.assertTrue(result["assignment"]["assigneeApplied"])
        # El assignee real viaja en la creacion del draft item.
        self.assertEqual(create.call_args.args[3], ["MDQ6VXNlcjE="])

    def test_sync_story_updates_existing_and_reports_unresolved(self):
        module = self.module
        parsed = {
            "ok": True, "filePath": "/tmp/HU-03.md", "markdown": "# HU-03\n\nDetalle",
            "storyId": "HU-03", "title": "Admin", "fullTitle": "HU-03 · Admin",
            "priority": "Alta", "estimation": "S", "size": "S", "hours": 2.0,
            "sprint": "", "state": "", "assignedRaw": "nadie@example.com",
            "assignedEmail": "nadie@example.com", "dependenciesText": "", "dependencyStoryIds": [],
        }
        with mock.patch.object(module, "parse_story_markdown", return_value=parsed):
            with mock.patch.object(module, "find_story_item", return_value={"ok": True, "itemId": "PVTI_3", "draftIssueId": "DI_3"}):
                with mock.patch.object(module, "_update_draft_item", return_value={"id": "DI_3"}) as update:
                    with mock.patch.object(module, "_resolve_user_id", return_value=""):
                        with mock.patch.object(module, "_apply_story_fields", return_value={"Status": "Backlog"}):
                            result = module.sync_story_from_markdown({
                                "projectId": "PVT_1", "filePath": "/tmp/HU-03.md", "schema": full_schema(),
                            })
        self.assertFalse(result["created"])
        self.assertEqual(result["status"], "Backlog")
        self.assertEqual(result["assignment"]["status"], "unresolved")
        update.assert_called_once()

    def test_sync_vision_creates_hu00_item(self):
        module = self.module
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "vision.md")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("# Vision\n\nContenido amplio")
            with mock.patch.object(module, "find_story_item", return_value={"ok": False, "itemId": "", "draftIssueId": ""}):
                with mock.patch.object(module, "_create_draft_item", return_value={"itemId": "PVTI_0", "draftIssueId": "DI_0"}) as create:
                    result = module.sync_vision_from_markdown({"projectId": "PVT_1", "filePath": path})
        self.assertTrue(result["created"])
        self.assertEqual(result["title"], "HU-00 · Vision")
        create.assert_called_once()

    def test_ensure_sprint_option_appends_to_existing_field(self):
        module = self.module
        schema = full_schema()
        updated = {"updateProjectV2Field": {"projectV2Field": {
            "id": "F_sprint", "name": "Sprint",
            "options": [
                {"id": "sp_1", "name": "Sprint 1", "color": "BLUE", "description": ""},
                {"id": "sp_2", "name": "Sprint 2", "color": "BLUE", "description": ""},
            ],
        }}}
        with mock.patch.object(module, "_graphql", return_value=updated) as graphql:
            option_id = module._ensure_sprint_option("PVT_1", schema, "Sprint 2")
        self.assertEqual(option_id, "sp_2")
        graphql.assert_called_once()

    # -- folder batch + report ---------------------------------------------

    def test_sync_stories_from_folder_report_reflects_field_mapping(self):
        module = self.module
        with tempfile.TemporaryDirectory() as tmpdir:
            stories_dir = os.path.join(tmpdir, "historias")
            os.makedirs(stories_dir, exist_ok=True)
            with open(os.path.join(tmpdir, "vision.md"), "w", encoding="utf-8") as handle:
                handle.write("# Vision\n")
            for filename in ("HU-01-login.md", "HU-02-logout.md"):
                with open(os.path.join(stories_dir, filename), "w", encoding="utf-8") as handle:
                    handle.write("# Stub\n")

            def fake_parse(args):
                sid = "HU-01" if "HU-01" in args["filePath"] else "HU-02"
                return {"storyId": sid,
                        "assignedEmail": "ana@example.com" if sid == "HU-01" else "nadie@example.com",
                        "dependencyStoryIds": []}

            def fake_sync(args):
                sid = "HU-01" if "HU-01" in args["filePath"] else "HU-02"
                resolved = sid == "HU-01"
                return {
                    "storyId": sid, "itemId": f"item-{sid}", "created": True, "status": "Backlog",
                    "fieldMapping": {"Status": "Backlog", "Prioridad": "Alta", "Talla": "M",
                                     "Horas": 4.0, "Sprint": "Sprint 1", "Responsable": "Ana (ana@example.com)"},
                    "assignment": {"status": "resolved" if resolved else "unresolved",
                                   "responsable": "Ana (ana@example.com)" if resolved else "nadie@example.com",
                                   "email": "ana@example.com" if resolved else "nadie@example.com"},
                }

            with mock.patch.object(module, "_resolve_project_schema", return_value=full_schema()):
                with mock.patch.object(module, "_load_team_github_map", return_value={"ana@example.com": "ana-gh"}):
                    with mock.patch.object(module, "sync_vision_from_markdown", return_value={"ok": True, "itemId": "PVTI_0", "created": True}):
                        with mock.patch.object(module, "parse_story_markdown", side_effect=fake_parse):
                            with mock.patch.object(module, "sync_story_from_markdown", side_effect=fake_sync):
                                result = module.sync_stories_from_folder({
                                    "projectId": "PVT_1",
                                    "storiesDir": stories_dir,
                                    "visionFilePath": os.path.join(tmpdir, "vision.md"),
                                    "cwd": tmpdir,
                                })
            self.assertTrue(result["ok"])
            self.assertEqual(result["storyCount"], 2)
            self.assertEqual(len(result["unresolvedAssignments"]), 1)
            self.assertEqual(result["unresolvedAssignments"][0]["storyId"], "HU-02")
            with open(result["reportPath"], encoding="utf-8") as handle:
                report = handle.read()
            self.assertIn("Provider: github", report)
            self.assertIn("Mapeo por HU (campo a campo)", report)
            self.assertIn("Prioridad", report)
            self.assertIn("Responsable", report)
            self.assertIn("no admiten adjuntos", report)
            self.assertIn("Unresolved Assignments", report)

    # -- team CSV github map ------------------------------------------------

    def test_load_team_github_map_reads_optional_github_column(self):
        module = self.module
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "equipo.csv")
            with open(csv_path, "w", encoding="utf-8") as handle:
                handle.write(
                    "nombre,email,rol,categoria,dedicacion,usa_agente_ia,github\n"
                    "Ana,ana@example.com,TL,senior,60,si,@ana-gh\n"
                )
            mapping = module._load_team_github_map(tmpdir)
        self.assertEqual(mapping.get("ana@example.com"), "ana-gh")

    def test_load_team_github_map_empty_without_github_column(self):
        module = self.module
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "equipo.csv")
            with open(csv_path, "w", encoding="utf-8") as handle:
                handle.write(
                    "nombre,email,rol,categoria,dedicacion,usa_agente_ia\n"
                    "Ana,ana@example.com,TL,senior,60,si\n"
                )
            mapping = module._load_team_github_map(tmpdir)
        self.assertEqual(mapping, {})

    # -- compose body / DoD -------------------------------------------------

    def test_compose_body_appends_dod_task_list(self):
        module = self.module
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_dir = os.path.join(tmpdir, "docs")
            os.makedirs(docs_dir)
            with open(os.path.join(docs_dir, "dod.md"), "w", encoding="utf-8") as handle:
                handle.write("# DoD\n\n- Tests en verde\n- Documentado\n")
            body = module._compose_body("# HU-01\n\nDetalle", tmpdir)
        self.assertIn("## Definition of Done", body)
        self.assertIn("- [ ] Tests en verde", body)
        self.assertIn("- [ ] Documentado", body)

    # -- graphql routing: gh primary, urllib fallback ----------------------

    def test_graphql_uses_gh_when_available(self):
        module = self.module
        fake_proc = mock.Mock(returncode=0, stdout=json.dumps({"data": {"viewer": {"id": "U_1"}}}), stderr="")
        with mock.patch.object(module, "_gh_available", return_value=True):
            with mock.patch.object(module.subprocess, "run", return_value=fake_proc) as run:
                data = module._graphql("query { viewer { id } }", {})
        self.assertEqual(data["viewer"]["id"], "U_1")
        args = run.call_args[0][0]
        self.assertEqual(args[:3], ["gh", "api", "graphql"])

    def test_graphql_falls_back_to_urllib_token_when_no_gh(self):
        module = self.module
        with mock.patch.object(module, "_gh_available", return_value=False):
            with mock.patch.object(module, "_graphql_via_gh") as via_gh:
                with mock.patch.object(module, "_graphql_via_urllib", return_value={"data": {"viewer": {"id": "U_2"}}}) as via_urllib:
                    data = module._graphql("query { viewer { id } }", {})
        via_gh.assert_not_called()
        via_urllib.assert_called_once()
        self.assertEqual(data["viewer"]["id"], "U_2")

    def test_graphql_via_urllib_requires_token(self):
        module = self.module
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                module._graphql_via_urllib("query", {})

    def test_graphql_raises_on_errors(self):
        module = self.module
        with mock.patch.object(module, "_gh_available", return_value=True):
            with mock.patch.object(module, "_graphql_via_gh", return_value={"errors": [{"message": "boom"}]}):
                with self.assertRaises(RuntimeError):
                    module._graphql("query", {})

    # -- set story status ---------------------------------------------------

    def test_set_story_status_resolves_option_and_patches(self):
        module = self.module
        with mock.patch.object(module, "_set_item_field") as set_field:
            result = module.set_story_status({
                "projectId": "PVT_1",
                "itemId": "PVTI_1",
                "status": "Sprint activo",
                "schema": full_schema(),
            })
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "Sprint activo")
        set_field.assert_called_once()
        args = set_field.call_args.args
        self.assertEqual(args[3], {"singleSelectOptionId": "st_sprint"})

    # -- save project targets ----------------------------------------------

    def test_save_project_targets_updates_env(self):
        module = self.module
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                with mock.patch.dict(os.environ, {}, clear=True):
                    result = module.save_project_targets({
                        "projectNumber": 7,
                        "projectId": "PVT_1",
                        "projectOwner": "octocat",
                        "projectUrl": "https://github.com/users/octocat/projects/7",
                    })
                    with open(os.path.join(tmpdir, ".env"), encoding="utf-8") as handle:
                        content = handle.read()
            finally:
                os.chdir(cwd)
        self.assertTrue(result["saved"])
        self.assertIn("GITHUB_PROJECT_NUMBER=7", content)
        self.assertIn("GITHUB_PROJECT_ID=PVT_1", content)
        self.assertIn("GITHUB_PROJECT_OWNER=octocat", content)

    def test_loads_env_from_project_file(self):
        module = self.module
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = os.path.join(tmpdir, ".env")
            with open(env_path, "w", encoding="utf-8") as handle:
                handle.write('GITHUB_TOKEN="ghp_token_value"\nGITHUB_PROJECT_ID=PVT_1\n')
            cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                with mock.patch.dict(os.environ, {}, clear=True):
                    module._load_project_env()
                    self.assertEqual(os.environ["GITHUB_TOKEN"], "ghp_token_value")
                    self.assertEqual(os.environ["GITHUB_PROJECT_ID"], "PVT_1")
            finally:
                os.chdir(cwd)


if __name__ == "__main__":
    unittest.main()
