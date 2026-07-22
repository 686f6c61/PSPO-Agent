#!/usr/bin/env python3
"""
Fallback oficial y controlado para operaciones de GitHub Projects v2 en PSPO Agent.

Esta version cubre:
- verificacion de credenciales y del scope `project`
- inspeccion segura del entorno
- creacion zero-template de un Project v2 privado con esquema de campos completo
  (Status, Prioridad, Talla, Horas, Sprint, Responsable), shortDescription y README
- persistencia de los targets del proyecto en `.env`
- sincronizacion de la vision (HU-00) y de las historias como draft items,
  mapeando campo a campo los metadatos de cada HU a su campo del proyecto
- lote en dos pasadas sobre docs/historias/HU-*.md + docs/vision.md con report

Backend primario: la CLI `gh` (gh api graphql). Si `gh` no está disponible,
cae a GraphQL directo con urllib usando GITHUB_TOKEN o GH_TOKEN.

Todo sin dependencias externas y leyendo credenciales desde `.env`.

Limites conocidos:
- los draft items no admiten adjuntos (el markdown completo va en el cuerpo)
- la asignacion real requiere el login de GitHub (columna `github` del CSV de equipo)
- la API publica no permite crear vistas de Project v2: las vistas recomendadas
  se documentan en el README del proyecto para crearlas a mano
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
GITHUB_API_URL = "https://api.github.com"

# Nombres de los campos del proyecto (clave normalizada -> nombre visible).
FIELD_NAMES = {
    "status": "Status",
    "prioridad": "Prioridad",
    "talla": "Talla",
    "horas": "Horas",
    "sprint": "Sprint",
    "responsable": "Responsable",
}

# Opciones del campo Status (nativo): nombre, color y descripcion semantica.
STATUS_OPTIONS = [
    ("Backlog", "GRAY", "Aprobada, sin comprometer en un sprint"),
    ("Sprint activo", "BLUE", "Comprometida en el sprint actual"),
    ("Bloqueada", "RED", "Dependencia sin resolver"),
    ("En progreso", "YELLOW", "En desarrollo"),
    ("En revision", "PURPLE", "En revision o QA"),
    ("Hecho", "GREEN", "Cumple la Definition of Done"),
]

# Prioridad: espejo de las etiquetas de Trello.
PRIORITY_OPTIONS = [
    ("Critica", "RED", "Maxima urgencia"),
    ("Alta", "ORANGE", "Prioridad alta"),
    ("Media", "YELLOW", "Prioridad media"),
    ("Baja", "BLUE", "Prioridad baja"),
]

# Talla t-shirt en horas efectivas con agentes.
SIZE_OPTIONS = [
    ("XS", "GRAY", "1 hora efectiva"),
    ("S", "BLUE", "2 horas efectivas"),
    ("M", "GREEN", "4 horas efectivas"),
    ("L", "YELLOW", "8 horas efectivas"),
    ("XL", "ORANGE", "16 horas efectivas"),
]

SIZE_HOURS = {"XS": 1, "S": 2, "M": 4, "L": 8, "XL": 16}


# ---------------------------------------------------------------------------
# Entorno y persistencia en .env (mismo mecanismo que Trello/Notion)
# ---------------------------------------------------------------------------


def _project_env_path() -> Path:
    return Path.cwd() / ".env"


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def _candidate_env_paths() -> list[Path]:
    cwd = Path.cwd()
    seen: set[Path] = set()
    candidates: list[Path] = []
    for directory in (cwd, *cwd.parents):
        if directory not in seen:
            seen.add(directory)
            candidates.append(directory / ".env")
    return candidates


def _load_project_env() -> None:
    for env_path in _candidate_env_paths():
        if not env_path.is_file():
            continue
        try:
            with env_path.open(encoding="utf-8") as handle:
                for raw_line in handle:
                    line = raw_line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = _strip_quotes(value)
                    if not os.environ.get(key):
                        os.environ[key] = value
        except OSError:
            continue
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


def _default_project_name() -> str:
    raw = (
        (os.environ.get("PSPO_PROJECT_NAME") or "").strip()
        or Path.cwd().name.strip()
    )
    if not raw:
        return "Proyecto PSPO Agent"

    normalized = re.sub(r"[-_]+", " ", raw).strip()
    normalized = re.sub(r"\b(pspo|tmp|temp|github|onb\d+)\b", " ", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\b[a-z0-9]{6,}\b$", " ", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\s{2,}", " ", normalized).strip(" -_")
    return normalized or "Proyecto PSPO Agent"


def _github_token() -> str:
    return (
        (os.environ.get("GITHUB_TOKEN") or "").strip()
        or (os.environ.get("GH_TOKEN") or "").strip()
    )


def _gh_available() -> bool:
    return shutil.which("gh") is not None


def _project_title_prefix() -> str:
    return (os.environ.get("GITHUB_PROJECT_TITLE_PREFIX") or "PSPO").strip() or "PSPO"


def _env_status() -> dict[str, Any]:
    token = _github_token()
    gh_available = _gh_available()
    if token:
        auth_method = "token"
    elif gh_available:
        auth_method = "gh"
    else:
        auth_method = "none"
    return {
        "hasGithubToken": bool((os.environ.get("GITHUB_TOKEN") or "").strip()),
        "hasGhToken": bool((os.environ.get("GH_TOKEN") or "").strip()),
        "hasAnyToken": bool(token),
        "ghCliAvailable": gh_available,
        "authMethod": auth_method,
        "tokenMasked": _mask(token),
        "hasProjectNumber": bool((os.environ.get("GITHUB_PROJECT_NUMBER") or "").strip()),
        "hasProjectId": bool((os.environ.get("GITHUB_PROJECT_ID") or "").strip()),
        "projectNumber": (os.environ.get("GITHUB_PROJECT_NUMBER") or "").strip(),
        "projectId": (os.environ.get("GITHUB_PROJECT_ID") or "").strip(),
        "projectOwner": (os.environ.get("GITHUB_PROJECT_OWNER") or "").strip(),
        "projectUrl": (os.environ.get("GITHUB_PROJECT_URL") or "").strip(),
    }


# ---------------------------------------------------------------------------
# Cliente GraphQL: gh primario, urllib con token como fallback
# ---------------------------------------------------------------------------


def _graphql_via_gh(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps({"query": query, "variables": variables}, ensure_ascii=False)
    try:
        proc = subprocess.run(
            ["gh", "api", "graphql", "--input", "-"],
            input=body,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"No se pudo ejecutar gh: {exc}") from exc
    if proc.returncode != 0:
        message = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"GitHub gh error: {message or 'fallo desconocido'}")
    raw = (proc.stdout or "").strip()
    return json.loads(raw) if raw else {}


def _graphql_via_urllib(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    token = _github_token()
    if not token:
        raise RuntimeError(
            "No hay autenticacion de GitHub: instala gh y ejecuta `gh auth login` "
            "o define GITHUB_TOKEN o GH_TOKEN en el .env del proyecto."
        )
    data = json.dumps({"query": query, "variables": variables}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        GITHUB_GRAPHQL_URL,
        data=data,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "pspo-agent",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        raise RuntimeError(f"GitHub API {exc.code}: {body or str(exc)}") from exc


def _graphql(query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    variables = variables or {}
    if _gh_available():
        payload = _graphql_via_gh(query, variables)
    else:
        payload = _graphql_via_urllib(query, variables)
    errors = payload.get("errors")
    if errors:
        messages = "; ".join(
            str(item.get("message") or item) for item in errors if isinstance(item, dict)
        ) or json.dumps(errors, ensure_ascii=False)
        raise RuntimeError(f"GitHub GraphQL error: {messages}")
    data = payload.get("data")
    if data is None:
        raise RuntimeError("Respuesta de GitHub sin campo data.")
    return data


def _oauth_scopes() -> list[str]:
    """Lee los scopes del token via la cabecera X-OAuth-Scopes de /user.

    Los tokens fine-grained no exponen scopes, por lo que una lista vacia
    significa "desconocido", no "sin permisos".
    """
    if _gh_available():
        try:
            proc = subprocess.run(
                ["gh", "api", "-i", "user"],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (OSError, subprocess.SubprocessError):
            return []
        if proc.returncode != 0:
            return []
        for line in (proc.stdout or "").splitlines():
            if line.lower().startswith("x-oauth-scopes:"):
                raw = line.split(":", 1)[1].strip()
                return [scope.strip() for scope in raw.split(",") if scope.strip()]
        return []

    token = _github_token()
    if not token:
        return []
    request = urllib.request.Request(
        f"{GITHUB_API_URL}/user",
        headers={
            "Authorization": f"bearer {token}",
            "User-Agent": "pspo-agent",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.headers.get("X-OAuth-Scopes", "") or ""
    except urllib.error.HTTPError as exc:
        raw = exc.headers.get("X-OAuth-Scopes", "") if exc.headers else ""
    except OSError:
        raw = ""
    return [scope.strip() for scope in raw.split(",") if scope.strip()]


def _has_project_scope(scopes: list[str]) -> bool:
    # Se necesita escritura: `read:project` solo permite leer y no crea proyectos
    # ni escribe items. Los tokens classic usan `project` (control total).
    lowered = {scope.lower() for scope in scopes}
    return bool(lowered & {"project", "write:project"})


# ---------------------------------------------------------------------------
# Consultas y mutaciones GraphQL
# ---------------------------------------------------------------------------


VIEWER_QUERY = "query { viewer { id login } }"

USER_ID_QUERY = "query($login: String!) { user(login: $login) { id } }"

CREATE_PROJECT_MUTATION = """
mutation($ownerId: ID!, $title: String!) {
  createProjectV2(input: {ownerId: $ownerId, title: $title}) {
    projectV2 { id number title url }
  }
}
"""

UPDATE_PROJECT_META_MUTATION = """
mutation($projectId: ID!, $shortDescription: String!, $readme: String!) {
  updateProjectV2(input: {
    projectId: $projectId,
    public: false,
    shortDescription: $shortDescription,
    readme: $readme
  }) {
    projectV2 { id }
  }
}
"""

PROJECT_FIELDS_QUERY = """
query($projectId: ID!) {
  node(id: $projectId) {
    ... on ProjectV2 {
      fields(first: 50) {
        nodes {
          ... on ProjectV2FieldCommon { id name dataType }
          ... on ProjectV2SingleSelectField {
            id
            name
            dataType
            options { id name color description }
          }
        }
      }
    }
  }
}
"""

CREATE_SINGLE_SELECT_FIELD_MUTATION = """
mutation($projectId: ID!, $name: String!, $options: [ProjectV2SingleSelectFieldOptionInput!]!) {
  createProjectV2Field(input: {
    projectId: $projectId,
    dataType: SINGLE_SELECT,
    name: $name,
    singleSelectOptions: $options
  }) {
    projectV2Field {
      ... on ProjectV2SingleSelectField {
        id
        name
        dataType
        options { id name color description }
      }
    }
  }
}
"""

CREATE_SIMPLE_FIELD_MUTATION = """
mutation($projectId: ID!, $name: String!, $dataType: ProjectV2CustomFieldType!) {
  createProjectV2Field(input: {projectId: $projectId, dataType: $dataType, name: $name}) {
    projectV2Field {
      ... on ProjectV2FieldCommon { id name dataType }
    }
  }
}
"""

UPDATE_FIELD_OPTIONS_MUTATION = """
mutation($fieldId: ID!, $options: [ProjectV2SingleSelectFieldOptionInput!]!) {
  updateProjectV2Field(input: {fieldId: $fieldId, singleSelectOptions: $options}) {
    projectV2Field {
      ... on ProjectV2SingleSelectField {
        id
        name
        options { id name color description }
      }
    }
  }
}
"""

PROJECT_ITEMS_QUERY = """
query($projectId: ID!, $cursor: String) {
  node(id: $projectId) {
    ... on ProjectV2 {
      items(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          content {
            ... on DraftIssue { id title }
            ... on Issue { id title }
          }
        }
      }
    }
  }
}
"""

ADD_DRAFT_ITEM_MUTATION = """
mutation($projectId: ID!, $title: String!, $body: String!, $assigneeIds: [ID!]) {
  addProjectV2DraftIssue(input: {
    projectId: $projectId,
    title: $title,
    body: $body,
    assigneeIds: $assigneeIds
  }) {
    projectItem {
      id
      content { ... on DraftIssue { id title } }
    }
  }
}
"""

UPDATE_DRAFT_ITEM_MUTATION = """
mutation($draftIssueId: ID!, $title: String!, $body: String!, $assigneeIds: [ID!]) {
  updateProjectV2DraftIssue(input: {
    draftIssueId: $draftIssueId,
    title: $title,
    body: $body,
    assigneeIds: $assigneeIds
  }) {
    draftIssue { id title }
  }
}
"""

SET_ITEM_FIELD_MUTATION = """
mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: ProjectV2FieldValue!) {
  updateProjectV2ItemFieldValue(input: {
    projectId: $projectId,
    itemId: $itemId,
    fieldId: $fieldId,
    value: $value
  }) {
    projectV2Item { id }
  }
}
"""


# ---------------------------------------------------------------------------
# Helpers de texto y markdown (espejo del fallback de Notion)
# ---------------------------------------------------------------------------


def _normalize_label(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or "").strip())
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s{2,}", " ", normalized).strip()


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
        parts = [part.strip().strip("*") for part in line.strip().strip("|").split("|")]
        if len(parts) < 2:
            continue
        key = _normalize_label(parts[0])
        value = parts[1].strip()
        if key and value:
            rows[key] = value
    return rows


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


def _extract_email(text: str) -> str:
    match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", str(text or ""))
    return match.group(0).strip().lower() if match else ""


def _parse_estimation(text: str) -> tuple[str, float | None]:
    """Extrae (talla, horas) de un valor de estimacion como 'M', '4h' o 'M (4h)'."""
    raw = str(text or "").strip()
    size = ""
    size_match = re.search(r"\b(XS|S|M|L|XL)\b", raw, re.IGNORECASE)
    if size_match:
        size = size_match.group(1).upper()
    hours: float | None = None
    hours_match = re.search(r"(\d+(?:[.,]\d+)?)", raw)
    if hours_match:
        hours = float(hours_match.group(1).replace(",", "."))
    if size and hours is None:
        hours = float(SIZE_HOURS[size])
    if hours is not None and not size:
        size = min(SIZE_HOURS, key=lambda name: abs(SIZE_HOURS[name] - hours))
    return size, hours


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
    size, hours = _parse_estimation(metadata.get("estimacion", ""))
    assigned_raw = metadata.get("asignado a", "")
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
        "size": size,
        "hours": hours,
        "sprint": metadata.get("sprint", ""),
        "state": metadata.get("estado", ""),
        "assignedRaw": assigned_raw,
        "assignedEmail": _extract_email(assigned_raw),
        "dependenciesText": metadata.get("dependencias", ""),
        "metadata": metadata,
    }
    parsed["dependencyStoryIds"] = _parse_story_ids(parsed["dependenciesText"])
    return parsed


def _read_dod_checklist(cwd: str | Path | None = None) -> list[str]:
    base = Path(cwd) if cwd else Path.cwd()
    dod_path = base / "docs" / "dod.md"
    if not dod_path.is_file():
        return []
    items: list[str] = []
    for raw_line in dod_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        bullet = re.match(r"^(?:[-*]|\d+\.)\s*(?:\[[ xX]\]\s*)?(.+)$", line)
        if bullet:
            text = bullet.group(1).strip()
            if text:
                items.append(text)
    return items


def _compose_body(markdown: str, cwd: str | Path | None = None) -> str:
    """El cuerpo es el markdown EN BRUTO de la HU, con la DoD como task list al final."""
    body = (markdown or "").rstrip()
    if "definition of done" in body.lower():
        return body
    dod_items = _read_dod_checklist(cwd)
    if not dod_items:
        return body
    lines = ["", "## Definition of Done", ""]
    lines.extend(f"- [ ] {item}" for item in dod_items)
    return (body + "\n" + "\n".join(lines)).strip()


def _story_matches(item_title: str, story_id: str, full_title: str) -> bool:
    normalized_item = _normalize_label(item_title)
    if story_id:
        normalized_story = _normalize_label(story_id)
        if normalized_item == normalized_story or normalized_item.startswith(normalized_story + " "):
            return True
    if full_title and normalized_item == _normalize_label(full_title):
        return True
    return False


def _resolve_status(parsed: dict[str, Any], override: str = "") -> str:
    """Estado de la HU -> opcion de Status. Prioridad: override > metadato Estado > sprint."""
    override = (override or "").strip()
    if override:
        return override
    state = str(parsed.get("state") or "").strip()
    if state:
        state_norm = _normalize_label(state)
        for name, _color, _desc in STATUS_OPTIONS:
            if _normalize_label(name) == state_norm:
                return name
    sprint = str(parsed.get("sprint") or "").strip().lower()
    if not sprint or sprint in {"backlog", "futuro", "sin sprint", "ninguno", "ninguna"}:
        return "Backlog"
    return "Sprint activo"


# ---------------------------------------------------------------------------
# README y shortDescription del proyecto (autodocumentacion del kanban)
# ---------------------------------------------------------------------------


def _project_short_description(project_name: str) -> str:
    return (
        f"Backlog PSPO Agent · {project_name}: historias con Status, Prioridad, "
        "Talla, Horas, Sprint y Responsable."
    )


def _project_readme(project_name: str) -> str:
    status_rows = "\n".join(
        f"| {name} | {desc} |" for name, _color, desc in STATUS_OPTIONS
    )
    return (
        f"# {project_name} — Backlog PSPO Agent\n\n"
        "Kanban generado por PSPO Agent. Cada historia (HU) es un draft item con "
        "el markdown completo en el cuerpo y sus metadatos mapeados campo a campo.\n\n"
        "## Estados del kanban (campo Status)\n\n"
        "| Estado | Significado y regla de transicion |\n"
        "|---|---|\n"
        f"{status_rows}\n\n"
        "Flujo habitual: Backlog -> Sprint activo -> En progreso -> En revision -> Hecho. "
        "Bloqueada es transversal: una historia entra en Bloqueada cuando tiene una "
        "dependencia sin resolver y vuelve a su estado anterior al desbloquearse.\n\n"
        "## Glosario de campos\n\n"
        "- **Status**: estado del kanban (ver tabla).\n"
        "- **Prioridad**: Critica, Alta, Media o Baja.\n"
        "- **Talla**: estimacion t-shirt (XS=1h, S=2h, M=4h, L=8h, XL=16h).\n"
        "- **Horas**: horas efectivas estimadas (numero).\n"
        "- **Sprint**: sprint asignado, creado bajo demanda segun la HU.\n"
        "- **Responsable**: persona asignada como `Nombre (email)`; ademas se asigna "
        "el usuario real de GitHub cuando el equipo aporta su login.\n\n"
        "## Vistas recomendadas\n\n"
        "La API publica de GitHub no permite crear vistas de Project v2 por "
        "programacion, asi que crealas a mano (30 segundos cada una):\n\n"
        "1. **Tablero por Status**: vista Board agrupada por el campo Status.\n"
        "2. **Tabla por Sprint**: vista Table agrupada por el campo Sprint.\n"
    )


# ---------------------------------------------------------------------------
# Esquema de campos del proyecto
# ---------------------------------------------------------------------------


def _all_fields(project_id: str) -> list[dict[str, Any]]:
    data = _graphql(PROJECT_FIELDS_QUERY, {"projectId": project_id})
    node = data.get("node") or {}
    fields = ((node.get("fields") or {}).get("nodes")) or []
    return [field for field in fields if isinstance(field, dict) and field.get("id")]


def _build_schema(fields: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    schema: dict[str, dict[str, Any]] = {}
    for field in fields:
        name_norm = _normalize_label(str(field.get("name") or ""))
        key = None
        for candidate_key, visible in FIELD_NAMES.items():
            if _normalize_label(visible) == name_norm:
                key = candidate_key
                break
        if not key:
            continue
        options = field.get("options")
        options_full = [
            {
                "id": str(option.get("id") or ""),
                "name": str(option.get("name") or ""),
                "color": str(option.get("color") or "GRAY"),
                "description": str(option.get("description") or ""),
            }
            for option in (options or [])
            if isinstance(option, dict)
        ]
        schema[key] = {
            "fieldId": str(field.get("id") or ""),
            "dataType": str(field.get("dataType") or ""),
            "options": {_normalize_label(opt["name"]): opt["id"] for opt in options_full},
            "optionsFull": options_full,
        }
    return schema


def _resolve_project_schema(project_id: str) -> dict[str, dict[str, Any]]:
    return _build_schema(_all_fields(project_id))


def _option_inputs(options: list[tuple[str, str, str]]) -> list[dict[str, str]]:
    return [
        {"name": name, "color": color, "description": description}
        for name, color, description in options
    ]


def _refresh_schema_entry(schema: dict[str, dict[str, Any]], key: str, field: dict[str, Any]) -> None:
    options_full = [
        {
            "id": str(option.get("id") or ""),
            "name": str(option.get("name") or ""),
            "color": str(option.get("color") or "GRAY"),
            "description": str(option.get("description") or ""),
        }
        for option in (field.get("options") or [])
        if isinstance(option, dict)
    ]
    schema[key] = {
        "fieldId": str(field.get("id") or ""),
        "dataType": str(field.get("dataType") or schema.get(key, {}).get("dataType") or ""),
        "options": {_normalize_label(opt["name"]): opt["id"] for opt in options_full},
        "optionsFull": options_full,
    }


def _ensure_status_field(project_id: str, schema: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Garantiza que el campo Status nativo tiene las 6 opciones estandar."""
    entry = schema.get("status")
    if not entry:
        raise RuntimeError("El proyecto no expone el campo Status nativo.")
    standard_norm = {_normalize_label(name) for name, _c, _d in STATUS_OPTIONS}
    if standard_norm.issubset(set(entry["options"].keys())):
        return {"fieldId": entry["fieldId"], "created": False, "updated": False}
    data = _graphql(UPDATE_FIELD_OPTIONS_MUTATION, {
        "fieldId": entry["fieldId"],
        "options": _option_inputs(STATUS_OPTIONS),
    })
    field = (data.get("updateProjectV2Field") or {}).get("projectV2Field") or {}
    _refresh_schema_entry(schema, "status", field)
    return {"fieldId": entry["fieldId"], "created": False, "updated": True}


