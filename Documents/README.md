# PSPO Agent Developer Docs

La documentación técnica y operativa del plugin vive ahora en `Documents/`.

`docs/` queda reservado para artefactos generados por el propio flujo de producto:

- `docs/vision.md`
- `docs/backlog.md`
- `docs/historias/HU-*.md`
- `docs/auditoria-hu.md`
- `docs/asignaciones.md`
- `docs/dependencias.md`
- `docs/sprint-plan.md`
- `docs/publish-report.md`

## Qué es este plugin

PSPO Agent es un plugin no oficial de Claude Code que cubre el ciclo completo de trabajo de producto:

1. Descubrimiento o análisis de requisitos.
2. Generación de backlog e historias de usuario.
3. Validación, asignación y mapa de dependencias.
4. Planificación de sprint adaptada a equipos que usan agentes.
5. Publicación en Trello o Notion con resumen, adjunto `.md`, dependencias y asignación real cuando puede resolverse.

## Foto actual del plugin

- `19` comandos registrados en [`../.claude-plugin/plugin.json`](../.claude-plugin/plugin.json)
- `18` skills registradas en [`../.claude-plugin/plugin.json`](../.claude-plugin/plugin.json)
- `6` agentes especializados en [`../agents/`](../agents/)
- `14` herramientas MCP de Trello en [`../servers/trello-mcp.py`](../servers/trello-mcp.py)
- fallback oficial de Notion en [`../servers/notion-fallback.py`](../servers/notion-fallback.py)
- orquestación con hooks en [`../hooks/hooks.json`](../hooks/hooks.json)
- configuración global en [`../settings.json`](../settings.json)
- distribución e instalación en [`../install.sh`](../install.sh) y [`../install.ps1`](../install.ps1)

## Cómo leer esta documentación

1. [`configuration.md`](./configuration.md)
   Configuración, instalación, `.env`, `settings.json`, `.mcp.json`, marketplace y desinstalación.

2. [`architecture.md`](./architecture.md)
   Arquitectura real del plugin, flujos interactivo y autopilot, runtime y artefactos.

3. [`commands-skills-agents.md`](./commands-skills-agents.md)
   Catálogo completo de comandos, skills y agentes con referencias a cada archivo.

4. [`hooks-and-runtime.md`](./hooks-and-runtime.md)
   Todos los hooks, guardrails de autopilot y ficheros de estado en `.pspo-agent/runtime/`.

5. [`trello-integration.md`](./trello-integration.md)
   MCP de Trello, launcher, fallback oficial, listas, etiquetas y contrato de publicación.

6. [`notion-integration.md`](./notion-integration.md)
   Integración zero-template de Notion, contrato de `.env`, modelo de páginas y límites de la API.

7. [`security.md`](./security.md)
   Modelo de seguridad, manejo de secretos, bloqueos y normas de extensión segura.

8. [`testing-and-release.md`](./testing-and-release.md)
   Suite de tests, cobertura por archivo, estrategia E2E y checklist de release.

## Reglas de diseño importantes

- `autopilot` orquesta; no debe reinventar el flujo manualmente.
- `product-phase` es el carril no interactivo para generar artefactos de producto.
- `publish` debe garantizar siempre:
  - resumen corto en la tarjeta
  - `.md` adjunto
  - miembro asignado real si la HU tiene owner
- la selección de proveedor de publicación vive en `.pspo-agent/runtime/publish-provider.json`
- los secretos de Trello y Notion nunca deben aparecer en prompts, logs ni lecturas directas de `.env`.

## Fuentes de verdad

- Manifest del plugin: [`../.claude-plugin/plugin.json`](../.claude-plugin/plugin.json)
- MCP configurado: [`../.mcp.json`](../.mcp.json)
- Ajustes por defecto: [`../settings.json`](../settings.json)
- Servidor MCP: [`../servers/trello-mcp.py`](../servers/trello-mcp.py)
- Fallback oficial: [`../servers/trello-fallback.py`](../servers/trello-fallback.py)
- Fallback oficial Notion: [`../servers/notion-fallback.py`](../servers/notion-fallback.py)
- Launcher MCP: [`../servers/trello-mcp-launcher.py`](../servers/trello-mcp-launcher.py)
- Selector de proveedor: [`../hooks/scripts/publish-provider.py`](../hooks/scripts/publish-provider.py)
- Hooks: [`../hooks/hooks.json`](../hooks/hooks.json)
- Ejemplo de credenciales: [`../.env.example`](../.env.example)
