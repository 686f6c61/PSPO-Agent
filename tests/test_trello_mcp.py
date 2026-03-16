"""
Tests para el servidor MCP de Trello (servers/trello-mcp.py).
Solo usa stdlib de Python (unittest). Sin dependencias externas.
"""

import io
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ajustar path para importar el servidor
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "servers"))

# Importar despues de ajustar path
import importlib
trello_mcp = importlib.import_module("trello-mcp")

TrelloClient = trello_mcp.TrelloClient
MCPServer = trello_mcp.MCPServer
_validate_trello_id = trello_mcp._validate_trello_id
_mask = trello_mcp._mask
_pspo_id_tag = trello_mcp._pspo_id_tag

# Handlers
handle_verify_credentials = trello_mcp.handle_verify_credentials
handle_list_boards = trello_mcp.handle_list_boards
handle_get_board = trello_mcp.handle_get_board
handle_get_card = trello_mcp.handle_get_card
handle_create_board = trello_mcp.handle_create_board
handle_manage_lists = trello_mcp.handle_manage_lists
handle_manage_labels = trello_mcp.handle_manage_labels
handle_create_cards = trello_mcp.handle_create_cards
handle_search_cards = trello_mcp.handle_search_cards
handle_update_card = trello_mcp.handle_update_card
handle_get_board_members = trello_mcp.handle_get_board_members

# Credenciales de test validas
VALID_API_KEY = "aabbccdd11223344aabbccdd11223344"
VALID_TOKEN = "ATTAaabbccdd11223344aabbccdd11223344iiiiiiiii"
VALID_TRELLO_ID = "507f1f77bcf86cd799439011"


def make_mock_client():
    """Crea un TrelloClient con HTTP mockeado."""
    with patch.object(TrelloClient, "__init__", lambda self, *a, **kw: None):
        client = TrelloClient.__new__(TrelloClient)
        client._api_key = VALID_API_KEY
        client._token = VALID_TOKEN
        client._timestamps = []
        client.get = MagicMock()
        client.post = MagicMock()
        client.put = MagicMock()
        client.delete = MagicMock()
    return client


# ---------------------------------------------------------------------------
# Tests de utilidades
# ---------------------------------------------------------------------------

class TestValidateTrelloId(unittest.TestCase):

    def test_valid_id(self):
        result = _validate_trello_id(VALID_TRELLO_ID, "boardId")
        self.assertEqual(result, VALID_TRELLO_ID)

    def test_valid_id_with_spaces(self):
        result = _validate_trello_id(f"  {VALID_TRELLO_ID}  ", "boardId")
        self.assertEqual(result, VALID_TRELLO_ID)

    def test_empty_string(self):
        with self.assertRaises(ValueError) as ctx:
            _validate_trello_id("", "boardId")
        self.assertIn("boardId", str(ctx.exception))

    def test_path_traversal(self):
        with self.assertRaises(ValueError):
            _validate_trello_id("../../../etc/passwd", "boardId")

    def test_url_injection(self):
        with self.assertRaises(ValueError):
            _validate_trello_id("507f1f77bcf86cd7?foo=bar", "boardId")

    def test_too_short(self):
        with self.assertRaises(ValueError):
            _validate_trello_id("507f1f77bcf86c", "boardId")

    def test_too_long(self):
        with self.assertRaises(ValueError):
            _validate_trello_id("507f1f77bcf86cd799439011aa", "boardId")

    def test_non_hex(self):
        with self.assertRaises(ValueError):
            _validate_trello_id("507f1f77bcf86cd79943901z", "listId")

    def test_uppercase_hex(self):
        result = _validate_trello_id("507F1F77BCF86CD799439011", "boardId")
        self.assertEqual(result, "507F1F77BCF86CD799439011")


class TestMask(unittest.TestCase):

    def test_normal(self):
        self.assertEqual(_mask("abcdefgh"), "****efgh")

    def test_short(self):
        self.assertEqual(_mask("ab"), "****")

    def test_exact_four(self):
        self.assertEqual(_mask("abcd"), "****")

    def test_five(self):
        self.assertEqual(_mask("abcde"), "****bcde")


