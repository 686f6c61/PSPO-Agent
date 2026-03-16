#!/usr/bin/env bash
# Hook PreToolUse (matcher: Read): bloquea lecturas crudas de `.env` y avisa
# sobre otros ficheros sensibles.

set -euo pipefail

INPUT=$(cat)

TARGETS=$(echo "$INPUT" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    tool_input = data.get('tool_input', {})
    values = []
    for key in ('file_path', 'path', 'notebook_path'):
        value = tool_input.get(key)
        if isinstance(value, str):
            values.append(value)
    for key in ('paths',):
        value = tool_input.get(key)
        if isinstance(value, list):
            values.extend(str(v) for v in value)
    print('\n'.join(values))
except Exception:
    pass
" 2>/dev/null || true)

if echo "$TARGETS" | grep -Eqi '(^|/)\.env($|[.])|credentials|secret|token'; then
    if echo "$TARGETS" | grep -Eqi '(^|/)\.env($|[.])'; then
        echo "BLOCKED" >&2
        echo "No leas .env en crudo: expone secretos en el historial. Usa Bash con el helper oficial: .pspo-agent/runtime/trello-fallback.sh env-status --pretty" >&2
        echo "No leas .env en crudo: expone secretos en el historial. Usa Bash con el helper oficial: .pspo-agent/runtime/trello-fallback.sh env-status --pretty"
        exit 2
    fi
    echo "[pspo-agent] Aviso: lectura de fichero sensible detectada." >&2
    echo "[pspo-agent] No muestres ni copies valores de API keys, tokens o credenciales en la conversacion." >&2
fi

exit 0
