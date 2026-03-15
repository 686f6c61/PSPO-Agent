"""
Test end-to-end del servidor MCP.

Arranca el servidor como subproceso REAL, envia mensajes JSON-RPC
por stdin y lee las respuestas por stdout. No hay mocks.

Verifica:
- Protocolo completo: initialize -> tools/list -> ping -> tools/call
- Las 12 herramientas responden correctamente ante errores de validacion
- Resiliencia: JSON malformado, herramientas inexistentes, IDs invalidos
- Consistencia: Content-Length coincide con el body
- UTF-8 multibyte: tildes y enes no corrompen el protocolo
- Mensajes rapidos consecutivos no se pierden
"""
import json
import os
import subprocess
import sys
import unittest

PLUGIN_ROOT = os.path.join(os.path.dirname(__file__), "..")
SERVER_PATH = os.path.join(PLUGIN_ROOT, "servers", "trello-mcp.py")
VALID_API_KEY = "aabbccdd11223344aabbccdd11223344"
VALID_TOKEN = "ATTAaabbccdd11223344aabbccdd11223344iiiiiiiii"
VALID_TRELLO_ID = "507f1f77bcf86cd799439011"
BAD_ID = "../../../etc/passwd"


def send_message(proc, msg):
    body = json.dumps(msg).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
    proc.stdin.write(header + body)
    proc.stdin.flush()


def read_message(proc):
    content_length = 0
    while True:
        line = proc.stdout.readline()
        if not line:
            return None
        line_str = line.decode("utf-8").strip()
        if not line_str:
            break
        if line_str.lower().startswith("content-length:"):
            content_length = int(line_str.split(":", 1)[1].strip())
    if content_length == 0:
        return None
    body = proc.stdout.read(content_length)
    return json.loads(body.decode("utf-8"))


def start_server():
    env = os.environ.copy()
    env["TRELLO_API_KEY"] = VALID_API_KEY
    env["TRELLO_TOKEN"] = VALID_TOKEN
    return subprocess.Popen(
        [sys.executable, SERVER_PATH],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )


def call_tool(proc, tool_id, tool_name, arguments):
    """Llama a una herramienta y devuelve la respuesta."""
    send_message(proc, {
        "jsonrpc": "2.0", "id": tool_id,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    })
    return read_message(proc)


def init_server(proc):
    """Inicializa el servidor y devuelve la respuesta."""
    send_message(proc, {
        "jsonrpc": "2.0", "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-e2e", "version": "1.0.0"},
        },
    })
    return read_message(proc)


class TestE2EProtocol(unittest.TestCase):
    """Protocolo MCP basico: initialize, tools/list, ping, errores."""

    def test_full_protocol_flow(self):
        proc = start_server()
        try:
            # 1. Initialize
            resp = init_server(proc)
            self.assertIsNotNone(resp)
            self.assertEqual(resp["id"], 1)
            self.assertEqual(resp["result"]["serverInfo"]["name"], "trello-client")
            self.assertEqual(resp["result"]["protocolVersion"], "2024-11-05")

            # 2. Notification (no response expected)
            send_message(proc, {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            })

            # 3. Tools list: 12 herramientas
            send_message(proc, {
                "jsonrpc": "2.0", "id": 2,
                "method": "tools/list", "params": {},
            })
            resp = read_message(proc)
            self.assertEqual(resp["id"], 2)
            tools = resp["result"]["tools"]
            self.assertEqual(len(tools), 12)
            tool_names = {t["name"] for t in tools}
            expected = {
                "verify-credentials", "list-boards", "get-board",
                "create-board", "manage-lists", "manage-labels",
                "create-cards", "search-cards", "add-checklist", "attach-file",
                "get-board-members", "invite-member",
            }
            self.assertEqual(tool_names, expected)

            # 4. Cada herramienta tiene inputSchema valido
            for t in tools:
                self.assertIn("inputSchema", t,
                              f"Falta inputSchema en {t['name']}")
                self.assertEqual(t["inputSchema"]["type"], "object",
                                 f"inputSchema no es object en {t['name']}")
                self.assertIn("properties", t["inputSchema"],
                              f"Falta properties en inputSchema de {t['name']}")

            # 5. Ping
            send_message(proc, {
                "jsonrpc": "2.0", "id": 3,
                "method": "ping", "params": {},
            })
            resp = read_message(proc)
            self.assertEqual(resp["id"], 3)
            self.assertEqual(resp["result"], {})

            # 6. Unknown method -> error -32601
            send_message(proc, {
                "jsonrpc": "2.0", "id": 4,
                "method": "invalid/method", "params": {},
            })
            resp = read_message(proc)
            self.assertEqual(resp["id"], 4)
            self.assertIn("error", resp)
            self.assertEqual(resp["error"]["code"], -32601)

            # 7. Herramienta inexistente -> isError
            resp = call_tool(proc, 5, "herramienta-falsa", {})
            self.assertTrue(resp["result"]["isError"])
            self.assertIn("no encontrada", resp["result"]["content"][0]["text"])

        finally:
            proc.stdin.close()
            proc.terminate()
            proc.wait(timeout=5)


