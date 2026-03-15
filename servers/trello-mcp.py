#!/usr/bin/env python3
"""
Servidor MCP para la integracion con la API de Trello.
Plugin PSPO Agent para Claude Code.

Protocolo: JSON-RPC 2.0 sobre stdio (Content-Length headers).
Dependencias: ninguna (solo stdlib de Python 3.8+).
"""

import hashlib
import json
import logging
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="[trello-mcp] %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("trello-mcp")

# ---------------------------------------------------------------------------
# Cliente HTTP para la API de Trello
# ---------------------------------------------------------------------------

TRELLO_BASE = "https://api.trello.com"
MAX_RETRIES = 3
BACKOFF_DELAYS = [1.0, 2.0, 4.0]
RETRYABLE_CODES = {429, 500, 502, 503, 504}
RATE_LIMIT_PER_SECOND = 10

API_KEY_RE = re.compile(r"^[a-f0-9]{32}$", re.IGNORECASE)
TOKEN_RE = re.compile(r"^ATTA[a-zA-Z0-9]+$")
TOKEN_MIN_LEN = 41
TRELLO_ID_RE = re.compile(r"^[a-f0-9]{24}$", re.IGNORECASE)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_MESSAGE_SIZE = 10 * 1024 * 1024  # 10 MB

LABEL_COLORS = [
    "green", "yellow", "orange", "red", "purple",
    "blue", "sky", "lime", "pink", "black",
]


def _validate_trello_id(value: str, field_name: str) -> str:
    """Valida que un ID de Trello tenga formato correcto (24 hex)."""
    trimmed = value.strip()
    if not TRELLO_ID_RE.match(trimmed):
        raise ValueError(
            f"{field_name} no tiene formato valido de ID de Trello "
            f"(se esperan 24 caracteres hexadecimales, recibido: '{trimmed}')."
        )
    return trimmed


def _mask(value: str) -> str:
    if len(value) <= 4:
        return "****"
    return f"****{value[-4:]}"


def _error_description(status: int, body: str) -> dict:
    body = body[:200] if body else "sin detalle"
    messages = {
        400: ("Peticion incorrecta: " + body,
              "Verifica los parametros de la peticion."),
        401: ("Credenciales de Trello invalidas o token expirado.",
              "Ejecuta el onboarding para reconfigurar las credenciales."),
        403: ("Sin permisos para acceder a este recurso de Trello.",
              "Verifica que el token tiene los permisos necesarios (scope: read,write)."),
        404: ("Recurso no encontrado en Trello: " + body,
              "Verifica que el ID del recurso es correcto y que no ha sido eliminado."),
        429: ("Trello ha bloqueado la peticion por demasiadas peticiones.",
              "Espera unos segundos e intentalo de nuevo."),
    }
    if status in messages:
        msg, action = messages[status]
        return {"message": msg, "suggestedAction": action}
    if status >= 500:
        return {
            "message": f"Error del servidor de Trello ({status}): {body}",
            "suggestedAction": "Trello tiene problemas temporales. Intentalo de nuevo en unos minutos.",
        }
    return {
        "message": f"Error inesperado de Trello ({status}): {body}",
        "suggestedAction": "Contacta con soporte si el error persiste.",
    }