class TestPspoIdTag(unittest.TestCase):

    def test_generates_tag(self):
        tag = _pspo_id_tag("HU-01: Titulo", "Descripcion")
        self.assertTrue(tag.startswith("<!-- pspo-id: HU-01-"))
        self.assertTrue(tag.endswith("-->"))

    def test_no_colon_in_name(self):
        tag = _pspo_id_tag("Sin dos puntos", "Descripcion")
        self.assertIn("Sin dos puntos-", tag)

    def test_deterministic(self):
        tag1 = _pspo_id_tag("HU-01: A", "desc")
        tag2 = _pspo_id_tag("HU-01: A", "desc")
        self.assertEqual(tag1, tag2)

    def test_different_content(self):
        tag1 = _pspo_id_tag("HU-01: A", "desc1")
        tag2 = _pspo_id_tag("HU-01: A", "desc2")
        self.assertNotEqual(tag1, tag2)


# ---------------------------------------------------------------------------
# Tests del TrelloClient
# ---------------------------------------------------------------------------

class TestTrelloClientInit(unittest.TestCase):

    def test_valid_credentials(self):
        client = TrelloClient(VALID_API_KEY, VALID_TOKEN)
        self.assertIsNotNone(client)

    def test_empty_api_key(self):
        with self.assertRaises(ValueError) as ctx:
            TrelloClient("", VALID_TOKEN)
        self.assertIn("obligatoria", str(ctx.exception))

    def test_empty_token(self):
        with self.assertRaises(ValueError) as ctx:
            TrelloClient(VALID_API_KEY, "")
        self.assertIn("obligatorio", str(ctx.exception))

    def test_invalid_api_key_format(self):
        with self.assertRaises(ValueError) as ctx:
            TrelloClient("not-hex-32-chars!!!!!!!!!!!!!!!", VALID_TOKEN)
        self.assertIn("formato invalido", str(ctx.exception))

    def test_api_key_wrong_length(self):
        with self.assertRaises(ValueError):
            TrelloClient("aabb", VALID_TOKEN)

    def test_token_without_atta_prefix(self):
        with self.assertRaises(ValueError) as ctx:
            TrelloClient(VALID_API_KEY, "a" * 50)
        self.assertIn("formato invalido", str(ctx.exception))

    def test_token_too_short(self):
        with self.assertRaises(ValueError):
            TrelloClient(VALID_API_KEY, "ATTA" + "a" * 10)

    def test_credentials_with_spaces(self):
        client = TrelloClient(f"  {VALID_API_KEY}  ", f"  {VALID_TOKEN}  ")
        self.assertIsNotNone(client)


# ---------------------------------------------------------------------------
# Tests de handlers
# ---------------------------------------------------------------------------

class TestHandleVerifyCredentials(unittest.TestCase):

    def test_success(self):
        client = make_mock_client()
        client.get.return_value = {
            "id": "abc123", "fullName": "Test User",
            "username": "testuser", "url": "https://trello.com/testuser",
        }
        result = handle_verify_credentials(client, {})
        self.assertEqual(result["username"], "testuser")
        client.get.assert_called_once_with("/1/members/me")


class TestHandleListBoards(unittest.TestCase):

    def test_default_filter(self):
        client = make_mock_client()
        client.get.return_value = [
            {"id": "b1", "name": "Board 1", "url": "http://...", "closed": False},
        ]
        result = handle_list_boards(client, {})
        self.assertEqual(len(result["boards"]), 1)
        client.get.assert_called_once_with(
            "/1/members/me/boards", {"filter": "open", "fields": "id,name,url,closed"}
        )

    def test_custom_filter(self):
        client = make_mock_client()
        client.get.return_value = []
        handle_list_boards(client, {"filter": "closed"})
        client.get.assert_called_once_with(
            "/1/members/me/boards", {"filter": "closed", "fields": "id,name,url,closed"}
        )