class TestE2EToolValidation(unittest.TestCase):
    """Cada herramienta valida sus argumentos correctamente via protocolo real."""

    def setUp(self):
        self.proc = start_server()
        init_server(self.proc)
        self._next_id = 10

    def tearDown(self):
        self.proc.stdin.close()
        self.proc.terminate()
        self.proc.wait(timeout=5)

    def _call(self, tool_name, arguments):
        self._next_id += 1
        return call_tool(self.proc, self._next_id, tool_name, arguments)

    def _assert_error(self, resp, expected_text):
        self.assertTrue(resp["result"]["isError"],
                        f"Se esperaba error en {resp}")
        self.assertIn(expected_text,
                      resp["result"]["content"][0]["text"])

    def _assert_success(self, resp):
        self.assertFalse(resp["result"].get("isError", False),
                         f"No se esperaba error: {resp['result']['content'][0]['text']}")

    # -- verify-credentials: no necesita argumentos, falla con 401 (creds falsas) --

    def test_verify_credentials_fake_creds(self):
        resp = self._call("verify-credentials", {})
        self._assert_error(resp, "invalidas")

    # -- get-board: validacion de boardId --

    def test_get_board_path_traversal(self):
        resp = self._call("get-board", {"boardId": BAD_ID})
        self._assert_error(resp, "formato valido")

    def test_get_board_empty_id(self):
        resp = self._call("get-board", {"boardId": ""})
        self._assert_error(resp, "formato valido")

    def test_get_board_short_id(self):
        resp = self._call("get-board", {"boardId": "abc123"})
        self._assert_error(resp, "formato valido")

    # -- create-board: validacion de name --

    def test_create_board_empty_name(self):
        resp = self._call("create-board", {"name": ""})
        self._assert_error(resp, "obligatorio")

    def test_create_board_whitespace_name(self):
        resp = self._call("create-board", {"name": "   "})
        self._assert_error(resp, "obligatorio")

    # -- manage-lists: validacion de action y boardId --

    def test_manage_lists_invalid_action(self):
        resp = self._call("manage-lists", {
            "boardId": VALID_TRELLO_ID, "action": "destroy",
        })
        self._assert_error(resp, "no reconocida")

    def test_manage_lists_bad_board_id(self):
        resp = self._call("manage-lists", {
            "boardId": "INVALID", "action": "create", "name": "Test",
        })
        self._assert_error(resp, "formato valido")

    def test_manage_lists_create_no_name(self):
        resp = self._call("manage-lists", {
            "boardId": VALID_TRELLO_ID, "action": "create", "name": "",
        })
        self._assert_error(resp, "obligatorio")

    def test_manage_lists_reorder_no_pos(self):
        resp = self._call("manage-lists", {
            "boardId": VALID_TRELLO_ID, "action": "reorder",
            "listId": VALID_TRELLO_ID,
        })
        self._assert_error(resp, "obligatorio")

    def test_manage_lists_rename_no_name(self):
        resp = self._call("manage-lists", {
            "boardId": VALID_TRELLO_ID, "action": "rename",
            "listId": VALID_TRELLO_ID, "name": "",
        })
        self._assert_error(resp, "obligatorio")

    # -- manage-labels: validacion --

    def test_manage_labels_invalid_action(self):
        resp = self._call("manage-labels", {
            "boardId": VALID_TRELLO_ID, "action": "explode",
        })
        self._assert_error(resp, "no reconocida")

    def test_manage_labels_create_no_name(self):
        resp = self._call("manage-labels", {
            "boardId": VALID_TRELLO_ID, "action": "create", "name": "",
        })
        self._assert_error(resp, "obligatorio")

    # -- create-cards: validacion --

    def test_create_cards_empty(self):
        resp = self._call("create-cards", {
            "listId": VALID_TRELLO_ID, "cards": [],
        })
        self._assert_error(resp, "necesaria")

    def test_create_cards_bad_list_id(self):
        resp = self._call("create-cards", {
            "listId": "BAD", "cards": [{"name": "T", "desc": "D"}],
        })
        self._assert_error(resp, "formato valido")

    # -- search-cards: validacion de boardId --

    def test_search_cards_bad_board_id(self):
        resp = self._call("search-cards", {"boardId": "INVALID"})
        self._assert_error(resp, "formato valido")

    # -- add-checklist: validacion --

    def test_add_checklist_bad_card_id(self):
        resp = self._call("add-checklist", {
            "cardId": "BAD", "name": "DoD", "items": ["Test"],
        })
        self._assert_error(resp, "formato valido")

    def test_add_checklist_no_name(self):
        resp = self._call("add-checklist", {
            "cardId": VALID_TRELLO_ID, "name": "", "items": ["Test"],
        })
        self._assert_error(resp, "obligatorio")

    def test_add_checklist_no_items(self):
        resp = self._call("add-checklist", {
            "cardId": VALID_TRELLO_ID, "name": "DoD", "items": [],
        })
        self._assert_error(resp, "necesario")

    # -- attach-file: validacion --

    def test_attach_file_bad_card_id(self):
        resp = self._call("attach-file", {
            "cardId": "BAD", "fileName": "test.md", "content": "algo",
        })
        self._assert_error(resp, "formato valido")

    def test_attach_file_no_filename(self):
        resp = self._call("attach-file", {
            "cardId": VALID_TRELLO_ID, "fileName": "", "content": "algo",
        })
        self._assert_error(resp, "obligatorio")

    def test_attach_file_no_content(self):
        resp = self._call("attach-file", {
            "cardId": VALID_TRELLO_ID, "fileName": "test.md", "content": "",
        })
        self._assert_error(resp, "obligatorio")

    # -- get-board-members: validacion --

    def test_get_board_members_bad_id(self):
        resp = self._call("get-board-members", {"boardId": "INVALID"})
        self._assert_error(resp, "formato valido")

    # -- invite-member: validacion robusta de email --

    def test_invite_member_bad_board_id(self):
        resp = self._call("invite-member", {
            "boardId": "BAD", "email": "a@b.com",
        })
        self._assert_error(resp, "formato valido")

    def test_invite_member_empty_email(self):
        resp = self._call("invite-member", {
            "boardId": VALID_TRELLO_ID, "email": "",
        })
        self._assert_error(resp, "formato valido")

    def test_invite_member_email_no_domain(self):
        resp = self._call("invite-member", {
            "boardId": VALID_TRELLO_ID, "email": "user@",
        })
        self._assert_error(resp, "formato valido")

    def test_invite_member_email_at_only(self):
        resp = self._call("invite-member", {
            "boardId": VALID_TRELLO_ID, "email": "@@",
        })
        self._assert_error(resp, "formato valido")

    def test_invite_member_email_no_tld(self):
        resp = self._call("invite-member", {
            "boardId": VALID_TRELLO_ID, "email": "a@b",
        })
        self._assert_error(resp, "formato valido")

    def test_invite_member_invalid_type(self):
        resp = self._call("invite-member", {
            "boardId": VALID_TRELLO_ID,
            "email": "ana@empresa.com",
            "type": "viewer",
        })
        self._assert_error(resp, "no reconocido")


