# ADR-001: Estructura como plugin de Claude Code (no skill suelta)

| Campo | Valor |
|-------|-------|
| **Estado** | Aceptado |
| **Fecha** | 2026-03-13 |
| **Autor** | El Dibujante de Cajas |

## Contexto

PSPO Agent necesita integrarse con Claude Code para funcionar. Existen varias formas de extender Claude Code: ficheros en `.claude/commands/`, skills sueltas en `.claude/skills/`, o un plugin completo con directorio propio y manifiesto `plugin.json`.

El producto tiene multiples componentes interrelacionados: 6+ skills, 2 agentes, hooks de validacion y un servidor MCP. Necesita distribuirse como una unidad coherente que los usuarios puedan instalar y desinstalar de forma limpia.

## Opciones consideradas

### Opcion A: Skills sueltas en `.claude/skills/`

- **Pros:** Configuracion minima. Sin manifiesto. Facil de empezar.
- **Contras:** No hay namespace (conflictos de nombres con otras skills del usuario). No se puede distribuir como unidad. No soporta bundling de servidor MCP. No hay gestion de versiones.

### Opcion B: Plugin completo con `.claude-plugin/plugin.json`

- **Pros:** Namespace automatico (`/pspo-agent:nombre`). Distribucion como unidad via marketplaces. Soporta skills, agentes, hooks y servidores MCP empaquetados. Gestion de versiones con semver. Instalacion/desinstalacion limpia.
- **Contras:** Mas estructura inicial. Requiere manifiesto. Nombres mas largos al invocar.

### Opcion C: Solo CLAUDE.md con instrucciones

- **Pros:** Cero configuracion. Solo un fichero.
- **Contras:** No se puede encapsular un servidor MCP. No hay separacion de responsabilidades. Todo mezclado en un fichero gigante. Imposible de distribuir. No escala.

## Decision

**Opcion B: Plugin completo.**

La cantidad de componentes (6 skills, 2 agentes, 1 servidor MCP, hooks) justifica la estructura de plugin. El namespace evita conflictos. La distribucion via marketplace es necesaria para la adopcion. El overhead del manifiesto es minimo (un fichero JSON de 10 lineas).

## Consecuencias

- **Ganancia:** Distribucion limpia, versionado, namespace, empaquetado de MCP.
- **Coste:** El usuario invoca con `/pspo-agent:nombre` en lugar de `/nombre` (mas caracteres).
- **Deuda tecnica:** Ninguna significativa. La estructura de plugin es el formato oficial recomendado por Claude Code para extensiones compartidas.