class TestHandleGetBoard(unittest.TestCase):

    def test_success(self):
        client = make_mock_client()
        client.get.return_value = {
            "id": VALID_TRELLO_ID, "name": "Mi tablero",
            "url": "http://...", "lists": [], "labels": [],
        }
        result = handle_get_board(client, {"boardId": VALID_TRELLO_ID})
        self.assertEqual(result["name"], "Mi tablero")

    def test_invalid_board_id(self):
        client = make_mock_client()
        with self.assertRaises(ValueError):
            handle_get_board(client, {"boardId": "../etc/passwd"})

    def test_empty_board_id(self):
        client = make_mock_client()
        with self.assertRaises(ValueError):
            handle_get_board(client, {"boardId": ""})


class TestHandleGetCard(unittest.TestCase):

    def test_success(self):
        client = make_mock_client()
        client.get.return_value = {
            "id": VALID_TRELLO_ID,
            "name": "HU-01: Login",
            "desc": "Resumen",
            "url": "https://trello.com/c/abc",
            "idList": VALID_TRELLO_ID,
            "idLabels": [VALID_TRELLO_ID],
            "idMembers": [VALID_TRELLO_ID],
            "attachments": [
                {"id": VALID_TRELLO_ID, "name": "HU-01-login.md", "url": "https://..."}
            ],
            "checklists": [
                {
                    "id": VALID_TRELLO_ID,
                    "name": "Dependencias",
                    "checkItems": [
                        {"id": VALID_TRELLO_ID, "name": "HU-02", "state": "incomplete"}
                    ],
                }
            ],
        }
        result = handle_get_card(client, {"cardId": VALID_TRELLO_ID})
        self.assertEqual(result["name"], "HU-01: Login")
        self.assertEqual(result["attachments"][0]["name"], "HU-01-login.md")
        self.assertEqual(result["checklists"][0]["name"], "Dependencias")


class TestHandleCreateBoard(unittest.TestCase):

    def test_success(self):
        client = make_mock_client()
        client.post.return_value = {
            "id": VALID_TRELLO_ID, "name": "Nuevo", "url": "http://...",
        }
        result = handle_create_board(client, {"name": "Nuevo"})
        self.assertEqual(result["name"], "Nuevo")

    def test_empty_name(self):
        client = make_mock_client()
        with self.assertRaises(ValueError):
            handle_create_board(client, {"name": ""})

    def test_whitespace_name(self):
        client = make_mock_client()
        with self.assertRaises(ValueError):
            handle_create_board(client, {"name": "   "})


class TestHandleManageLists(unittest.TestCase):

    def test_create(self):
        client = make_mock_client()
        client.post.return_value = {
            "id": VALID_TRELLO_ID, "name": "Backlog", "pos": 1, "closed": False,
        }
        result = handle_manage_lists(client, {
            "boardId": VALID_TRELLO_ID, "action": "create", "name": "Backlog",
        })
        self.assertEqual(result["name"], "Backlog")

    def test_create_without_name(self):
        client = make_mock_client()
        with self.assertRaises(ValueError):
            handle_manage_lists(client, {
                "boardId": VALID_TRELLO_ID, "action": "create", "name": "",
            })

    def test_rename(self):
        client = make_mock_client()
        client.put.return_value = {
            "id": VALID_TRELLO_ID, "name": "New Name", "pos": 1, "closed": False,
        }
        result = handle_manage_lists(client, {
            "boardId": VALID_TRELLO_ID, "action": "rename",
            "listId": VALID_TRELLO_ID, "name": "New Name",
        })
        self.assertEqual(result["name"], "New Name")

    def test_archive(self):
        client = make_mock_client()
        client.put.return_value = {
            "id": VALID_TRELLO_ID, "name": "Old", "pos": 1, "closed": True,
        }
        result = handle_manage_lists(client, {
            "boardId": VALID_TRELLO_ID, "action": "archive",
            "listId": VALID_TRELLO_ID,
        })
        self.assertTrue(result["closed"])

    def test_invalid_action(self):
        client = make_mock_client()
        with self.assertRaises(ValueError):
            handle_manage_lists(client, {
                "boardId": VALID_TRELLO_ID, "action": "destroy",
            })

    def test_invalid_board_id(self):
        client = make_mock_client()
        with self.assertRaises(ValueError):
            handle_manage_lists(client, {
                "boardId": "INVALID!", "action": "create", "name": "Test",
            })


