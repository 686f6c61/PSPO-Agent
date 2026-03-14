"""
Test end-to-end del servidor MCP.

Arranca el servidor como subproceso, envia mensajes JSON-RPC reales
por stdin y lee las respuestas por stdout. Verifica el protocolo
completo: initialize -> tools/list -> tools/call.
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


class TestE2EProtocol(unittest.TestCase):

    def test_full_protocol_flow(self):
        proc = start_server()
        try:
            # 1. Initialize
            send_message(proc, {
                "jsonrpc": "2.0", "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test-e2e", "version": "1.0.0"},
                },
            })
            resp = read_message(proc)
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

            # 3. Tools list
            send_message(proc, {
                "jsonrpc": "2.0", "id": 2,
                "method": "tools/list", "params": {},
            })
            resp = read_message(proc)
            self.assertEqual(resp["id"], 2)
            tools = resp["result"]["tools"]
            self.assertEqual(len(tools), 10)
            tool_names = {t["name"] for t in tools}
            expected = {
                "verify-credentials", "list-boards", "get-board",
                "create-board", "manage-lists", "manage-labels",
                "create-cards", "search-cards", "add-checklist", "attach-file",
            }
            self.assertEqual(tool_names, expected)

            # 4. Cada herramienta tiene inputSchema
            for t in tools:
                self.assertIn("inputSchema", t)
                self.assertIn("type", t["inputSchema"])

            # 5. Ping
            send_message(proc, {
                "jsonrpc": "2.0", "id": 3,
                "method": "ping", "params": {},
            })
            resp = read_message(proc)
            self.assertEqual(resp["id"], 3)
            self.assertEqual(resp["result"], {})

            # 6. Unknown method -> error
            send_message(proc, {
                "jsonrpc": "2.0", "id": 4,
                "method": "invalid/method", "params": {},
            })
            resp = read_message(proc)
            self.assertEqual(resp["id"], 4)
            self.assertIn("error", resp)
            self.assertEqual(resp["error"]["code"], -32601)

            # 7. Tool call con ID invalido (path traversal)
            send_message(proc, {
                "jsonrpc": "2.0", "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "get-board",
                    "arguments": {"boardId": "../../../etc/passwd"},
                },
            })
            resp = read_message(proc)
            self.assertEqual(resp["id"], 5)
            self.assertTrue(resp["result"]["isError"])
            self.assertIn("formato valido", resp["result"]["content"][0]["text"])

            # 8. Tool call con herramienta inexistente
            send_message(proc, {
                "jsonrpc": "2.0", "id": 6,
                "method": "tools/call",
                "params": {"name": "herramienta-falsa", "arguments": {}},
            })
            resp = read_message(proc)
            self.assertTrue(resp["result"]["isError"])
            self.assertIn("no encontrada", resp["result"]["content"][0]["text"])

        finally:
            proc.stdin.close()
            proc.terminate()
            proc.wait(timeout=5)

    def test_utf8_multibyte(self):
        proc = start_server()
        try:
            # Initialize
            send_message(proc, {
                "jsonrpc": "2.0", "id": 1,
                "method": "initialize", "params": {},
            })
            read_message(proc)

            # Mensaje con caracteres multibyte (tildes, ene)
            send_message(proc, {
                "jsonrpc": "2.0", "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "search-cards",
                    "arguments": {
                        "boardId": "507f1f77bcf86cd799439011",
                        "query": "busqueda con tildes aeiou y ene",
                    },
                },
            })
            resp = read_message(proc)
            # Falla con 401 (credenciales falsas), pero el protocolo no se corrompe
            self.assertIsNotNone(resp, "Respuesta nula: el protocolo se corrompio con UTF-8")
            self.assertEqual(resp["id"], 2)

        finally:
            proc.stdin.close()
            proc.terminate()
            proc.wait(timeout=5)

    def test_multiple_rapid_messages(self):
        """Verifica que el servidor maneja multiples mensajes rapidos sin corromper."""
        proc = start_server()
        try:
            send_message(proc, {
                "jsonrpc": "2.0", "id": 1,
                "method": "initialize", "params": {},
            })
            read_message(proc)

            # Enviar 5 pings rapidos
            for i in range(2, 7):
                send_message(proc, {
                    "jsonrpc": "2.0", "id": i,
                    "method": "ping", "params": {},
                })

            # Leer las 5 respuestas
            for i in range(2, 7):
                resp = read_message(proc)
                self.assertIsNotNone(resp, f"Respuesta {i} nula")
                self.assertEqual(resp["id"], i)
                self.assertEqual(resp["result"], {})

        finally:
            proc.stdin.close()
            proc.terminate()
            proc.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