def _create_single_select_field(
    project_id: str,
    schema: dict[str, dict[str, Any]],
    key: str,
    options: list[tuple[str, str, str]],
) -> None:
    data = _graphql(CREATE_SINGLE_SELECT_FIELD_MUTATION, {
        "projectId": project_id,
        "name": FIELD_NAMES[key],
        "options": _option_inputs(options),
    })
    field = (data.get("createProjectV2Field") or {}).get("projectV2Field") or {}
    _refresh_schema_entry(schema, key, field)


def _create_simple_field(
    project_id: str,
    schema: dict[str, dict[str, Any]],
    key: str,
    data_type: str,
) -> None:
    data = _graphql(CREATE_SIMPLE_FIELD_MUTATION, {
        "projectId": project_id,
        "name": FIELD_NAMES[key],
        "dataType": data_type,
    })
    field = (data.get("createProjectV2Field") or {}).get("projectV2Field") or {}
    schema[key] = {
        "fieldId": str(field.get("id") or ""),
        "dataType": str(field.get("dataType") or data_type),
        "options": {},
        "optionsFull": [],
    }


def _ensure_project_schema(project_id: str) -> dict[str, dict[str, Any]]:
    """Materializa (idempotente) el esquema de campos del proyecto."""
    schema = _resolve_project_schema(project_id)
    status_result = _ensure_status_field(project_id, schema)
    created: list[str] = []
    if "prioridad" not in schema:
        _create_single_select_field(project_id, schema, "prioridad", PRIORITY_OPTIONS)
        created.append("Prioridad")
    if "talla" not in schema:
        _create_single_select_field(project_id, schema, "talla", SIZE_OPTIONS)
        created.append("Talla")
    if "horas" not in schema:
        _create_simple_field(project_id, schema, "horas", "NUMBER")
        created.append("Horas")
    if "responsable" not in schema:
        _create_simple_field(project_id, schema, "responsable", "TEXT")
        created.append("Responsable")
    schema["_meta"] = {"statusUpdated": status_result.get("updated"), "createdFields": created}
    return schema


