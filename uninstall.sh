#!/usr/bin/env bash
# =============================================================================
# PSPO Agent - Desinstalador para Claude Code (Linux y macOS)
# =============================================================================
#
# Compatible con: Linux (Ubuntu, Debian, Fedora, Arch...) y macOS (12+)
#
# Uso:
#   bash uninstall.sh [--keep-config] [--keep-docs] [--force]
#
# Opciones:
#   --keep-config  No borrar .env ni credenciales
#   --keep-docs    No borrar los documentos generados (docs/, CSVs de equipo compatibles)
#   --force        No pedir confirmacion
#
# Para Windows, usa uninstall.ps1 (PowerShell).
#
# El script:
#   1. Pide confirmacion (salvo con --force)
#   2. Desregistra el plugin de Claude Code
#   3. Elimina cache de Python (__pycache__)
#   4. Opcionalmente elimina credenciales (.env)
#   5. Opcionalmente elimina documentos generados
#   6. Muestra resumen de lo eliminado y lo conservado
# =============================================================================

set -euo pipefail

# --- Colores ---
if [ -t 1 ] && command -v tput &>/dev/null && [ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]; then
    RED=$(tput setaf 1)
    GREEN=$(tput setaf 2)
    YELLOW=$(tput setaf 3)
    BLUE=$(tput setaf 4)
    BOLD=$(tput bold)
    RESET=$(tput sgr0)
else
    RED="" GREEN="" YELLOW="" BLUE="" BOLD="" RESET=""
fi

info()  { echo "${BLUE}[*]${RESET} $1"; }
ok()    { echo "${GREEN}[OK]${RESET} $1"; }
warn()  { echo "${YELLOW}[!]${RESET} $1"; }
fail()  { echo "${RED}[ERROR]${RESET} $1" >&2; exit 1; }

# --- Deteccion de SO ---
case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*)
        echo "${RED}[ERROR]${RESET} Este script no es compatible con Windows."
        echo "  Usa uninstall.ps1 en PowerShell:"
        echo "  powershell -ExecutionPolicy Bypass -File uninstall.ps1"
        exit 1
        ;;
esac

# --- Directorio del plugin ---
PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Parsear argumentos ---
KEEP_CONFIG=false
KEEP_DOCS=false
FORCE=false
TEAM_CSV_HEADER="nombre,email,rol,categoria,dedicacion,usa_agente_ia"

is_compatible_team_csv() {
    local file="$1"
    [ -f "$file" ] || return 1
    local header
    header="$(head -n 1 "$file" 2>/dev/null | tr -d '\r')"
    [ "$header" = "$TEAM_CSV_HEADER" ]
}