class TrelloClient:
    def __init__(self, api_key: str, token: str):
        api_key = api_key.strip()
        token = token.strip()

        if not api_key:
            raise ValueError("TRELLO_API_KEY es obligatoria.")
        if not token:
            raise ValueError("TRELLO_TOKEN es obligatorio.")
        if not API_KEY_RE.match(api_key):
            raise ValueError(
                "TRELLO_API_KEY tiene formato invalido. "
                "Se esperan 32 caracteres hexadecimales."
            )
        if len(token) < TOKEN_MIN_LEN or not TOKEN_RE.match(token):
            raise ValueError(
                "TRELLO_TOKEN tiene formato invalido. "
                "Se espera prefijo ATTA, longitud minima 41 y solo caracteres alfanumericos."
            )

        self._api_key = api_key
        self._token = token
        self._timestamps: list = []
        log.info("Credenciales validadas. API Key: %s, Token: %s",
                 _mask(api_key), _mask(token))

    def _build_url(self, path: str, params: dict = None) -> str:
        qs = {"key": self._api_key, "token": self._token}
        if params:
            qs.update(params)
        return f"{TRELLO_BASE}{path}?{urllib.parse.urlencode(qs)}"

    def _wait_rate_limit(self):
        now = time.time()
        self._timestamps = [t for t in self._timestamps if now - t < 1.0]
        if len(self._timestamps) >= RATE_LIMIT_PER_SECOND:
            wait = 1.0 - (now - self._timestamps[0])
            if wait > 0:
                log.info("Rate limit activo. Esperando %.0fms.", wait * 1000)
                time.sleep(wait)
            now = time.time()
            self._timestamps = [t for t in self._timestamps if now - t < 1.0]
        self._timestamps.append(time.time())

    def _request(self, method: str, path: str, params: dict = None,
                 body: dict = None):
        url = self._build_url(path, params)
        log.info("API %s %s", method, path)

        for attempt in range(MAX_RETRIES):
            self._wait_rate_limit()
            data = None
            headers = {}
            if body is not None:
                data = json.dumps(body).encode("utf-8")
                headers["Content-Type"] = "application/json"

            req = urllib.request.Request(url, data=data, headers=headers,
                                        method=method)
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                resp_body = ""
                try:
                    resp_body = e.read().decode("utf-8", errors="replace")
                except Exception:
                    pass

                log.info("Error API HTTP %d en %s: %s", e.code, path, resp_body)

                if e.code not in RETRYABLE_CODES:
                    info = _error_description(e.code, resp_body)
                    raise RuntimeError(
                        f"[HTTP {e.code}] {info['message']} | {info['suggestedAction']}"
                    )
                if attempt == MAX_RETRIES - 1:
                    info = _error_description(e.code, resp_body)
                    raise RuntimeError(
                        f"[HTTP {e.code}] {info['message']} | {info['suggestedAction']}"
                    )
                delay = BACKOFF_DELAYS[attempt] if attempt < len(BACKOFF_DELAYS) else 4.0
                log.info("Reintento %d/%d tras %.0fms de backoff.",
                         attempt + 1, MAX_RETRIES, delay * 1000)
                time.sleep(delay)
            except urllib.error.URLError as e:
                log.info("Error de red en %s: %s", path, e.reason)
                if attempt == MAX_RETRIES - 1:
                    raise RuntimeError(
                        f"Error de red al conectar con Trello: {e.reason} | "
                        "Verifica tu conexion a internet e intentalo de nuevo."
                    )
                delay = BACKOFF_DELAYS[attempt] if attempt < len(BACKOFF_DELAYS) else 4.0
                log.info("Reintento %d/%d tras error de red.", attempt + 1, MAX_RETRIES)
                time.sleep(delay)

        raise RuntimeError("Error inesperado: se agotaron los reintentos.")

    def get(self, path: str, params: dict = None):
        return self._request("GET", path, params=params)

    def post(self, path: str, body: dict):
        return self._request("POST", path, body=body)

    def put(self, path: str, body: dict):
        return self._request("PUT", path, body=body)

    def delete(self, path: str):
        return self._request("DELETE", path)


# ---------------------------------------------------------------------------
# Handlers de las herramientas
# ---------------------------------------------------------------------------

def handle_verify_credentials(client: TrelloClient, _args: dict) -> dict:
    member = client.get("/1/members/me")
    return {
        "id": member["id"],
        "fullName": member["fullName"],
        "username": member["username"],
        "url": member["url"],
    }


def handle_list_boards(client: TrelloClient, args: dict) -> dict:
    filt = args.get("filter", "open")
    boards = client.get("/1/members/me/boards",
                        {"filter": filt, "fields": "id,name,url,closed"})
    return {
        "boards": [
            {"id": b["id"], "name": b["name"], "url": b["url"],
             "closed": b.get("closed", False)}
            for b in boards
        ]
    }


def handle_get_board(client: TrelloClient, args: dict) -> dict:
    board_id = _validate_trello_id(args.get("boardId") or "", "boardId")
    board = client.get(f"/1/boards/{board_id}",
                       {"lists": "open", "labels": "all", "fields": "id,name,url"})
    return {
        "id": board["id"],
        "name": board["name"],
        "url": board["url"],
        "lists": board.get("lists", []),
        "labels": board.get("labels", []),
    }


def handle_create_board(client: TrelloClient, args: dict) -> dict:
    name = (args.get("name") or "").strip()
    if not name:
        raise ValueError("name es obligatorio para crear un tablero.")
    board = client.post("/1/boards", {
        "name": name,
        "defaultLists": args.get("defaultLists", False),
    })
    return {"id": board["id"], "name": board["name"], "url": board["url"]}


