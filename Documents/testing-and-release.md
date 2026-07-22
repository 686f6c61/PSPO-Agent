# Testing y Release

## Suite de tests

Directorio:

- [`../tests/`](../tests/)

Estado actual verificado localmente:

- `514` tests en verde con `uv run --with pytest pytest tests/ -q`

## Qué cubre cada archivo

| Archivo | Cobertura principal |
|---|---|
| [`../tests/test_skills.py`](../tests/test_skills.py) | estructura de skills, agentes, hooks y settings |
| [`../tests/test_content.py`](../tests/test_content.py) | contratos de contenido y reglas críticas |
| [`../tests/test_trello_mcp.py`](../tests/test_trello_mcp.py) | handlers del MCP con mocks |
| [`../tests/test_e2e_mcp.py`](../tests/test_e2e_mcp.py) | protocolo MCP real end to end |
| [`../tests/test_trello_fallback.py`](../tests/test_trello_fallback.py) | fallback oficial de Trello |
| [`../tests/test_notion_fallback.py`](../tests/test_notion_fallback.py) | fallback oficial de Notion |
| [`../tests/test_github_fallback.py`](../tests/test_github_fallback.py) | fallback oficial de GitHub Projects |
| [`../tests/test_publish_provider.py`](../tests/test_publish_provider.py) | selección de proveedor de publicación |
| [`../tests/test_config.py`](../tests/test_config.py) | manifest, plugin config, settings y conteos |
| [`../tests/test_autopilot_guard.py`](../tests/test_autopilot_guard.py) | máquina de estado de autopilot |
| [`../tests/test_autopilot_bootstrap.py`](../tests/test_autopilot_bootstrap.py) | bootstrap de runtime |
| [`../tests/test_autopilot_gate_persistence.py`](../tests/test_autopilot_gate_persistence.py) | persistencia de la gate |
| [`../tests/test_autopilot_hooks_runtime.py`](../tests/test_autopilot_hooks_runtime.py) | comportamiento real de hooks |
| [`../tests/test_autopilot_stop.py`](../tests/test_autopilot_stop.py) | bloqueo de stop prematuro |

## Comandos habituales

Suite completa:

```bash
python3 -m unittest discover -s tests
```

Foco en hooks:

```bash
python3 -m unittest discover -s tests -p 'test_autopilot*.py'
```

Foco en Trello:

```bash
python3 -m unittest discover -s tests -p 'test_trello_*.py'
python3 -m unittest discover -s tests -p 'test_e2e_mcp.py'
```

## Qué validar antes de una release

1. suite completa en verde
2. smoke de `start`
3. smoke de `autopilot`
4. onboarding con `.env` vacío
5. onboarding con `.env` ya válido
6. publish con:
   - resumen
   - adjunto `.md`
   - `idMembers`
7. protección contra lectura de `.env`
8. bloqueo de `curl`/`Fetch` directo a Trello, Notion o GitHub

## E2E recomendado

Workspace temporal mínimo:

- `.pspo-agent/inbox/brief.md`
- CSV compatible de 1-2 personas
- `.env` con credenciales del proveedor elegido (Trello, Notion o GitHub) si se quiere llegar a publicación

Resultado esperado:

- `docs/vision.md`
- `docs/backlog.md`
- `docs/historias/HU-*.md`
- `docs/auditoria-hu.md`
- tablero creado o reutilizado
- tarjetas con resumen + `.md` + owner real

## Checklist de release

1. subir versión en:
   - [`../.claude-plugin/plugin.json`](../.claude-plugin/plugin.json)
   - [`../.claude-plugin/marketplace.json`](../.claude-plugin/marketplace.json)
   - [`../settings.json`](../settings.json) si aplica
   - [`../install.sh`](../install.sh)
   - [`../install.ps1`](../install.ps1)
2. actualizar [`../CHANGELOG.md`](../CHANGELOG.md)
3. validar web y README si cambió el comportamiento
4. probar instalación limpia
5. probar desinstalación

