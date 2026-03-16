#!/usr/bin/env python3
"""
Fallback oficial para Trello cuando el MCP `trello-client` no arranca.

Lee credenciales desde el `.env` del proyecto usando el mismo cargador que el
launcher del MCP y ejecuta exactamente los mismos handlers definidos en
`trello-mcp.py`, pero a traves de una CLI local y controlada.

Uso:
  python3 "$CLAUDE_PLUGIN_ROOT/servers/trello-fallback.py" verify-credentials
  python3 "$CLAUDE_PLUGIN_ROOT/servers/trello-fallback.py" create-board <<'JSON'
  {"name":"Proyecto - Backlog"}
  JSON
  python3 "$CLAUDE_PLUGIN_ROOT/servers/trello-fallback.py" save-board-id 1234567890abcdef
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar el modulo {module_name} desde {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _plugin_server_path(name: str) -> Path:
    return Path(__file__).with_name(name)


def _load_runtime_modules():
    launcher = _load_module(_plugin_server_path("trello-mcp-launcher.py"), "trello_mcp_launcher")
    mcp = _load_module(_plugin_server_path("trello-mcp.py"), "trello_mcp_server")
    return launcher, mcp


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fallback oficial y seguro para operaciones de Trello en PSPO Agent."
    )
    parser.add_argument("tool", help="Operacion a ejecutar (mismo nombre que la herramienta MCP).")
    parser.add_argument(
        "tool_arg",
        nargs="?",
        default=None,
        help="Argumento posicional opcional para helpers locales como save-board-id.",
    )
    parser.add_argument(
        "--args-json",
        default=None,
        help="Argumentos JSON inline. Si no se indica, se leen desde stdin como JSON.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Imprime el JSON formateado con indentacion.",
    )
    return parser.parse_args()


def _load_arguments(raw_inline: str | None) -> dict:
    raw = raw_inline
    if raw is None:
        raw = sys.stdin.read().strip()

    if not raw:
        return {}

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Los argumentos no contienen un JSON valido: {exc}") from exc

    if not isinstance(parsed, dict):
        raise ValueError("Los argumentos JSON deben ser un objeto.")

    file_path = parsed.get("filePath")
    if file_path and "content" not in parsed:
        file_on_disk = Path(str(file_path)).expanduser()
        parsed["content"] = file_on_disk.read_text(encoding="utf-8")
        parsed.setdefault("fileName", file_on_disk.name)

    return parsed


def _mask(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if len(value) <= 4:
        return "****"
    return f"****{value[-4:]}"


def _env_status() -> dict:
    return {
        "hasApiKey": bool(os.environ.get("TRELLO_API_KEY", "").strip()),
        "hasToken": bool(os.environ.get("TRELLO_TOKEN", "").strip()),
        "hasBoardId": bool(os.environ.get("TRELLO_BOARD_ID", "").strip()),
        "tokenCreated": os.environ.get("TRELLO_TOKEN_CREATED", "").strip(),
        "apiKeyMasked": _mask(os.environ.get("TRELLO_API_KEY", "")),
        "tokenMasked": _mask(os.environ.get("TRELLO_TOKEN", "")),
        "boardId": os.environ.get("TRELLO_BOARD_ID", "").strip(),
    }


def _project_env_path() -> Path:
    return Path.cwd() / ".env"


def _save_board_id(board_id: str) -> dict:
    board_id = (board_id or "").strip()
    if not board_id:
        raise ValueError("save-board-id requiere un board ID no vacio.")

    env_path = _project_env_path()
    lines: list[str] = []
    found = False

    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    updated_lines: list[str] = []
    for line in lines:
        if line.startswith("TRELLO_BOARD_ID="):
            updated_lines.append(f"TRELLO_BOARD_ID={board_id}")
            found = True
        else:
            updated_lines.append(line)

    if not found:
        if updated_lines and updated_lines[-1].strip():
            updated_lines.append("")
        updated_lines.append(f"TRELLO_BOARD_ID={board_id}")

    env_path.write_text("\n".join(updated_lines).rstrip() + "\n", encoding="utf-8")
    try:
        os.chmod(env_path, 0o600)
    except OSError:
        pass

    os.environ["TRELLO_BOARD_ID"] = board_id
    return {
        "saved": True,
        "boardId": board_id,
        "envPath": str(env_path),
    }


def main() -> int:
    args = _parse_args()

    try:
        launcher, mcp = _load_runtime_modules()
        launcher._load_project_env()
        tool_name = "create-cards" if args.tool == "create-card" else args.tool
        if args.tool == "env-status":
            result = _env_status()
        elif args.tool == "save-board-id":
            payload = _load_arguments(args.args_json)
            board_id = args.tool_arg or str(payload.get("boardId") or "")
            result = _save_board_id(board_id)
        else:
            client = mcp.TrelloClient(
                os.environ.get("TRELLO_API_KEY", ""),
                os.environ.get("TRELLO_TOKEN", ""),
            )
            tool = mcp.TOOL_MAP.get(tool_name)
            if tool is None:
                raise ValueError(f"Herramienta no soportada por el fallback oficial: {args.tool}")
            payload = _load_arguments(args.args_json)
            result = tool["handler"](client, payload)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.pretty:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