def _ensure_sprint_option(project_id: str, schema: dict[str, dict[str, Any]], sprint_name: str) -> str:
    """Crea el campo Sprint bajo demanda y garantiza la opcion del sprint dado."""
    sprint_name = (sprint_name or "").strip()
    if not sprint_name:
        return ""
    norm = _normalize_label(sprint_name)
    entry = schema.get("sprint")
    if not entry:
        _create_single_select_field(
            project_id, schema, "sprint", [(sprint_name, "BLUE", "")]
        )
        return schema["sprint"]["options"].get(norm, "")
    if norm in entry["options"]:
        return entry["options"][norm]
    new_options = [
        {
            "id": opt["id"],
            "name": opt["name"],
            "color": opt["color"],
            "description": opt["description"],
        }
        for opt in entry["optionsFull"]
    ]
    new_options.append({"name": sprint_name, "color": "BLUE", "description": ""})
    data = _graphql(UPDATE_FIELD_OPTIONS_MUTATION, {
        "fieldId": entry["fieldId"],
        "options": new_options,
    })
    field = (data.get("updateProjectV2Field") or {}).get("projectV2Field") or {}
    _refresh_schema_entry(schema, "sprint", field)
    return schema["sprint"]["options"].get(norm, "")


# ---------------------------------------------------------------------------
# Operaciones de proyecto
# ---------------------------------------------------------------------------


