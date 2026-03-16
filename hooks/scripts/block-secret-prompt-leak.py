#!/usr/bin/env python3
"""Bloquea prompts de Agent/Task que filtren secretos literales de Trello."""

from __future__ import annotations

import json
import re
import sys


HEX32_RE = re.compile(r"\b[a-f0-9]{32}\b", re.IGNORECASE)
TOKEN_RE = re.compile(r"\bATTA[a-zA-Z0-9]{20,}\b")
ASSIGNMENT_RE = re.compile(r"TRELLO_(API_KEY|TOKEN)\s*=\s*([^\s\"']+)")
QUERY_RE = re.compile(r"(?:^|[?&])(key|token)=([A-Za-z0-9]+)")


def _has_secret_literal(tool_input: object) -> bool:
    text = json.dumps(tool_input, ensure_ascii=False)

    for match in ASSIGNMENT_RE.finditer(text):
        value = match.group(2)
        if value.startswith("${") and value.endswith("}"):
            continue
        if match.group(1) == "API_KEY" and HEX32_RE.fullmatch(value):
            return True
        if match.group(1) == "TOKEN" and TOKEN_RE.fullmatch(value):
            return True

    if TOKEN_RE.search(text):
        return True

    for _, value in QUERY_RE.findall(text):
        if HEX32_RE.fullmatch(value) or TOKEN_RE.fullmatch(value):
            return True

    return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    tool_input = payload.get("tool_input") or {}
    if not _has_secret_literal(tool_input):
        return 0

    message = (
        "Nunca copies API keys ni tokens de Trello en prompts de Agent/Task. "
        "Pasa solo la ruta del fichero .env o describe la operacion a realizar; "
        "el agente publisher debe usar trello-client/MCP y no necesita secretos literales."
    )
    print(message, file=sys.stderr)
    print(message)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
