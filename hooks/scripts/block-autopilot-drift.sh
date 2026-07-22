#!/usr/bin/env bash
# Hook PreToolUse (matcher: Glob, Read, ToolSearch, TodoWrite): bloquea
# desvíos laterales durante la fase temprana del modo carpeta-autopilot.

set -euo pipefail

emit_block() {
    local message="$1"
    echo "BLOCKED" >&2
    echo "$message" >&2
    echo "$message"
}

# Resolver interprete de Python sin depender de que 'python3' exista en PATH
# (en Windows suele ser 'python'). Sin interprete no se puede computar el
# estado del autopilot: fail-open avisado, porque bloquear Read/Glob de forma
# global dejaria la sesion inutilizable.
PY="$(command -v python3 || command -v python || true)"
if [ -z "${PY}" ]; then
    echo "[pspo-agent] Aviso: no se encontro python3 ni python; se omite el guardarrail de desvios (fail-open)." >&2
    exit 0
fi

INPUT=$(cat)

eval "$(printf '%s' "$INPUT" | "$PY" -c "
import json, os, shlex, sys

try:
    data = json.load(sys.stdin)
except Exception:
    data = {}

tool_name = data.get('tool_name', '')
tool_input = data.get('tool_input', {}) or {}
cwd = data.get('cwd') or os.getcwd()
path = tool_input.get('path') or ''
file_path = tool_input.get('file_path') or ''
pattern = tool_input.get('pattern') or ''
query = tool_input.get('query') or ''
joined_values = chr(10).join(str(v) for v in (path, file_path, pattern, query) if v)

print(f'TOOL_NAME={shlex.quote(tool_name)}')
print(f'CWD={shlex.quote(cwd)}')
print(f'ALL_VALUES={shlex.quote(joined_values)}')
")"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Un unico volcado del estado del guard en vez de reinvocarlo campo a campo.
eval "$("$PY" "${SCRIPT_DIR}/autopilot-guard.py" --ensure-scaffold --dump-shell "${CWD}")"
provider_needs_choice="${publish_provider_needs_choice}"
is_autopilot_entry=0
if [[ -z "${active_skill}" || "${active_skill}" == "pspo-agent:autopilot" ]]; then
    is_autopilot_entry=1
fi

normalized_cwd="$(printf '%s' "${CWD}" | tr '[:upper:]' '[:lower:]')"
normalized_values="$(printf '%s' "${ALL_VALUES}" | tr '[:upper:]' '[:lower:]')"
normalized_runtime="${normalized_cwd}/.pspo-agent/runtime/autopilot-context.md"
normalized_inbox_prefix="${normalized_cwd}/.pspo-agent/inbox"
runtime_hint=".pspo-agent/runtime/autopilot-context.md"
runtime_prefix_hint=".pspo-agent/runtime/"
inbox_hint=".pspo-agent/inbox"
inbox_glob_hint=".pspo-agent/inbox/*"
env_hint=".env"
env_example_hint=".env.example"
gitignore_hint=".gitignore"
settings_hint=".claude/settings.local.json"
docs_vision_hint="docs/vision.md"
docs_backlog_hint="docs/backlog.md"
docs_analysis_hint="docs/analisis-requisitos.md"
docs_audit_hint="docs/auditoria-hu.md"
docs_stories_hint="docs/historias/hu-"

if [[ "${phase}" == "prepare-context" ]]; then
    "$PY" "${SCRIPT_DIR}/autopilot-bootstrap.py" "${CWD}" >/dev/null 2>&1 || true
fi