def verify_credentials(_: dict[str, Any]) -> dict[str, Any]:
    data = _graphql(VIEWER_QUERY)
    viewer = data.get("viewer") or {}
    scopes = _oauth_scopes()
    has_scope = _has_project_scope(scopes)
    scope_known = bool(scopes)
    result = {
        "ok": True,
        "login": viewer.get("login"),
        "viewerId": viewer.get("id"),
        "authMethod": "gh" if _gh_available() else "token",
        "scopes": scopes,
        "hasProjectScope": has_scope,
        "projectScopeKnown": scope_known,
    }
    if scope_known and not has_scope:
        result["warning"] = (
            "Falta el scope `project`. Ejecuta `gh auth refresh -s project` "
            "o genera un token con el scope `project`."
        )
    return result


def _viewer() -> dict[str, Any]:
    data = _graphql(VIEWER_QUERY)
    viewer = data.get("viewer") or {}
    if not viewer.get("id"):
        raise RuntimeError("No se pudo resolver el usuario autenticado de GitHub.")
    return viewer


def _resolve_user_id(login: str) -> str:
    login = (login or "").strip().lstrip("@")
    if not login:
        return ""
    try:
        data = _graphql(USER_ID_QUERY, {"login": login})
    except RuntimeError:
        return ""
    user = data.get("user") or {}
    return str(user.get("id") or "")


