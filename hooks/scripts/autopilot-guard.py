#!/usr/bin/env python3
"""Estado determinista del modo autopilot para los hooks de PSPO Agent."""

from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import os
import shlex
import sys


# Campos que necesitan los envoltorios .sh. El modo --dump-shell los vuelca
# todos en una sola invocacion para que cada hook haga un unico eval en vez
# de reinvocar el guard (y reimportar modulos y releer .env) una vez por campo.
SHELL_DUMP_FIELDS = (
    "phase",
    "gate_status",
    "branch_skill",
    "branch_skill_file",
    "next_review_skill",
    "next_plan_publish_skill",
    "active_skill",
    "start_bootstrap",
    "start_bootstrap_file",
    "onboarding_bootstrap",
    "onboarding_bootstrap_file",
    "publish_provider",
    "publish_provider_needs_choice",
)


REQUIRED_TEAM_COLUMNS = {
    "nombre",
    "email",
    "rol",
    "categoria",
    "dedicacion",
    "usa_agente_ia",
}


def _load_provider_module():
    path = os.path.join(os.path.dirname(__file__), "publish-provider.py")
    spec = importlib.util.spec_from_file_location("publish_provider", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


PUBLISH_PROVIDER = _load_provider_module()


def _ensure_scaffold(cwd: str) -> None:
    os.makedirs(os.path.join(cwd, ".pspo-agent", "runtime"), exist_ok=True)
    os.makedirs(os.path.join(cwd, "docs", "historias"), exist_ok=True)


def _has_team_csv(cwd: str) -> bool:
    candidates = glob.glob(os.path.join(cwd, "*.csv"))
    candidates.extend(glob.glob(os.path.join(cwd, ".pspo-agent", "inbox", "*.csv")))
    for path in candidates:
        try:
            with open(path, encoding="utf-8") as handle:
                header = handle.readline().strip().lower()
        except OSError:
            continue
        columns = {value.strip() for value in header.split(",") if value.strip()}
        if REQUIRED_TEAM_COLUMNS.issubset(columns):
            return True
    return False


def _trello_ready(cwd: str) -> bool:
    return bool(PUBLISH_PROVIDER.trello_ready(cwd))


def _trello_credentials_ready(cwd: str) -> bool:
    return bool(PUBLISH_PROVIDER.trello_credentials_ready(cwd))


def compute_state(cwd: str, ensure_scaffold: bool = False) -> dict[str, object]:
    provider_state = PUBLISH_PROVIDER.compute_state(cwd)
    runtime_dir = os.path.join(cwd, ".pspo-agent", "runtime")
    inbox_dir = os.path.join(cwd, ".pspo-agent", "inbox")
    context_file = os.path.join(runtime_dir, "autopilot-context.md")
    status_file = os.path.join(runtime_dir, "product-phase.status")
    gate_file = os.path.join(runtime_dir, "final-gate.status")
    branch_skill_file = os.path.join(runtime_dir, "autopilot-branch-skill.status")
    active_skill_file = os.path.join(runtime_dir, "active-skill.status")
    start_bootstrap_file = os.path.join(runtime_dir, "start-bootstrap.status")
    onboarding_bootstrap_file = os.path.join(runtime_dir, "onboarding-bootstrap.status")

    analysis_file = os.path.join(cwd, "docs", "analisis-requisitos.md")
    backlog_file = os.path.join(cwd, "docs", "backlog.md")
    audit_file = os.path.join(cwd, "docs", "auditoria-hu.md")
    stories = glob.glob(os.path.join(cwd, "docs", "historias", "HU-*.md"))
    assignments_file = os.path.join(cwd, "docs", "asignaciones.md")
    dependencies_file = os.path.join(cwd, "docs", "dependencias.md")
    sprint_plan_file = os.path.join(cwd, "docs", "sprint-plan.md")

    inbox_exists = os.path.isdir(inbox_dir)
    context_exists = os.path.isfile(context_file)
    runtime_reentry_exists = any(
        os.path.isfile(path)
        for path in (status_file, gate_file, branch_skill_file)
    )
    autopilot_active = inbox_exists or context_exists or runtime_reentry_exists

    if ensure_scaffold and autopilot_active:
        _ensure_scaffold(cwd)

    marker_value = ""
    if os.path.isfile(status_file):
        try:
            with open(status_file, encoding="utf-8") as handle:
                marker_value = handle.read().strip().lower()
        except OSError:
            marker_value = ""

    gate_value = ""
    if os.path.isfile(gate_file):
        try:
            with open(gate_file, encoding="utf-8") as handle:
                gate_value = handle.read().strip().lower()
        except OSError:
            gate_value = ""

    branch_skill_value = ""
    if os.path.isfile(branch_skill_file):
        try:
            with open(branch_skill_file, encoding="utf-8") as handle:
                branch_skill_value = handle.read().strip()
        except OSError:
            branch_skill_value = ""

    active_skill_value = ""
    if os.path.isfile(active_skill_file):
        try:
            with open(active_skill_file, encoding="utf-8") as handle:
                active_skill_value = handle.read().strip()
        except OSError:
            active_skill_value = ""

    start_bootstrap_value = ""
    if os.path.isfile(start_bootstrap_file):
        try:
            with open(start_bootstrap_file, encoding="utf-8") as handle:
                start_bootstrap_value = handle.read().strip().lower()
        except OSError:
            start_bootstrap_value = ""

    onboarding_bootstrap_value = ""
    if os.path.isfile(onboarding_bootstrap_file):
        try:
            with open(onboarding_bootstrap_file, encoding="utf-8") as handle:
                onboarding_bootstrap_value = handle.read().strip().lower()
        except OSError:
            onboarding_bootstrap_value = ""

    product_ready = (
        os.path.isfile(analysis_file)
        and os.path.isfile(backlog_file)
        and os.path.isfile(audit_file)
        and bool(stories)
    )
    if not autopilot_active:
        phase = "inactive"
    elif marker_value == "active":
        phase = "product-phase-active"
    elif product_ready:
        phase = "product-ready"
    elif context_exists or runtime_reentry_exists:
        phase = "delegate-product-phase"
    else:
        phase = "prepare-context"

    next_action = {
        "inactive": "",
        "prepare-context": 'Glob(".pspo-agent/inbox/*")',
        "delegate-product-phase": 'Skill("pspo-agent:product-phase")',
        "product-phase-active": "Completar la persistencia de docs/ antes de detenerse",
        "product-ready": 'AskUserQuestion("Revisar historias" | "Planificar y publicar")',
    }[phase]

    publish_provider = str(provider_state.get("publish_provider") or "").strip()
    provider_needs_choice = bool(provider_state.get("publish_provider_needs_choice"))

    if not product_ready:
        next_plan_publish_skill = ""
    elif provider_needs_choice:
        next_plan_publish_skill = "pspo-agent:onboarding"
    elif publish_provider == "trello" and not _trello_ready(cwd):
        next_plan_publish_skill = "pspo-agent:onboarding"
    elif publish_provider == "notion" and not bool(provider_state.get("notion_ready")):
        next_plan_publish_skill = "pspo-agent:onboarding"
    elif publish_provider == "github" and not bool(provider_state.get("github_ready")):
        next_plan_publish_skill = "pspo-agent:onboarding"
    elif not _has_team_csv(cwd):
        next_plan_publish_skill = "pspo-agent:team"
    elif not os.path.isfile(assignments_file):
        next_plan_publish_skill = "pspo-agent:assign"
    elif not os.path.isfile(dependencies_file):
        next_plan_publish_skill = "pspo-agent:dependencies"
    elif not os.path.isfile(sprint_plan_file):
        next_plan_publish_skill = "pspo-agent:sprint-plan"
    else:
        next_plan_publish_skill = "pspo-agent:publish"

    return {
        "cwd": cwd,
        "autopilot_active": autopilot_active,
        "phase": phase,
        "next_action": next_action,
        "inbox_dir": inbox_dir,
        "context_file": context_file,
        "status_file": status_file,
        "status_value": marker_value,
        "gate_file": gate_file,
        "gate_status": gate_value,
        "branch_skill_file": branch_skill_file,
        "branch_skill": branch_skill_value,
        "active_skill_file": active_skill_file,
        "active_skill": active_skill_value,
        "start_bootstrap_file": start_bootstrap_file,
        "start_bootstrap": start_bootstrap_value,
        "onboarding_bootstrap_file": onboarding_bootstrap_file,
        "onboarding_bootstrap": onboarding_bootstrap_value,
        "analysis_ready": os.path.isfile(analysis_file),
        "backlog_ready": os.path.isfile(backlog_file),
        "audit_ready": os.path.isfile(audit_file),
        "stories_ready": bool(stories),
        "story_count": len(stories),
        "product_ready": product_ready,
        "has_team_csv": _has_team_csv(cwd),
        "publish_provider_file": provider_state["selection_file"],
        "selected_publish_provider": provider_state["selected_provider"],
        "selected_publish_provider_source": provider_state["selected_provider_source"],
        "publish_provider": publish_provider,
        "publish_provider_source": provider_state["publish_provider_source"],
        "configured_publish_providers": provider_state["configured_providers"],
        "ready_publish_providers": provider_state["ready_providers"],
        "publish_provider_needs_choice": provider_needs_choice,
        "trello_credentials_ready": _trello_credentials_ready(cwd),
        "trello_ready": _trello_ready(cwd),
        "notion_credentials_ready": bool(provider_state["notion_credentials_ready"]),
        "notion_ready": bool(provider_state["notion_ready"]),
        "notion_targets_ready": bool(provider_state.get("notion_targets_ready")),
        "github_credentials_ready": bool(provider_state.get("github_credentials_ready")),
        "github_ready": bool(provider_state.get("github_ready")),
        "github_targets_ready": bool(provider_state.get("github_targets_ready")),
        "assignments_ready": os.path.isfile(assignments_file),
        "dependencies_ready": os.path.isfile(dependencies_file),
        "sprint_plan_ready": os.path.isfile(sprint_plan_file),
        "next_review_skill": "pspo-agent:validate" if product_ready else "",
        "next_plan_publish_skill": next_plan_publish_skill,
    }


def _format_field(value: object) -> str:
    """Serializa un campo del estado igual que hace el modo --field."""
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)


def _dump_shell(state: dict[str, object]) -> None:
    """Vuelca los campos de SHELL_DUMP_FIELDS como asignaciones de shell.

    Cada valor se protege con shlex.quote para que el consumidor haga un
    unico `eval` seguro y disponga de todas las variables sin reinvocar
    el guard campo a campo.
    """
    for field in SHELL_DUMP_FIELDS:
        rendered = _format_field(state.get(field, ""))
        sys.stdout.write(f"{field}={shlex.quote(rendered)}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cwd", nargs="?", default=os.getcwd())
    parser.add_argument("--field", dest="field")
    parser.add_argument("--dump-shell", action="store_true")
    parser.add_argument("--ensure-scaffold", action="store_true")
    args = parser.parse_args()

    state = compute_state(
        os.path.abspath(args.cwd),
        ensure_scaffold=args.ensure_scaffold,
    )
    if args.dump_shell:
        _dump_shell(state)
        return 0

    if args.field:
        sys.stdout.write(_format_field(state.get(args.field, "")))
        return 0

    json.dump(state, sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