case "${phase}" in
    inactive)
        if [[ "${active_skill}" == "pspo-agent:start" ]]; then
            if [[ "${start_bootstrap}" != "done" ]]; then
                emit_block "En /pspo-agent:start no explores el workspace ni uses ToolSearch todavia. Primera accion valida: Bash(\".pspo-agent/runtime/trello-fallback.sh env-status --pretty\"), Bash(\".pspo-agent/runtime/notion-fallback.sh env-status --pretty\") o Bash(\".pspo-agent/runtime/publish-provider.py .\")."
                exit 2
            fi
            if [[ "${TOOL_NAME}" == "ToolSearch" || "${TOOL_NAME}" == "TodoWrite" ]]; then
                emit_block "En /pspo-agent:start no uses ToolSearch ni TodoWrite. Tras env-status y publish-provider, continua con publisher o trello-fallback para Trello, notion-fallback para Notion, o con globs concretos del proyecto."
                exit 2
            fi
            if [[ "${TOOL_NAME}" == "Glob" ]]; then
                if [[ "${normalized_values}" != *"docs/historias/hu-"* ]] \
                    && [[ "${normalized_values}" != *"*.csv"* ]] \
                    && [[ "${normalized_values}" != *"docs/asignaciones.md"* ]] \
                    && [[ "${normalized_values}" != *"docs/dependencias.md"* ]] \
                    && [[ "${normalized_values}" != *"docs/sprint-plan.md"* ]] \
                    && [[ "${normalized_values}" != *"docs/vision.md"* ]]; then
                    emit_block "En /pspo-agent:start solo puedes usar globs acotados del proyecto (HU-*.md, *.csv, asignaciones, dependencias, sprint-plan, vision) despues de env-status."
                    exit 2
                fi
            fi
        fi
        if [[ "${active_skill}" == "pspo-agent:onboarding" ]]; then
            if [[ "${onboarding_bootstrap}" != "done" ]]; then
                emit_block "En /pspo-agent:onboarding no explores rutas laterales todavia. Primera accion valida: Bash(\".pspo-agent/runtime/trello-fallback.sh env-status --pretty\"), Bash(\".pspo-agent/runtime/notion-fallback.sh env-status --pretty\") o Bash(\".pspo-agent/runtime/publish-provider.py .\")."
                exit 2
            fi
            if [[ "${TOOL_NAME}" == "ToolSearch" || "${TOOL_NAME}" == "TodoWrite" ]]; then
                emit_block "En /pspo-agent:onboarding no uses ToolSearch ni TodoWrite. Tras env-status y publish-provider, sigue por el carril oficial del proveedor: publisher/trello-fallback para Trello o notion-fallback para Notion."
                exit 2
            fi
        fi
        if [[ "${active_skill}" == "pspo-agent:publish" ]]; then
            if [[ "${TOOL_NAME}" == "ToolSearch" || "${TOOL_NAME}" == "TodoWrite" ]]; then
                emit_block "En /pspo-agent:publish no uses ToolSearch ni TodoWrite. Lee solo docs/backlog.md, docs/vision.md, docs/historias/HU-*.md y usa publish-provider/env-status si necesitas estado remoto."
                exit 2
            fi
            if [[ "${TOOL_NAME}" == "Glob" || "${TOOL_NAME}" == "Read" ]] \
                && [[ "${normalized_values}" == *".claude/"* \
                    || "${normalized_values}" == *".local.md"* \
                    || "${normalized_values}" == *"claude.md"* ]]; then
                emit_block "En /pspo-agent:publish no uses .claude, *.local.md ni CLAUDE.md como fuente de verdad. Publica solo desde docs/, publish-provider y los wrappers oficiales."
                exit 2
            fi
        fi
        if [[ "${TOOL_NAME}" == "Glob" ]]; then
            if [[ "${normalized_values}" == *".claude/pspo-agent"* ]] \
                || [[ "${normalized_values}" == *".claude/"*".local.md"* ]] \
                || [[ "${normalized_values}" == *"docs/product/"* ]]; then
                emit_block "No uses .claude ni docs/product como fuente de verdad del plugin. Usa env-status, .env.example, .gitignore y artefactos reales de docs/."
                exit 2
            fi
            if [[ "${normalized_values}" == *".pspo-agent"* ]] \
                && [[ "${normalized_values}" != *".pspo-agent/inbox"* ]] \
                && [[ "${normalized_values}" != *".pspo-agent/runtime"* ]]; then
                emit_block "No hagas barridos genericos de .pspo-agent. Usa solo rutas concretas como .pspo-agent/inbox/* o .pspo-agent/runtime/autopilot-context.md cuando el flujo lo requiera."
                exit 2
            fi
        fi
        exit 0
        ;;