def create_project(args: dict[str, Any]) -> dict[str, Any]:
    viewer = _viewer()
    owner_id = viewer.get("id")
    owner_login = viewer.get("login")
    project_name = (args.get("projectName") or "").strip() or _default_project_name()
    prefix = (args.get("titlePrefix") or _project_title_prefix()).strip()
    title = (args.get("title") or f"{prefix} · {project_name}").strip()

    data = _graphql(CREATE_PROJECT_MUTATION, {"ownerId": owner_id, "title": title})
    project = (data.get("createProjectV2") or {}).get("projectV2") or {}
    project_id = str(project.get("id") or "")
    if not project_id:
        raise RuntimeError("GitHub no devolvio el id del proyecto creado.")

    # Privado + shortDescription + README (autodocumentacion del kanban).
    _graphql(UPDATE_PROJECT_META_MUTATION, {
        "projectId": project_id,
        "shortDescription": _project_short_description(project_name),
        "readme": _project_readme(project_name),
    })

    schema = _ensure_project_schema(project_id)
    meta = schema.get("_meta", {})

    return {
        "ok": True,
        "provider": "github",
        "projectId": project_id,
        "projectNumber": project.get("number"),
        "projectTitle": project.get("title") or title,
        "projectUrl": project.get("url"),
        "projectOwner": owner_login,
        "statusFieldId": schema.get("status", {}).get("fieldId"),
        "statusUpdated": meta.get("statusUpdated"),
        "createdFields": meta.get("createdFields", []),
        "fields": sorted(k for k in schema if k != "_meta"),
    }


def save_project_targets(args: dict[str, Any]) -> dict[str, Any]:
    values = {
        "GITHUB_PROJECT_NUMBER": str(
            args.get("projectNumber") or os.environ.get("GITHUB_PROJECT_NUMBER", "")
        ),
        "GITHUB_PROJECT_ID": args.get("projectId") or os.environ.get("GITHUB_PROJECT_ID", ""),
        "GITHUB_PROJECT_OWNER": args.get("projectOwner")
        or os.environ.get("GITHUB_PROJECT_OWNER", ""),
        "GITHUB_PROJECT_URL": args.get("projectUrl") or os.environ.get("GITHUB_PROJECT_URL", ""),
    }
    return _save_env_values(values)


def setup_targets(args: dict[str, Any]) -> dict[str, Any]:
    project = create_project(args)
    saved = save_project_targets({
        "projectNumber": project.get("projectNumber"),
        "projectId": project.get("projectId"),
        "projectOwner": project.get("projectOwner"),
        "projectUrl": project.get("projectUrl"),
    })
    return {
        "ok": True,
        "provider": "github",
        "projectId": project.get("projectId"),
        "projectNumber": project.get("projectNumber"),
        "projectUrl": project.get("projectUrl"),
        "projectOwner": project.get("projectOwner"),
        "createdFields": project.get("createdFields", []),
        "savedEnvPath": saved.get("envPath"),
        "savedKeys": saved.get("keys"),
    }


def _resolve_project_id(args: dict[str, Any]) -> str:
    project_id = str(args.get("projectId") or "").strip()
    if not project_id:
        project_id = str(os.environ.get("GITHUB_PROJECT_ID") or "").strip()
    if not project_id:
        raise ValueError(
            "projectId es obligatorio. Configura GITHUB_PROJECT_ID o crea el proyecto primero."
        )
    return project_id