def handle_manage_lists(client: TrelloClient, args: dict) -> dict:
    board_id = _validate_trello_id(args.get("boardId") or "", "boardId")
    action = args.get("action", "")
    list_id = (args.get("listId") or "").strip()
    name = (args.get("name") or "").strip()
    pos = args.get("pos")

    def _fmt(lst):
        return {"id": lst["id"], "name": lst["name"],
                "pos": lst.get("pos", 0), "closed": lst.get("closed", False)}

    if action == "create":
        if not name:
            raise ValueError("name es obligatorio para crear una lista.")
        body = {"name": name}
        if pos is not None:
            body["pos"] = pos
        return _fmt(client.post(f"/1/boards/{board_id}/lists", body))

    if action == "rename":
        list_id = _validate_trello_id(list_id, "listId")
        if not name:
            raise ValueError("name es obligatorio para renombrar una lista.")
        return _fmt(client.put(f"/1/lists/{list_id}", {"name": name}))

    if action == "reorder":
        list_id = _validate_trello_id(list_id, "listId")
        if pos is None:
            raise ValueError("pos es obligatorio para reordenar una lista.")
        return _fmt(client.put(f"/1/lists/{list_id}", {"pos": pos}))

    if action == "archive":
        list_id = _validate_trello_id(list_id, "listId")
        return _fmt(client.put(f"/1/lists/{list_id}", {"closed": True}))

    raise ValueError(f'Accion "{action}" no reconocida. Usa: create, rename, reorder, archive.')


def handle_manage_labels(client: TrelloClient, args: dict) -> dict:
    board_id = _validate_trello_id(args.get("boardId") or "", "boardId")
    action = args.get("action", "")
    label_id = (args.get("labelId") or "").strip()
    name = (args.get("name") or "").strip()
    color = args.get("color")

    def _fmt(lbl):
        return {"id": lbl["id"], "name": lbl.get("name", ""),
                "color": lbl.get("color")}

    if action == "create":
        if not name:
            raise ValueError("name es obligatorio para crear una etiqueta.")
        return _fmt(client.post(f"/1/boards/{board_id}/labels",
                                {"name": name, "color": color}))

    if action == "update":
        label_id = _validate_trello_id(label_id, "labelId")
        body = {}
        if name:
            body["name"] = name
        if color is not None:
            body["color"] = color
        return _fmt(client.put(f"/1/labels/{label_id}", body))

    if action == "delete":
        label_id = _validate_trello_id(label_id, "labelId")
        client.delete(f"/1/labels/{label_id}")
        return {"id": label_id, "name": name or "", "color": color}

    raise ValueError(f'Accion "{action}" no reconocida. Usa: create, update, delete.')


def _pspo_id_tag(card_name: str, card_desc: str) -> str:
    h = hashlib.sha256(f"{card_name}::{card_desc}".encode()).hexdigest()[:8]
    prefix = card_name.split(":")[0].strip()
    return f"<!-- pspo-id: {prefix}-{h} -->"


def handle_create_cards(client: TrelloClient, args: dict) -> dict:
    list_id = _validate_trello_id(args.get("listId") or "", "listId")
    cards = args.get("cards") or []
    if not cards:
        raise ValueError("Al menos una tarjeta es necesaria.")

    created = []
    failed = []

    for card in cards:
        try:
            desc = card.get("desc", "")
            name = card.get("name", "")
            if not re.search(r"<!-- pspo-id: .+? -->", desc):
                desc = f"{desc}\n\n{_pspo_id_tag(name, desc)}"

            body = {"idList": list_id, "name": name, "desc": desc}
            labels = card.get("idLabels")
            if labels:
                body["idLabels"] = ",".join(labels)
            pos = card.get("pos")
            if pos:
                body["pos"] = pos
            members = card.get("idMembers")
            if members:
                body["idMembers"] = ",".join(members)

            result = client.post("/1/cards", body)
            created.append({
                "id": result["id"], "name": result["name"],
                "url": result["url"],
            })
        except Exception as e:
            failed.append({"name": card.get("name", "?"), "error": str(e)})

    return {"created": created, "failed": failed}