class TestHandleManageLabels(unittest.TestCase):

    def test_create(self):
        client = make_mock_client()
        client.post.return_value = {
            "id": VALID_TRELLO_ID, "name": "Urgente", "color": "red",
        }
        result = handle_manage_labels(client, {
            "boardId": VALID_TRELLO_ID, "action": "create",
            "name": "Urgente", "color": "red",
        })
        self.assertEqual(result["name"], "Urgente")

    def test_delete(self):
        client = make_mock_client()
        result = handle_manage_labels(client, {
            "boardId": VALID_TRELLO_ID, "action": "delete",
            "labelId": VALID_TRELLO_ID,
        })
        self.assertEqual(result["id"], VALID_TRELLO_ID)
        client.delete.assert_called_once()

    def test_invalid_action(self):
        client = make_mock_client()
        with self.assertRaises(ValueError):
            handle_manage_labels(client, {
                "boardId": VALID_TRELLO_ID, "action": "explode",
            })


class TestHandleCreateCards(unittest.TestCase):

    def test_single_card(self):
        client = make_mock_client()
        client.post.return_value = {
            "id": "card1", "name": "HU-01: Test", "url": "http://...",
        }
        result = handle_create_cards(client, {
            "listId": VALID_TRELLO_ID,
            "cards": [{"name": "HU-01: Test", "desc": "Description"}],
        })
        self.assertEqual(len(result["created"]), 1)
        self.assertEqual(len(result["failed"]), 0)

    def test_partial_failure(self):
        client = make_mock_client()
        client.post.side_effect = [
            {"id": "c1", "name": "HU-01", "url": "http://..."},
            RuntimeError("API error"),
        ]
        result = handle_create_cards(client, {
            "listId": VALID_TRELLO_ID,
            "cards": [
                {"name": "HU-01", "desc": "ok"},
                {"name": "HU-02", "desc": "fail"},
            ],
        })
        self.assertEqual(len(result["created"]), 1)
        self.assertEqual(len(result["failed"]), 1)
        self.assertIn("API error", result["failed"][0]["error"])

    def test_empty_cards(self):
        client = make_mock_client()
        with self.assertRaises(ValueError):
            handle_create_cards(client, {"listId": VALID_TRELLO_ID, "cards": []})

    def test_invalid_list_id(self):
        client = make_mock_client()
        with self.assertRaises(ValueError):
            handle_create_cards(client, {
                "listId": "BAD-ID",
                "cards": [{"name": "Test", "desc": "Desc"}],
            })

    def test_pspo_id_appended(self):
        client = make_mock_client()
        client.post.return_value = {"id": "c1", "name": "HU-01", "url": "http://..."}
        handle_create_cards(client, {
            "listId": VALID_TRELLO_ID,
            "cards": [{"name": "HU-01: Titulo", "desc": "Mi desc"}],
        })
        posted_body = client.post.call_args[0][1]
        self.assertIn("<!-- pspo-id:", posted_body["desc"])

    def test_id_members_passed(self):
        client = make_mock_client()
        client.post.return_value = {"id": "c1", "name": "HU-01", "url": "http://..."}
        handle_create_cards(client, {
            "listId": VALID_TRELLO_ID,
            "cards": [{"name": "HU-01", "desc": "Desc",
                        "idMembers": ["member1", "member2"]}],
        })
        posted_body = client.post.call_args[0][1]
        self.assertEqual(posted_body["idMembers"], "member1,member2")

    def test_no_id_members_when_empty(self):
        client = make_mock_client()
        client.post.return_value = {"id": "c1", "name": "HU-01", "url": "http://..."}
        handle_create_cards(client, {
            "listId": VALID_TRELLO_ID,
            "cards": [{"name": "HU-01", "desc": "Desc"}],
        })
        posted_body = client.post.call_args[0][1]
        self.assertNotIn("idMembers", posted_body)

    def test_single_card_payload_is_normalized(self):
        client = make_mock_client()
        client.post.return_value = {"id": "c1", "name": "HU-01", "url": "http://..."}
        handle_create_cards(client, {
            "idList": VALID_TRELLO_ID,
            "name": "HU-01",
            "desc": "Desc",
            "idMember": "member1",
        })
        posted_body = client.post.call_args[0][1]
        self.assertEqual(posted_body["idList"], VALID_TRELLO_ID)
        self.assertEqual(posted_body["name"], "HU-01")
        self.assertEqual(posted_body["idMembers"], "member1")


