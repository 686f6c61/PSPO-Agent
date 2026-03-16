#!/usr/bin/env python3
"""Persist the currently active PSPO skill for runtime guardrails."""

from __future__ import annotations

import json
import os
import stat
import textwrap
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
    trello_fallback_wrapper = os.path.join(runtime_dir, "trello-fallback.sh")
    notion_fallback_wrapper = os.path.join(runtime_dir, "notion-fallback.sh")
    publish_provider_wrapper = os.path.join(runtime_dir, "publish-provider.py")
    plugin_root = (os.environ.get("CLAUDE_PLUGIN_ROOT") or "").strip()

    with open(active_skill_file, "w", encoding="utf-8") as handle:
        handle.write(f"{skill_name}\n")

    if plugin_root:
        trello_wrapper_body = (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            f"python3 {json.dumps(os.path.join(plugin_root, 'servers', 'trello-fallback.py'))} \"$@\"\n"
        )
        with open(trello_fallback_wrapper, "w", encoding="utf-8") as handle:
            handle.write(trello_wrapper_body)
        current_mode = os.stat(trello_fallback_wrapper).st_mode
        os.chmod(trello_fallback_wrapper, current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        notion_wrapper_body = (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            f"python3 {json.dumps(os.path.join(plugin_root, 'servers', 'notion-fallback.py'))} \"$@\"\n"
        )
        with open(notion_fallback_wrapper, "w", encoding="utf-8") as handle:
            handle.write(notion_wrapper_body)
        current_mode = os.stat(notion_fallback_wrapper).st_mode
        os.chmod(notion_fallback_wrapper, current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        publish_provider_body = textwrap.dedent(
            f"""\
            #!/usr/bin/env python3
            import subprocess
            import sys

            raise SystemExit(
                subprocess.call(
                    ["python3", {json.dumps(os.path.join(plugin_root, 'hooks', 'scripts', 'publish-provider.py'))}, *sys.argv[1:]]
                )
            )
            """
        )
        with open(publish_provider_wrapper, "w", encoding="utf-8") as handle:
            handle.write(publish_provider_body)
        current_mode = os.stat(publish_provider_wrapper).st_mode
        os.chmod(publish_provider_wrapper, current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

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