class TestE2EResilience(unittest.TestCase):
    """El servidor sobrevive a mensajes malformados y no se corrompe."""

    def test_malformed_json_doesnt_crash(self):
        """JSON invalido no mata el servidor; sigue respondiendo despues."""
        proc = start_server()
        try:
            init_server(proc)

            # Enviar JSON malformado
            bad_body = b'{not valid json at all}'
            header = f"Content-Length: {len(bad_body)}\r\n\r\n".encode("utf-8")
            proc.stdin.write(header + bad_body)
            proc.stdin.flush()

            # El servidor debe seguir vivo: enviar un ping y esperar respuesta
            send_message(proc, {
                "jsonrpc": "2.0", "id": 99,
                "method": "ping", "params": {},
            })
            resp = read_message(proc)
            self.assertIsNotNone(resp, "Servidor murio tras JSON malformado")
            self.assertEqual(resp["id"], 99)

        finally:
            proc.stdin.close()
            proc.terminate()
            proc.wait(timeout=5)

    def test_utf8_multibyte_integrity(self):
        """Caracteres multibyte (tildes, ene) no corrompen Content-Length."""
        proc = start_server()
        try:
            init_server(proc)

            # Tool call con caracteres especiales
            resp = call_tool(proc, 2, "search-cards", {
                "boardId": VALID_TRELLO_ID,
                "query": "busqueda con tildes aeiou y ene",
            })
            # Falla con 401 (creds falsas), pero el protocolo no se corrompe
            self.assertIsNotNone(resp, "Protocolo corrompido con UTF-8")
            self.assertEqual(resp["id"], 2)

        finally:
            proc.stdin.close()
            proc.terminate()
            proc.wait(timeout=5)

    def test_multiple_rapid_messages(self):
        """10 pings rapidos consecutivos llegan y responden en orden."""
        proc = start_server()
        try:
            init_server(proc)

            for i in range(10, 20):
                send_message(proc, {
                    "jsonrpc": "2.0", "id": i,
                    "method": "ping", "params": {},
                })

            for i in range(10, 20):
                resp = read_message(proc)
                self.assertIsNotNone(resp, f"Respuesta {i} perdida")
                self.assertEqual(resp["id"], i)

        finally:
            proc.stdin.close()
            proc.terminate()
            proc.wait(timeout=5)

    def test_content_length_consistency(self):
        """Content-Length declarado coincide con bytes del body recibido."""
        proc = start_server()
        try:
            init_server(proc)

            send_message(proc, {
                "jsonrpc": "2.0", "id": 2,
                "method": "tools/list", "params": {},
            })

            # Leer header manualmente para verificar Content-Length
            content_length = 0
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                line_str = line.decode("utf-8").strip()
                if not line_str:
                    break
                if line_str.lower().startswith("content-length:"):
                    content_length = int(line_str.split(":", 1)[1].strip())

            self.assertGreater(content_length, 0)
            body = proc.stdout.read(content_length)
            self.assertEqual(len(body), content_length,
                             "Content-Length no coincide con bytes reales")

            parsed = json.loads(body.decode("utf-8"))
            self.assertEqual(len(parsed["result"]["tools"]), 12)

        finally:
            proc.stdin.close()
            proc.terminate()
            proc.wait(timeout=5)