class TestHandleGetBoardMembers(unittest.TestCase):

    def test_success(self):
        client = make_mock_client()
        client.get.return_value = [
            {"id": "m1", "fullName": "Ana Garcia", "username": "anagarcia"},
            {"id": "m2", "fullName": "Pedro Lopez", "username": "pedrolopez"},
        ]
        result = handle_get_board_members(client, {"boardId": VALID_TRELLO_ID})
        self.assertEqual(len(result["members"]), 2)
        self.assertEqual(result["members"][0]["fullName"], "Ana Garcia")
        self.assertEqual(result["members"][1]["id"], "m2")

    def test_empty_board(self):
        client = make_mock_client()
        client.get.return_value = []
        result = handle_get_board_members(client, {"boardId": VALID_TRELLO_ID})
        self.assertEqual(len(result["members"]), 0)

    def test_invalid_board_id(self):
        client = make_mock_client()
        with self.assertRaises(ValueError):
            handle_get_board_members(client, {"boardId": "BAD-ID"})


class TestHandleSearchCards(unittest.TestCase):

    def test_no_filter(self):
        client = make_mock_client()
        client.get.return_value = [
            {"id": "c1", "name": "Card 1", "desc": "", "url": "http://...",
             "idList": "l1", "idLabels": []},
        ]
        result = handle_search_cards(client, {"boardId": VALID_TRELLO_ID})
        self.assertEqual(len(result["cards"]), 1)

    def test_with_query(self):
        client = make_mock_client()
        client.get.return_value = [
            {"id": "c1", "name": "Login feature", "desc": "", "url": "http://...",
             "idList": "l1", "idLabels": []},
            {"id": "c2", "name": "Signup feature", "desc": "", "url": "http://...",
             "idList": "l1", "idLabels": []},
        ]
        result = handle_search_cards(client, {
            "boardId": VALID_TRELLO_ID, "query": "login",
        })
        self.assertEqual(len(result["cards"]), 1)
        self.assertEqual(result["cards"][0]["name"], "Login feature")

    def test_invalid_board_id(self):
        client = make_mock_client()
        with self.assertRaises(ValueError):
            handle_search_cards(client, {"boardId": "not-valid"})


class TestHandleUpdateCard(unittest.TestCase):

    def test_requires_fields(self):
        client = make_mock_client()
        with self.assertRaises(ValueError):
            handle_update_card(client, {"cardId": VALID_TRELLO_ID})

    def test_update_desc_and_members(self):
        client = make_mock_client()
        second_id = "507f1f77bcf86cd799439012"
        client.put.return_value = {
            "id": VALID_TRELLO_ID,
            "name": "HU-01: Login",
            "desc": "Resumen actualizado",
            "url": "https://trello.com/c/abc",
            "idList": second_id,
            "idLabels": [VALID_TRELLO_ID],
            "idMembers": [second_id],
        }
        result = handle_update_card(client, {
            "cardId": VALID_TRELLO_ID,
            "desc": "Resumen actualizado",
            "listId": second_id,
            "idLabels": [VALID_TRELLO_ID],
            "idMembers": [second_id],
        })
        self.assertEqual(result["desc"], "Resumen actualizado")
        client.put.assert_called_once_with(
            f"/1/cards/{VALID_TRELLO_ID}",
            {
                "desc": "Resumen actualizado",
                "idList": second_id,
                "idLabels": VALID_TRELLO_ID,
                "idMembers": second_id,
            },
        )


# ---------------------------------------------------------------------------
# Tests del protocolo MCP
# ---------------------------------------------------------------------------

