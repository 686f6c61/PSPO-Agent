# =============================================================================
# PSPO Agent - Desinstalador para Claude Code (Windows)
# =============================================================================
#
# Uso:
#   powershell -ExecutionPolicy Bypass -File uninstall.ps1
#   powershell -ExecutionPolicy Bypass -File uninstall.ps1 -KeepConfig
#   powershell -ExecutionPolicy Bypass -File uninstall.ps1 -KeepDocs
#   powershell -ExecutionPolicy Bypass -File uninstall.ps1 -Force
#
# Parametros:
#   -KeepConfig  No borrar .env ni credenciales
#   -KeepDocs    No borrar los documentos generados (docs/, team.csv)
#   -Force       No pedir confirmacion
#
# El script:
#   1. Pide confirmacion (salvo con -Force)
#   2. Desregistra el plugin de Claude Code
#   3. Elimina cache de Python (__pycache__)
#   4. Opcionalmente elimina credenciales (.env)
#   5. Opcionalmente elimina documentos generados
#   6. Muestra resumen de lo eliminado y lo conservado
# =============================================================================

param(
    [switch]$KeepConfig,
    [switch]$KeepDocs,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# --- Directorio del plugin ---
$PluginRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# --- Funciones de logging ---
function Write-Info  { param($msg) Write-Host "[*] $msg" -ForegroundColor Cyan }
function Write-Ok    { param($msg) Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Warn  { param($msg) Write-Host "[!] $msg" -ForegroundColor Yellow }
function Write-Fail  { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "PSPO Agent - Desinstalador (Windows)" -ForegroundColor White
Write-Host "========================================"
Write-Host ""

# --- Verificar que estamos en el directorio correcto ---
$pluginJsonPath = Join-Path $PluginRoot ".claude-plugin\plugin.json"
if (-not (Test-Path $pluginJsonPath)) {
    Write-Fail "No se encuentra .claude-plugin\plugin.json.`n  Ejecuta este script desde el directorio raiz del plugin PSPO Agent."
}

$pluginContent = Get-Content $pluginJsonPath -Raw
if ($pluginContent -notmatch '"name"\s*:\s*"pspo-agent"') {
    Write-Fail "Este directorio no contiene el plugin 'pspo-agent'."
}

# =============================================================================
# 1. Confirmacion
# =============================================================================
if (-not $Force) {
    Write-Host "Se va a desinstalar PSPO Agent del directorio:"
    Write-Host "  $PluginRoot"
    Write-Host ""
    Write-Host "Esto eliminara:"
    Write-Host "  [-] Cache de Python (__pycache__/)"

    if (-not $KeepConfig) {
        Write-Host "  [-] Credenciales (.env)"
    } else {
        Write-Host "  [+] Credenciales (.env) -- SE CONSERVAN (-KeepConfig)" -ForegroundColor Green
    }

    if (-not $KeepDocs) {
        Write-Host "  [-] Documentos generados (docs/, team.csv)"
    } else {
        Write-Host "  [+] Documentos generados -- SE CONSERVAN (-KeepDocs)" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "NO se eliminan:" -ForegroundColor White
    Write-Host "  [+] Codigo fuente (skills/, agents/, servers/trello-mcp.py)"
    Write-Host "  [+] Configuracion (.claude-plugin/, hooks/, .mcp.json)"
    Write-Host "  [+] Ficheros de control de versiones (.git/)"
    Write-Host ""

    $confirm = Read-Host "Continuar con la desinstalacion? [s/N]"
    if ($confirm -notmatch '^[sS]$') {
        Write-Host ""
        Write-Info "Desinstalacion cancelada."
        exit 0
    }
    Write-Host ""
}

# =============================================================================
# 2. Desregistrar plugin de Claude Code
# =============================================================================
Write-Info "Desregistrando plugin de Claude Code..."

$claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
if ($claudeCmd) {
    $pluginList = & claude plugin list 2>&1
    if ($pluginList -match "pspo-agent") {
        & claude plugin uninstall "pspo-agent@pspo-agent" 2>&1 | Out-Null
        Write-Ok "Plugin desinstalado de Claude Code"
    } else {
        Write-Info "Plugin no estaba instalado en Claude Code"
    }

    $marketplaceList = & claude plugin marketplace list 2>&1
    if ($marketplaceList -match "pspo-agent") {
        & claude plugin marketplace remove "pspo-agent" 2>&1 | Out-Null
        Write-Ok "Marketplace eliminado de Claude Code"
    } else {
        Write-Info "Marketplace no estaba registrado"
    }
} else {
    Write-Warn "Claude Code no encontrado. No se puede desregistrar automaticamente."
}

# =============================================================================
# 3. Eliminar cache de Python
# =============================================================================
Write-Info "Eliminando cache de Python..."

$removedCount = 0

$pycache = Join-Path $PluginRoot "servers\__pycache__"
if (Test-Path $pycache) {
    Remove-Item -Path $pycache -Recurse -Force
    Write-Ok "Eliminado: servers\__pycache__\"
    $removedCount++
}

# =============================================================================
# 4. Credenciales
# =============================================================================
if (-not $KeepConfig) {
    Write-Info "Eliminando credenciales..."

    $envFile = Join-Path $PluginRoot ".env"
    if (Test-Path $envFile) {
        $item = Get-Item $envFile -Force
        $item.Attributes = $item.Attributes -band (-bnot [System.IO.FileAttributes]::Hidden)
        Remove-Item -Path $envFile -Force
        Write-Ok "Eliminado: .env"
        $removedCount++
    } else {
        Write-Info ".env no existe, nada que eliminar"
    }
} else {
    Write-Info "Credenciales conservadas (-KeepConfig)"
}

# =============================================================================
# 5. Documentos generados
# =============================================================================
if (-not $KeepDocs) {
    Write-Info "Eliminando documentos generados..."

    $docsToRemove = @(
        "docs\historias",
        "docs\vision.md",
        "docs\backlog.md",
        "docs\asignaciones.md",
        "docs\dependencias.md",
        "docs\sprint-plan.md",
        "docs\dod.md",
        "team.csv"
    )

    foreach ($item in $docsToRemove) {
        $fullPath = Join-Path $PluginRoot $item
        if (Test-Path $fullPath) {
            Remove-Item -Path $fullPath -Recurse -Force
            Write-Ok "Eliminado: $item"
            $removedCount++
        }
    }
} else {
    Write-Info "Documentos generados conservados (-KeepDocs)"
}

# =============================================================================
# 6. Resumen
# =============================================================================
Write-Host ""
Write-Host "========================================"
Write-Host "Desinstalacion completada" -ForegroundColor Green
Write-Host "========================================"
Write-Host ""
Write-Host "  Elementos eliminados: $removedCount"
Write-Host ""

if ($KeepConfig -or $KeepDocs) {
    Write-Host "  Conservado:" -ForegroundColor White
    if ($KeepConfig) {
        Write-Host "    [+] .env (credenciales)"
    }
    if ($KeepDocs) {
        Write-Host "    [+] docs/ (documentos generados)"
        Write-Host "    [+] team.csv (equipo)"
    }
    Write-Host ""
}

Write-Host "  Siempre conservado:" -ForegroundColor White
Write-Host "    [+] Codigo fuente (skills/, agents/, servers/trello-mcp.py)"
Write-Host "    [+] Configuracion (.claude-plugin/, hooks/, .mcp.json)"
Write-Host "    [+] .env.example (plantilla sin credenciales)"
Write-Host ""
Write-Host "  Para reinstalar: " -NoNewline
Write-Host "irm https://raw.githubusercontent.com/686f6c61/PSPO-Agent/main/install.ps1 | iex" -ForegroundColor Cyan
Write-Host ""
