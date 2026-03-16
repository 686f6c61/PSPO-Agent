#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# PSPO Agent -- script de instalacion para Claude Code
#
# Uso:
#   curl -fsSL https://raw.githubusercontent.com/686f6c61/PSPO-Agent/main/install.sh | bash
#
# Que hace:
#   1. Verifica que Claude Code esta instalado
#   2. Registra el marketplace del plugin con claude plugin marketplace add
#   3. Instala el plugin con claude plugin install
#   4. Listo para usar: /pspo-agent:start
#
# El servidor MCP de Trello esta escrito en Python puro (stdlib).
# No necesita Node.js, npm, pip ni compilacion.
#
# El script delega toda la gestion en la CLI nativa de Claude Code
# (claude plugin marketplace / claude plugin install) para garantizar
# compatibilidad con cualquier version futura de la herramienta.
# ---------------------------------------------------------------------------

set -euo pipefail

REPO="686f6c61/PSPO-Agent"
PLUGIN_NAME="pspo-agent"
VERSION="1.0.7"

# -- Colores ----------------------------------------------------------------

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

info()  { printf "${BLUE}>${NC} %s\n" "$1"; }
ok()    { printf "${GREEN}+${NC} %s\n" "$1"; }
error() { printf "${RED}x${NC} %s\n" "$1" >&2; }

# -- Verificaciones ---------------------------------------------------------

# Python 3 es necesario para el servidor MCP de Trello
if command -v python3 &>/dev/null; then
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
    ok "Python ${PYTHON_VERSION} detectado"
else
    error "Python 3 no esta instalado. Es necesario para el servidor MCP."
    error "Instala desde: https://www.python.org/downloads/"
    exit 1
fi

if [[ -z "${HOME:-}" ]] || [[ ! -d "${HOME}" ]]; then
    error "La variable HOME no esta definida o no apunta a un directorio valido"
    exit 1
fi

if [ ! -d "${HOME}/.claude" ]; then
    error "No se encontro el directorio ~/.claude"
    error "Asegurate de tener Claude Code instalado: https://docs.anthropic.com/en/docs/claude-code"
    exit 1
fi

if ! command -v claude &>/dev/null; then
    error "El comando 'claude' no esta disponible en el PATH"
    error "Asegurate de tener Claude Code instalado y accesible desde la terminal"
    exit 1
fi

# -- Instalacion ------------------------------------------------------------

printf "\n${BOLD}PSPO Agent${NC} ${DIM}v${VERSION}${NC}\n"
printf "${DIM}Product Owner profesional para Claude Code${NC}\n\n"

# -- 1. Registrar marketplace -----------------------------------------------
# Si ya existe, lo eliminamos primero para forzar un refresh del cache.

info "Registrando marketplace..."

if claude plugin marketplace list 2>/dev/null | grep -q "${PLUGIN_NAME}"; then
    claude plugin marketplace remove "${PLUGIN_NAME}" >/dev/null 2>&1 || true
fi

if claude plugin marketplace add "${REPO}" 2>&1; then
    ok "Marketplace registrado"
else
    error "No se pudo registrar el marketplace"
    error "Verifica tu conexion a internet y que el repositorio sea accesible:"
    error "  https://github.com/${REPO}"
    exit 1
fi

# -- 2. Instalar plugin -----------------------------------------------------

info "Instalando plugin..."

# Si hay una version anterior instalada, la eliminamos primero
if claude plugin list 2>/dev/null | grep -q "${PLUGIN_NAME}@${PLUGIN_NAME}"; then
    claude plugin uninstall "${PLUGIN_NAME}@${PLUGIN_NAME}" >/dev/null 2>&1 || true
fi

if claude plugin install "${PLUGIN_NAME}@${PLUGIN_NAME}" 2>&1; then
    ok "Plugin instalado y habilitado"
else
    error "No se pudo instalar el plugin"
    error "Puedes intentar instalarlo manualmente:"
    error "  claude plugin marketplace add ${REPO}"
    error "  claude plugin install ${PLUGIN_NAME}@${PLUGIN_NAME}"
    exit 1
fi

# -- Resultado --------------------------------------------------------------

printf "\n${GREEN}${BOLD}Instalacion completada${NC}\n\n"
printf "  Reinicia Claude Code y ejecuta:\n"
printf "  ${BOLD}/pspo-agent:start${NC}\n\n"
printf "  El asistente de onboarding te guiara para configurar\n"
printf "  las credenciales de Trello y tu primer tablero.\n\n"
printf "  ${DIM}Repositorio: https://github.com/${REPO}${NC}\n"
printf "  ${DIM}Web: https://pspo-agent.com${NC}\n\n"
