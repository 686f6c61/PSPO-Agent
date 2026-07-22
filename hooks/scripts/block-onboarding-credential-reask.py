#!/usr/bin/env python3
"""Bloquea volver a pedir API Key/Token cuando .env ya tiene credenciales validas."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from typing import Any


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GUARD_PATH = os.path.join(SCRIPT_DIR, "autopilot-guard.py")

CREDENTIAL_HINTS = (
    "api key",
    "token",
    "credenciales",
    "reintentar api key",
    "reintentar token",
)

TRELLO_HINTS = ("trello", "power-up")
BOARD_HINTS = (
    "tablero existente",
    "crear uno nuevo",
    "crear tablero nuevo",
    "crear un tablero nuevo",
    "cree uno nuevo",
    "usar uno existente",
    "usar un tablero",
    "que use un tablero",
    "prefieres que cree uno nuevo",
    "que tablero de trello quieres usar",
)


def _deny(message: str) -> None:
    """Emite la denegacion con el esquema vigente de PreToolUse."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }, ensure_ascii=False))


def _load_guard():
    spec = importlib.util.spec_from_file_location("autopilot_guard", GUARD_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _iter_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from _iter_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_strings(nested)


def _normalize(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _is_credential_reask(payload: dict[str, Any]) -> bool:
    tool_name = str(payload.get("tool_name") or "")
    if tool_name and tool_name != "AskUserQuestion":
        return False

    normalized = [_normalize(text) for text in _iter_strings(payload.get("tool_input", {}))]
    if not normalized:
        return False

    has_credential_hint = any(
        any(hint in text for hint in CREDENTIAL_HINTS) for text in normalized
    )
    has_trello_hint = any(any(hint in text for hint in TRELLO_HINTS) for text in normalized)
    return has_credential_hint and has_trello_hint


def _is_board_choice_question(payload: dict[str, Any]) -> bool:
    tool_name = str(payload.get("tool_name") or "")
    if tool_name and tool_name != "AskUserQuestion":
        return False

    normalized = [_normalize(text) for text in _iter_strings(payload.get("tool_input", {}))]
    if not normalized:
        return False

    has_board_hint = any(any(hint in text for hint in BOARD_HINTS) for text in normalized)
    has_header = any("tablero" in text for text in normalized)
    has_trello_board_question = any(
        "tablero" in text and "trello" in text for text in normalized
    )
    return (has_board_hint and has_header) or has_trello_board_question


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    cwd = os.path.abspath(payload.get("cwd") or os.getcwd())
    guard = _load_guard()
    state = guard.compute_state(cwd, ensure_scaffold=True)
    if _is_credential_reask(payload):
        if not bool(state.get("trello_credentials_ready")):
            return 0

        if bool(state.get("trello_ready")):
            message = (
                "Ya existen TRELLO_API_KEY, TRELLO_TOKEN y TRELLO_BOARD_ID validos en .env. "
                "No vuelvas a pedir credenciales. Verifica el tablero con get-board y muestra "
                "el resumen final."
            )
        else:
            message = (
                "Ya existen TRELLO_API_KEY y TRELLO_TOKEN validos en .env. No vuelvas a pedir "
                "API Key ni Token. Continua directamente con la configuracion de tablero: "
                "list-boards, seleccion interactiva o creacion de tablero nuevo, y guarda "
                "TRELLO_BOARD_ID."
            )
        _deny(message)
        return 0

    branch_skill = str(state.get("branch_skill") or "").strip()
    active_skill = str(state.get("active_skill") or "").strip()
    publish_provider = str(state.get("publish_provider") or "").strip()
    provider_needs_choice = bool(state.get("publish_provider_needs_choice"))
    notion_credentials_ready = bool(state.get("notion_credentials_ready"))
    notion_ready = bool(state.get("notion_ready"))
    notion_targets_ready = bool(state.get("notion_targets_ready"))
    if (
        _is_board_choice_question(payload)
        and bool(state.get("autopilot_active"))
        and branch_skill == "pspo-agent:onboarding"
        and not bool(state.get("trello_ready"))
    ):
        project_name = os.path.basename(cwd.rstrip(os.sep)) or "Proyecto"
        message = (
            "En modo autopilot no preguntes si usar un tablero existente o crear uno nuevo. "
            f"Crea automaticamente un tablero nuevo llamado '{project_name} - Backlog', "
            "configura las listas estandar (Backlog, Sprint activo, Bloqueada, En progreso, "
            "En revision, Hecho), crea las etiquetas de prioridad y guarda TRELLO_BOARD_ID."
        )
        _deny(message)
        return 0

    tool_name = str(payload.get("tool_name") or "")
    if (
        tool_name == "AskUserQuestion"
        and active_skill == "pspo-agent:onboarding"
        and publish_provider == "notion"
        and not provider_needs_choice
        and notion_credentials_ready
        and notion_ready
        and not notion_targets_ready
    ):
        message = (
            "En /pspo-agent:onboarding con Notion ya autenticado y pagina padre valida no preguntes "
            "si quieres crear la estructura o dejarla para mas tarde. Continua automaticamente con "
            "notion-fallback.sh verify-credentials, retrieve-page, create-project y save-project-targets."
        )
        _deny(message)
        return 0

    if (
        tool_name == "AskUserQuestion"
        and active_skill == "pspo-agent:onboarding"
        and publish_provider == "notion"
        and not provider_needs_choice
        and notion_credentials_ready
        and notion_ready
        and notion_targets_ready
    ):
        message = (
            "En /pspo-agent:onboarding con Notion ya configurado y destino creado no preguntes de nuevo. "
            "Continua automaticamente con notion-fallback.sh verify-credentials, "
            "retrieve-page, create-project y save-project-targets."
        )
        _deny(message)
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