collect_compatible_team_csvs() {
    local file
    shopt -s nullglob
    for file in "${PLUGIN_ROOT}"/*.csv; do
        if is_compatible_team_csv "$file"; then
            printf '%s\n' "$file"
        fi
    done
    shopt -u nullglob
}

for arg in "$@"; do
    case "$arg" in
        --keep-config) KEEP_CONFIG=true ;;
        --keep-docs)   KEEP_DOCS=true ;;
        --force)       FORCE=true ;;
        --help|-h)
            echo "Uso: bash uninstall.sh [--keep-config] [--keep-docs] [--force]"
            echo ""
            echo "Opciones:"
            echo "  --keep-config  No borrar .env ni credenciales"
            echo "  --keep-docs    No borrar documentos generados (docs/, CSVs de equipo compatibles)"
            echo "  --force        No pedir confirmacion"
            exit 0
            ;;
        *)
            warn "Argumento desconocido: $arg"
            ;;
    esac
done

echo ""
echo "${BOLD}PSPO Agent - Desinstalador${RESET}"
echo "========================================"
echo ""

# --- Verificar que estamos en el directorio correcto ---
if [ ! -f "${PLUGIN_ROOT}/.claude-plugin/plugin.json" ]; then
    fail "No se encuentra .claude-plugin/plugin.json.\n  Ejecuta este script desde el directorio raiz del plugin PSPO Agent."
fi

PLUGIN_NAME=$(grep -o '"name"[[:space:]]*:[[:space:]]*"[^"]*"' "${PLUGIN_ROOT}/.claude-plugin/plugin.json" | head -1 | sed 's/.*: *"//;s/"$//')
if [ "$PLUGIN_NAME" != "pspo-agent" ]; then
    fail "Este directorio contiene el plugin '${PLUGIN_NAME}', no 'pspo-agent'."
fi

# =============================================================================
# 1. Confirmacion
# =============================================================================
if [ "$FORCE" = false ]; then
    echo "Se va a desinstalar ${BOLD}PSPO Agent${RESET} del directorio:"
    echo "  ${PLUGIN_ROOT}"
    echo ""
    echo "Esto eliminara:"
    echo "  [-] Cache de Python (__pycache__/)"
    if [ "$KEEP_CONFIG" = false ]; then
        echo "  [-] Credenciales (.env)"
    else
        echo "  [+] Credenciales (.env) -- SE CONSERVAN (--keep-config)"
    fi
    if [ "$KEEP_DOCS" = false ]; then
        echo "  [-] Documentos generados (docs/, CSVs de equipo compatibles en la raiz)"
    else
        echo "  [+] Documentos generados -- SE CONSERVAN (--keep-docs)"
    fi
    echo ""
    echo "${BOLD}NO se eliminan:${RESET}"
    echo "  [+] Codigo fuente del plugin (skills/, agents/, servers/trello-mcp.py)"
    echo "  [+] Configuracion del plugin (.claude-plugin/, hooks/, .mcp.json)"
    echo "  [+] Ficheros de control de versiones (.git/)"
    echo ""

    read -rp "Continuar con la desinstalacion? [s/N] " CONFIRM
    if [[ ! "$CONFIRM" =~ ^[sS]$ ]]; then
        echo ""
        info "Desinstalacion cancelada."
        exit 0
    fi
    echo ""
fi

# =============================================================================
# 2. Desregistrar plugin de Claude Code
# =============================================================================
info "Desregistrando plugin de Claude Code..."

if command -v claude &>/dev/null; then
    if claude plugin list 2>/dev/null | grep -q "pspo-agent"; then
        claude plugin uninstall pspo-agent 2>/dev/null || true
        ok "Plugin desinstalado de Claude Code"
    else
        info "Plugin no estaba instalado en Claude Code"
    fi

    if claude plugin marketplace list 2>/dev/null | grep -q "pspo-agent"; then
        claude plugin marketplace remove pspo-agent 2>/dev/null || true
        ok "Marketplace eliminado de Claude Code"
    else
        info "Marketplace no estaba registrado"
    fi
else
    warn "Claude Code no encontrado. No se puede desregistrar automaticamente."
    warn "Si lo instalaste manualmente, revisa ~/.claude/settings.json"
fi

# =============================================================================
# 3. Eliminar artefactos de build
# =============================================================================
info "Eliminando cache de Python..."

REMOVED_COUNT=0

# __pycache__ del servidor MCP
if [ -d "${PLUGIN_ROOT}/servers/__pycache__" ]; then
    rm -rf "${PLUGIN_ROOT}/servers/__pycache__"
    ok "Eliminado: servers/__pycache__/"
    REMOVED_COUNT=$((REMOVED_COUNT + 1))
fi

# =============================================================================
# 4. Credenciales
# =============================================================================
if [ "$KEEP_CONFIG" = false ]; then
    info "Eliminando credenciales..."

    if [ -f "${PLUGIN_ROOT}/.env" ]; then
        rm -f "${PLUGIN_ROOT}/.env"
        ok "Eliminado: .env"
        REMOVED_COUNT=$((REMOVED_COUNT + 1))
    else
        info ".env no existe, nada que eliminar"
    fi
else
    info "Credenciales conservadas (--keep-config)"
fi

# =============================================================================
# 5. Documentos generados
# =============================================================================
if [ "$KEEP_DOCS" = false ]; then
    info "Eliminando documentos generados..."

    # docs/ completo: salida generada por el flujo del plugin
    if [ -d "${PLUGIN_ROOT}/docs" ]; then
        rm -rf "${PLUGIN_ROOT}/docs"
        ok "Eliminado: docs/"
        REMOVED_COUNT=$((REMOVED_COUNT + 1))
    fi

    TEAM_CSV_FILES=()
    while IFS= read -r file; do
        TEAM_CSV_FILES+=("$file")
    done < <(collect_compatible_team_csvs)
    if [ "${#TEAM_CSV_FILES[@]}" -gt 0 ]; then
        for file in "${TEAM_CSV_FILES[@]}"; do
            rm -f "$file"
            ok "Eliminado: $(basename "$file")"
            REMOVED_COUNT=$((REMOVED_COUNT + 1))
        done
    else
        info "No hay CSVs de equipo compatibles en la raiz"
    fi
else
    info "Documentos generados conservados (--keep-docs)"
fi

# =============================================================================
# 6. Resumen
# =============================================================================
echo ""
echo "========================================"
echo "${GREEN}${BOLD}Desinstalacion completada${RESET}"
echo "========================================"
echo ""
echo "  Elementos eliminados: ${REMOVED_COUNT}"
echo ""

if [ "$KEEP_CONFIG" = true ] || [ "$KEEP_DOCS" = true ]; then
    echo "  ${BOLD}Conservado:${RESET}"
    if [ "$KEEP_CONFIG" = true ]; then
        echo "    [+] .env (credenciales)"
    fi
    if [ "$KEEP_DOCS" = true ]; then
        echo "    [+] docs/ (documentos generados)"
        echo "    [+] CSV(s) de equipo compatibles en la raiz"
    fi
    echo ""
fi

echo "  ${BOLD}Siempre conservado:${RESET}"
echo "    [+] Codigo fuente (skills/, agents/, servers/)"
echo "    [+] Configuracion (.claude-plugin/, hooks/, .mcp.json)"
echo "    [+] .env.example (plantilla sin credenciales)"
echo ""
echo "  Para reinstalar: ${BLUE}curl -fsSL https://raw.githubusercontent.com/686f6c61/PSPO-Agent/main/install.sh | bash${RESET}"
echo ""
