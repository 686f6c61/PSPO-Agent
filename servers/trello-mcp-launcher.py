#!/usr/bin/env python3
"""
Lanzador del servidor MCP de Trello.

Claude Code puede iniciar el MCP sin haber exportado las variables de entorno del
proyecto. Este wrapper carga TRELLO_API_KEY y TRELLO_TOKEN desde el `.env` del
repositorio activo antes de delegar en `trello-mcp.py`.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from datetime import datetime


ENV_KEYS = ("TRELLO_API_KEY", "TRELLO_TOKEN", "TRELLO_BOARD_ID", "TRELLO_TOKEN_CREATED")
DEBUG_LOG = Path("/tmp/pspo-agent-mcp-launcher.log")


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def _is_unset_env_value(value: str | None) -> bool:
    if value is None:
        return True
    value = value.strip()
    return not value or (value.startswith("${") and value.endswith("}"))


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        values[key] = _strip_quotes(value.strip())
    return values


def _debug_log(message: str) -> None:
    try:
        DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
        with DEBUG_LOG.open("a", encoding="utf-8") as handle:
            handle.write(f"{datetime.utcnow().isoformat()}Z {message}\n")
    except OSError:
        pass


def _load_project_env() -> None:
    cwd = Path.cwd().resolve()
    env_hints = []
    for name in ("CLAUDE_PROJECT_DIR", "CLAUDE_CWD", "PWD", "INIT_CWD"):
        value = os.environ.get(name, "").strip()
        if value:
            env_hints.append((name, value))

    candidates: list[Path] = []
    for _, value in env_hints:
        try:
            hint_path = Path(value).resolve()
        except OSError:
            continue
        candidates.extend([hint_path, *hint_path.parents])

    candidates.extend([cwd, *cwd.parents])

    seen: set[Path] = set()
    unique_candidates: list[Path] = []
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        unique_candidates.append(candidate)

    _debug_log(
        "launcher-start "
        f"cwd={cwd} "
        + " ".join(f"{name}={value}" for name, value in env_hints)
    )

    for candidate in unique_candidates:
        env_path = candidate / ".env"
        _debug_log(f"checking-env {env_path}")
        if not env_path.is_file():
            continue
        values = _parse_env_file(env_path)
        for key in ENV_KEYS:
            if values.get(key) and _is_unset_env_value(os.environ.get(key)):
                os.environ[key] = values[key]
        loaded_keys = [key for key in ENV_KEYS if os.environ.get(key)]
        _debug_log(f"loaded-env {env_path} keys={','.join(loaded_keys)}")
        break


def _load_server_main():
    server_path = Path(__file__).with_name("trello-mcp.py")
    spec = importlib.util.spec_from_file_location("trello_mcp_server", server_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar el servidor MCP desde {server_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main


def main() -> None:
    _load_project_env()
    server_main = _load_server_main()
    server_main()


if __name__ == "__main__":
    main()