def _list_project_items(project_id: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        data = _graphql(PROJECT_ITEMS_QUERY, {"projectId": project_id, "cursor": cursor})
        node = data.get("node") or {}
        items = node.get("items") or {}
        for item in items.get("nodes") or []:
            if isinstance(item, dict):
                results.append(item)
        page_info = items.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = str(page_info.get("endCursor") or "").strip() or None
        if not cursor:
            break
    return results


def find_story_item(args: dict[str, Any]) -> dict[str, Any]:
    project_id = _resolve_project_id(args)
    story_id = str(args.get("storyId") or "").strip()
    full_title = str(args.get("title") or "").strip()
    for item in _list_project_items(project_id):
        content = item.get("content") or {}
        item_title = str(content.get("title") or "").strip()
        if _story_matches(item_title, story_id, full_title):
            return {
                "ok": True,
                "itemId": str(item.get("id") or ""),
                "draftIssueId": str(content.get("id") or ""),
                "title": item_title,
                "item": item,
            }
    return {"ok": False, "itemId": "", "draftIssueId": "", "title": "", "item": None}


def _create_draft_item(project_id: str, title: str, body: str, assignee_ids: list[str]) -> dict[str, Any]:
    data = _graphql(ADD_DRAFT_ITEM_MUTATION, {
        "projectId": project_id,
        "title": title,
        "body": body,
        "assigneeIds": assignee_ids or [],
    })
    item = (data.get("addProjectV2DraftIssue") or {}).get("projectItem") or {}
    content = item.get("content") or {}
    return {
        "itemId": str(item.get("id") or ""),
        "draftIssueId": str(content.get("id") or ""),
    }


def _update_draft_item(draft_issue_id: str, title: str, body: str, assignee_ids: list[str]) -> dict[str, Any]:
    data = _graphql(UPDATE_DRAFT_ITEM_MUTATION, {
        "draftIssueId": draft_issue_id,
        "title": title,
        "body": body,
        "assigneeIds": assignee_ids or [],
    })
    return (data.get("updateProjectV2DraftIssue") or {}).get("draftIssue") or {}


def _set_item_field(project_id: str, item_id: str, field_id: str, value: dict[str, Any]) -> None:
    _graphql(SET_ITEM_FIELD_MUTATION, {
        "projectId": project_id,
        "itemId": item_id,
        "fieldId": field_id,
        "value": value,
    })


def _set_single_select(
    project_id: str,
    item_id: str,
    entry: dict[str, Any] | None,
    value_name: str,
) -> str:
    if not entry or not value_name:
        return ""
    option_id = entry["options"].get(_normalize_label(value_name))
    if not option_id:
        return ""
    _set_item_field(project_id, item_id, entry["fieldId"], {"singleSelectOptionId": option_id})
    return value_name


def set_story_status(args: dict[str, Any]) -> dict[str, Any]:
    project_id = _resolve_project_id(args)
    item_id = str(args.get("itemId") or "").strip()
    if not item_id:
        raise ValueError("itemId es obligatorio para set-story-status.")
    status = str(args.get("status") or "").strip() or "Backlog"
    schema = args.get("schema") or _resolve_project_schema(project_id)
    applied = _set_single_select(project_id, item_id, schema.get("status"), status)
    if not applied:
        raise ValueError(f"No se pudo resolver la opcion de estado '{status}'.")
    return {"ok": True, "itemId": item_id, "status": applied}


def _apply_story_fields(
    project_id: str,
    item_id: str,
    schema: dict[str, dict[str, Any]],
    parsed: dict[str, Any],
    status: str,
    responsable_text: str,
) -> dict[str, Any]:
    """Mapea campo a campo los metadatos de la HU a los campos del proyecto."""
    mapping: dict[str, Any] = {}

    applied = _set_single_select(project_id, item_id, schema.get("status"), status)
    if applied:
        mapping["Status"] = applied

    priority = str(parsed.get("priority") or "").strip()
    applied = _set_single_select(project_id, item_id, schema.get("prioridad"), priority)
    if applied:
        mapping["Prioridad"] = applied

    size = str(parsed.get("size") or "").strip()
    applied = _set_single_select(project_id, item_id, schema.get("talla"), size)
    if applied:
        mapping["Talla"] = applied

    hours = parsed.get("hours")
    horas_entry = schema.get("horas")
    if horas_entry and hours is not None:
        _set_item_field(project_id, item_id, horas_entry["fieldId"], {"number": float(hours)})
        mapping["Horas"] = float(hours)

    sprint = str(parsed.get("sprint") or "").strip()
    if sprint:
        option_id = _ensure_sprint_option(project_id, schema, sprint)
        if option_id:
            _set_item_field(
                project_id, item_id, schema["sprint"]["fieldId"], {"singleSelectOptionId": option_id}
            )
            mapping["Sprint"] = sprint

    responsable_entry = schema.get("responsable")
    if responsable_entry and responsable_text:
        _set_item_field(project_id, item_id, responsable_entry["fieldId"], {"text": responsable_text})
        mapping["Responsable"] = responsable_text

    return mapping


def sync_vision_from_markdown(args: dict[str, Any]) -> dict[str, Any]:
    file_path = str(args.get("filePath") or "docs/vision.md").strip()
    markdown = _read_markdown_file(file_path)
    title = str(args.get("title") or "HU-00 · Vision").strip() or "HU-00 · Vision"
    project_id = _resolve_project_id(args)
    body = _compose_body(markdown, args.get("cwd"))

    existing = find_story_item({"projectId": project_id, "storyId": "HU-00", "title": title})
    if existing.get("ok") and existing.get("draftIssueId"):
        _update_draft_item(existing["draftIssueId"], title, body, [])
        return {
            "ok": True,
            "created": False,
            "itemId": existing.get("itemId"),
            "draftIssueId": existing.get("draftIssueId"),
            "title": title,
        }

    created = _create_draft_item(project_id, title, body, [])
    return {
        "ok": True,
        "created": True,
        "itemId": created.get("itemId"),
        "draftIssueId": created.get("draftIssueId"),
        "title": title,
    }


def sync_story_from_markdown(args: dict[str, Any]) -> dict[str, Any]:
    parsed = parse_story_markdown(args)
    project_id = _resolve_project_id(args)
    schema = args.get("schema") or _resolve_project_schema(project_id)
    status = _resolve_status(parsed, str(args.get("status") or ""))
    body = _compose_body(parsed["markdown"], args.get("cwd"))
    title = parsed["fullTitle"]

    # Asignacion: Responsable (texto) siempre; assignee real si hay login de GitHub.
    responsable_text = str(parsed.get("assignedRaw") or "").strip()
    assigned_email = str(parsed.get("assignedEmail") or "").strip()
    github_login = str(args.get("assignedGithub") or "").strip().lstrip("@")
    assignee_ids: list[str] = []
    if github_login:
        user_id = _resolve_user_id(github_login)
        if user_id:
            assignee_ids = [user_id]

    if assignee_ids:
        assignment_status = "resolved"
    elif assigned_email:
        assignment_status = "unresolved"
    else:
        assignment_status = "unassigned"

    existing = find_story_item({
        "projectId": project_id,
        "storyId": parsed["storyId"],
        "title": title,
    })
    if existing.get("ok") and existing.get("draftIssueId"):
        _update_draft_item(existing["draftIssueId"], title, body, assignee_ids)
        item_id = existing.get("itemId")
        created = False
    else:
        result = _create_draft_item(project_id, title, body, assignee_ids)
        item_id = result.get("itemId")
        created = True

    field_mapping: dict[str, Any] = {}
    if item_id:
        field_mapping = _apply_story_fields(
            project_id, item_id, schema, parsed, status, responsable_text
        )

    return {
        "ok": True,
        "created": created,
        "itemId": item_id,
        "storyId": parsed["storyId"],
        "title": title,
        "status": status,
        "fieldMapping": field_mapping,
        "assignment": {
            "responsable": responsable_text,
            "email": assigned_email,
            "github": github_login,
            "assigneeApplied": bool(assignee_ids),
            "status": assignment_status,
        },
        "parsed": {
            "priority": parsed["priority"],
            "size": parsed["size"],
            "hours": parsed["hours"],
            "sprint": parsed["sprint"],
            "state": parsed["state"],
            "dependencyStoryIds": parsed["dependencyStoryIds"],
        },
    }


# ---------------------------------------------------------------------------
# Equipo: mapa email -> login de GitHub desde el CSV compatible
# ---------------------------------------------------------------------------


REQUIRED_TEAM_COLUMNS = {
    "nombre",
    "email",
    "rol",
    "categoria",
    "dedicacion",
    "usa_agente_ia",
}


def _load_team_github_map(cwd: str | Path | None = None) -> dict[str, str]:
    import csv

    base = Path(cwd) if cwd else Path.cwd()
    candidates = sorted(base.glob("*.csv"))
    candidates.extend(sorted((base / ".pspo-agent" / "inbox").glob("*.csv")))
    for path in candidates:
        if not path.is_file():
            continue
        try:
            with path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                fieldnames = {name.strip().lower() for name in (reader.fieldnames or [])}
                if not REQUIRED_TEAM_COLUMNS.issubset(fieldnames):
                    continue
                if "github" not in fieldnames:
                    return {}
                mapping: dict[str, str] = {}
                for row in reader:
                    email = str(row.get("email") or "").strip().lower()
                    login = str(row.get("github") or "").strip().lstrip("@")
                    if email and login:
                        mapping[email] = login
                return mapping
        except OSError:
            continue
    return {}


# ---------------------------------------------------------------------------
# Report local del lote
# ---------------------------------------------------------------------------


def _write_markdown_report(report_path: Path, content: str) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _render_github_publish_report(result: dict[str, Any]) -> str:
    lines = [
        "# Publish Report",
        "",
        "- Provider: github",
        f"- Generated at: {datetime.now(timezone.utc).isoformat()}",
        f"- Project: {result.get('projectUrl', '') or result.get('projectId', '')}",
        f"- Stories dir: {result.get('storiesDir', '')}",
        f"- Story count: {result.get('storyCount', 0)}",
        f"- Synced stories: {result.get('syncedStoryCount', 0)}",
        f"- Dependency resolution: {result.get('dependencySyncCount', 0)}",
        "",
        "> Nota: los draft items de GitHub Projects no admiten adjuntos; el markdown",
        "> completo de cada HU viaja en el cuerpo del item.",
        "",
    ]

    vision = result.get("vision") or {}
    if vision:
        lines.extend([
            "## Vision",
            "",
            f"- Item ID: {vision.get('itemId', '')}",
            f"- Created: {vision.get('created', False)}",
            "",
        ])

    lines.extend([
        "## Mapeo por HU (campo a campo)",
        "",
        "| Story | Item ID | Status | Prioridad | Talla | Horas | Sprint | Responsable |",
        "|---|---|---|---|---|---|---|---|",
    ])
    for item in result.get("firstPass") or []:
        if not isinstance(item, dict):
            continue
        fm = item.get("fieldMapping") or {}
        lines.append(
            f"| {item.get('storyId', '')} | {item.get('itemId', '')} | "
            f"{fm.get('Status', '')} | {fm.get('Prioridad', '')} | {fm.get('Talla', '')} | "
            f"{fm.get('Horas', '')} | {fm.get('Sprint', '')} | {fm.get('Responsable', '')} |"
        )

    unresolved_assignments = result.get("unresolvedAssignments") or []
    if unresolved_assignments:
        lines.extend([
            "",
            "## Unresolved Assignments",
            "",
            "| Story | Responsable | Email | File |",
            "|---|---|---|---|",
        ])
        for item in unresolved_assignments:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"| {item.get('storyId', '')} | {item.get('responsable', '')} | "
                f"{item.get('email', '')} | {item.get('filePath', '')} |"
            )

    dependencies = result.get("secondPass") or []
    resolved_deps = [
        item for item in dependencies
        if isinstance(item, dict) and item.get("resolvedDependencyItemIds")
    ]
    if resolved_deps:
        lines.extend([
            "",
            "## Dependencies",
            "",
            "| Story | Resolved | Unresolved |",
            "|---|---:|---|",
        ])
        for item in resolved_deps:
            unresolved = ", ".join(item.get("unresolvedDependencyStoryIds") or [])
            lines.append(
                f"| {item.get('storyId', '')} | "
                f"{len(item.get('resolvedDependencyItemIds') or [])} | {unresolved} |"
            )

    errors = result.get("errors") or []
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
                f"| {item.get('scope', '')} | {item.get('filePath', '')} | "
                f"{str(item.get('error', '')).replace('|', '/')} |"
            )

    return "\n".join(lines)


