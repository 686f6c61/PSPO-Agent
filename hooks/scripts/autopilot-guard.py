#!/usr/bin/env python3
"""Estado determinista del modo autopilot para los hooks de PSPO Agent."""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys


REQUIRED_TEAM_COLUMNS = {
    "nombre",
    "email",
    "rol",
    "categoria",
    "dedicacion",
    "usa_agente_ia",
}


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


def _load_dotenv_values(cwd: str) -> dict[str, str]:
    result: dict[str, str] = {}
    env_path = os.path.join(cwd, ".env")
    if not os.path.isfile(env_path):
        return result
    try:
        with open(env_path, encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                result[key.strip()] = value.strip()
    except OSError:
        return {}
    return result


def _valid_secret(value: str) -> bool:
    value = value.strip()
    if not value:
        return False
    if value.startswith("${") and value.endswith("}"):
        return False
    return True


def _trello_ready(cwd: str) -> bool:
    dotenv = _load_dotenv_values(cwd)

    def get(name: str) -> str:
        return (os.environ.get(name) or dotenv.get(name) or "").strip()

    return all(
        _valid_secret(get(name))
        for name in ("TRELLO_API_KEY", "TRELLO_TOKEN", "TRELLO_BOARD_ID")
    )


def _trello_credentials_ready(cwd: str) -> bool:
    dotenv = _load_dotenv_values(cwd)

    def get(name: str) -> str:
        return (os.environ.get(name) or dotenv.get(name) or "").strip()

    return all(_valid_secret(get(name)) for name in ("TRELLO_API_KEY", "TRELLO_TOKEN"))


def compute_state(cwd: str, ensure_scaffold: bool = False) -> dict[str, object]:
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

    if not product_ready:
        next_plan_publish_skill = ""
    elif not _trello_ready(cwd):
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
        "trello_credentials_ready": _trello_credentials_ready(cwd),
        "trello_ready": _trello_ready(cwd),
        "assignments_ready": os.path.isfile(assignments_file),
        "dependencies_ready": os.path.isfile(dependencies_file),
        "sprint_plan_ready": os.path.isfile(sprint_plan_file),
        "next_review_skill": "pspo-agent:validate" if product_ready else "",
        "next_plan_publish_skill": next_plan_publish_skill,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cwd", nargs="?", default=os.getcwd())
    parser.add_argument("--field", dest="field")
    parser.add_argument("--ensure-scaffold", action="store_true")
    args = parser.parse_args()

    state = compute_state(
        os.path.abspath(args.cwd),
        ensure_scaffold=args.ensure_scaffold,
    )
    if args.field:
        value = state.get(args.field, "")
        if isinstance(value, bool):
            sys.stdout.write("1" if value else "0")
        else:
            sys.stdout.write(str(value))
        return 0

    json.dump(state, sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
