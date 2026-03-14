#!/usr/bin/env bash
# Hook PostToolUse: Despues de que la herramienta Write escribe un fichero,
# verifica si el fichero escrito es un .env y si esta en .gitignore.
#
# Este hook lee la entrada estandar (stdin) para obtener los datos del
# tool_output que incluyen la ruta del fichero escrito.
#
# Codigos de salida:
#   0 = todo correcto (no es .env, o .env esta en .gitignore)
#   0 = aviso emitido (siempre sale con 0 para no bloquear, solo avisa)

set -euo pipefail

# Leer el input del hook (JSON con datos del tool use)
INPUT=$(cat)

# Extraer la ruta del fichero escrito del input
# El formato depende de la implementacion de Claude Code hooks
FILE_PATH=$(echo "$INPUT" | grep -oE '"file_path"\s*:\s*"[^"]*"' | head -1 | sed 's/.*: *"//;s/"$//' || true)

# Si no pudimos extraer la ruta, intentar con el campo 'path'
if [ -z "$FILE_PATH" ]; then
    FILE_PATH=$(echo "$INPUT" | grep -oE '"path"\s*:\s*"[^"]*"' | head -1 | sed 's/.*: *"//;s/"$//' || true)
fi

# Si no es un fichero .env, no hacemos nada
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

BASENAME=$(basename "$FILE_PATH")
if [[ "$BASENAME" != ".env" && "$BASENAME" != .env.* ]]; then
    # No es un fichero .env, nada que verificar
    exit 0
fi

# Si es .env.example, no necesita estar en .gitignore
if [ "$BASENAME" = ".env.example" ]; then
    exit 0
fi

# Verificar que .gitignore existe
GITIGNORE_FILE=".gitignore"
if [ ! -f "$GITIGNORE_FILE" ]; then
    echo "[!] AVISO: Se ha escrito un fichero $BASENAME pero no existe .gitignore."
    echo "    Las credenciales podrian subirse al repositorio."
    echo "    Crea un .gitignore y anade '.env' como entrada."
    exit 0
fi

# Verificar que .env esta en .gitignore.
# Patrones aceptados: .env, /.env, .env (con espacios o comentario tras el nombre),
# .env* (glob de gitignore), /.env* (glob anclado al directorio raiz).
if ! grep -qE "^/?\.env($|\s|#)" "$GITIGNORE_FILE" 2>/dev/null; then
    # Verificar tambien patrones glob como .env* o /.env*
    if ! grep -qE "^/?\.env[.*]" "$GITIGNORE_FILE" 2>/dev/null; then
        echo "[!] AVISO: Se ha escrito un fichero $BASENAME pero .env NO esta en .gitignore."
        echo "    Las credenciales podrian subirse al repositorio."
        echo "    Anade '.env' al fichero .gitignore."
    fi
fi

exit 0
