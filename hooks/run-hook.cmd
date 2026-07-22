: << 'CMDBLOCK'
@echo off
REM Envoltorio poliglota multiplataforma para los hooks de PSPO Agent.
REM Fichero valido a la vez como batch de Windows y como script sh de Unix.
REM
REM En Windows (cmd.exe): ejecuta esta seccion batch, localiza bash o python
REM  y lanza el script indicado, relativo a hooks/scripts/.
REM En Unix (sh/bash): el interprete lo trata como script (: es no-op) y
REM  ejecuta la seccion de abajo tras el heredoc.
REM
REM Uso: run-hook.cmd <nombre-script-relativo-a-scripts> [args...]
REM  Los .sh se ejecutan con bash (en Windows, el bash de Git para Windows).
REM  Los .py se ejecutan con python3 o, si no existe, con python.

if "%~1"=="" (
    echo run-hook.cmd: falta el nombre del script 1>&2
    exit /b 1
)

set "TARGET=%~dp0scripts\%~1"
set "ARGS=%2 %3 %4 %5 %6 %7 %8 %9"
if /i "%~x1"==".py" goto runpy
goto runsh

:runpy
where python3 >nul 2>nul && goto runpy3
where python >nul 2>nul && goto runpy2
echo run-hook.cmd: no se encontro python3 ni python; se omite %~1 1>&2
exit /b 0
:runpy3
python3 "%TARGET%" %ARGS%
exit /b %ERRORLEVEL%
:runpy2
python "%TARGET%" %ARGS%
exit /b %ERRORLEVEL%

:runsh
if exist "C:\Program Files\Git\bin\bash.exe" goto shgit
if exist "C:\Program Files (x86)\Git\bin\bash.exe" goto shgit86
where bash >nul 2>nul && goto shpath
echo run-hook.cmd: no se encontro bash; se omite %~1 1>&2
exit /b 0
:shgit
"C:\Program Files\Git\bin\bash.exe" "%TARGET%" %ARGS%
exit /b %ERRORLEVEL%
:shgit86
"C:\Program Files (x86)\Git\bin\bash.exe" "%TARGET%" %ARGS%
exit /b %ERRORLEVEL%
:shpath
bash "%TARGET%" %ARGS%
exit /b %ERRORLEVEL%
CMDBLOCK

# --- Unix (sh/bash) ---
# Nota: se usa $0 en lugar de ${BASH_SOURCE[0]:-$0} por compatibilidad POSIX.
# ${BASH_SOURCE} provoca "Bad substitution" en sistemas donde /bin/sh es dash.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_NAME="$1"
shift
TARGET="${SCRIPT_DIR}/scripts/${SCRIPT_NAME}"

case "${SCRIPT_NAME}" in
    *.py)
        PY="$(command -v python3 || command -v python || true)"
        if [ -z "${PY}" ]; then
            echo "run-hook.cmd: no se encontro python3 ni python; se omite ${SCRIPT_NAME}" 1>&2
            exit 0
        fi
        exec "${PY}" "${TARGET}" "$@"
        ;;
    *)
        exec bash "${TARGET}" "$@"
        ;;
esac