esac

if [[ "${phase}" == "product-ready" ]]; then
    case "${gate_status}" in
        review)
            if [[ -n "${branch_skill}" ]] && [[ "${is_autopilot_entry}" == "1" ]]; then
                emit_block "Autopilot ya tiene la rama 'Revisar historias' seleccionada. No reabras la inbox ni explores el workspace: la siguiente accion valida es Skill(\"${branch_skill}\")."
                exit 2
            fi
            if [[ -n "${branch_skill}" ]]; then
                exit 0
            fi
            emit_block "La gate final ya esta resuelta en 'Revisar historias'. No reabras la inbox ni explores el workspace desde autopilot. La siguiente accion valida es Skill(\"${next_review_skill}\")."
            exit 2
            ;;
        plan-publish)
            if [[ -n "${branch_skill}" ]] && [[ "${is_autopilot_entry}" == "1" ]]; then
                emit_block "Autopilot ya tiene la rama 'Planificar y publicar' seleccionada. No reabras la inbox ni explores el workspace: la siguiente accion valida es Skill(\"${branch_skill}\")."
                exit 2
            fi
            if [[ "${branch_skill}" == "pspo-agent:onboarding" ]]; then
                if [[ "${TOOL_NAME}" == "ToolSearch" ]] \
                    && [[ "${normalized_values}" == *"askuserquestion"* ]]; then
                    exit 0
                fi
                if [[ "${TOOL_NAME}" == "Glob" || "${TOOL_NAME}" == "Read" ]] \
                    && [[ "${normalized_values}" == *"${env_hint}"* \
                        || "${normalized_values}" == *"${env_example_hint}"* \
                        || "${normalized_values}" == *"${gitignore_hint}"* \
                        || "${normalized_values}" == *"${settings_hint}"* \
                        || "${normalized_values}" == *"${normalized_runtime}"* \
                        || "${normalized_values}" == *"${runtime_hint}"* \
                        || "${normalized_values}" == *"${runtime_prefix_hint}"* \
                        || "${normalized_values}" == *"${normalized_inbox_prefix}"* \
                        || "${normalized_values}" == *"${inbox_hint}"* \
                        || "${normalized_values}" == *"${inbox_glob_hint}"* ]]; then
                    exit 0
                fi
                if [[ "${provider_needs_choice}" == "1" || -z "${publish_provider}" ]]; then
                    emit_block "Durante onboarding desde autopilot primero resuelve el proveedor remoto. Secuencia valida: Bash(\".pspo-agent/runtime/trello-fallback.sh env-status --pretty\"), Bash(\".pspo-agent/runtime/notion-fallback.sh env-status --pretty\"), Bash(\".pspo-agent/runtime/github-fallback.sh env-status --pretty\") y Bash(\".pspo-agent/runtime/publish-provider.py .\"). Solo puedes tocar .env.example, .gitignore, .claude/settings.local.json, .pspo-agent/runtime/autopilot-context.md y .pspo-agent/inbox/*."
                    exit 2
                fi
                if [[ "${publish_provider}" == "notion" ]]; then
                    emit_block "Durante onboarding desde autopilot con proveedor Notion no explores .claude global, caches ni rutas externas. Siguiente secuencia valida: Bash(\".pspo-agent/runtime/notion-fallback.sh env-status --pretty\"), luego Bash(\".pspo-agent/runtime/notion-fallback.sh verify-credentials --pretty\"), despues retrieve-page/create-project/save-project-targets. Solo puedes tocar .env.example, .gitignore, .claude/settings.local.json, .pspo-agent/runtime/autopilot-context.md y .pspo-agent/inbox/*."
                    exit 2
                fi
                if [[ "${publish_provider}" == "github" ]]; then
                    emit_block "Durante onboarding desde autopilot con proveedor GitHub Projects no explores .claude global, caches ni rutas externas. Siguiente secuencia valida: Bash(\".pspo-agent/runtime/github-fallback.sh env-status --pretty\"), luego Bash(\".pspo-agent/runtime/github-fallback.sh verify-credentials --pretty\"), despues create-project/save-project-targets. Solo puedes tocar .env.example, .gitignore, .claude/settings.local.json, .pspo-agent/runtime/autopilot-context.md y .pspo-agent/inbox/*."
                    exit 2
                fi
                if [[ "${publish_provider}" == "local" ]]; then
                    emit_block "Durante onboarding desde autopilot con proveedor local no explores .claude global, caches ni rutas externas. No hay onboarding remoto: sal del carril lateral y continua con team/assign/dependencies/sprint-plan/publish local. Solo puedes tocar .env.example, .gitignore, .claude/settings.local.json, .pspo-agent/runtime/autopilot-context.md y .pspo-agent/inbox/*."
                    exit 2
                fi
                emit_block "Durante onboarding desde autopilot con proveedor Trello no explores .claude global, caches ni rutas externas. Siguiente secuencia valida: Bash(\".pspo-agent/runtime/trello-fallback.sh env-status --pretty\"), luego el agente publisher o trello-fallback para verify-credentials y despues create-board/manage-lists/manage-labels. Solo puedes tocar .env.example, .gitignore, .claude/settings.local.json, .pspo-agent/runtime/autopilot-context.md y .pspo-agent/inbox/*."
                exit 2
            fi
            if [[ -n "${branch_skill}" ]]; then
                exit 0
            fi
            emit_block "La gate final ya esta resuelta en 'Planificar y publicar'. No reabras la inbox ni explores el workspace desde autopilot. La siguiente accion valida es Skill(\"${next_plan_publish_skill}\")."
            exit 2
            ;;
        done)
            exit 0
            ;;
    esac
    normalized_values="$(printf '%s' "${ALL_VALUES}" | tr '[:upper:]' '[:lower:]')"
    if [[ "${TOOL_NAME}" == "ToolSearch" ]] \
        && [[ "${normalized_values}" == *"askuserquestion"* ]]; then
        exit 0
    fi
    emit_block "Autopilot ya tiene backlog, auditoria y HUs listos. No vuelvas a leer la inbox ni a explorar el workspace. No uses ToolSearch: llama directamente a AskUserQuestion con header 'Autopilot', las opciones 'Revisar historias' y 'Planificar y publicar', y multiSelect=false."
    exit 2