def handle_search_cards(client: TrelloClient, args: dict) -> dict:
    board_id = _validate_trello_id(args.get("boardId") or "", "boardId")
    query = (args.get("query") or "").strip().lower()

    all_cards = client.get(f"/1/boards/{board_id}/cards",
                           {"fields": "id,name,desc,url,idList,idLabels"})
    if query:
        all_cards = [c for c in all_cards
                     if query in c.get("name", "").lower()
                     or query in c.get("desc", "").lower()]

    return {
        "cards": [
            {"id": c["id"], "name": c["name"], "desc": c.get("desc", ""),
             "url": c["url"], "idList": c.get("idList", ""),
             "idLabels": c.get("idLabels", [])}
            for c in all_cards
        ]
    }


def handle_add_checklist(client: TrelloClient, args: dict) -> dict:
    card_id = _validate_trello_id(args.get("cardId") or "", "cardId")
    name = (args.get("name") or "").strip()
    if not name:
        raise ValueError("name es obligatorio para crear un checklist.")
    items = args.get("items") or []
    if not items:
        raise ValueError("Al menos un item es necesario en el checklist.")

    checklist = client.post(f"/1/cards/{card_id}/checklists", {"name": name})
    checklist_id = checklist["id"]

    created_items = []
    for item in items:
        item_name = item if isinstance(item, str) else item.get("name", "")
        if not item_name.strip():
            continue
        result = client.post(f"/1/checklists/{checklist_id}/checkItems",
                             {"name": item_name.strip()})
        created_items.append({
            "id": result.get("id", ""),
            "name": result.get("name", item_name),
        })

    return {
        "checklistId": checklist_id,
        "name": name,
        "cardId": card_id,
        "items": created_items,
    }


