import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock


PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..")
FALLBACK_PATH = os.path.join(PLUGIN_ROOT, "servers", "notion-fallback.py")


def load_module():
    spec = importlib.util.spec_from_file_location("notion_fallback", FALLBACK_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestNotionFallback(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_env_status_masks_token(self):
        module = self.module
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.dict(os.environ, {
            "NOTION_TOKEN": "ntn_super_secret_token",
            "NOTION_PARENT_PAGE_ID": "325b0a8fa25480599971f0c19b43e43c",
        }, clear=False):
            with mock.patch.object(sys, "argv", ["notion-fallback.py", "env-status", "--pretty"]):
                with mock.patch("sys.stdout", stdout), mock.patch("sys.stderr", stderr), mock.patch("sys.stdin", io.StringIO("")):
                    exit_code = module.main()

        self.assertEqual(exit_code, 0, stderr.getvalue())
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["hasNotionToken"])
        self.assertTrue(payload["hasParentPageId"])
        self.assertTrue(payload["tokenMasked"].startswith("****"))

    def test_verify_credentials_uses_users_me(self):
        module = self.module
        with mock.patch.object(module, "_request_json", return_value={
            "id": "user-123",
            "type": "bot",
            "name": "PSPO Agent",
            "bot": {"workspace_name": "Workspace Demo"},
        }) as request:
            payload = module.verify_credentials({})
        request.assert_called_once_with("GET", "/v1/users/me")
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["botUserId"], "user-123")
        self.assertEqual(payload["workspaceName"], "Workspace Demo")

    def test_help_lists_supported_tools_and_onboarding_sequence(self):
        module = self.module
        payload = module.help_info({})
        self.assertTrue(payload["ok"])
        self.assertIn("setup-targets", payload["supportedTools"])
        self.assertIn("parse-story-markdown", payload["supportedTools"])
        self.assertIn("sync-story-from-markdown", payload["supportedTools"])
        self.assertIn("list-tools", payload["supportedTools"])
        self.assertIn("create-project", payload["supportedTools"])
        self.assertIn("save-project-targets", payload["supportedTools"])
        self.assertTrue(payload["onboardingSequence"][0].endswith("env-status --pretty"))
        self.assertTrue(any("setup-targets --pretty" in step for step in payload["onboardingSequence"]))
        self.assertEqual(payload["publishSequence"][0], "sync-vision-from-markdown")

    def test_parse_story_markdown_extracts_metadata_sections_and_dependencies(self):
        module = self.module
        markdown = """# HU-02 · Cerrar sesion

| Campo | Valor |
| --- | --- |
| ID | HU-02 |
| Prioridad | Media |
| Estimacion | 1h |
| Sprint | Sprint 1 |
| Asignado a | reg@00b.tech |
| Dependencias | HU-01, HU-03 |

## Resumen

Como persona usuaria quiero cerrar sesion para salir de la zona privada.
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "HU-02-cerrar-sesion.md")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(markdown)
            payload = module.parse_story_markdown({"filePath": path})
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["storyId"], "HU-02")
        self.assertEqual(payload["title"], "Cerrar sesion")
        self.assertEqual(payload["fullTitle"], "HU-02 · Cerrar sesion")
        self.assertEqual(payload["priority"], "Media")
        self.assertEqual(payload["estimation"], "1h")
        self.assertEqual(payload["assignedEmail"], "reg@00b.tech")
        self.assertEqual(payload["dependencyStoryIds"], ["HU-01", "HU-03"])
        self.assertIn("cerrar sesion", payload["summary"].lower())

    def test_setup_targets_orchestrates_create_and_save(self):
        module = self.module
        with mock.patch.object(module, "create_project", return_value={
            "projectPageId": "325b0a8f-a254-811d-9d61-cd6286cd22f0",
            "visionPageId": "325b0a8f-a254-816d-9b4a-cc6465ac4ca4",
            "databaseId": "325b0a8f-a254-8035-a28f-f05853061f74",
            "dataSourceId": "325b0a8f-a254-80bb-acca-000c5b54c077",
            "projectUrl": "https://notion.so/project",
            "visionUrl": "https://notion.so/vision",
        }) as create_project:
            with mock.patch.object(module, "save_project_targets", return_value={
                "envPath": "/tmp/.env",
                "keys": ["NOTION_DATABASE_ID", "NOTION_PROJECT_PAGE_ID"],
            }) as save_targets:
                payload = module.setup_targets({
                    "parentPageId": "325b0a8fa25480599971f0c19b43e43c",
                    "projectName": "Login MVP",
                })

        create_project.assert_called_once()
        save_targets.assert_called_once()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["projectPageId"], "325b0a8f-a254-811d-9d61-cd6286cd22f0")
        self.assertEqual(payload["visionPageId"], "325b0a8f-a254-816d-9b4a-cc6465ac4ca4")
        self.assertEqual(payload["databaseId"], "325b0a8f-a254-8035-a28f-f05853061f74")

    def test_create_project_orchestrates_root_vision_and_database(self):
        module = self.module
        responses = [
            {"id": "325b0a8f-a254-8059-9971-f0c19b43e111", "url": "https://notion.so/page-root"},
            {"id": "325b0a8f-a254-8059-9971-f0c19b43e112", "url": "https://notion.so/page-vision"},
            {"id": "325b0a8f-a254-8059-9971-f0c19b43e113", "data_sources": [{"id": "325b0a8f-a254-8059-9971-f0c19b43e114"}]},
        ]
        with mock.patch.object(module, "_request_json", side_effect=responses) as request:
            with mock.patch.object(module, "ensure_dependency_relations", return_value={"ok": True}) as ensure_relations:
                result = module.create_project({
                    "parentPageId": "325b0a8fa25480599971f0c19b43e43c",
                    "projectName": "Login MVP",
                    "visionMarkdown": "# Vision\n\nProyecto de login.",
                })

        self.assertTrue(result["ok"])
        self.assertEqual(result["projectPageId"], "325b0a8f-a254-8059-9971-f0c19b43e111")
        self.assertEqual(result["visionPageId"], "325b0a8f-a254-8059-9971-f0c19b43e112")
        self.assertEqual(result["databaseId"], "325b0a8f-a254-8059-9971-f0c19b43e113")
        self.assertEqual(result["dataSourceId"], "325b0a8f-a254-8059-9971-f0c19b43e114")
        self.assertEqual(request.call_count, 3)
        ensure_relations.assert_called_once_with({"dataSourceId": "325b0a8f-a254-8059-9971-f0c19b43e114"})

    def test_create_project_uses_default_name_when_project_name_is_missing(self):
        module = self.module
        responses = [
            {"id": "325b0a8f-a254-8059-9971-f0c19b43e111", "url": "https://notion.so/page-root"},
            {"id": "325b0a8f-a254-8059-9971-f0c19b43e112", "url": "https://notion.so/page-vision"},
            {"id": "325b0a8f-a254-8059-9971-f0c19b43e113", "data_sources": [{"id": "325b0a8f-a254-8059-9971-f0c19b43e114"}]},
        ]
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory(prefix="pspo-notion-onb5-") as tmpdir:
            try:
                os.chdir(tmpdir)
                with mock.patch.object(module, "_request_json", side_effect=responses) as request:
                    with mock.patch.object(module, "ensure_dependency_relations", return_value={"ok": True}):
                        result = module.create_project({
                            "parentPageId": "325b0a8fa25480599971f0c19b43e43c",
                        })
            finally:
                os.chdir(cwd)

        self.assertTrue(result["ok"])
        first_payload = request.call_args_list[0].args[2]
        title = first_payload["properties"]["title"]["title"][0]["text"]["content"]
        self.assertTrue(title.startswith("PSPO · "))

    def test_create_story_page_uses_data_source_parent(self):
        module = self.module
        with mock.patch.object(module, "_request_json", return_value={"id": "story-page"}) as request:
            result = module.create_story_page({
                "dataSourceId": "325b0a8fa2548035a28ff05853061f74",
                "title": "HU-01: Login",
                "storyId": "HU-01",
                "summary": "Acceso a zona privada",
                "status": "Backlog",
                "priority": "Alta",
                "estimateHours": 2,
                "markdown": "# HU-01\n\nComo usuario...",
                "assignedUserId": "e37e8ced-e897-41ff-9f50-78797cefc767",
            })
        self.assertEqual(result["id"], "story-page")
        args = request.call_args[0]
        self.assertEqual(args[0], "POST")
        self.assertEqual(args[1], "/v1/pages")
        payload = args[2]
        self.assertEqual(payload["parent"]["type"], "data_source_id")
        self.assertIn("children", payload)
        self.assertEqual(payload["properties"]["Asignado_a"]["people"][0]["id"], "e37e8ced-e897-41ff-9f50-78797cefc767")

    def test_create_story_page_resolves_assignee_by_email(self):
        module = self.module
        with mock.patch.object(module, "resolve_user_by_email", return_value={
            "ok": True,
            "matches": [{"id": "e37e8ced-e897-41ff-9f50-78797cefc767"}],
        }):
            with mock.patch.object(module, "_request_json", return_value={"id": "story-page"}) as request:
                module.create_story_page({
                    "dataSourceId": "325b0a8fa2548035a28ff05853061f74",
                    "title": "HU-01: Login",
                    "assignedEmail": "reg@00b.tech",
                })
        payload = request.call_args[0][2]
        self.assertEqual(payload["properties"]["Asignado_a"]["people"][0]["id"], "e37e8ced-e897-41ff-9f50-78797cefc767")

    def test_create_story_page_accepts_runtime_aliases(self):
        module = self.module
        with mock.patch.object(module, "retrieve_database", return_value={
            "id": "2dc7d4a3-f5c4-42f6-8bd1-7d704c2f0edc",
            "data_sources": [{"id": "5a40701b-4e3f-442b-8bd3-a1f7aacae918"}],
        }):
            with mock.patch.object(module, "_request_json", return_value={"id": "story-page"}) as request:
                module.create_story_page({
                    "databaseId": "2dc7d4a3-f5c4-42f6-8bd1-7d704c2f0edc",
                    "title": "HU-02: Logout",
                    "storyId": "HU-02",
                    "estimation": "1h",
                    "assignedTo": "e37e8ced-e897-41ff-9f50-78797cefc767",
                })
        payload = request.call_args[0][2]
        self.assertEqual(payload["parent"]["data_source_id"], "5a40701b-4e3f-442b-8bd3-a1f7aacae918")
        self.assertEqual(payload["properties"]["Estimacion_h"]["number"], 1.0)
        self.assertEqual(payload["properties"]["Asignado_a"]["people"][0]["id"], "e37e8ced-e897-41ff-9f50-78797cefc767")

    def test_resolve_data_source_id_falls_back_to_env_database_id(self):
        module = self.module
        with mock.patch.dict(os.environ, {
            "NOTION_DATABASE_ID": "2dc7d4a3-f5c4-42f6-8bd1-7d704c2f0edc",
        }, clear=False):
            with mock.patch.object(module, "retrieve_database", return_value={
                "id": "2dc7d4a3-f5c4-42f6-8bd1-7d704c2f0edc",
                "data_sources": [{"id": "5a40701b-4e3f-442b-8bd3-a1f7aacae918"}],
            }):
                result = module._resolve_data_source_id({})
        self.assertEqual(result, "5a40701b-4e3f-442b-8bd3-a1f7aacae918")

    def test_ensure_dependency_relations_creates_dual_relation_when_missing(self):
        module = self.module
        with mock.patch.object(module, "retrieve_data_source", return_value={
            "id": "5a40701b-4e3f-442b-8bd3-a1f7aacae918",
            "properties": {
                "Titulo": {"type": "title"},
            },
        }):
            with mock.patch.object(module, "update_data_source", return_value={"ok": True}) as update_data_source:
                result = module.ensure_dependency_relations({
                    "dataSourceId": "5a40701b4e3f442b8bd3a1f7aacae918",
                })
        self.assertTrue(result["ok"])
        self.assertTrue(result["created"])
        payload = update_data_source.call_args[0][0]["properties"]
        self.assertIn("Bloqueada_por", payload)
        self.assertEqual(
            payload["Bloqueada_por"]["relation"]["dual_property"]["synced_property_name"],
            "Bloquea",
        )

    def test_find_story_page_queries_data_source_by_story_id(self):
        module = self.module
        with mock.patch.object(module, "_request_json", return_value={
            "results": [{"id": "story-page-1"}],
        }) as request:
            result = module.find_story_page({
                "dataSourceId": "5a40701b4e3f442b8bd3a1f7aacae918",
                "storyId": "HU-01",
            })
        self.assertTrue(result["ok"])
        self.assertEqual(result["page"]["id"], "story-page-1")
        args = request.call_args[0]
        self.assertEqual(args[0], "POST")
        self.assertIn("/query", args[1])
        self.assertEqual(args[2]["filter"]["property"], "ID")

    def test_update_story_page_uses_patch_and_relation_property(self):
        module = self.module
        with mock.patch.object(module, "_request_json", return_value={"id": "story-page"}) as request:
            result = module.update_story_page({
                "pageId": "325b0a8fa25481e4a1e5d029abca0857",
                "title": "HU-02: Logout",
                "storyId": "HU-02",
                "dependencyPageIds": ["325b0a8fa25481da83aacd772d9b160d"],
                "assignedTo": "e37e8ced-e897-41ff-9f50-78797cefc767",
                "estimation": "1h",
            })
        self.assertTrue(result["ok"])
        self.assertEqual(result["page"]["id"], "story-page")
        args = request.call_args[0]
        self.assertEqual(args[0], "PATCH")
        self.assertIn("/v1/pages/", args[1])
        payload = args[2]
        self.assertEqual(payload["properties"]["Estimacion_h"]["number"], 1.0)
        self.assertEqual(payload["properties"]["Asignado_a"]["people"][0]["id"], "e37e8ced-e897-41ff-9f50-78797cefc767")
        self.assertEqual(payload["properties"]["Bloqueada_por"]["relation"][0]["id"], "325b0a8f-a254-81da-83aa-cd772d9b160d")

    def test_update_story_page_replaces_body_when_markdown_is_present(self):
        module = self.module
        with mock.patch.object(module, "_request_json", return_value={"id": "story-page"}) as request:
            with mock.patch.object(module, "_replace_page_body", return_value={"ok": True, "appendedBlockCount": 3}) as replace_body:
                result = module.update_story_page({
                    "pageId": "325b0a8fa25481e4a1e5d029abca0857",
                    "title": "HU-02: Logout",
                    "markdown": "# HU-02\n\nDetalle largo",
                })
        self.assertTrue(result["ok"])
        replace_body.assert_called_once()
        self.assertEqual(result["bodySync"]["appendedBlockCount"], 3)
        self.assertEqual(request.call_count, 1)

    def test_sync_story_from_markdown_creates_page_and_attaches_markdown(self):
        module = self.module
        parsed = {
            "ok": True,
            "filePath": "/tmp/HU-01-login.md",
            "markdown": "# HU-01\n\nDetalle",
            "storyId": "HU-01",
            "title": "Acceso",
            "fullTitle": "HU-01 · Acceso",
            "summary": "Resumen",
            "priority": "Alta",
            "estimation": "2h",
            "sprint": "Sprint 1",
            "assignedEmail": "reg@00b.tech",
            "dependenciesText": "Ninguna",
            "dependencyStoryIds": [],
        }
        with mock.patch.object(module, "parse_story_markdown", return_value=parsed):
            with mock.patch.object(module, "find_story_page", return_value={"ok": False, "page": None}) as find_story:
                with mock.patch.object(module, "create_story_page", return_value={"id": "325b0a8f-a254-81e4-a1e5-d029abca0857"}) as create_story:
                    with mock.patch.object(module, "upload_and_attach_markdown", return_value={"ok": True}) as attach_markdown:
                        with mock.patch.object(module, "retrieve_page", return_value={
                            "properties": {
                                "Asignado_a": {"people": [{"id": "e37e8ced-e897-41ff-9f50-78797cefc767"}]},
                                "Documento_MD": {"files": [{"name": "HU-01-login.md"}]},
                            }
                        }):
                            result = module.sync_story_from_markdown({
                                "dataSourceId": "5a40701b4e3f442b8bd3a1f7aacae918",
                                "filePath": "/tmp/HU-01-login.md",
                            })
        self.assertTrue(result["ok"])
        self.assertTrue(result["created"])
        self.assertEqual(result["pageId"], "325b0a8f-a254-81e4-a1e5-d029abca0857")
        find_story.assert_called_once()
        create_story.assert_called_once()
        create_payload = create_story.call_args[0][0]
        self.assertEqual(create_payload["title"], "HU-01 · Acceso")
        self.assertEqual(create_payload["status"], "Backlog")
        attach_markdown.assert_called_once()

    def test_sync_story_from_markdown_reports_unresolved_assignment_and_skipped_attachment(self):
        module = self.module
        parsed = {
            "ok": True,
            "filePath": "/tmp/HU-03-admin.md",
            "markdown": "# HU-03\n\nDetalle",
            "storyId": "HU-03",
            "title": "Admin",
            "fullTitle": "HU-03 · Admin",
            "summary": "Resumen admin",
            "priority": "Alta",
            "estimation": "2h",
            "sprint": "Sprint 2",
            "assignedEmail": "nadie@example.com",
            "dependenciesText": "",
            "dependencyStoryIds": [],
        }
        with mock.patch.object(module, "parse_story_markdown", return_value=parsed):
            with mock.patch.object(module, "find_story_page", return_value={"ok": True, "page": {"id": "page-123"}}):
                with mock.patch.object(module, "update_story_page", return_value={"ok": True, "page": {"id": "page-123"}}):
                    with mock.patch.object(module, "upload_and_attach_markdown", return_value={"ok": True, "skipped": True, "reason": "already_attached"}):
                        with mock.patch.object(module, "retrieve_page", return_value={
                            "properties": {
                                "Asignado_a": {"people": []},
                                "Documento_MD": {"files": [{"name": "HU-03-admin.md"}]},
                            }
                        }):
                            result = module.sync_story_from_markdown({
                                "dataSourceId": "5a40701b4e3f442b8bd3a1f7aacae918",
                                "filePath": "/tmp/HU-03-admin.md",
                            })
        self.assertEqual(result["assignment"]["status"], "unresolved")
        self.assertTrue(result["attachment"]["skipped"])
        self.assertTrue(result["verification"]["hasMarkdownAttachment"])

    def test_sync_story_from_markdown_updates_existing_page(self):
        module = self.module
        parsed = {
            "ok": True,
            "filePath": "/tmp/HU-02-logout.md",
            "markdown": "# HU-02\n\nDetalle",
            "storyId": "HU-02",
            "title": "Cerrar sesion",
            "fullTitle": "HU-02 · Cerrar sesion",
            "summary": "Resumen logout",
            "priority": "Media",
            "estimation": "1h",
            "sprint": "Sprint 1",
            "assignedEmail": "reg@00b.tech",
            "dependenciesText": "HU-01",
            "dependencyStoryIds": ["HU-01"],
        }
        with mock.patch.object(module, "parse_story_markdown", return_value=parsed):
            with mock.patch.object(module, "find_story_page", return_value={"ok": True, "page": {"id": "325b0a8f-a254-81e4-a1e5-d029abca0857"}}):
                with mock.patch.object(module, "update_story_page", return_value={"ok": True, "page": {"id": "325b0a8f-a254-81e4-a1e5-d029abca0857"}}) as update_story:
                    with mock.patch.object(module, "upload_and_attach_markdown", return_value={"ok": True}):
                        with mock.patch.object(module, "retrieve_page", return_value={
                            "properties": {
                                "Asignado_a": {"people": [{"id": "e37e8ced-e897-41ff-9f50-78797cefc767"}]},
                                "Documento_MD": {"files": [{"name": "HU-02-logout.md"}]},
                            }
                        }):
                            result = module.sync_story_from_markdown({
                                "dataSourceId": "5a40701b4e3f442b8bd3a1f7aacae918",
                                "filePath": "/tmp/HU-02-logout.md",
                                "status": "Sprint activo",
                            })
        self.assertTrue(result["ok"])
        self.assertFalse(result["created"])
        self.assertEqual(result["pageId"], "325b0a8f-a254-81e4-a1e5-d029abca0857")
        update_payload = update_story.call_args[0][0]
        self.assertEqual(update_payload["pageId"], "325b0a8f-a254-81e4-a1e5-d029abca0857")
        self.assertEqual(update_payload["status"], "Sprint activo")
        self.assertEqual(update_payload["markdown"], "# HU-02\n\nDetalle")

    def test_sync_story_dependencies_from_markdown_uses_story_ids_from_file(self):
        module = self.module
        parsed = {
            "ok": True,
            "filePath": "/tmp/HU-02-logout.md",
            "markdown": "# HU-02\n\nDetalle",
            "storyId": "HU-02",
            "title": "Cerrar sesion",
            "fullTitle": "HU-02 · Cerrar sesion",
            "summary": "Resumen logout",
            "priority": "Media",
            "estimation": "1h",
            "sprint": "Sprint 1",
            "assignedEmail": "reg@00b.tech",
            "dependenciesText": "HU-01",
            "dependencyStoryIds": ["HU-01"],
        }
        with mock.patch.object(module, "parse_story_markdown", return_value=parsed):
            with mock.patch.object(module, "find_story_page", return_value={"ok": True, "page": {"id": "page-123"}}):
                with mock.patch.object(module, "set_story_dependencies", return_value={
                    "ok": True,
                    "resolvedDependencyPageIds": ["page-001"],
                    "unresolvedDependencyStoryIds": [],
                }) as set_deps:
                    result = module.sync_story_dependencies_from_markdown({
                        "dataSourceId": "5a40701b4e3f442b8bd3a1f7aacae918",
                        "filePath": "/tmp/HU-02-logout.md",
                    })
        self.assertTrue(result["ok"])
        self.assertEqual(result["pageId"], "page-123")
        self.assertEqual(result["resolvedDependencyPageIds"], ["page-001"])
        set_payload = set_deps.call_args[0][0]
        self.assertEqual(set_payload["dependencyStoryIds"], ["HU-01"])

    def test_sync_vision_from_markdown_updates_existing_vision_page(self):
        module = self.module
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "vision.md")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("# Vision\n\nContenido amplio")
            with mock.patch.dict(os.environ, {
                "NOTION_VISION_PAGE_ID": "325b0a8fa254816d9b4acc6465ac4ca4",
            }, clear=False):
                with mock.patch.object(module, "_update_page_title", return_value={"id": "vision-page"}) as update_title:
                    with mock.patch.object(module, "_replace_page_body", return_value={"ok": True, "appendedBlockCount": 2}) as replace_body:
                        result = module.sync_vision_from_markdown({"filePath": path})
        self.assertTrue(result["ok"])
        self.assertFalse(result["created"])
        update_title.assert_called_once()
        replace_body.assert_called_once()
        self.assertEqual(result["pageId"], "325b0a8f-a254-816d-9b4a-cc6465ac4ca4")

    def test_sync_vision_from_markdown_creates_page_when_missing(self):
        module = self.module
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "vision.md")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("# Vision\n\nContenido amplio")
            with mock.patch.dict(os.environ, {
                "NOTION_PROJECT_PAGE_ID": "325b0a8fa254811d9d61cd6286cd22f0",
                "NOTION_PARENT_PAGE_ID": "325b0a8fa25480599971f0c19b43e43c",
                "NOTION_DATABASE_ID": "2dc7d4a3f5c442f68bd17d704c2f0edc",
                "NOTION_VISION_PAGE_ID": "",
            }, clear=False):
                with mock.patch.object(module, "_create_page", return_value={"id": "325b0a8f-a254-816d-9b4a-cc6465ac4ca4", "url": "https://notion.so/vision"}) as create_page:
                    with mock.patch.object(module, "save_project_targets", return_value={"saved": True}) as save_targets:
                        result = module.sync_vision_from_markdown({"filePath": path})
        self.assertTrue(result["ok"])
        self.assertTrue(result["created"])
        create_page.assert_called_once()
        save_targets.assert_called_once()
        self.assertEqual(result["pageId"], "325b0a8f-a254-816d-9b4a-cc6465ac4ca4")

    def test_sync_stories_from_folder_runs_two_passes_and_vision(self):
        module = self.module
        with tempfile.TemporaryDirectory() as tmpdir:
            stories_dir = os.path.join(tmpdir, "historias")
            os.makedirs(stories_dir, exist_ok=True)
            with open(os.path.join(tmpdir, "vision.md"), "w", encoding="utf-8") as handle:
                handle.write("# Vision\n")
            for filename in ("HU-01-login.md", "HU-02-logout.md"):
                with open(os.path.join(stories_dir, filename), "w", encoding="utf-8") as handle:
                    handle.write("# Stub\n")
            with mock.patch.object(module, "sync_vision_from_markdown", return_value={"ok": True, "pageId": "vision-page"}) as sync_vision:
                with mock.patch.object(module, "sync_story_from_markdown", side_effect=[
                    {
                        "storyId": "HU-01", "pageId": "page-01", "created": True,
                        "assignment": {"status": "resolved", "email": "reg@00b.tech"},
                        "attachment": {"skipped": False},
                    },
                    {
                        "storyId": "HU-02", "pageId": "page-02", "created": False,
                        "assignment": {"status": "unresolved", "email": "missing@example.com"},
                        "attachment": {"skipped": True, "reason": "already_attached"},
                    },
                ]) as sync_story:
                    with mock.patch.object(module, "sync_story_dependencies_from_markdown", side_effect=[
                        {"storyId": "HU-01", "pageId": "page-01", "resolvedDependencyPageIds": [], "unresolvedDependencyStoryIds": []},
                        {"storyId": "HU-02", "pageId": "page-02", "resolvedDependencyPageIds": ["page-01"], "unresolvedDependencyStoryIds": []},
                    ]) as sync_deps:
                        result = module.sync_stories_from_folder({
                            "storiesDir": stories_dir,
                            "visionFilePath": os.path.join(tmpdir, "vision.md"),
                            "dataSourceId": "5a40701b4e3f442b8bd3a1f7aacae918",
                            "status": "Sprint activo",
                        })
                        self.assertTrue(result["ok"])
                        self.assertEqual(result["storyCount"], 2)
                        self.assertEqual(result["syncedStoryCount"], 2)
                        self.assertEqual(result["dependencySyncCount"], 2)
                        sync_vision.assert_called_once()
                        self.assertEqual(sync_story.call_count, 2)
                        self.assertEqual(sync_deps.call_count, 2)
                        self.assertEqual(len(result["unresolvedAssignments"]), 1)
                        self.assertEqual(result["unresolvedAssignments"][0]["storyId"], "HU-02")
                        self.assertEqual(len(result["attachmentSkips"]), 1)
                        self.assertEqual(result["attachmentSkips"][0]["storyId"], "HU-02")
                        report_path = result["reportPath"]
                        self.assertTrue(os.path.isfile(report_path))
                        with open(report_path, encoding="utf-8") as handle:
                            report = handle.read()
                        self.assertIn("Unresolved Assignments", report)
                        self.assertIn("Attachment Skips", report)
                        self.assertIn("HU-02", report)

    def test_set_story_dependencies_resolves_story_ids_and_patches_relation(self):
        module = self.module
        with mock.patch.object(module, "ensure_dependency_relations", return_value={"ok": True}):
            with mock.patch.object(module, "find_story_page", side_effect=[
                {"ok": True, "page": {"id": "325b0a8f-a254-81b3-8f98-fc910cc826ac"}},
                {"ok": True, "page": {"id": "325b0a8f-a254-81da-83aa-cd772d9b160d"}},
            ]):
                with mock.patch.object(module, "_request_json", return_value={"id": "updated-page"}) as request:
                    result = module.set_story_dependencies({
                        "dataSourceId": "5a40701b4e3f442b8bd3a1f7aacae918",
                        "storyId": "HU-02",
                        "dependencyStoryIds": ["HU-01"],
                    })
        self.assertTrue(result["ok"])
        self.assertEqual(result["resolvedDependencyPageIds"], ["325b0a8f-a254-81da-83aa-cd772d9b160d"])
        args = request.call_args[0]
        self.assertEqual(args[0], "PATCH")
        self.assertIn("/v1/pages/325b0a8f-a254-81b3-8f98-fc910cc826ac", args[1])
        self.assertEqual(
            args[2]["properties"]["Bloqueada_por"]["relation"][0]["id"],
            "325b0a8f-a254-81da-83aa-cd772d9b160d",
        )

    def test_resolve_user_by_email_matches_exact_person_email(self):
        module = self.module
        with mock.patch.object(module, "list_users", return_value={
            "results": [
                {
                    "id": "user-1",
                    "name": "Ada",
                    "type": "person",
                    "person": {"email": "ada@example.com"},
                },
                {
                    "id": "user-2",
                    "name": "Bot",
                    "type": "bot",
                    "bot": {},
                },
            ]
        }):
            result = module.resolve_user_by_email({"email": "ADA@example.com"})
        self.assertTrue(result["ok"])
        self.assertEqual(result["matches"][0]["id"], "user-1")

    def test_upload_and_attach_markdown_orchestrates_upload_attach_and_block(self):
        module = self.module
        with tempfile.TemporaryDirectory() as tmpdir:
            md_path = os.path.join(tmpdir, "HU-01-login.md")
            with open(md_path, "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            with mock.patch.object(module, "retrieve_page", return_value={
                "properties": {"Documento_MD": {"files": []}}
            }):
                with mock.patch.object(module, "create_file_upload", return_value={"id": "325b0a8f-a254-8059-9971-f0c19b43e120", "upload_url": "https://upload.test"}) as create_upload:
                    with mock.patch.object(module, "send_file_upload", return_value={"status": "uploaded"}) as send_upload:
                        with mock.patch.object(module, "attach_file_to_page_property", return_value={"id": "325b0a8f-a254-8059-9971-f0c19b43e121"}) as attach_prop:
                            with mock.patch.object(module, "append_file_block", return_value={"results": []}) as append_block:
                                result = module.upload_and_attach_markdown({
                                    "pageId": "325b0a8fa25481e4a1e5d029abca0857",
                                    "filePath": md_path,
                                })
        self.assertTrue(result["ok"])
        create_upload.assert_called_once()
        send_upload.assert_called_once()
        attach_prop.assert_called_once()
        append_block.assert_called_once()

    def test_upload_and_attach_markdown_skips_when_same_filename_already_exists(self):
        module = self.module
        with tempfile.TemporaryDirectory() as tmpdir:
            md_path = os.path.join(tmpdir, "HU-01-login.md")
            with open(md_path, "w", encoding="utf-8") as handle:
                handle.write("# HU-01\n")
            with mock.patch.object(module, "retrieve_page", return_value={
                "properties": {
                    "Documento_MD": {
                        "files": [{"name": "HU-01-login.md"}],
                    }
                }
            }):
                with mock.patch.object(module, "create_file_upload") as create_upload:
                    result = module.upload_and_attach_markdown({
                        "pageId": "325b0a8fa25481e4a1e5d029abca0857",
                        "filePath": md_path,
                    })
        self.assertTrue(result["ok"])
        self.assertTrue(result["skipped"])
        self.assertEqual(result["reason"], "already_attached")
        create_upload.assert_not_called()

    def test_loads_env_from_project_file(self):
        module = self.module
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = os.path.join(tmpdir, ".env")
            with open(env_path, "w", encoding="utf-8") as handle:
                handle.write(
                    "NOTION_TOKEN=ntn_token\n"
                    "NOTION_PARENT_PAGE_ID=325b0a8fa25480599971f0c19b43e43c\n"
                )
            cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                with mock.patch.dict(os.environ, {}, clear=True):
                    module._load_project_env()
                    self.assertEqual(os.environ["NOTION_TOKEN"], "ntn_token")
                    self.assertEqual(os.environ["NOTION_PARENT_PAGE_ID"], "325b0a8fa25480599971f0c19b43e43c")
            finally:
                os.chdir(cwd)

    def test_save_project_targets_updates_env(self):
        module = self.module
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = module.save_project_targets({
                    "parentPageId": "325b0a8fa25480599971f0c19b43e43c",
                    "projectPageId": "325b0a8fa254811d9d61cd6286cd22f0",
                    "visionPageId": "325b0a8fa254816d9b4acc6465ac4ca4",
                    "databaseId": "aba349f0269649169a242d4895303daa",
                })
                with open(os.path.join(tmpdir, ".env"), encoding="utf-8") as handle:
                    content = handle.read()
            finally:
                os.chdir(cwd)
        self.assertTrue(result["saved"])
        self.assertIn("NOTION_PARENT_PAGE_ID=325b0a8fa25480599971f0c19b43e43c", content)
        self.assertIn("NOTION_PROJECT_PAGE_ID=325b0a8fa254811d9d61cd6286cd22f0", content)
        self.assertIn("NOTION_VISION_PAGE_ID=325b0a8fa254816d9b4acc6465ac4ca4", content)
        self.assertIn("NOTION_DATABASE_ID=aba349f0269649169a242d4895303daa", content)


if __name__ == "__main__":
    unittest.main()