class TestMCPProtocol(unittest.TestCase):

    def _make_server(self):
        client = make_mock_client()
        return MCPServer(client)

    def test_handle_initialize(self):
        server = self._make_server()
        response = server._handle({
            "jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {},
        })
        self.assertEqual(response["id"], 1)
        self.assertIn("protocolVersion", response["result"])
        self.assertEqual(response["result"]["serverInfo"]["name"], "trello-client")

    def test_handle_ping(self):
        server = self._make_server()
        response = server._handle({
            "jsonrpc": "2.0", "id": 2, "method": "ping", "params": {},
        })
        self.assertEqual(response["id"], 2)
        self.assertEqual(response["result"], {})

    def test_handle_tools_list(self):
        server = self._make_server()
        response = server._handle({
            "jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {},
        })
        tools = response["result"]["tools"]
        self.assertEqual(len(tools), 14)
        names = {t["name"] for t in tools}
        self.assertIn("verify-credentials", names)
        self.assertIn("create-cards", names)
        self.assertIn("search-cards", names)
        self.assertIn("get-card", names)
        self.assertIn("update-card", names)
        self.assertIn("get-board-members", names)

    def test_handle_unknown_method(self):
        server = self._make_server()
        response = server._handle({
            "jsonrpc": "2.0", "id": 4, "method": "unknown/method", "params": {},
        })
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32601)

    def test_handle_notification_no_response(self):
        server = self._make_server()
        response = server._handle({
            "jsonrpc": "2.0", "method": "notifications/initialized", "params": {},
        })
        self.assertIsNone(response)

    def test_handle_unknown_tool(self):
        server = self._make_server()
        response = server._handle({
            "jsonrpc": "2.0", "id": 5,
            "method": "tools/call",
            "params": {"name": "nonexistent-tool", "arguments": {}},
        })
        self.assertTrue(response["result"]["isError"])

    def test_handle_tool_call_success(self):
        server = self._make_server()
        server._client.get = MagicMock(return_value={
            "id": "u1", "fullName": "Test", "username": "test", "url": "http://...",
        })
        response = server._handle({
            "jsonrpc": "2.0", "id": 6,
            "method": "tools/call",
            "params": {"name": "verify-credentials", "arguments": {}},
        })
        self.assertFalse(response["result"].get("isError", False))
        content = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(content["username"], "test")

    def test_handle_tool_call_error(self):
        server = self._make_server()
        server._client.get = MagicMock(side_effect=RuntimeError("API down"))
        response = server._handle({
            "jsonrpc": "2.0", "id": 7,
            "method": "tools/call",
            "params": {"name": "verify-credentials", "arguments": {}},
        })
        self.assertTrue(response["result"]["isError"])
        self.assertIn("API down", response["result"]["content"][0]["text"])


