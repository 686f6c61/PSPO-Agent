#!/usr/bin/env python3
"""Persiste la rama elegida en la gate final de /pspo-agent:autopilot."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from typing import Any


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GUARD_PATH = os.path.join(SCRIPT_DIR, "autopilot-guard.py")

FINAL_GATE_QUESTION = (
    "Autopilot ha terminado la fase de producto. Que quieres hacer ahora?"
)
REVIEW_LABEL = "revisar historias"
PLAN_LABEL = "planificar y publicar"


def _load_guard():
    spec = importlib.util.spec_from_file_location("autopilot_guard", GUARD_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _iter_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _iter_dicts(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_dicts(nested)


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


def _is_autopilot_gate_question(payload: dict[str, Any]) -> bool:
    tool_name = str(payload.get("tool_name") or "")
    if tool_name and tool_name != "AskUserQuestion":
        return False

    for item in _iter_dicts(payload.get("tool_input", {})):
        question = _normalize(str(item.get("question") or ""))
        header = _normalize(str(item.get("header") or ""))
        if question == _normalize(FINAL_GATE_QUESTION) and header == "autopilot":
            return True

    normalized_strings = {
        _normalize(text) for text in _iter_strings(payload.get("tool_input", {}))
    }
    return (
        _normalize(FINAL_GATE_QUESTION) in normalized_strings
        and "autopilot" in normalized_strings
    )


def _extract_answers(payload: dict[str, Any]) -> list[str]:
    collected: list[str] = []
    for item in _iter_dicts(payload):
        answers = item.get("answers")
        if answers is None:
            continue
        collected.extend(_normalize(text) for text in _iter_strings(answers))
    return collected


def _status_from_answers(payload: dict[str, Any]) -> str:
    for answer in _extract_answers(payload):
        if answer == REVIEW_LABEL:
            return "review"
        if answer == PLAN_LABEL:
            return "plan-publish"
    return ""


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    cwd = os.path.abspath(payload.get("cwd") or os.getcwd())
    guard = _load_guard()
    state = guard.compute_state(cwd, ensure_scaffold=True)

    if state.get("phase") != "product-ready":
        return 0
    if str(state.get("gate_status") or "").strip().lower() in {
        "review",
        "plan-publish",
        "done",
    }:
        return 0
    if not _is_autopilot_gate_question(payload):
        return 0

    new_status = _status_from_answers(payload)
    if not new_status:
        return 0

    gate_file = str(state.get("gate_file") or "")
    if not gate_file:
        return 0

    os.makedirs(os.path.dirname(gate_file), exist_ok=True)
    with open(gate_file, "w", encoding="utf-8") as handle:
        handle.write(f"{new_status}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