def sync_stories_from_folder(args: dict[str, Any]) -> dict[str, Any]:
    stories_dir = Path(str(args.get("storiesDir") or "docs/historias").strip()).expanduser()
    if not stories_dir.is_dir():
        raise ValueError(f"No existe el directorio de historias: {stories_dir}")

    files = sorted(path for path in stories_dir.glob("HU-*.md") if path.is_file())
    if not files:
        raise ValueError(f"No hay historias HU-*.md en {stories_dir}")

    project_id = _resolve_project_id(args)
    schema = args.get("schema") or _resolve_project_schema(project_id)
    cwd = args.get("cwd") or str(Path.cwd())
    team_map = _load_team_github_map(cwd)

    first_pass: list[dict[str, Any]] = []
    second_pass: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    unresolved_assignments: list[dict[str, Any]] = []
    report_path = Path(
        str(args.get("reportPath") or (stories_dir.parent / "publish-report.md"))
    ).expanduser()

    vision_path = str(args.get("visionFilePath") or "docs/vision.md").strip()
    vision_result = None
    if bool(args.get("syncVision", True)) and Path(vision_path).is_file():
        try:
            vision_result = sync_vision_from_markdown({
                "projectId": project_id,
                "filePath": vision_path,
                "title": args.get("visionTitle") or "HU-00 · Vision",
                "cwd": cwd,
            })
        except Exception as exc:
            errors.append({"scope": "vision", "filePath": vision_path, "error": str(exc)})

    for path in files:
        try:
            parsed = parse_story_markdown({"filePath": str(path)})
            assigned_github = team_map.get(str(parsed.get("assignedEmail") or "").strip().lower(), "")
            result = sync_story_from_markdown({
                "projectId": project_id,
                "filePath": str(path),
                "schema": schema,
                "assignedGithub": assigned_github,
                "status": args.get("status"),
                "cwd": cwd,
            })
            first_pass.append({
                "filePath": str(path),
                "storyId": result.get("storyId"),
                "itemId": result.get("itemId"),
                "created": result.get("created"),
                "status": result.get("status"),
                "fieldMapping": result.get("fieldMapping"),
                "assignment": result.get("assignment"),
            })
            if (result.get("assignment") or {}).get("status") == "unresolved":
                unresolved_assignments.append({
                    "filePath": str(path),
                    "storyId": result.get("storyId"),
                    "responsable": (result.get("assignment") or {}).get("responsable", ""),
                    "email": (result.get("assignment") or {}).get("email", ""),
                })
        except Exception as exc:
            errors.append({"scope": "story", "filePath": str(path), "error": str(exc)})

    # Segunda pasada: resolver dependencias HU-XX a item ids existentes.
    # Los draft items no admiten relaciones nativas, asi que se reporta la
    # resolucion como informacion de trazabilidad.
    for path in files:
        try:
            parsed = parse_story_markdown({"filePath": str(path)})
            dependency_ids = parsed.get("dependencyStoryIds") or []
            if not dependency_ids:
                continue
            resolved: list[str] = []
            unresolved: list[str] = []
            for dependency_story_id in dependency_ids:
                found = find_story_item({"projectId": project_id, "storyId": dependency_story_id})
                if found.get("ok") and found.get("itemId"):
                    resolved.append(found["itemId"])
                else:
                    unresolved.append(dependency_story_id)
            second_pass.append({
                "filePath": str(path),
                "storyId": parsed.get("storyId"),
                "resolvedDependencyItemIds": resolved,
                "unresolvedDependencyStoryIds": unresolved,
            })
        except Exception as exc:
            errors.append({"scope": "dependencies", "filePath": str(path), "error": str(exc)})

    result = {
        "ok": not errors,
        "provider": "github",
        "projectId": project_id,
        "projectUrl": os.environ.get("GITHUB_PROJECT_URL", ""),
        "storiesDir": str(stories_dir),
        "vision": vision_result,
        "firstPass": first_pass,
        "secondPass": second_pass,
        "errors": errors,
        "storyCount": len(files),
        "syncedStoryCount": len(first_pass),
        "dependencySyncCount": len(second_pass),
        "unresolvedAssignments": unresolved_assignments,
        "reportPath": str(report_path),
    }
    _write_markdown_report(report_path, _render_github_publish_report(result))
    return result