fi

case "${TOOL_NAME}" in
    ToolSearch|TodoWrite)
        if [[ "${TOOL_NAME}" == "ToolSearch" ]] \
            && [[ "${phase}" == "product-ready" ]] \
            && [[ "${gate_status}" != "review" && "${gate_status}" != "plan-publish" && "${gate_status}" != "done" ]] \
            && [[ "${normalized_values}" == *"askuserquestion"* ]]; then
            exit 0
        fi
        if [[ "${phase}" == "product-phase-active" ]]; then
            emit_block "Durante product-phase no uses ToolSearch ni TodoWrite. Siguiente accion valida: Read(\".pspo-agent/runtime/autopilot-context.md\") o leer solo artefactos concretos de docs/."
            exit 2
        fi
        emit_block "En /pspo-agent:autopilot no uses ToolSearch ni TodoWrite. Siguiente accion valida: Glob(\".pspo-agent/inbox/*\") y, cuando exista runtime, Skill(\"pspo-agent:product-phase\")."
        exit 2
        ;;
esac

if [[ "${phase}" == "delegate-product-phase" ]]; then
    if [[ "${active_skill}" == "pspo-agent:product-phase" ]]; then
        if [[ "${TOOL_NAME}" == "Read" || "${TOOL_NAME}" == "Glob" ]] \
            && [[ "${normalized_values}" == *"${normalized_runtime}"* \
                || "${normalized_values}" == *"${runtime_hint}"* \
                || "${normalized_values}" == *"${docs_vision_hint}"* \
                || "${normalized_values}" == *"${docs_backlog_hint}"* \
                || "${normalized_values}" == *"${docs_analysis_hint}"* \
                || "${normalized_values}" == *"${docs_audit_hint}"* \
                || "${normalized_values}" == *"${docs_stories_hint}"* ]]; then
            exit 0
        fi
        emit_block "Durante product-phase solo puedes leer el runtime y artefactos concretos de docs/ (vision, backlog, analisis, auditoria e historias HU-*.md)."
        exit 2
    fi
    if [[ "${TOOL_NAME}" == "Read" ]] \
        && [[ "${normalized_values}" == *"${normalized_runtime}"* || "${normalized_values}" == *"${runtime_hint}"* ]]; then
        exit 0
    fi
    emit_block "Ya existe .pspo-agent/runtime/autopilot-context.md. La siguiente accion debe ser Skill(\"pspo-agent:product-phase\"), no seguir leyendo ni explorando."
    exit 2
