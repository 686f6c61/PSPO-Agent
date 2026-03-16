#!/usr/bin/env python3
"""
Fallback oficial y controlado para operaciones de Notion en PSPO Agent.

Esta primera version cubre:
- verificacion de credenciales
- inspeccion segura del entorno
- lectura de pagina/database
- listado de usuarios visibles por la integracion
- creacion zero-template de proyecto + HU-00 + backlog
- creacion de paginas de HU dentro del backlog

Todo sin dependencias externas y leyendo credenciales desde `.env`.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.request
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


DEFAULT_NOTION_VERSION = "2026-03-11"


def _project_env_path() -> Path:
    return Path.cwd() / ".env"


def _load_project_env() -> None:
    env_path = _project_env_path()
    if not env_path.is_file():
        return
    try:
        with env_path.open(encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if not os.environ.get(key):
                    os.environ[key] = value
    except OSError:
        return


def _save_env_values(values: dict[str, str]) -> dict[str, Any]:
    env_path = _project_env_path()
    lines: list[str] = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    remaining = {key: str(value).strip() for key, value in values.items() if str(value).strip()}
    updated_lines: list[str] = []
    seen: set[str] = set()
    for line in lines:
        if "=" not in line or line.lstrip().startswith("#"):
            updated_lines.append(line)
            continue
        key, _ = line.split("=", 1)
        key = key.strip()
        if key in remaining:
            updated_lines.append(f"{key}={remaining[key]}")
            seen.add(key)
        else:
            updated_lines.append(line)

    for key, value in remaining.items():
        if key in seen:
            continue
        if updated_lines and updated_lines[-1].strip():
            updated_lines.append("")
        updated_lines.append(f"{key}={value}")

    env_path.write_text("\n".join(updated_lines).rstrip() + "\n", encoding="utf-8")
    try:
        os.chmod(env_path, 0o600)
    except OSError:
        pass
    for key, value in remaining.items():
        os.environ[key] = value
    return {
        "saved": True,
        "envPath": str(env_path),
        "keys": sorted(remaining.keys()),
    }


def _mask(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if len(value) <= 4:
        return "****"
    return f"****{value[-4:]}"


def _normalize_id(value: str, field_name: str) -> str:
    raw = (value or "").strip()
    if not raw:
        raise ValueError(f"{field_name} es obligatorio.")
    raw = raw.replace("-", "")
    if not re.fullmatch(r"[0-9a-fA-F]{32}", raw):
        raise ValueError(f"{field_name} debe ser un UUID de Notion valido.")
    return (
        f"{raw[0:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:32]}"
    ).lower()


def _default_project_name() -> str:
    raw = (
        (os.environ.get("PSPO_PROJECT_NAME") or "").strip()
        or Path.cwd().name.strip()
    )
    if not raw:
        return "Proyecto PSPO Agent"

    normalized = re.sub(r"[-_]+", " ", raw).strip()
    normalized = re.sub(r"\b(pspo|tmp|temp|notion|onb\d+)\b", " ", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\b[a-z0-9]{6,}\b$", " ", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\s{2,}", " ", normalized).strip(" -_")
    return normalized or "Proyecto PSPO Agent"


def _env_status() -> dict[str, Any]:
    return {
        "hasNotionToken": bool(os.environ.get("NOTION_TOKEN", "").strip()),
        "hasParentPageId": bool(os.environ.get("NOTION_PARENT_PAGE_ID", "").strip()),
        "hasDatabaseId": bool(os.environ.get("NOTION_DATABASE_ID", "").strip()),
        "hasProjectPageId": bool(os.environ.get("NOTION_PROJECT_PAGE_ID", "").strip()),
        "hasVisionPageId": bool(os.environ.get("NOTION_VISION_PAGE_ID", "").strip()),
        "tokenMasked": _mask(os.environ.get("NOTION_TOKEN", "")),
        "parentPageId": os.environ.get("NOTION_PARENT_PAGE_ID", "").strip(),
        "databaseId": os.environ.get("NOTION_DATABASE_ID", "").strip(),
        "projectPageId": os.environ.get("NOTION_PROJECT_PAGE_ID", "").strip(),
        "visionPageId": os.environ.get("NOTION_VISION_PAGE_ID", "").strip(),
        "apiVersion": os.environ.get("NOTION_API_VERSION", DEFAULT_NOTION_VERSION).strip() or DEFAULT_NOTION_VERSION,
    }


def help_info(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "provider": "notion",
        "supportedTools": [
            "list-tools",
            "env-status",
            "verify-credentials",
            "retrieve-page",
            "retrieve-database",
            "retrieve-data-source",
            "update-data-source",
            "ensure-dependency-relations",
            "list-users",
            "resolve-user-by-email",
            "setup-targets",
            "create-project",
            "sync-vision-from-markdown",
            "parse-story-markdown",
            "query-story-pages",
            "find-story-page",
            "create-story-page",
            "update-story-page",
            "sync-story-from-markdown",
            "set-story-dependencies",
            "sync-story-dependencies-from-markdown",
            "sync-stories-from-folder",
            "save-project-targets",
            "create-file-upload",
            "send-file-upload",
            "attach-file-to-page-property",
            "append-file-block",
            "upload-and-attach-markdown",
        ],
        "onboardingSequence": [
            ".pspo-agent/runtime/notion-fallback.sh env-status --pretty",
            ".pspo-agent/runtime/notion-fallback.sh verify-credentials --pretty",
            ".pspo-agent/runtime/notion-fallback.sh retrieve-page <NOTION_PARENT_PAGE_ID> --pretty",
            ".pspo-agent/runtime/notion-fallback.sh setup-targets --pretty",
            ".pspo-agent/runtime/notion-fallback.sh create-project --pretty",
            ".pspo-agent/runtime/notion-fallback.sh ensure-dependency-relations --pretty",
            ".pspo-agent/runtime/notion-fallback.sh save-project-targets --pretty",
        ],
        "publishSequence": [
            "sync-vision-from-markdown",
            "parse-story-markdown",
            "sync-story-from-markdown",
            "sync-story-dependencies-from-markdown",
            "sync-stories-from-folder",
            "resolve-user-by-email",
        ],
        "notes": [
            "No inspecciones .env ni el repo con grep/find/sed durante onboarding.",
            "Usa los wrappers oficiales y pasa JSON por --args-json o stdin cuando aplique.",
        ],
    }


def save_project_targets(args: dict[str, Any]) -> dict[str, Any]:
    values = {
        "NOTION_PARENT_PAGE_ID": args.get("parentPageId") or os.environ.get("NOTION_PARENT_PAGE_ID", ""),
        "NOTION_PROJECT_PAGE_ID": args.get("projectPageId") or "",
        "NOTION_VISION_PAGE_ID": args.get("visionPageId") or "",
        "NOTION_DATABASE_ID": args.get("databaseId") or "",
    }
    return _save_env_values(values)


def setup_targets(args: dict[str, Any]) -> dict[str, Any]:
    project = create_project(args)
    saved = save_project_targets({
        "parentPageId": args.get("parentPageId") or os.environ.get("NOTION_PARENT_PAGE_ID", ""),
        "projectPageId": project.get("projectPageId") or "",
        "visionPageId": project.get("visionPageId") or "",
        "databaseId": project.get("databaseId") or "",
    })
    return {
        "ok": True,
        "provider": "notion",
        "projectPageId": project.get("projectPageId"),
        "visionPageId": project.get("visionPageId"),
        "databaseId": project.get("databaseId"),
        "dataSourceId": project.get("dataSourceId"),
        "projectUrl": project.get("projectUrl"),
        "visionUrl": project.get("visionUrl"),
        "savedEnvPath": saved.get("envPath"),
        "savedKeys": saved.get("keys"),
    }


def _headers(*, content_type: str = "application/json") -> dict[str, str]:
    token = (os.environ.get("NOTION_TOKEN") or "").strip()
    if not token:
        raise ValueError("NOTION_TOKEN no esta configurado.")
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": os.environ.get("NOTION_API_VERSION", DEFAULT_NOTION_VERSION).strip() or DEFAULT_NOTION_VERSION,
    }
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def _request_json(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.notion.com{path}",
        data=data,
        headers=_headers(),
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {"message": body or str(exc)}
        raise RuntimeError(
            f"Notion API {exc.code}: {payload.get('message') or payload.get('code') or body}"
        ) from exc


def _request_raw(
    method: str,
    url: str,
    *,
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=data,
        headers=headers or _headers(content_type=""),
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {"message": body or str(exc)}
        raise RuntimeError(
            f"Notion API {exc.code}: {payload.get('message') or payload.get('code') or body}"
        ) from exc


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fallback oficial y seguro para operaciones de Notion en PSPO Agent."
    )
    parser.add_argument("tool", help="Operacion a ejecutar.")
    parser.add_argument(
        "tool_arg",
        nargs="?",
        default=None,
        help="Argumento posicional opcional para helpers como retrieve-page.",
    )
    parser.add_argument("--args-json", default=None)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--parent-page-id", default=None)
    parser.add_argument("--project-page-id", default=None)
    parser.add_argument("--database-id", default=None)
    parser.add_argument("--project-name", default=None)
    parser.add_argument("--project-title", default=None)
    parser.add_argument("--vision-title", default=None)
    parser.add_argument("--database-title", default=None)
    return parser.parse_args()


def _load_arguments(raw_inline: str | None) -> dict[str, Any]:
    raw = raw_inline
    if raw is None:
        raw = sys.stdin.read().strip()
    if not raw:
        return {}
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("Los argumentos JSON deben ser un objeto.")
    return parsed


def _title(value: str) -> list[dict[str, Any]]:
    return [{"type": "text", "text": {"content": value}}]


def _rich_text(value: str) -> list[dict[str, Any]]:
    return [{"type": "text", "text": {"content": value}}] if value else []


def _coerce_number(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("estimateHours es obligatorio.")
    match = re.search(r"-?\d+(?:[.,]\d+)?", raw)
    if not match:
        raise ValueError(f"No se pudo interpretar la estimacion numerica: {raw}")
    return float(match.group(0).replace(",", "."))


def _normalize_label(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or "").strip())
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s{2,}", " ", normalized).strip()


def _paragraph_block(text: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": _rich_text(text)},
    }


def _heading_block(level: int, text: str) -> dict[str, Any]:
    key = f"heading_{level}"
    return {
        "object": "block",
        "type": key,
        key: {"rich_text": _rich_text(text)},
    }


def _code_block(text: str, language: str = "markdown") -> dict[str, Any]:
    return {
        "object": "block",
        "type": "code",
        "code": {
            "rich_text": _rich_text(text),
            "language": language,
        },
    }


def _bulleted_block(text: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": _rich_text(text)},
    }


def _file_block(file_upload_id: str, caption: str = "") -> dict[str, Any]:
    return {
        "object": "block",
        "type": "file",
        "file": {
            "type": "file_upload",
            "file_upload": {"id": _normalize_id(file_upload_id, "fileUploadId")},
            "caption": _rich_text(caption),
        },
    }


def markdown_to_blocks(markdown: str) -> list[dict[str, Any]]:
    lines = [line.rstrip() for line in (markdown or "").splitlines()]
    blocks: list[dict[str, Any]] = []
    code_lines: list[str] = []
    code_language = "markdown"
    in_code = False

    for line in lines:
        if line.startswith("```"):
            if in_code:
                blocks.append(_code_block("\n".join(code_lines).strip(), code_language))
                code_lines = []
                code_language = "markdown"
                in_code = False
            else:
                in_code = True
                code_language = (line[3:].strip() or "markdown")
            continue

        if in_code:
            code_lines.append(line)
            continue

        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# "):
            blocks.append(_heading_block(1, stripped[2:].strip()))
        elif stripped.startswith("## "):
            blocks.append(_heading_block(2, stripped[3:].strip()))
        elif stripped.startswith("### "):
            blocks.append(_heading_block(3, stripped[4:].strip()))
        elif stripped.startswith("- "):
            blocks.append(_bulleted_block(stripped[2:].strip()))
        else:
            blocks.append(_paragraph_block(stripped))

    if in_code and code_lines:
        blocks.append(_code_block("\n".join(code_lines).strip(), code_language))

    return blocks[:100]


def _read_markdown_file(file_path: str) -> str:
    path = Path(file_path).expanduser()
    if not path.is_file():
        raise ValueError(f"No existe el fichero: {path}")
    return path.read_text(encoding="utf-8")


def _extract_section(markdown: str, heading: str) -> str:
    pattern = rf"(?ms)^##\s+{re.escape(heading)}\s*\n+(.*?)(?=^##\s+|\Z)"
    match = re.search(pattern, markdown)
    return match.group(1).strip() if match else ""


def _parse_metadata_table(markdown: str) -> dict[str, str]:
    lines = markdown.splitlines()
    rows: dict[str, str] = {}
    in_table = False
    for raw_line in lines:
        line = raw_line.rstrip()
        if not in_table:
            if _normalize_label(line) == "campo valor":
                in_table = True
            continue
        if not line.strip():
            break
        if not line.strip().startswith("|"):
            break
        if re.fullmatch(r"\|\s*-+\s*\|\s*-+\s*\|", line.strip()):
            continue
        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(parts) < 2:
            continue
        key = _normalize_label(parts[0])
        value = parts[1].strip()
        if key and value:
            rows[key] = value
    return rows


def parse_story_markdown(args: dict[str, Any]) -> dict[str, Any]:
    file_path = str(args.get("filePath") or "").strip()
    if not file_path:
        raise ValueError("filePath es obligatorio.")
    markdown = _read_markdown_file(file_path)
    title_line_match = re.search(r"(?m)^#\s+(.+)$", markdown)
    title_line = title_line_match.group(1).strip() if title_line_match else Path(file_path).stem
    story_match = re.match(r"(?P<id>HU-\d+)\s*[·:-]\s*(?P<title>.+)$", title_line)
    metadata = _parse_metadata_table(markdown)
    story_id = str(metadata.get("id") or (story_match.group("id") if story_match else "")).strip()
    title = story_match.group("title").strip() if story_match else title_line
    summary = _extract_section(markdown, "Resumen")
    if not summary:
        summary = _extract_section(markdown, "Objetivo")
    parsed = {
        "ok": True,
        "filePath": str(Path(file_path).expanduser()),
        "markdown": markdown,
        "storyId": story_id,
        "title": title,
        "fullTitle": f"{story_id} · {title}".strip(" ·") if story_id else title,
        "summary": summary,
        "priority": metadata.get("prioridad", ""),
        "estimation": metadata.get("estimacion", ""),
        "sprint": metadata.get("sprint", ""),
        "assignedEmail": metadata.get("asignado a", ""),
        "dependenciesText": metadata.get("dependencias", ""),
        "metadata": metadata,
    }
    parsed["dependencyStoryIds"] = _parse_story_ids(parsed["dependenciesText"])
    return parsed


def _list_block_children(block_id: str) -> list[dict[str, Any]]:
    normalized_block_id = _normalize_id(block_id, "blockId")
    results: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        suffix = f"?page_size=100{f'&start_cursor={cursor}' if cursor else ''}"
        payload = _request_json("GET", f"/v1/blocks/{normalized_block_id}/children{suffix}")
        batch = payload.get("results") or []
        if isinstance(batch, list):
            results.extend(item for item in batch if isinstance(item, dict))
        if not payload.get("has_more"):
            break
        cursor = str(payload.get("next_cursor") or "").strip() or None
        if not cursor:
            break
    return results


def _delete_block(block_id: str) -> dict[str, Any]:
    normalized_block_id = _normalize_id(block_id, "blockId")
    return _request_json("DELETE", f"/v1/blocks/{normalized_block_id}")


def _append_block_children(block_id: str, children: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized_block_id = _normalize_id(block_id, "blockId")
    appended: list[dict[str, Any]] = []
    for start in range(0, len(children), 100):
        chunk = children[start:start + 100]
        if not chunk:
            continue
        response = _request_json("PATCH", f"/v1/blocks/{normalized_block_id}/children", {
            "children": chunk,
        })
        batch = response.get("results") or []
        if isinstance(batch, list):
            appended.extend(item for item in batch if isinstance(item, dict))
    return appended


def _replace_page_body(page_id: str, markdown: str) -> dict[str, Any]:
    normalized_page_id = _normalize_id(page_id, "pageId")
    children = _list_block_children(normalized_page_id)
    deleted: list[str] = []
    for child in children:
        child_id = str(child.get("id") or "").strip()
        if not child_id:
            continue
        _delete_block(child_id)
        deleted.append(child_id)
    appended = _append_block_children(normalized_page_id, markdown_to_blocks(markdown)) if markdown else []
    return {
        "ok": True,
        "pageId": normalized_page_id,
        "deletedBlockIds": deleted,
        "appendedBlockCount": len(appended),
    }


def verify_credentials(_: dict[str, Any]) -> dict[str, Any]:
    payload = _request_json("GET", "/v1/users/me")
    return {
        "ok": True,
        "botUserId": payload.get("id"),
        "type": payload.get("type"),
        "name": payload.get("name"),
        "workspaceName": (
            payload.get("bot", {}).get("workspace_name")
            if isinstance(payload.get("bot"), dict)
            else ""
        ),
    }


def retrieve_page(args: dict[str, Any]) -> dict[str, Any]:
    page_id = _normalize_id(args.get("pageId") or "", "pageId")
    return _request_json("GET", f"/v1/pages/{page_id}")


def retrieve_database(args: dict[str, Any]) -> dict[str, Any]:
    database_id = _normalize_id(args.get("databaseId") or "", "databaseId")
    return _request_json("GET", f"/v1/databases/{database_id}")


def retrieve_data_source(args: dict[str, Any]) -> dict[str, Any]:
    data_source_id = _normalize_id(args.get("dataSourceId") or "", "dataSourceId")
    return _request_json("GET", f"/v1/data_sources/{data_source_id}")


def update_data_source(args: dict[str, Any]) -> dict[str, Any]:
    data_source_id = _normalize_id(args.get("dataSourceId") or "", "dataSourceId")
    properties = args.get("properties")
    if not isinstance(properties, dict) or not properties:
        raise ValueError("properties es obligatorio para update-data-source.")
    return _request_json("PATCH", f"/v1/data_sources/{data_source_id}", {"properties": properties})


def _resolve_data_source_id(args: dict[str, Any]) -> str:
    raw_data_source_id = str(args.get("dataSourceId") or "").strip()
    if not raw_data_source_id:
        raw_data_source_id = str(os.environ.get("NOTION_DATA_SOURCE_ID") or "").strip()
    if raw_data_source_id:
        return _normalize_id(raw_data_source_id, "dataSourceId")

    raw_database_id = str(args.get("databaseId") or "").strip()
    if not raw_database_id:
        raw_database_id = str(os.environ.get("NOTION_DATABASE_ID") or "").strip()
    if not raw_database_id:
        raise ValueError("dataSourceId es obligatorio.")

    database = retrieve_database({"databaseId": raw_database_id})
    data_sources = database.get("data_sources") or []
    if data_sources and isinstance(data_sources[0], dict):
        candidate = str(data_sources[0].get("id") or "").strip()
        if candidate:
            return _normalize_id(candidate, "dataSourceId")
    raise ValueError("No se pudo resolver dataSourceId a partir de databaseId.")


def list_users(_: dict[str, Any]) -> dict[str, Any]:
    return _request_json("GET", "/v1/users")


def resolve_user_by_email(args: dict[str, Any]) -> dict[str, Any]:
    email = str(args.get("email") or "").strip().lower()
    if not email:
        raise ValueError("email es obligatorio.")
    payload = list_users({})
    matches = []
    for user in payload.get("results", []):
        if not isinstance(user, dict):
            continue
        person = user.get("person")
        if not isinstance(person, dict):
            continue
        candidate = str(person.get("email") or "").strip().lower()
        if candidate == email:
            matches.append(
                {
                    "id": user.get("id"),
                    "name": user.get("name"),
                    "email": person.get("email"),
                    "type": user.get("type"),
                }
            )
    return {
        "ok": bool(matches),
        "email": email,
        "matches": matches,
    }


def create_file_upload(args: dict[str, Any]) -> dict[str, Any]:
    filename = str(args.get("filename") or "").strip()
    if not filename:
        raise ValueError("filename es obligatorio.")
    content_type = str(args.get("contentType") or "").strip()
    if not content_type:
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    payload = {
        "mode": "single_part",
        "filename": filename,
        "content_type": content_type,
    }
    return _request_json("POST", "/v1/file_uploads", payload)


def _multipart_body(field_name: str, filename: str, content_type: str, content: bytes) -> tuple[bytes, str]:
    boundary = f"----pspo-agent-{uuid4().hex}"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8") + content + f"\r\n--{boundary}--\r\n".encode("utf-8")
    return body, boundary


def send_file_upload(args: dict[str, Any]) -> dict[str, Any]:
    file_upload_id = _normalize_id(args.get("fileUploadId") or "", "fileUploadId")
    upload_url = str(args.get("uploadUrl") or "").strip()
    filename = str(args.get("filename") or "").strip()
    if not filename:
        raise ValueError("filename es obligatorio.")

    content_path = str(args.get("filePath") or "").strip()
    content_value = args.get("content")
    if content_path:
        content = Path(content_path).expanduser().read_bytes()
    elif isinstance(content_value, str):
        content = content_value.encode("utf-8")
    else:
        raise ValueError("Debes proporcionar filePath o content para subir el fichero.")

    content_type = str(args.get("contentType") or "").strip()
    if not content_type:
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    if not upload_url:
        created = _request_json("GET", f"/v1/file_uploads/{file_upload_id}")
        upload_url = str(created.get("upload_url") or "").strip()
    if not upload_url:
        raise ValueError("No se ha podido resolver uploadUrl para el file upload.")

    body, boundary = _multipart_body("file", filename, content_type, content)
    headers = {
        "Authorization": f"Bearer {(os.environ.get('NOTION_TOKEN') or '').strip()}",
        "Notion-Version": os.environ.get("NOTION_API_VERSION", DEFAULT_NOTION_VERSION).strip() or DEFAULT_NOTION_VERSION,
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
    return _request_raw("POST", upload_url, data=body, headers=headers)


def attach_file_to_page_property(args: dict[str, Any]) -> dict[str, Any]:
    page_id = _normalize_id(args.get("pageId") or "", "pageId")
    file_upload_id = _normalize_id(args.get("fileUploadId") or "", "fileUploadId")
    property_name = str(args.get("propertyName") or "Documento_MD").strip()
    filename = str(args.get("filename") or "").strip()
    file_ref: dict[str, Any] = {
        "type": "file_upload",
        "file_upload": {"id": file_upload_id},
    }
    if filename:
        file_ref["name"] = filename
    payload = {
        "properties": {
            property_name: {
                "files": [file_ref],
            }
        }
    }
    return _request_json("PATCH", f"/v1/pages/{page_id}", payload)


def append_file_block(args: dict[str, Any]) -> dict[str, Any]:
    page_id = _normalize_id(args.get("pageId") or "", "pageId")
    file_upload_id = _normalize_id(args.get("fileUploadId") or "", "fileUploadId")
    caption = str(args.get("caption") or "").strip()
    payload = {
        "children": [
            _file_block(file_upload_id, caption),
        ]
    }
    return _request_json("PATCH", f"/v1/blocks/{page_id}/children", payload)


def _page_property_file_names(page_payload: dict[str, Any], property_name: str = "Documento_MD") -> list[str]:
    properties = page_payload.get("properties") or {}
    prop = properties.get(property_name) or {}
    files = prop.get("files") or []
    names: list[str] = []
    for item in files:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if name:
            names.append(name)
    return names


def _write_markdown_report(report_path: Path, content: str) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _render_notion_publish_report(result: dict[str, Any]) -> str:
    lines = [
        "# Publish Report",
        "",
        f"- Provider: notion",
        f"- Generated at: {datetime.now(timezone.utc).isoformat()}",
        f"- Stories dir: {result.get('storiesDir', '')}",
        f"- Story count: {result.get('storyCount', 0)}",
        f"- Synced stories: {result.get('syncedStoryCount', 0)}",
        f"- Dependency sync: {result.get('dependencySyncCount', 0)}",
        "",
    ]

    vision = result.get("vision") or {}
    if vision:
        lines.extend([
            "## Vision",
            "",
            f"- Page ID: {vision.get('pageId', '')}",
            f"- Created: {vision.get('created', False)}",
            "",
        ])

    lines.extend([
        "## Stories",
        "",
        "| Story | Page ID | Created | Assignment | Attachment |",
        "|---|---|---:|---|---|",
    ])
    second_pass_index = {
        str(item.get("storyId") or ""): item
        for item in (result.get("secondPass") or [])
        if isinstance(item, dict)
    }
    for item in result.get("firstPass") or []:
        if not isinstance(item, dict):
            continue
        story_id = str(item.get("storyId") or "")
        assignment = item.get("assignment") or {}
        attachment = item.get("attachment") or {}
        dep_info = second_pass_index.get(story_id, {})
        dep_suffix = ""
        if dep_info:
            dep_suffix = f" / deps:{len(dep_info.get('resolvedDependencyPageIds') or [])}"
        attachment_label = "reused" if attachment.get("skipped") else "uploaded"
        lines.append(
            f"| {story_id} | {item.get('pageId', '')} | {item.get('created', False)} | "
            f"{assignment.get('status', '')}{dep_suffix} | {attachment_label} |"
        )

    unresolved_assignments = result.get("unresolvedAssignments") or []
    attachment_skips = result.get("attachmentSkips") or []
    errors = result.get("errors") or []

    if unresolved_assignments:
        lines.extend([
            "",
            "## Unresolved Assignments",
            "",
            "| Story | Email | File |",
            "|---|---|---|",
        ])
        for item in unresolved_assignments:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"| {item.get('storyId', '')} | {item.get('email', '')} | {item.get('filePath', '')} |"
            )

    if attachment_skips:
        lines.extend([
            "",
            "## Attachment Skips",
            "",
            "| Story | Reason | File |",
            "|---|---|---|",
        ])
        for item in attachment_skips:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"| {item.get('storyId', '')} | {item.get('reason', '')} | {item.get('filePath', '')} |"
            )

    if errors:
        lines.extend([
            "",
            "## Errors",
            "",
            "| Scope | File | Error |",
            "|---|---|---|",
        ])
        for item in errors:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"| {item.get('scope', '')} | {item.get('filePath', '')} | {str(item.get('error', '')).replace('|', '/')} |"
            )

    return "\n".join(lines)


def upload_and_attach_markdown(args: dict[str, Any]) -> dict[str, Any]:
    page_id = _normalize_id(args.get("pageId") or "", "pageId")
    file_path = str(args.get("filePath") or "").strip()
    if not file_path:
        raise ValueError("filePath es obligatorio.")
    path = Path(file_path).expanduser()
    if not path.is_file():
        raise ValueError(f"No existe el fichero: {path}")
    filename = str(args.get("filename") or path.name).strip()
    content_type = str(args.get("contentType") or "text/markdown").strip()
    property_name = str(args.get("propertyName") or "Documento_MD").strip()

    if bool(args.get("skipIfFilenameExists", True)):
        page_payload = retrieve_page({"pageId": page_id})
        if filename in _page_property_file_names(page_payload, property_name):
            return {
                "ok": True,
                "skipped": True,
                "reason": "already_attached",
                "pageId": page_id,
                "filename": filename,
                "propertyName": property_name,
            }

    created = create_file_upload({"filename": filename, "contentType": content_type})
    file_upload_id = str(created.get("id") or "")
    sent = send_file_upload({
        "fileUploadId": file_upload_id,
        "uploadUrl": created.get("upload_url") or "",
        "filePath": str(path),
        "filename": filename,
        "contentType": content_type,
    })
    attached = attach_file_to_page_property({
        "pageId": page_id,
        "fileUploadId": file_upload_id,
        "propertyName": property_name,
        "filename": filename,
    })
    block_result = None
    if bool(args.get("appendFileBlock", True)):
        block_result = append_file_block({
            "pageId": page_id,
            "fileUploadId": file_upload_id,
            "caption": str(args.get("caption") or filename),
        })
    return {
        "ok": True,
        "skipped": False,
        "fileUploadId": file_upload_id,
        "uploadStatus": sent.get("status"),
        "attachedProperty": attached.get("id"),
        "fileBlockAppended": bool(block_result),
    }


def _default_database_schema() -> dict[str, Any]:
    return {
        "Titulo": {"title": {}},
        "ID": {"rich_text": {}},
        "Resumen": {"rich_text": {}},
        "Estado": {
            "select": {
                "options": [
                    {"name": "Backlog", "color": "default"},
                    {"name": "Sprint activo", "color": "blue"},
                    {"name": "Bloqueada", "color": "red"},
                    {"name": "En progreso", "color": "yellow"},
                    {"name": "En revision", "color": "purple"},
                    {"name": "Hecho", "color": "green"},
                ]
            }
        },
        "Prioridad": {
            "select": {
                "options": [
                    {"name": "Critica", "color": "red"},
                    {"name": "Alta", "color": "orange"},
                    {"name": "Media", "color": "yellow"},
                    {"name": "Baja", "color": "blue"},
                ]
            }
        },
        "Estimacion_h": {"number": {"format": "number"}},
        "Sprint": {"rich_text": {}},
        "Asignado_a": {"people": {}},
        "Dependencias": {"rich_text": {}},
        "Documento_MD": {"files": {}},
    }


def _ensure_dual_relation(data_source_id: str, properties: dict[str, Any]) -> dict[str, Any]:
    blocked_by = properties.get("Bloqueada_por")
    if isinstance(blocked_by, dict) and blocked_by.get("type") == "relation":
        return {"ok": True, "created": False, "dataSourceId": data_source_id}

    payload = {
        "Bloqueada_por": {
            "relation": {
                "data_source_id": data_source_id,
                "dual_property": {
                    "synced_property_name": "Bloquea",
                },
            }
        }
    }
    updated = update_data_source({
        "dataSourceId": data_source_id,
        "properties": payload,
    })
    return {
        "ok": True,
        "created": True,
        "dataSourceId": data_source_id,
        "updated": updated,
    }


def ensure_dependency_relations(args: dict[str, Any]) -> dict[str, Any]:
    data_source_id = _resolve_data_source_id(args)
    data_source = retrieve_data_source({"dataSourceId": data_source_id})
    properties = data_source.get("properties") or {}
    if not isinstance(properties, dict):
        properties = {}
    return _ensure_dual_relation(data_source_id, properties)


def _create_page(parent: dict[str, Any], title: str, children: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "parent": parent,
        "properties": {
            "title": {
                "title": _title(title),
            }
        },
    }
    if children:
        payload["children"] = children
    return _request_json("POST", "/v1/pages", payload)


def _update_page_title(page_id: str, title: str) -> dict[str, Any]:
    normalized_page_id = _normalize_id(page_id, "pageId")
    payload = {
        "properties": {
            "title": {
                "title": _title(title),
            }
        }
    }
    return _request_json("PATCH", f"/v1/pages/{normalized_page_id}", payload)


def _create_database(parent_page_id: str, title: str) -> dict[str, Any]:
    payload = {
        "parent": {"type": "page_id", "page_id": _normalize_id(parent_page_id, "parentPageId")},
        "title": _title(title),
        "initial_data_source": {
            "properties": _default_database_schema(),
        },
    }
    return _request_json("POST", "/v1/databases", payload)


def create_project(args: dict[str, Any]) -> dict[str, Any]:
    parent_page_id = _normalize_id(
        args.get("parentPageId") or os.environ.get("NOTION_PARENT_PAGE_ID") or "",
        "parentPageId",
    )
    project_name = (args.get("projectName") or "").strip() or _default_project_name()

    project_title = (args.get("projectTitle") or f"PSPO · {project_name}").strip()
    vision_title = (args.get("visionTitle") or "HU-00 · Vision").strip()
    database_title = (args.get("databaseTitle") or "Backlog").strip()
    vision_markdown = (
        args.get("visionMarkdown")
        or f"# Vision\n\n{project_name}\n\n## Contexto\n\nProyecto creado por PSPO Agent en modo zero-template."
    )

    project_page = _create_page(
        {"type": "page_id", "page_id": parent_page_id},
        project_title,
        children=[_paragraph_block("Proyecto creado por PSPO Agent.")],
    )
    project_page_id = project_page["id"]

    vision_page = _create_page(
        {"type": "page_id", "page_id": project_page_id},
        vision_title,
        children=markdown_to_blocks(str(vision_markdown)),
    )
    database = _create_database(project_page_id, database_title)
    data_sources = database.get("data_sources") or []
    data_source_id = ""
    if data_sources and isinstance(data_sources[0], dict):
        data_source_id = str(data_sources[0].get("id") or "")
    if data_source_id:
        ensure_dependency_relations({"dataSourceId": data_source_id})

    return {
        "ok": True,
        "projectPageId": project_page_id,
        "visionPageId": vision_page.get("id"),
        "databaseId": database.get("id"),
        "dataSourceId": data_source_id,
        "projectUrl": project_page.get("url"),
        "visionUrl": vision_page.get("url"),
    }


def _story_properties(args: dict[str, Any]) -> dict[str, Any]:
    title = (args.get("title") or "").strip()
    if not title:
        raise ValueError("title es obligatorio.")
    properties: dict[str, Any] = {
        "Titulo": {"title": _title(title)},
    }
    mapping = {
        "storyId": ("ID", lambda value: {"rich_text": _rich_text(str(value))}),
        "summary": ("Resumen", lambda value: {"rich_text": _rich_text(str(value))}),
        "status": ("Estado", lambda value: {"select": {"name": str(value)}}),
        "priority": ("Prioridad", lambda value: {"select": {"name": str(value)}}),
        "estimateHours": ("Estimacion_h", lambda value: {"number": _coerce_number(value)}),
        "sprint": ("Sprint", lambda value: {"rich_text": _rich_text(str(value))}),
        "dependencies": ("Dependencias", lambda value: {"rich_text": _rich_text(str(value))}),
    }
    for key, (field_name, builder) in mapping.items():
        value = args.get(key)
        if value not in (None, ""):
            properties[field_name] = builder(value)
    if "Estimacion_h" not in properties and args.get("estimation") not in (None, ""):
        properties["Estimacion_h"] = {"number": _coerce_number(args.get("estimation"))}

    assigned_user_ids = args.get("assignedUserIds")
    assigned_user_id = args.get("assignedUserId")
    assigned_email = str(args.get("assignedEmail") or "").strip()
    assigned_to = str(args.get("assignedTo") or "").strip()
    if not assigned_email and assigned_to and "@" in assigned_to:
        assigned_email = assigned_to
    if assigned_user_ids in (None, "") and assigned_user_id in (None, "") and assigned_to and "@" not in assigned_to:
        assigned_user_id = assigned_to
    if assigned_user_ids in (None, "") and assigned_user_id not in (None, ""):
        assigned_user_ids = [assigned_user_id]
    if assigned_user_ids in (None, "") and assigned_email:
        resolution = resolve_user_by_email({"email": assigned_email})
        matches = resolution.get("matches") or []
        if matches:
            assigned_user_ids = [matches[0]["id"]]
    if isinstance(assigned_user_ids, list) and assigned_user_ids:
        properties["Asignado_a"] = {
            "people": [
                {"id": _normalize_id(str(user_id), "assignedUserId")}
                for user_id in assigned_user_ids
            ]
        }
    dependency_page_ids = args.get("dependencyPageIds")
    if dependency_page_ids is None:
        dependency_page_ids = args.get("blockedByPageIds")
    if isinstance(dependency_page_ids, list):
        properties["Bloqueada_por"] = {
            "relation": [
                {"id": _normalize_id(str(page_id), "dependencyPageId")}
                for page_id in dependency_page_ids
                if str(page_id).strip()
            ]
        }
    return properties


def _parse_story_ids(raw_value: Any) -> list[str]:
    if raw_value in (None, "", [], ()):
        return []
    if isinstance(raw_value, list):
        values = [str(item).strip() for item in raw_value]
    else:
        normalized = str(raw_value).replace("\n", ",")
        values = [part.strip() for part in normalized.split(",")]
    return [
        value
        for value in values
        if value
        and value.lower() not in {"ninguna", "ninguno", "sin dependencias", "none", "n/a"}
    ]


def query_story_pages(args: dict[str, Any]) -> dict[str, Any]:
    data_source_id = _resolve_data_source_id(args)
    story_id = str(args.get("storyId") or "").strip()
    title = str(args.get("title") or "").strip()
    filter_payload: dict[str, Any] | None = None
    if story_id:
        filter_payload = {
            "property": "ID",
            "rich_text": {"equals": story_id},
        }
    elif title:
        filter_payload = {
            "property": "Titulo",
            "title": {"equals": title},
        }
    payload: dict[str, Any] = {"page_size": int(args.get("pageSize") or 100)}
    if filter_payload:
        payload["filter"] = filter_payload
    return _request_json("POST", f"/v1/data_sources/{data_source_id}/query", payload)


def find_story_page(args: dict[str, Any]) -> dict[str, Any]:
    payload = query_story_pages(args)
    results = payload.get("results") or []
    first = results[0] if results else None
    return {
        "ok": bool(first),
        "count": len(results),
        "page": first,
    }


def create_story_page(args: dict[str, Any]) -> dict[str, Any]:
    data_source_id = _resolve_data_source_id(args)
    properties = _story_properties(args)

    body_markdown = str(args.get("markdown") or "")
    payload: dict[str, Any] = {
        "parent": {"type": "data_source_id", "data_source_id": data_source_id},
        "properties": properties,
    }
    if body_markdown:
        payload["children"] = markdown_to_blocks(body_markdown)

    return _request_json("POST", "/v1/pages", payload)


def update_story_page(args: dict[str, Any]) -> dict[str, Any]:
    page_id = _normalize_id(args.get("pageId") or "", "pageId")
    properties = _story_properties(args)
    payload: dict[str, Any] = {"properties": properties}
    updated_page = _request_json("PATCH", f"/v1/pages/{page_id}", payload)
    body_sync = None
    markdown = str(args.get("markdown") or "").strip()
    if markdown:
        body_sync = _replace_page_body(page_id, markdown)
    return {
        "ok": True,
        "page": updated_page,
        "bodySync": body_sync,
    }


def sync_vision_from_markdown(args: dict[str, Any]) -> dict[str, Any]:
    file_path = str(args.get("filePath") or "docs/vision.md").strip()
    markdown = _read_markdown_file(file_path)
    title = str(args.get("title") or "HU-00 · Vision").strip() or "HU-00 · Vision"
    vision_page_id = str(args.get("visionPageId") or os.environ.get("NOTION_VISION_PAGE_ID") or "").strip()

    if vision_page_id:
        normalized_page_id = _normalize_id(vision_page_id, "visionPageId")
        _update_page_title(normalized_page_id, title)
        body_sync = _replace_page_body(normalized_page_id, markdown)
        return {
            "ok": True,
            "created": False,
            "pageId": normalized_page_id,
            "title": title,
            "bodySync": body_sync,
        }

    project_page_id = str(args.get("projectPageId") or os.environ.get("NOTION_PROJECT_PAGE_ID") or "").strip()
    if not project_page_id:
        raise ValueError("NOTION_PROJECT_PAGE_ID o visionPageId es obligatorio para sincronizar HU-00.")

    created_page = _create_page(
        {"type": "page_id", "page_id": _normalize_id(project_page_id, "projectPageId")},
        title,
        children=markdown_to_blocks(markdown),
    )
    page_id = str(created_page.get("id") or "").strip()
    save_project_targets({
        "parentPageId": os.environ.get("NOTION_PARENT_PAGE_ID", ""),
        "projectPageId": project_page_id,
        "visionPageId": page_id,
        "databaseId": os.environ.get("NOTION_DATABASE_ID", ""),
    })
    return {
        "ok": True,
        "created": True,
        "pageId": page_id,
        "title": title,
        "url": created_page.get("url"),
    }


def set_story_dependencies(args: dict[str, Any]) -> dict[str, Any]:
    page_id = str(args.get("pageId") or "").strip()
    if page_id:
        normalized_page_id = _normalize_id(page_id, "pageId")
    else:
        page = find_story_page(args)
        page_payload = page.get("page") or {}
        candidate = str(page_payload.get("id") or "").strip()
        if not candidate:
            raise ValueError("No se ha podido resolver la pagina de la historia.")
        normalized_page_id = _normalize_id(candidate, "pageId")

    data_source_id = _resolve_data_source_id(args)
    ensure_dependency_relations({"dataSourceId": data_source_id})

    dependency_page_ids = args.get("dependencyPageIds")
    resolved_page_ids: list[str] = []
    unresolved_story_ids: list[str] = []
    if isinstance(dependency_page_ids, list):
        resolved_page_ids = [
            _normalize_id(str(page_id), "dependencyPageId")
            for page_id in dependency_page_ids
            if str(page_id).strip()
        ]
    else:
        dependency_story_ids = _parse_story_ids(
            args.get("dependencyStoryIds", args.get("dependencies"))
        )
        for dependency_story_id in dependency_story_ids:
            result = find_story_page({
                "dataSourceId": data_source_id,
                "storyId": dependency_story_id,
            })
            page_payload = result.get("page") or {}
            candidate = str(page_payload.get("id") or "").strip()
            if candidate:
                resolved_page_ids.append(_normalize_id(candidate, "dependencyPageId"))
            else:
                unresolved_story_ids.append(dependency_story_id)

    payload = {
        "properties": {
            "Bloqueada_por": {
                "relation": [{"id": page_id} for page_id in resolved_page_ids],
            }
        }
    }
    updated = _request_json("PATCH", f"/v1/pages/{normalized_page_id}", payload)
    return {
        "ok": True,
        "pageId": normalized_page_id,
        "resolvedDependencyPageIds": resolved_page_ids,
        "unresolvedDependencyStoryIds": unresolved_story_ids,
        "page": updated,
    }


def sync_story_from_markdown(args: dict[str, Any]) -> dict[str, Any]:
    parsed = parse_story_markdown(args)
    data_source_id = _resolve_data_source_id(args)
    status = str(args.get("status") or "").strip() or "Backlog"

    story_args = {
        "dataSourceId": data_source_id,
        "title": parsed["fullTitle"],
        "storyId": parsed["storyId"],
        "summary": parsed["summary"],
        "priority": parsed["priority"],
        "estimateHours": parsed["estimation"],
        "sprint": parsed["sprint"],
        "assignedEmail": parsed["assignedEmail"],
        "dependencies": parsed["dependenciesText"],
        "markdown": parsed["markdown"],
    }
    if status:
        story_args["status"] = status

    existing = find_story_page({
        "dataSourceId": data_source_id,
        "storyId": parsed["storyId"],
        "title": parsed["fullTitle"],
    })
    page = existing.get("page") or {}
    existing_page_id = str(page.get("id") or "").strip()

    if existing_page_id:
        sync_result = update_story_page({
            "pageId": existing_page_id,
            **story_args,
        })
        page_id = existing_page_id
        created = False
    else:
        sync_result = create_story_page(story_args)
        page_id = str(sync_result.get("id") or "").strip()
        created = True

    attachment = upload_and_attach_markdown({
        "pageId": page_id,
        "filePath": parsed["filePath"],
        "filename": Path(parsed["filePath"]).name,
        "appendFileBlock": True,
        "skipIfFilenameExists": True,
    })
    final_page = retrieve_page({"pageId": page_id})
    assignee_count = len(((final_page.get("properties") or {}).get("Asignado_a") or {}).get("people") or [])
    file_count = len(_page_property_file_names(final_page))
    if parsed["assignedEmail"]:
        assignment_status = "resolved" if assignee_count > 0 else "unresolved"
    else:
        assignment_status = "unassigned"
    return {
        "ok": True,
        "created": created,
        "pageId": page_id,
        "storyId": parsed["storyId"],
        "title": parsed["fullTitle"],
        "syncResult": sync_result,
        "attachment": attachment,
        "assignment": {
            "email": parsed["assignedEmail"],
            "status": assignment_status,
            "peopleCount": assignee_count,
        },
        "verification": {
            "fileCount": file_count,
            "hasMarkdownAttachment": file_count > 0,
        },
        "parsed": {
            "summary": parsed["summary"],
            "priority": parsed["priority"],
            "estimation": parsed["estimation"],
            "sprint": parsed["sprint"],
            "assignedEmail": parsed["assignedEmail"],
            "dependencyStoryIds": parsed["dependencyStoryIds"],
        },
    }


def sync_story_dependencies_from_markdown(args: dict[str, Any]) -> dict[str, Any]:
    parsed = parse_story_markdown(args)
    data_source_id = _resolve_data_source_id(args)
    page_lookup = find_story_page({
        "dataSourceId": data_source_id,
        "storyId": parsed["storyId"],
        "title": parsed["fullTitle"],
    })
    page = page_lookup.get("page") or {}
    page_id = str(page.get("id") or "").strip()
    if not page_id:
        raise ValueError(
            f"No existe pagina remota para {parsed['storyId'] or parsed['fullTitle']}. Sincroniza la HU antes."
        )
    result = set_story_dependencies({
        "dataSourceId": data_source_id,
        "pageId": page_id,
        "dependencyStoryIds": parsed["dependencyStoryIds"],
    })
    return {
        "ok": True,
        "pageId": page_id,
        "storyId": parsed["storyId"],
        "resolvedDependencyPageIds": result.get("resolvedDependencyPageIds", []),
        "unresolvedDependencyStoryIds": result.get("unresolvedDependencyStoryIds", []),
    }


def sync_stories_from_folder(args: dict[str, Any]) -> dict[str, Any]:
    stories_dir = Path(str(args.get("storiesDir") or "docs/historias").strip()).expanduser()
    if not stories_dir.is_dir():
        raise ValueError(f"No existe el directorio de historias: {stories_dir}")

    files = sorted(path for path in stories_dir.glob("HU-*.md") if path.is_file())
    if not files:
        raise ValueError(f"No hay historias HU-*.md en {stories_dir}")

    data_source_id = _resolve_data_source_id(args)
    status = str(args.get("status") or "").strip()
    first_pass: list[dict[str, Any]] = []
    second_pass: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    unresolved_assignments: list[dict[str, Any]] = []
    attachment_skips: list[dict[str, Any]] = []
    report_path = Path(
        str(args.get("reportPath") or (stories_dir.parent / "publish-report.md"))
    ).expanduser()

    vision_path = str(args.get("visionFilePath") or "docs/vision.md").strip()
    vision_result = None
    if bool(args.get("syncVision", True)) and Path(vision_path).is_file():
        try:
            vision_result = sync_vision_from_markdown({
                "filePath": vision_path,
                "title": args.get("visionTitle") or "HU-00 · Vision",
            })
        except Exception as exc:
            errors.append({"scope": "vision", "filePath": vision_path, "error": str(exc)})

    for path in files:
        try:
            sync_args = {
                "dataSourceId": data_source_id,
                "filePath": str(path),
            }
            if status:
                sync_args["status"] = status
            result = sync_story_from_markdown(sync_args)
            first_pass.append({
                "filePath": str(path),
                "storyId": result.get("storyId"),
                "pageId": result.get("pageId"),
                "created": result.get("created"),
                "assignment": result.get("assignment"),
                "attachment": result.get("attachment"),
            })
            if (result.get("assignment") or {}).get("status") == "unresolved":
                unresolved_assignments.append({
                    "filePath": str(path),
                    "storyId": result.get("storyId"),
                    "email": (result.get("assignment") or {}).get("email", ""),
                })
            if bool((result.get("attachment") or {}).get("skipped")):
                attachment_skips.append({
                    "filePath": str(path),
                    "storyId": result.get("storyId"),
                    "reason": (result.get("attachment") or {}).get("reason", ""),
                })
        except Exception as exc:
            errors.append({"scope": "story", "filePath": str(path), "error": str(exc)})

    for path in files:
        try:
            result = sync_story_dependencies_from_markdown({
                "dataSourceId": data_source_id,
                "filePath": str(path),
            })
            second_pass.append({
                "filePath": str(path),
                "storyId": result.get("storyId"),
                "pageId": result.get("pageId"),
                "resolvedDependencyPageIds": result.get("resolvedDependencyPageIds", []),
                "unresolvedDependencyStoryIds": result.get("unresolvedDependencyStoryIds", []),
            })
        except Exception as exc:
            errors.append({"scope": "dependencies", "filePath": str(path), "error": str(exc)})

    result = {
        "ok": not errors,
        "storiesDir": str(stories_dir),
        "vision": vision_result,
        "firstPass": first_pass,
        "secondPass": second_pass,
        "errors": errors,
        "storyCount": len(files),
        "syncedStoryCount": len(first_pass),
        "dependencySyncCount": len(second_pass),
        "unresolvedAssignments": unresolved_assignments,
        "attachmentSkips": attachment_skips,
        "reportPath": str(report_path),
    }
    _write_markdown_report(report_path, _render_notion_publish_report(result))
    return result


TOOL_MAP = {
    "help": help_info,
    "list-tools": help_info,
    "verify-credentials": verify_credentials,
    "save-project-targets": save_project_targets,
    "retrieve-page": retrieve_page,
    "retrieve-database": retrieve_database,
    "retrieve-data-source": retrieve_data_source,
    "update-data-source": update_data_source,
    "ensure-dependency-relations": ensure_dependency_relations,
    "list-users": list_users,
    "resolve-user-by-email": resolve_user_by_email,
    "setup-targets": setup_targets,
    "create-file-upload": create_file_upload,
    "send-file-upload": send_file_upload,
    "attach-file-to-page-property": attach_file_to_page_property,
    "append-file-block": append_file_block,
    "upload-and-attach-markdown": upload_and_attach_markdown,
    "create-project": create_project,
    "sync-vision-from-markdown": sync_vision_from_markdown,
    "parse-story-markdown": parse_story_markdown,
    "query-story-pages": query_story_pages,
    "find-story-page": find_story_page,
    "create-story-page": create_story_page,
    "update-story-page": update_story_page,
    "sync-story-from-markdown": sync_story_from_markdown,
    "set-story-dependencies": set_story_dependencies,
    "sync-story-dependencies-from-markdown": sync_story_dependencies_from_markdown,
    "sync-stories-from-folder": sync_stories_from_folder,
}


def main() -> int:
    args = _parse_args()
    try:
        _load_project_env()
        if args.tool == "env-status":
            result = _env_status()
        else:
            handler = TOOL_MAP.get(args.tool)
            if handler is None:
                raise ValueError(f"Herramienta no soportada por el fallback oficial: {args.tool}")
            payload = _load_arguments(args.args_json)
            flag_mapping = {
                "parentPageId": args.parent_page_id,
                "projectPageId": args.project_page_id,
                "databaseId": args.database_id,
                "projectName": args.project_name,
                "projectTitle": args.project_title,
                "visionTitle": args.vision_title,
                "databaseTitle": args.database_title,
            }
            for key, value in flag_mapping.items():
                if value not in (None, ""):
                    payload.setdefault(key, value)
            if args.tool_arg:
                if args.tool == "retrieve-page":
                    payload.setdefault("pageId", args.tool_arg)
                elif args.tool == "retrieve-database":
                    payload.setdefault("databaseId", args.tool_arg)
            result = handler(payload)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.pretty:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