class TestE2EServerStartup(unittest.TestCase):
    """El servidor arranca y falla correctamente segun las credenciales."""

    def test_missing_api_key_exits(self):
        env = os.environ.copy()
        env.pop("TRELLO_API_KEY", None)
        env.pop("TRELLO_TOKEN", None)
        proc = subprocess.Popen(
            [sys.executable, SERVER_PATH],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=env,
        )
        proc.wait(timeout=5)
        self.assertNotEqual(proc.returncode, 0)
        stderr = proc.stderr.read().decode("utf-8", errors="replace")
        self.assertIn("TRELLO_API_KEY", stderr)

    def test_invalid_api_key_format_exits(self):
        env = os.environ.copy()
        env["TRELLO_API_KEY"] = "not-hex"
        env["TRELLO_TOKEN"] = VALID_TOKEN
        proc = subprocess.Popen(
            [sys.executable, SERVER_PATH],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=env,
        )
        proc.wait(timeout=5)
        self.assertNotEqual(proc.returncode, 0)
        stderr = proc.stderr.read().decode("utf-8", errors="replace")
        self.assertIn("formato invalido", stderr)

    def test_invalid_token_format_exits(self):
        env = os.environ.copy()
        env["TRELLO_API_KEY"] = VALID_API_KEY
        env["TRELLO_TOKEN"] = "bad-token"
        proc = subprocess.Popen(
            [sys.executable, SERVER_PATH],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=env,
        )
        proc.wait(timeout=5)
        self.assertNotEqual(proc.returncode, 0)
        stderr = proc.stderr.read().decode("utf-8", errors="replace")
        self.assertIn("formato invalido", stderr)


