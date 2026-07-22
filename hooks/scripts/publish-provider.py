#!/usr/bin/env python3
"""Deteccion y persistencia del proveedor de publicacion de PSPO Agent."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any


SUPPORTED_PROVIDERS = ("trello", "notion", "github", "local")

# Proveedores remotos en el orden de preferencia para deteccion y auto-seleccion.
REMOTE_PROVIDERS = ("trello", "notion", "github")


def _runtime_dir(cwd: str) -> str:
    return os.path.join(cwd, ".pspo-agent", "runtime")


def selection_file(cwd: str) -> str:
    return os.path.join(_runtime_dir(cwd), "publish-provider.json")


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


def _get_env(cwd: str, name: str) -> str:
    dotenv = _load_dotenv_values(cwd)
    return (os.environ.get(name) or dotenv.get(name) or "").strip()


def _valid_secret(value: str) -> bool:
    value = value.strip()
    if not value:
        return False
    if value.startswith("${") and value.endswith("}"):
        return False
    return True


def trello_credentials_ready(cwd: str) -> bool:
    return all(
        _valid_secret(_get_env(cwd, name))
        for name in ("TRELLO_API_KEY", "TRELLO_TOKEN")
    )


def trello_ready(cwd: str) -> bool:
    return trello_credentials_ready(cwd) and _valid_secret(_get_env(cwd, "TRELLO_BOARD_ID"))


def notion_credentials_ready(cwd: str) -> bool:
    return _valid_secret(_get_env(cwd, "NOTION_TOKEN"))


def notion_ready(cwd: str) -> bool:
    if not notion_credentials_ready(cwd):
        return False
    return any(
        _valid_secret(_get_env(cwd, name))
        for name in ("NOTION_PARENT_PAGE_ID", "NOTION_DATABASE_ID", "NOTION_PROJECT_PAGE_ID")
    )


def notion_targets_ready(cwd: str) -> bool:
    return any(
        _valid_secret(_get_env(cwd, name))
        for name in ("NOTION_DATABASE_ID", "NOTION_PROJECT_PAGE_ID")
    )


def github_targets_ready(cwd: str) -> bool:
    return any(
        _valid_secret(_get_env(cwd, name))
        for name in ("GITHUB_PROJECT_ID", "GITHUB_PROJECT_NUMBER")
    )


def github_credentials_ready(cwd: str) -> bool:
    """GitHub se considera configurado por señales de proyecto, no por el estado
    global de `gh` en la maquina.

    Cuenta como configurado si el proyecto tiene un token propio en `.env`
    (`GITHUB_TOKEN`/`GH_TOKEN`) o si ya tiene targets persistidos (creados vía
    `gh` durante el onboarding). Esto mantiene la deteccion determinista: la
    autenticacion global de `gh` la resuelve el fallback `github-fallback.py`
    y la superficie el `env-status` para que el onboarding pueda ofrecer GitHub.
    """
    if any(
        _valid_secret(_get_env(cwd, name))
        for name in ("GITHUB_TOKEN", "GH_TOKEN")
    ):
        return True
    return github_targets_ready(cwd)


def github_ready(cwd: str) -> bool:
    return github_credentials_ready(cwd) and github_targets_ready(cwd)


def _provider_details(cwd: str) -> dict[str, dict[str, bool]]:
    return {
        "trello": {
            "credentials_ready": trello_credentials_ready(cwd),
            "ready": trello_ready(cwd),
        },
        "notion": {
            "credentials_ready": notion_credentials_ready(cwd),
            "ready": notion_ready(cwd),
        },
        "github": {
            "credentials_ready": github_credentials_ready(cwd),
            "ready": github_ready(cwd),
        },
        "local": {
            "credentials_ready": True,
            "ready": True,
        },
    }


def _load_selection(cwd: str) -> dict[str, Any]:
    path = selection_file(cwd)
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def save_selection(cwd: str, provider: str, source: str = "user") -> str:
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Proveedor no soportado: {provider}")
    path = selection_file(cwd)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {
        "provider": provider,
        "source": source,
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return path


def clear_selection(cwd: str) -> None:
    try:
        os.remove(selection_file(cwd))
    except FileNotFoundError:
        pass


def compute_state(cwd: str) -> dict[str, Any]:
    details = _provider_details(cwd)
    configured_providers = [
        provider
        for provider in REMOTE_PROVIDERS
        if details[provider]["credentials_ready"]
    ]
    ready_providers = [
        provider
        for provider in REMOTE_PROVIDERS
        if details[provider]["ready"]
    ]

    selection = _load_selection(cwd)
    selected_provider = str(selection.get("provider") or "").strip().lower()
    selected_source = str(selection.get("source") or "").strip().lower()
    selected_valid = selected_provider in SUPPORTED_PROVIDERS

    publish_provider = ""
    provider_source = ""

    if selected_valid:
        if selected_provider == "local":
            publish_provider = "local"
            provider_source = selected_source or "runtime"
        elif selected_provider in configured_providers:
            publish_provider = selected_provider
            provider_source = selected_source or "runtime"

    if not publish_provider:
        if len(ready_providers) == 1:
            publish_provider = ready_providers[0]
            provider_source = "auto-ready"
        elif len(configured_providers) == 1:
            publish_provider = configured_providers[0]
            provider_source = "auto-configured"
        elif not configured_providers:
            publish_provider = "local"
            provider_source = "auto-local"

    return {
        "selection_file": selection_file(cwd),
        "supported_providers": list(SUPPORTED_PROVIDERS),
        "configured_providers": configured_providers,
        "ready_providers": ready_providers,
        "selected_provider": selected_provider if selected_valid else "",
        "selected_provider_source": selected_source if selected_valid else "",
        "publish_provider": publish_provider,
        "publish_provider_source": provider_source,
        "publish_provider_needs_choice": len(configured_providers) > 1 and not publish_provider,
        "trello_credentials_ready": details["trello"]["credentials_ready"],
        "trello_ready": details["trello"]["ready"],
        "notion_credentials_ready": details["notion"]["credentials_ready"],
        "notion_ready": details["notion"]["ready"],
        "notion_targets_ready": notion_targets_ready(cwd),
        "github_credentials_ready": details["github"]["credentials_ready"],
        "github_ready": details["github"]["ready"],
        "github_targets_ready": github_targets_ready(cwd),
        "local_ready": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cwd", nargs="?", default=os.getcwd())
    parser.add_argument("--field", dest="field")
    parser.add_argument("--select", dest="provider")
    parser.add_argument("--source", dest="source", default="user")
    parser.add_argument("--clear-selection", action="store_true")
    args = parser.parse_args()

    cwd = os.path.abspath(args.cwd)

    if args.clear_selection:
        clear_selection(cwd)
        return 0

    if args.provider:
        save_selection(cwd, args.provider.strip().lower(), source=args.source.strip().lower())

    state = compute_state(cwd)

    if args.field:
        value = state.get(args.field, "")
        if isinstance(value, bool):
            sys.stdout.write("1" if value else "0")
        elif isinstance(value, list):
            sys.stdout.write(",".join(str(item) for item in value))
        else:
            sys.stdout.write(str(value))
        return 0

    json.dump(state, sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
