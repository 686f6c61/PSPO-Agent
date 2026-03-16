#!/usr/bin/env python3
"""Bloquea el Stop prematuro durante /pspo-agent:autopilot."""

from __future__ import annotations

import importlib.util
import json
import os
import sys


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GUARD_PATH = os.path.join(SCRIPT_DIR, "autopilot-guard.py")


def _load_guard():
    spec = importlib.util.spec_from_file_location("autopilot_guard", GUARD_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _build_reason(state: dict[str, object]) -> str:
    phase = state.get("phase", "inactive")
    next_action = state.get("next_action", "")
    gate_status = str(state.get("gate_status", "") or "").strip().lower()
    branch_skill = str(state.get("branch_skill", "") or "").strip()
    next_review_skill = str(state.get("next_review_skill", "") or "").strip()
    next_plan_publish_skill = str(
        state.get("next_plan_publish_skill", "") or ""
    ).strip()

    if phase == "prepare-context":
        return (
            "Autopilot no puede detenerse todavia. La inbox existe pero aun no se ha "
            "materializado el contexto runtime.\n\n"
            f"Siguiente accion valida: {next_action}"
        )
    if phase == "delegate-product-phase":
        return (
            "Autopilot ya tiene `.pspo-agent/runtime/autopilot-context.md` y no debe "
            "terminar antes de lanzar la skill no interactiva de producto.\n\n"
            f"Siguiente accion valida: {next_action}"
        )
    if phase == "product-phase-active":
        return (
            "La fase de producto sigue activa y no puede cerrarse hasta dejar "
            "`docs/analisis-requisitos.md`, `docs/vision.md`, `docs/backlog.md`, "
            "`docs/historias/HU-*.md` y `docs/auditoria-hu.md` persistidos.\n\n"
            f"Siguiente accion valida: {next_action}"
        )
    if phase == "product-ready":
        if gate_status == "review" and not branch_skill:
            return (
                "La gate final ya esta resuelta en 'Revisar historias', pero aun no se "
                "ha abierto la skill hija.\n\n"
                f'Siguiente accion valida: Skill("{next_review_skill}")'
            )
        if gate_status == "plan-publish" and not branch_skill:
            return (
                "La gate final ya esta resuelta en 'Planificar y publicar', pero aun "
                "no se ha abierto la skill operacional correspondiente.\n\n"
                f'Siguiente accion valida: Skill("{next_plan_publish_skill}")'
            )
        return (
            "Autopilot ya dejo los artefactos listos, pero aun no ha abierto la "
            "gate final interactiva.\n\n"
            "Antes de detenerte debes usar AskUserQuestion con estas dos opciones:\n"
            '- "Revisar historias"\n'
            '- "Planificar y publicar"\n\n'
            "Formato valido:\n"
            "AskUserQuestion({questions:[{question:\"Autopilot ha terminado la fase de "
            "producto. Que quieres hacer ahora?\",header:\"Autopilot\",options:[{label:"
            "\"Revisar historias\",description:\"Abrir validacion antes de planificar o "
            "publicar.\"},{label:\"Planificar y publicar\",description:\"Usar CSV "
            "compatible si existe, planificar sprint y publicar en Trello con resumen + "
            "adjunto .md.\"}],multiSelect:false}]})\n\n"
            f"Siguiente accion valida: {next_action}"
        )
    return ""


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}

    cwd = os.path.abspath(data.get("cwd") or os.getcwd())
    guard = _load_guard()
    state = guard.compute_state(cwd, ensure_scaffold=True)
    phase = state.get("phase", "inactive")
    gate_status = str(state.get("gate_status", "") or "").strip().lower()
    branch_skill = str(state.get("branch_skill", "") or "").strip()

    if phase == "inactive":
        return 0
    if phase == "product-ready" and gate_status == "done":
        return 0
    if phase == "product-ready" and gate_status in {"review", "plan-publish"} and branch_skill:
        return 0

    reason = _build_reason(state)
    if not reason:
        return 0

    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