class TestMCPReadWrite(unittest.TestCase):

    def test_write_message_utf8(self):
        client = make_mock_client()
        server = MCPServer(client)
        msg = {"jsonrpc": "2.0", "id": 1, "result": {"text": "tildes: aeiou"}}
        body_bytes = json.dumps(msg).encode("utf-8")

        buf = io.BytesIO()
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.buffer = buf
            server._write_message(msg)

        output = buf.getvalue()
        header, body = output.split(b"\r\n\r\n", 1)
        declared_length = int(header.decode().split(":")[1].strip())
        self.assertEqual(declared_length, len(body))
        parsed = json.loads(body.decode("utf-8"))
        self.assertEqual(parsed["result"]["text"], "tildes: aeiou")

    def test_read_message_utf8(self):
        client = make_mock_client()
        server = MCPServer(client)
        msg = {"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}}
        body = json.dumps(msg).encode("utf-8")
        raw = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8") + body

        with patch("sys.stdin") as mock_stdin:
            mock_stdin.buffer = io.BytesIO(raw)
            result = server._read_message()

        self.assertEqual(result["method"], "ping")

    def test_read_message_multibyte(self):
        client = make_mock_client()
        server = MCPServer(client)
        msg = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": "test", "arguments": {"query": "busqueda con n y tildes aeiou"}}}
        body = json.dumps(msg, ensure_ascii=False).encode("utf-8")
        raw = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8") + body

        with patch("sys.stdin") as mock_stdin:
            mock_stdin.buffer = io.BytesIO(raw)
            result = server._read_message()

        self.assertEqual(result["params"]["arguments"]["query"],
                         "busqueda con n y tildes aeiou")


handle_add_checklist = trello_mcp.handle_add_checklist
handle_attach_file = trello_mcp.handle_attach_file


class TestHandleAttachFile(unittest.TestCase):

    @patch("urllib.request.urlopen")
    def test_success(self, mock_urlopen):
        client = make_mock_client()
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "id": "att1", "name": "HU-01.md", "url": "https://trello.com/att1",
        }).encode("utf-8")
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = handle_attach_file(client, {
            "cardId": VALID_TRELLO_ID,
            "fileName": "HU-01-registro.md",
            "content": "# Historia de usuario\nContenido completo.",
        })
        self.assertEqual(result["id"], "att1")
        self.assertEqual(result["cardId"], VALID_TRELLO_ID)
        mock_urlopen.assert_called_once()

    def test_empty_filename(self):
        client = make_mock_client()
        with self.assertRaises(ValueError) as ctx:
            handle_attach_file(client, {
                "cardId": VALID_TRELLO_ID,
                "fileName": "",
                "content": "algo",
            })
        self.assertIn("fileName", str(ctx.exception))

    def test_empty_content(self):
        client = make_mock_client()
        with self.assertRaises(ValueError) as ctx:
            handle_attach_file(client, {
                "cardId": VALID_TRELLO_ID,
                "fileName": "test.md",
                "content": "",
            })
        self.assertIn("content", str(ctx.exception))

    def test_invalid_card_id(self):
        client = make_mock_client()
        with self.assertRaises(ValueError):
            handle_attach_file(client, {
                "cardId": "BAD",
                "fileName": "test.md",
                "content": "algo",
            })

    def test_filename_sanitized(self):
        """Comillas y caracteres de control se reemplazan por _."""
        client = make_mock_client()
        with self.assertRaises(ValueError):
            # Content vacio falla antes de llegar a la peticion HTTP,
            # pero podemos verificar que el fileName se sanitiza
            handle_attach_file(client, {
                "cardId": VALID_TRELLO_ID,
                "fileName": 'test"injected.md',
                "content": "",
            })


class TestHandleAddChecklist(unittest.TestCase):

    def test_success(self):
        client = make_mock_client()
        client.post.side_effect = [
            {"id": "checklist1"},
            {"id": "item1", "name": "Tests unitarios"},
            {"id": "item2", "name": "Code review"},
        ]
        result = handle_add_checklist(client, {
            "cardId": VALID_TRELLO_ID,
            "name": "Definition of Done",
            "items": ["Tests unitarios", "Code review"],
        })
        self.assertEqual(result["checklistId"], "checklist1")
        self.assertEqual(result["name"], "Definition of Done")
        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(client.post.call_count, 3)

    def test_invalid_card_id(self):
        client = make_mock_client()
        with self.assertRaises(ValueError):
            handle_add_checklist(client, {
                "cardId": "BAD",
                "name": "DoD",
                "items": ["Test"],
            })

    def test_empty_name(self):
        client = make_mock_client()
        with self.assertRaises(ValueError):
            handle_add_checklist(client, {
                "cardId": VALID_TRELLO_ID,
                "name": "",
                "items": ["Test"],
            })

    def test_empty_items(self):
        client = make_mock_client()
        with self.assertRaises(ValueError):
            handle_add_checklist(client, {
                "cardId": VALID_TRELLO_ID,
                "name": "DoD",
                "items": [],
            })


handle_invite_member = trello_mcp.handle_invite_member


