# ---------------------------------------------------------------------------
# PSPO Agent -- script de instalacion para Claude Code (Windows)
#
# Uso:
#   irm https://raw.githubusercontent.com/686f6c61/PSPO-Agent/main/install.ps1 | iex
#
# Que hace:
#   1. Verifica que Python 3 y Claude Code estan instalados
#   2. Registra el marketplace del plugin con claude plugin marketplace add
#   3. Instala el plugin con claude plugin install
#   4. Listo para usar: /pspo-agent:start
#
# El servidor MCP de Trello esta escrito en Python puro (stdlib).
# No necesita Node.js, npm, pip ni compilacion.
# ---------------------------------------------------------------------------

$ErrorActionPreference = "Stop"

$Repo = "686f6c61/PSPO-Agent"
$PluginName = "pspo-agent"
$Version = "1.0.7"

# -- Funciones de logging ---------------------------------------------------

function Write-Info  { param($msg) Write-Host "> $msg" -ForegroundColor Blue }
function Write-Ok    { param($msg) Write-Host "+ $msg" -ForegroundColor Green }
function Write-Error { param($msg) Write-Host "x $msg" -ForegroundColor Red }

# -- Verificaciones ---------------------------------------------------------

# Python 3
$pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
}
if (-not $pythonCmd) {
    Write-Error "Python 3 no esta instalado. Es necesario para el servidor MCP."
    Write-Error "Instala desde: https://www.python.org/downloads/"
    Write-Error "O con winget: winget install Python.Python.3.12"
    exit 1
}
$pythonVersion = & $pythonCmd.Name --version 2>&1
Write-Ok "$pythonVersion detectado"

# Claude Code
$claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
if (-not $claudeCmd) {
    Write-Error "El comando 'claude' no esta disponible"
    Write-Error "Asegurate de tener Claude Code instalado: https://docs.anthropic.com/en/docs/claude-code"
    exit 1
}

$claudeDir = Join-Path $env:USERPROFILE ".claude"
if (-not (Test-Path $claudeDir)) {
    Write-Error "No se encontro el directorio ~/.claude"
    Write-Error "Ejecuta 'claude' al menos una vez antes de instalar el plugin"
    exit 1
}

# -- Instalacion ------------------------------------------------------------

Write-Host ""
Write-Host "PSPO Agent" -ForegroundColor White -NoNewline
Write-Host " v$Version" -ForegroundColor DarkGray
Write-Host "Product Owner profesional para Claude Code" -ForegroundColor DarkGray
Write-Host ""

# -- 1. Registrar marketplace -----------------------------------------------

Write-Info "Registrando marketplace..."

$marketplaceList = & claude plugin marketplace list 2>&1
if ($marketplaceList -match $PluginName) {
    & claude plugin marketplace remove $PluginName 2>&1 | Out-Null
}

try {
    & claude plugin marketplace add $Repo 2>&1
    Write-Ok "Marketplace registrado"
} catch {
    Write-Error "No se pudo registrar el marketplace"
    Write-Error "Verifica tu conexion a internet y que el repositorio sea accesible:"
    Write-Error "  https://github.com/$Repo"
    exit 1
}

# -- 2. Instalar plugin -----------------------------------------------------

Write-Info "Instalando plugin..."

$pluginList = & claude plugin list 2>&1
if ($pluginList -match "$PluginName@$PluginName") {
    & claude plugin uninstall "$PluginName@$PluginName" 2>&1 | Out-Null
}

try {
    & claude plugin install "$PluginName@$PluginName" 2>&1
    Write-Ok "Plugin instalado y habilitado"
} catch {
    Write-Error "No se pudo instalar el plugin"
    Write-Error "Puedes intentar instalarlo manualmente:"
    Write-Error "  claude plugin marketplace add $Repo"
    Write-Error "  claude plugin install $PluginName@$PluginName"
    exit 1
}

# -- Resultado --------------------------------------------------------------

Write-Host ""
Write-Host "Instalacion completada" -ForegroundColor Green
Write-Host ""
Write-Host "  Reinicia Claude Code y ejecuta:"
Write-Host "  /pspo-agent:start" -ForegroundColor White
Write-Host ""
Write-Host "  El asistente de onboarding te guiara para configurar"
Write-Host "  las credenciales de Trello y tu primer tablero."
Write-Host ""
Write-Host "  Repositorio: https://github.com/$Repo" -ForegroundColor DarkGray
Write-Host "  Web: https://pspo-agent.com" -ForegroundColor DarkGray
Write-Host ""
