#!/usr/bin/env python3
"""Persist the currently active PSPO skill for runtime guardrails."""

from __future__ import annotations

import json
import os
import stat
import sys


def _clear_file(path: str) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    tool_input = payload.get("tool_input", {}) or {}
    skill_name = (
        tool_input.get("skill")
        or tool_input.get("name")
        or ""
    ).strip()
    cwd = os.path.abspath(payload.get("cwd") or os.getcwd())

    if not skill_name.startswith("pspo-agent:"):
        return 0

    runtime_dir = os.path.join(cwd, ".pspo-agent", "runtime")
    os.makedirs(runtime_dir, exist_ok=True)

    active_skill_file = os.path.join(runtime_dir, "active-skill.status")
    start_bootstrap_file = os.path.join(runtime_dir, "start-bootstrap.status")
    onboarding_bootstrap_file = os.path.join(runtime_dir, "onboarding-bootstrap.status")
    fallback_wrapper = os.path.join(runtime_dir, "trello-fallback.sh")
    plugin_root = (os.environ.get("CLAUDE_PLUGIN_ROOT") or "").strip()

    with open(active_skill_file, "w", encoding="utf-8") as handle:
        handle.write(f"{skill_name}\n")

    if plugin_root:
        wrapper_body = (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            f"python3 {json.dumps(os.path.join(plugin_root, 'servers', 'trello-fallback.py'))} \"$@\"\n"
        )
        with open(fallback_wrapper, "w", encoding="utf-8") as handle:
            handle.write(wrapper_body)
        current_mode = os.stat(fallback_wrapper).st_mode
        os.chmod(fallback_wrapper, current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    if skill_name == "pspo-agent:start":
        _clear_file(start_bootstrap_file)
    if skill_name == "pspo-agent:onboarding":
        _clear_file(onboarding_bootstrap_file)
    if skill_name != "pspo-agent:start":
        _clear_file(start_bootstrap_file)
    if skill_name != "pspo-agent:onboarding":
        _clear_file(onboarding_bootstrap_file)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
