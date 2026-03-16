#!/usr/bin/env python3
"""Bootstrap determinista del contexto runtime de /pspo-agent:autopilot."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
from datetime import date

DOC_PRIORITY = [
    "instrucciones.md",
    "brief.md",
    "prd.md",
    "requirements.md",
    "brief.txt",
]
CSV_HEADER = [
    "nombre",
    "email",
    "rol",
    "categoria",
    "dedicacion",
    "usa_agente_ia",
]
CSV_PRIORITY = [
    "team.csv",
    "equipo.csv",
    "equipo-core.csv",
]


def _read_text(path: str) -> str:
    with open(path, encoding="utf-8") as handle:
        return handle.read().strip()


def _normalize_header(values: list[str]) -> list[str]:
    return [value.strip().lower() for value in values]


def _find_main_document(inbox_dir: str) -> str | None:
    for name in DOC_PRIORITY:
        candidate = os.path.join(inbox_dir, name)
        if os.path.isfile(candidate):
            return candidate
    return None


def _find_vision(inbox_dir: str) -> str | None:
    candidate = os.path.join(inbox_dir, "vision.md")
    if os.path.isfile(candidate):
        return candidate
    return None


def _collect_compatible_csvs(inbox_dir: str) -> list[str]:
    compatible: list[str] = []
    for entry in sorted(os.listdir(inbox_dir)):
        if not entry.lower().endswith(".csv"):
            continue
        candidate = os.path.join(inbox_dir, entry)
        if not os.path.isfile(candidate):
            continue
        try:
            with open(candidate, encoding="utf-8", newline="") as handle:
                reader = csv.reader(handle)
                header = next(reader, [])
        except (OSError, csv.Error):
            continue
        if _normalize_header(header) == CSV_HEADER:
            compatible.append(candidate)
    return compatible


def _choose_csv(paths: list[str]) -> tuple[str | None, bool]:
    if not paths:
        return None, False
    if len(paths) == 1:
        return paths[0], False
    by_name = {os.path.basename(path).lower(): path for path in paths}
    for name in CSV_PRIORITY:
        if name in by_name:
            return by_name[name], True
    return sorted(paths)[0], True


def _word_count(text: str) -> int:
    return len([token for token in text.split() if token.strip()])


def _mode_from_words(words: int) -> str:
    return "analyze" if words >= 100 else "discovery"


def _project_compatible_csvs(cwd: str) -> list[str]:
    compatible: list[str] = []
    for entry in sorted(os.listdir(cwd)):
        if not entry.lower().endswith(".csv"):
            continue
        candidate = os.path.join(cwd, entry)
        if not os.path.isfile(candidate):
            continue
        try:
            with open(candidate, encoding="utf-8", newline="") as handle:
                reader = csv.reader(handle)
                header = next(reader, [])
        except (OSError, csv.Error):
            continue
        if _normalize_header(header) == CSV_HEADER:
            compatible.append(candidate)
    return compatible


def _import_csv_to_root(cwd: str, csv_path: str | None) -> str | None:
    if not csv_path:
        return None
    if _project_compatible_csvs(cwd):
        return None
    target = os.path.join(cwd, os.path.basename(csv_path))
    if os.path.abspath(target) == os.path.abspath(csv_path):
        return os.path.relpath(target, cwd)
    shutil.copyfile(csv_path, target)
    return os.path.relpath(target, cwd)


def _render_team_table(csv_path: str | None) -> str:
    if not csv_path:
        return "No se detecto CSV compatible.\n"
    rows: list[list[str]] = []
    with open(csv_path, encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        for row in reader:
            if row:
                rows.append(row)
    if not rows:
        return "CSV compatible detectado, pero sin filas de equipo.\n"
    lines = [
        "| Nombre | Email | Rol | Categoria | Dedicacion (%) | Usa agente IA |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        padded = row + [""] * (6 - len(row))
        lines.append(
            f"| {padded[0]} | {padded[1]} | {padded[2]} | {padded[3]} | {padded[4]} | {padded[5]} |"
        )
    return "\n".join(lines) + "\n"


def bootstrap_context(cwd: str) -> dict[str, object]:
    inbox_dir = os.path.join(cwd, ".pspo-agent", "inbox")
    runtime_dir = os.path.join(cwd, ".pspo-agent", "runtime")
    context_path = os.path.join(runtime_dir, "autopilot-context.md")

    result = {
        "created": False,
        "context_path": context_path,
        "document_path": None,
        "vision_path": None,
        "csv_path": None,
        "csv_imported_path": None,
        "csv_ambiguous": False,
        "word_count": 0,
        "product_mode": "",
    }

    if not os.path.isdir(inbox_dir):
        return result

    if os.path.isfile(context_path):
        result["created"] = False
        return result

    document_path = _find_main_document(inbox_dir)
    if not document_path:
        return result

    os.makedirs(runtime_dir, exist_ok=True)
    os.makedirs(os.path.join(cwd, "docs", "historias"), exist_ok=True)

    document_body = _read_text(document_path)
    words = _word_count(document_body)
    product_mode = _mode_from_words(words)
    vision_path = _find_vision(inbox_dir)
    compatible_csvs = _collect_compatible_csvs(inbox_dir)
    chosen_csv, ambiguous_csv = _choose_csv(compatible_csvs)
    imported_csv = _import_csv_to_root(cwd, chosen_csv)
    vision_body = _read_text(vision_path) if vision_path else ""

    relative_document = os.path.relpath(document_path, cwd)
    relative_vision = os.path.relpath(vision_path, cwd) if vision_path else "ninguna"
    relative_csv = os.path.relpath(chosen_csv, cwd) if chosen_csv else "ninguno"
    relative_imported_csv = imported_csv or "sin importar"
    vision_content = vision_body if vision_body else "No se detecto vision de entrada adicional.\n"
    ambiguous_note = (
        "Si hay varios CSV compatibles, se ha elegido uno de forma determinista para no bloquear el carril."
        if ambiguous_csv
        else "No hubo ambiguedad al elegir el CSV compatible."
    )
    csv_import_note = (
        f"Se ha importado el CSV compatible a la raiz del proyecto como `{relative_imported_csv}`."
        if imported_csv
        else "No fue necesario importar un CSV compatible adicional a la raiz del proyecto."
    )

    context = f"""---