def handle_attach_file(client: TrelloClient, args: dict) -> dict:
    card_id = _validate_trello_id(args.get("cardId") or "", "cardId")
    file_name = (args.get("fileName") or "").strip()
    if not file_name:
        raise ValueError("fileName es obligatorio para adjuntar un fichero.")
    # Sanitizar fileName: eliminar caracteres peligrosos para cabeceras multipart
    file_name = re.sub(r'["\r\n\x00]', '_', file_name)
    content = args.get("content") or ""
    if not content:
        raise ValueError("content es obligatorio (contenido del fichero a adjuntar).")

    boundary = uuid.uuid4().hex
    body_parts = []
    body_parts.append(
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="name"\r\n'
        f'\r\n'
        f'{file_name}'
    )
    body_parts.append(
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="{file_name}"\r\n'
        f'Content-Type: text/markdown\r\n'
        f'\r\n'
        f'{content}'
    )
    body_parts.append(f'--{boundary}--')
    body_bytes = '\r\n'.join(body_parts).encode('utf-8')

    url = client._build_url(f"/1/cards/{card_id}/attachments")
    log.info("API POST /1/cards/%s/attachments (multipart)", card_id)

    for attempt in range(MAX_RETRIES):
        client._wait_rate_limit()
        req = urllib.request.Request(
            url,
            data=body_bytes,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return {
                    "id": result.get("id", ""),
                    "name": result.get("name", file_name),
                    "url": result.get("url", ""),
                    "cardId": card_id,
                }
        except urllib.error.HTTPError as e:
            resp_body = ""
            try:
                resp_body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            if e.code not in RETRYABLE_CODES or attempt == MAX_RETRIES - 1:
                info = _error_description(e.code, resp_body)
                raise RuntimeError(
                    f"[HTTP {e.code}] {info['message']} | {info['suggestedAction']}"
                )
            delay = BACKOFF_DELAYS[attempt] if attempt < len(BACKOFF_DELAYS) else 4.0
            time.sleep(delay)
        except urllib.error.URLError as e:
            if attempt == MAX_RETRIES - 1:
                raise RuntimeError(
                    f"Error de red al adjuntar fichero: {e.reason} | "
                    "Verifica tu conexion a internet e intentalo de nuevo."
                )
            delay = BACKOFF_DELAYS[attempt] if attempt < len(BACKOFF_DELAYS) else 4.0
            time.sleep(delay)

    raise RuntimeError("Error inesperado: se agotaron los reintentos en attach-file.")


# ---------------------------------------------------------------------------
def handle_get_board_members(client: TrelloClient, args: dict) -> dict:
    board_id = _validate_trello_id(args.get("boardId") or "", "boardId")
    members = client.get(f"/1/boards/{board_id}/members",
                         {"fields": "id,fullName,username"})
    result = []
    for m in members:
        entry = {
            "id": m["id"],
            "fullName": m.get("fullName", ""),
            "username": m.get("username", ""),
        }
        result.append(entry)
    return {"members": result}


def handle_invite_member(client: TrelloClient, args: dict) -> dict:
    board_id = _validate_trello_id(args.get("boardId") or "", "boardId")
    email = (args.get("email") or "").strip()
    if not email or not EMAIL_RE.match(email):
        raise ValueError("email es obligatorio y debe tener formato valido (usuario@dominio.ext).")
    full_name = (args.get("fullName") or "").strip()
    member_type = (args.get("type") or "normal").strip()
    if member_type not in ("admin", "normal", "observer"):
        raise ValueError(
            f'Tipo de miembro "{member_type}" no reconocido. Usa: admin, normal, observer.'
        )

    url = client._build_url(
        f"/1/boards/{board_id}/members",
        {"email": email},
    )
    body = {"fullName": full_name or email.split("@")[0], "type": member_type}
    data = json.dumps(body).encode("utf-8")
    log.info("API PUT /1/boards/%s/members (invite %s)", board_id, email)

    for attempt in range(MAX_RETRIES):
        client._wait_rate_limit()
        req = urllib.request.Request(url, data=data, method="PUT",
                                    headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return {
                    "boardId": board_id,
                    "email": email,
                    "fullName": full_name,
                    "type": member_type,
                    "membersInvited": result.get("membersInvited", []),
                }
        except urllib.error.HTTPError as e:
            resp_body = ""
            try:
                resp_body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            if e.code not in RETRYABLE_CODES or attempt == MAX_RETRIES - 1:
                info = _error_description(e.code, resp_body)
                raise RuntimeError(
                    f"[HTTP {e.code}] {info['message']} | {info['suggestedAction']}"
                )
            delay = BACKOFF_DELAYS[attempt] if attempt < len(BACKOFF_DELAYS) else 4.0
            time.sleep(delay)
        except urllib.error.URLError as e:
            if attempt == MAX_RETRIES - 1:
                raise RuntimeError(
                    f"Error de red al invitar miembro: {e.reason} | "
                    "Verifica tu conexion a internet e intentalo de nuevo."
                )
            delay = BACKOFF_DELAYS[attempt] if attempt < len(BACKOFF_DELAYS) else 4.0
            time.sleep(delay)

    raise RuntimeError("Error inesperado: se agotaron los reintentos en invite-member.")


# Definicion de herramientas MCP
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "verify-credentials",
        "description": "Verifica que la API Key y el Token de Trello son validos. Devuelve el nombre de usuario de la cuenta conectada.",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": handle_verify_credentials,
    },
    {
        "name": "list-boards",
        "description": "Lista los tableros de Trello del usuario autenticado.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filter": {
                    "type": "string",
                    "enum": ["open", "closed", "all"],
                    "description": "Filtro de estado: open (defecto), closed, all",
                },
            },
        },
        "handler": handle_list_boards,
    },
    {
        "name": "get-board",
        "description": "Obtiene un tablero de Trello con sus listas y etiquetas.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "boardId": {"type": "string", "description": "ID del tablero de Trello"},
            },
            "required": ["boardId"],
        },
        "handler": handle_get_board,
    },
    {
        "name": "create-board",
        "description": "Crea un tablero nuevo en Trello.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Nombre del tablero"},
                "defaultLists": {
                    "type": "boolean",
                    "description": "Crear con las listas por defecto de Trello (defecto: false)",
                },
            },
            "required": ["name"],
        },
        "handler": handle_create_board,
    },
    {
        "name": "manage-lists",
        "description": "Gestiona las listas (columnas) de un tablero de Trello. Acciones: create, rename, reorder, archive.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "boardId": {"type": "string", "description": "ID del tablero de Trello"},
                "action": {
                    "type": "string",
                    "enum": ["create", "rename", "reorder", "archive"],
                    "description": "Accion a realizar",
                },
                "listId": {
                    "type": "string",
                    "description": "ID de la lista (obligatorio para rename, reorder, archive)",
                },
                "name": {
                    "type": "string",
                    "description": "Nombre de la lista (obligatorio para create y rename)",
                },
                "pos": {
                    "description": "Posicion de la lista (numero, 'top' o 'bottom')",
                },
            },
            "required": ["boardId", "action"],
        },
        "handler": handle_manage_lists,
    },
    {
        "name": "manage-labels",
        "description": "Gestiona las etiquetas de un tablero de Trello. Acciones: create, update, delete.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "boardId": {"type": "string", "description": "ID del tablero de Trello"},
                "action": {
                    "type": "string",
                    "enum": ["create", "update", "delete"],
                    "description": "Accion a realizar",
                },
                "labelId": {
                    "type": "string",
                    "description": "ID de la etiqueta (obligatorio para update y delete)",
                },
                "name": {"type": "string", "description": "Nombre de la etiqueta"},
                "color": {
                    "type": ["string", "null"],
                    "enum": LABEL_COLORS + [None],
                    "description": "Color de la etiqueta",
                },
            },
            "required": ["boardId", "action"],
        },
        "handler": handle_manage_labels,
    },
    {
        "name": "create-cards",
        "description": "Crea una o varias tarjetas en una lista de Trello. Si alguna falla, devuelve las creadas y las fallidas.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "listId": {"type": "string", "description": "ID de la lista donde crear las tarjetas"},
                "cards": {
                    "type": "array",
                    "description": "Array de tarjetas a crear",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Titulo de la tarjeta"},
                            "desc": {"type": "string", "description": "Descripcion de la tarjeta (Markdown)"},
                            "idLabels": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "IDs de etiquetas a asignar",
                            },
                            "pos": {
                                "type": "string",
                                "enum": ["top", "bottom"],
                                "description": "Posicion en la lista",
                            },
                            "idMembers": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "IDs de miembros de Trello a asignar a la tarjeta (usar get-board-members para obtener los IDs)",
                            },
                        },
                        "required": ["name", "desc"],
                    },
                },
            },
            "required": ["listId", "cards"],
        },
        "handler": handle_create_cards,
    },
    {
        "name": "search-cards",
        "description": "Busca tarjetas en un tablero de Trello por nombre. Util para detectar duplicados antes de crear tarjetas.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "boardId": {"type": "string", "description": "ID del tablero de Trello"},
                "query": {
                    "type": "string",
                    "description": "Texto a buscar en el nombre de las tarjetas (case-insensitive)",
                },
            },
            "required": ["boardId"],
        },
        "handler": handle_search_cards,
    },
    {
        "name": "add-checklist",
        "description": "Anade un checklist a una tarjeta de Trello. Util para inyectar la Definition of Done como checklist verificable.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cardId": {"type": "string", "description": "ID de la tarjeta de Trello"},
                "name": {"type": "string", "description": "Nombre del checklist (ej: Definition of Done)"},
                "items": {
                    "type": "array",
                    "description": "Lista de items del checklist",
                    "items": {"type": "string"},
                },
            },
            "required": ["cardId", "name", "items"],
        },
        "handler": handle_add_checklist,
    },
    {
        "name": "attach-file",
        "description": "Adjunta un fichero de texto a una tarjeta de Trello. Sube el contenido como adjunto multipart. Util para adjuntar la historia completa en Markdown a la tarjeta.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cardId": {"type": "string", "description": "ID de la tarjeta de Trello"},
                "fileName": {"type": "string", "description": "Nombre del fichero a adjuntar (ej: HU-01-registro.md)"},
                "content": {"type": "string", "description": "Contenido del fichero a adjuntar"},
            },
            "required": ["cardId", "fileName", "content"],
        },
        "handler": handle_attach_file,
    },
    {
        "name": "get-board-members",
        "description": "Obtiene los miembros de un tablero de Trello con sus IDs, nombres y usernames. Util para mapear miembros del equipo a IDs de Trello antes de asignarlos a tarjetas.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "boardId": {"type": "string", "description": "ID del tablero de Trello"},
            },
            "required": ["boardId"],
        },
        "handler": handle_get_board_members,
    },
    {
        "name": "invite-member",
        "description": "Invita a un miembro al tablero de Trello por email. Trello envia la invitacion automaticamente.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "boardId": {"type": "string", "description": "ID del tablero de Trello"},
                "email": {"type": "string", "description": "Email del miembro a invitar"},
                "fullName": {"type": "string", "description": "Nombre completo del miembro"},
                "type": {
                    "type": "string",
                    "enum": ["admin", "normal", "observer"],
                    "description": "Tipo de miembro (defecto: normal)",
                },
            },
            "required": ["boardId", "email"],
        },
        "handler": handle_invite_member,
    },
]