fi

if [[ "${TOOL_NAME}" == "Glob" || "${TOOL_NAME}" == "Read" ]]; then
    if [[ "${phase}" == "prepare-context" ]] \
        && [[ "${normalized_values}" != *"${normalized_inbox_prefix}"* ]] \
        && [[ "${normalized_values}" != *"${inbox_hint}"* ]] \
        && [[ "${normalized_values}" != *"${normalized_runtime}"* ]] \
        && [[ "${normalized_values}" != *"${runtime_hint}"* ]]; then
        emit_block "En /pspo-agent:autopilot no inspecciones fuera de inbox o runtime/autopilot-context.md durante la preparacion. No leas docs, .claude, .env ni configuracion lateral antes de delegar. Primero usa Glob(\".pspo-agent/inbox/*\") y luego delega en Skill(\"pspo-agent:product-phase\")."
        exit 2
    fi

    if [[ "${phase}" == "product-phase-active" ]] \
        && [[ "${normalized_values}" == *"${normalized_inbox_prefix}"* || "${normalized_values}" == *"${inbox_hint}"* ]]; then
        emit_block "Durante product-phase no vuelvas a leer la inbox. El bootstrap ya materializo brief, vision y equipo en '.pspo-agent/runtime/autopilot-context.md'."
        exit 2
    fi

    if [[ "${phase}" == "product-phase-active" ]] \
        && [[ "${normalized_values}" == *"docs/**/*"* || "${normalized_values}" == *"docs/**"* ]]; then
        emit_block "Durante product-phase no hagas barridos amplios de docs/. Lee solo rutas concretas: 'docs/vision.md', 'docs/backlog.md', 'docs/analisis-requisitos.md', 'docs/auditoria-hu.md' o 'Glob(\"docs/historias/HU-*.md\")'."
        exit 2
    fi

    if [[ "${phase}" == "product-phase-active" ]] \
        && [[ "${normalized_values}" != *"${normalized_runtime}"* ]] \
        && [[ "${normalized_values}" != *"${runtime_hint}"* ]] \
        && [[ "${normalized_values}" != *"${docs_vision_hint}"* ]] \
        && [[ "${normalized_values}" != *"${docs_backlog_hint}"* ]] \
        && [[ "${normalized_values}" != *"${docs_analysis_hint}"* ]] \
        && [[ "${normalized_values}" != *"${docs_audit_hint}"* ]] \
        && [[ "${normalized_values}" != *"${docs_stories_hint}"* ]]; then
        emit_block "Durante product-phase no inspecciones .claude, .env ni configuracion lateral. Usa solo '.pspo-agent/runtime/autopilot-context.md' y artefactos concretos de docs/."
        exit 2
    fi
fi

exit 0