modo: autopilot
carpeta_entrada: .pspo-agent/inbox
fecha: {date.today().isoformat()}
documento_principal: {relative_document}
vision_fuente: {relative_vision}
csv_compatible: {relative_csv}
csv_importado_raiz: {relative_imported_csv}
palabras_documento: {words}
modo_producto: {product_mode}
bootstrap: automatico
---

# Resumen de bootstrap

- Documento principal detectado: `{relative_document}`
- Vision detectada: `{relative_vision}`
- CSV compatible detectado: `{relative_csv}`
- CSV importado en raiz: `{relative_imported_csv}`
- Palabras del documento principal: `{words}`
- Modo de producto seleccionado: `{product_mode}`
- Nota de seleccion de CSV: {ambiguous_note}
- Nota de importacion del CSV: {csv_import_note}

# Documento de entrada

## Ruta

`{relative_document}`

## Contenido

{document_body}

# Equipo

{_render_team_table(chosen_csv)}

# Vision de entrada

## Ruta

`{relative_vision}`

## Contenido

{vision_content}
"""

    with open(context_path, "w", encoding="utf-8") as handle:
        handle.write(context)

    result.update(
        {
            "created": True,
            "document_path": relative_document,
            "vision_path": None if not vision_path else relative_vision,
            "csv_path": None if not chosen_csv else relative_csv,
            "csv_imported_path": imported_csv,
            "csv_ambiguous": ambiguous_csv,
            "word_count": words,
            "product_mode": product_mode,
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cwd", nargs="?", default=os.getcwd())
    args = parser.parse_args()
    result = bootstrap_context(os.path.abspath(args.cwd))
    json.dump(result, fp=os.sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