TOOL_MAP = {t["name"]: t for t in TOOLS}

# ---------------------------------------------------------------------------
# Protocolo MCP (JSON-RPC 2.0 sobre stdio con Content-Length)
# ---------------------------------------------------------------------------


class _StreamClosed(Exception):
    """Senal interna: stdin se ha cerrado."""


class MCPServer:
    def __init__(self, client: TrelloClient):
        self._client = client

    def run(self):
        log.info("Servidor MCP iniciado. Esperando mensajes en stdin.")
        while True:
            try:
                msg = self._read_message()
            except _StreamClosed:
                break
            if msg is None:
                continue  # Mensaje descartado (JSON malformado, oversized)
            response = self._handle(msg)
            if response is not None:
                self._write_message(response)

    def _read_message(self):
        # Leer en modo binario para que Content-Length (bytes) sea coherente
        stdin = sys.stdin.buffer
        content_length = 0
        while True:
            line = stdin.readline()
            if not line:
                raise _StreamClosed()
            line_str = line.decode("utf-8", errors="replace").strip()
            if not line_str:
                break
            if line_str.lower().startswith("content-length:"):
                content_length = int(line_str.split(":", 1)[1].strip())

        if content_length == 0:
            log.warning("Mensaje recibido sin Content-Length o con longitud 0.")
            return None

        if content_length > MAX_MESSAGE_SIZE:
            log.error("Mensaje demasiado grande: %d bytes (maximo %d).",
                       content_length, MAX_MESSAGE_SIZE)
            stdin.read(content_length)  # Descartar datos
            return None

        data = stdin.read(content_length)
        if not data:
            raise _StreamClosed()

        try:
            return json.loads(data.decode("utf-8"))
        except json.JSONDecodeError as e:
            log.error("JSON malformado en mensaje entrante: %s", e)
            return None

    def _write_message(self, msg: dict):
        body = json.dumps(msg).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
        sys.stdout.buffer.write(header)
        sys.stdout.buffer.write(body)
        sys.stdout.buffer.flush()

    def _make_response(self, req_id, result: dict) -> dict:
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    def _make_error(self, req_id, code: int, message: str) -> dict:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": code, "message": message},
        }

    def _handle(self, msg: dict):
        method = msg.get("method", "")
        req_id = msg.get("id")
        params = msg.get("params", {})

        # Notificaciones (sin id) no requieren respuesta
        if req_id is None:
            return None

        if method == "initialize":
            return self._make_response(req_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "trello-client",
                    "version": "1.0.0",
                },
            })

        if method == "ping":
            return self._make_response(req_id, {})

        if method == "tools/list":
            tools_list = []
            for t in TOOLS:
                tools_list.append({
                    "name": t["name"],
                    "description": t["description"],
                    "inputSchema": t["inputSchema"],
                })
            return self._make_response(req_id, {"tools": tools_list})

        if method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            return self._call_tool(req_id, tool_name, tool_args)

        return self._make_error(req_id, -32601, f"Metodo no soportado: {method}")

    def _call_tool(self, req_id, name: str, args: dict):
        tool = TOOL_MAP.get(name)
        if not tool:
            return self._make_response(req_id, {
                "content": [{"type": "text",
                             "text": f"Herramienta no encontrada: {name}"}],
                "isError": True,
            })
        try:
            result = tool["handler"](self._client, args)
            return self._make_response(req_id, {
                "content": [{"type": "text",
                             "text": json.dumps(result, indent=2, ensure_ascii=False)}],
            })
        except Exception as e:
            log.error("Error en %s: %s", name, e)
            return self._make_response(req_id, {
                "content": [{"type": "text", "text": f"Error: {e}"}],
                "isError": True,
            })


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    api_key = os.environ.get("TRELLO_API_KEY", "")
    token = os.environ.get("TRELLO_TOKEN", "")

    if not api_key:
        log.error("TRELLO_API_KEY no esta definida en las variables de entorno.")
        sys.exit(1)
    if not token:
        log.error("TRELLO_TOKEN no esta definido en las variables de entorno.")
        sys.exit(1)

    try:
        client = TrelloClient(api_key, token)
    except ValueError as e:
        log.error(str(e))
        sys.exit(1)

    server = MCPServer(client)
    server.run()


if __name__ == "__main__":
    main()