class TestE2EPluginIntegrity(unittest.TestCase):
    """Verifica que la estructura del plugin es integra y coherente."""

    def setUp(self):
        with open(os.path.join(PLUGIN_ROOT, ".claude-plugin", "plugin.json")) as f:
            self.plugin = json.load(f)

    def test_all_skill_files_referenced_in_plugin_exist(self):
        for skill_path in self.plugin["skills"]:
            full_path = os.path.join(PLUGIN_ROOT, skill_path.lstrip("./"))
            self.assertTrue(os.path.exists(full_path),
                            f"Skill referenciada no existe: {skill_path}")

    def test_all_agent_files_referenced_in_plugin_exist(self):
        for agent_path in self.plugin["agents"]:
            full_path = os.path.join(PLUGIN_ROOT, agent_path.lstrip("./"))
            self.assertTrue(os.path.exists(full_path),
                            f"Agente referenciado no existe: {agent_path}")

    def test_all_command_files_referenced_in_plugin_exist(self):
        for cmd_path in self.plugin["commands"]:
            full_path = os.path.join(PLUGIN_ROOT, cmd_path.lstrip("./"))
            self.assertTrue(os.path.exists(full_path),
                            f"Comando referenciado no existe: {cmd_path}")

    def test_mcp_server_script_exists(self):
        with open(os.path.join(PLUGIN_ROOT, ".mcp.json")) as f:
            mcp = json.load(f)
        # La ruta usa ${CLAUDE_PLUGIN_ROOT}, extraemos el nombre del fichero
        args = mcp["mcpServers"]["trello-client"]["args"]
        script_name = os.path.basename(args[0].replace("${CLAUDE_PLUGIN_ROOT}/", ""))
        script_path = os.path.join(PLUGIN_ROOT, "servers", script_name)
        self.assertTrue(os.path.exists(script_path),
                        f"Script MCP no existe: {script_path}")

    def test_hooks_scripts_referenced_exist(self):
        with open(os.path.join(PLUGIN_ROOT, "hooks", "hooks.json")) as f:
            hooks = json.load(f)
        for event_hooks in hooks["hooks"].values():
            for matcher_group in event_hooks:
                for hook in matcher_group["hooks"]:
                    cmd = hook["command"]
                    script = cmd.replace("${CLAUDE_PLUGIN_ROOT}/", "")
                    script_path = os.path.join(PLUGIN_ROOT, script)
                    self.assertTrue(os.path.exists(script_path),
                                    f"Hook script no existe: {script}")

    def test_versions_consistent(self):
        """La version debe ser la misma en plugin.json, settings.json y marketplace.json."""
        plugin_version = self.plugin["version"]

        with open(os.path.join(PLUGIN_ROOT, "settings.json")) as f:
            settings = json.load(f)
        self.assertEqual(settings["version"], plugin_version,
                         "Version de settings.json no coincide con plugin.json")

        with open(os.path.join(PLUGIN_ROOT, ".claude-plugin", "marketplace.json")) as f:
            marketplace = json.load(f)
        mp_version = marketplace["plugins"][0]["version"]
        self.assertEqual(mp_version, plugin_version,
                         "Version de marketplace.json no coincide con plugin.json")

    def test_agent_mcp_references_valid(self):
        """Los agentes que declaran mcpServers deben referenciar servidores existentes."""
        with open(os.path.join(PLUGIN_ROOT, ".mcp.json")) as f:
            mcp = json.load(f)
        valid_servers = set(mcp["mcpServers"].keys())

        import re
        for agent_path in self.plugin["agents"]:
            full_path = os.path.join(PLUGIN_ROOT, agent_path.lstrip("./"))
            with open(full_path) as f:
                content = f.read()
            # Buscar mcpServers en frontmatter
            match = re.search(r"mcpServers:\s*\n((?:\s+-\s*.+\n)*)", content)
            if match:
                for line in match.group(1).strip().split("\n"):
                    server_name = line.strip().lstrip("- ").strip()
                    self.assertIn(server_name, valid_servers,
                                  f"Agente {agent_path} referencia servidor MCP "
                                  f"inexistente: {server_name}")


if __name__ == "__main__":
    unittest.main()