def help_info(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "provider": "github",
        "supportedTools": [
            "list-tools",
            "env-status",
            "verify-credentials",
            "create-project",
            "setup-targets",
            "save-project-targets",
            "sync-vision-from-markdown",
            "parse-story-markdown",
            "find-story-item",
            "set-story-status",
            "sync-story-from-markdown",
            "sync-stories-from-folder",
        ],
        "onboardingSequence": [
            ".pspo-agent/runtime/github-fallback.sh env-status --pretty",
            ".pspo-agent/runtime/github-fallback.sh verify-credentials --pretty",
            ".pspo-agent/runtime/github-fallback.sh create-project --pretty",
            ".pspo-agent/runtime/github-fallback.sh save-project-targets --pretty",
        ],
        "publishSequence": [
            "sync-vision-from-markdown",
            "parse-story-markdown",
            "sync-story-from-markdown",
            "sync-stories-from-folder",
        ],
        "projectFields": list(FIELD_NAMES.values()),
        "notes": [
            "Requiere gh autenticado (con scope project) o GITHUB_TOKEN/GH_TOKEN.",
            "Cada metadato de la HU se mapea a su campo: Status, Prioridad, Talla, Horas, Sprint, Responsable.",
            "Los draft items no admiten adjuntos; el markdown en bruto va en el cuerpo.",
            "La asignacion real necesita el login de GitHub (columna github del CSV de equipo).",
            "La API publica no permite crear vistas: se documentan en el README del proyecto.",
        ],
    }


TOOL_MAP = {
    "help": help_info,
    "list-tools": help_info,
    "verify-credentials": verify_credentials,
    "create-project": create_project,
    "setup-targets": setup_targets,
    "save-project-targets": save_project_targets,
    "sync-vision-from-markdown": sync_vision_from_markdown,
    "parse-story-markdown": parse_story_markdown,
    "find-story-item": find_story_item,
    "set-story-status": set_story_status,
    "sync-story-from-markdown": sync_story_from_markdown,
    "sync-stories-from-folder": sync_stories_from_folder,
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fallback oficial y seguro para GitHub Projects v2 en PSPO Agent."
    )
    parser.add_argument("tool", help="Operacion a ejecutar.")
    parser.add_argument(
        "tool_arg",
        nargs="?",
        default=None,
        help="Argumento posicional opcional para helpers como set-story-status.",
    )
    parser.add_argument("--args-json", default=None)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--project-id", default=None)
    parser.add_argument("--project-name", default=None)
    parser.add_argument("--title", default=None)
    parser.add_argument("--title-prefix", default=None)
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
                "projectId": args.project_id,
                "projectName": args.project_name,
                "title": args.title,
                "titlePrefix": args.title_prefix,
            }
            for key, value in flag_mapping.items():
                if value not in (None, ""):
                    payload.setdefault(key, value)
            if args.tool_arg:
                if args.tool == "set-story-status":
                    payload.setdefault("itemId", args.tool_arg)
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