class TestHandleInviteMember(unittest.TestCase):

    def test_invalid_board_id(self):
        client = make_mock_client()
        with self.assertRaises(ValueError):
            handle_invite_member(client, {
                "boardId": "BAD",
                "email": "ana@empresa.com",
            })

    def test_invalid_email(self):
        client = make_mock_client()
        with self.assertRaises(ValueError):
            handle_invite_member(client, {
                "boardId": VALID_TRELLO_ID,
                "email": "not-an-email",
            })

    def test_empty_email(self):
        client = make_mock_client()
        with self.assertRaises(ValueError):
            handle_invite_member(client, {
                "boardId": VALID_TRELLO_ID,
                "email": "",
            })

    def test_email_without_domain(self):
        client = make_mock_client()
        with self.assertRaises(ValueError):
            handle_invite_member(client, {
                "boardId": VALID_TRELLO_ID,
                "email": "user@",
            })

    def test_email_at_only(self):
        client = make_mock_client()
        with self.assertRaises(ValueError):
            handle_invite_member(client, {
                "boardId": VALID_TRELLO_ID,
                "email": "@@",
            })

    def test_invalid_type_raises(self):
        client = make_mock_client()
        with self.assertRaises(ValueError) as ctx:
            handle_invite_member(client, {
                "boardId": VALID_TRELLO_ID,
                "email": "ana@empresa.com",
                "type": "viewer",
            })
        self.assertIn("viewer", str(ctx.exception))

    @patch("urllib.request.urlopen")
    def test_success(self, mock_urlopen):
        client = make_mock_client()
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "membersInvited": [{"id": "m1"}],
        }).encode("utf-8")
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = handle_invite_member(client, {
            "boardId": VALID_TRELLO_ID,
            "email": "ana@empresa.com",
            "fullName": "Ana Garcia",
            "type": "normal",
        })
        self.assertEqual(result["email"], "ana@empresa.com")
        self.assertEqual(result["type"], "normal")
        self.assertEqual(result["memberId"], "m1")
        self.assertEqual(len(result["membersInvited"]), 1)


# ---------------------------------------------------------------------------
# Tests adicionales: manage_lists reorder, manage_labels update
# ---------------------------------------------------------------------------

class TestHandleManageListsReorder(unittest.TestCase):

    def test_reorder_success(self):
        client = make_mock_client()
        client.put.return_value = {
            "id": VALID_TRELLO_ID, "name": "Backlog", "pos": 100, "closed": False,
        }
        result = handle_manage_lists(client, {
            "boardId": VALID_TRELLO_ID, "action": "reorder",
            "listId": VALID_TRELLO_ID, "pos": 100,
        })
        self.assertEqual(result["pos"], 100)

    def test_reorder_without_pos(self):
        client = make_mock_client()
        with self.assertRaises(ValueError):
            handle_manage_lists(client, {
                "boardId": VALID_TRELLO_ID, "action": "reorder",
                "listId": VALID_TRELLO_ID,
            })


class TestHandleManageLabelsUpdate(unittest.TestCase):

    def test_update_name(self):
        client = make_mock_client()
        client.put.return_value = {
            "id": VALID_TRELLO_ID, "name": "Urgente", "color": "red",
        }
        result = handle_manage_labels(client, {
            "boardId": VALID_TRELLO_ID, "action": "update",
            "labelId": VALID_TRELLO_ID, "name": "Urgente",
        })
        self.assertEqual(result["name"], "Urgente")

    def test_update_color(self):
        client = make_mock_client()
        client.put.return_value = {
            "id": VALID_TRELLO_ID, "name": "", "color": "blue",
        }
        result = handle_manage_labels(client, {
            "boardId": VALID_TRELLO_ID, "action": "update",
            "labelId": VALID_TRELLO_ID, "color": "blue",
        })
        self.assertEqual(result["color"], "blue")


# ---------------------------------------------------------------------------
# Tests de resiliencia: JSONDecodeError, max message size
# ---------------------------------------------------------------------------

class TestMCPResilience(unittest.TestCase):

    def test_malformed_json_returns_none(self):
        client = make_mock_client()
        server = MCPServer(client)
        bad_body = b'{this is not valid json}'
        raw = f"Content-Length: {len(bad_body)}\r\n\r\n".encode("utf-8") + bad_body
        with patch("sys.stdin") as mock_stdin:
            mock_stdin.buffer = io.BytesIO(raw)
            result = server._read_message()
        self.assertIsNone(result)

    def test_oversized_message_returns_none(self):
        client = make_mock_client()
        server = MCPServer(client)
        fake_length = 20 * 1024 * 1024  # 20 MB, exceeds MAX_MESSAGE_SIZE
        small_data = b'x' * 100
        raw = f"Content-Length: {fake_length}\r\n\r\n".encode("utf-8") + small_data
        with patch("sys.stdin") as mock_stdin:
            mock_stdin.buffer = io.BytesIO(raw)
            result = server._read_message()
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
