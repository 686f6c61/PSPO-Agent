# PSPO Agent

Plugin de Product Owner profesional para Claude Code. Analisis de requisitos, descubrimiento de producto, historias de usuario con criterios Given/When/Then, planificacion de sprint con factor de productividad por agentes IA, y publicacion en Trello.

## Requisitos

- Python 3.8+
- Claude Code

## Instalacion

Un solo comando:

**Linux / macOS**

```bash
curl -fsSL https://raw.githubusercontent.com/686f6c61/PSPO-Agent/main/install.sh | bash
```

**Windows (PowerShell)**

```powershell
irm https://raw.githubusercontent.com/686f6c61/PSPO-Agent/main/install.ps1 | iex
```

## Primer uso

Reinicia Claude Code y ejecuta:

```
/pspo-agent:start
```

El asistente de onboarding te guiara para configurar las credenciales de Trello y tu primer tablero.

## Skills disponibles

| Skill | Comando | Descripcion |
|-------|---------|-------------|
| analyze | `/pspo-agent:analyze` | Analiza un documento crudo (brief, email, PRD) hasta alcanzar un 80% de claridad en 8 categorias. |
| start | `/pspo-agent:start` | Punto de entrada. Detecta configuracion y redirige al flujo correcto. |
| onboarding | `/pspo-agent:onboarding` | Asistente guiado: credenciales de Trello y configuracion de tablero. |
| discovery | `/pspo-agent:discovery` | Preguntas de descubrimiento desde cero (sin documento de partida). |
| generate-stories | `/pspo-agent:generate-stories` | Genera historias con criterios de aceptacion Given/When/Then. |
| validate | `/pspo-agent:validate` | Revision historia por historia: aprobar, rechazar o pedir cambios. |
| publish | `/pspo-agent:publish` | Publica en Trello con resumen + adjunto .md + checklist DoD. |
| save-docs | `/pspo-agent:save-docs` | Guarda artefactos de producto en Markdown local. |
| update | `/pspo-agent:update` | Comprueba y aplica actualizaciones del plugin. |
| team | `/pspo-agent:team` | Gestion de equipo: CSV con dedicacion y uso de agentes IA. |
| sprint-plan | `/pspo-agent:sprint-plan` | Planificacion de sprint: DoD, estimacion t-shirt, capacidad con factor IA. |
| sprint-review | `/pspo-agent:sprint-review` | Revision de sprint: estado de tarjetas y cumplimiento de DoD. |
| export | `/pspo-agent:export` | Exportacion a CSV, JSON y Jira CSV. |
| audit | `/pspo-agent:audit` | Auditoria senior: completitud, coherencia, HU que faltan/sobran. |

## Agentes

| Agente | Responsabilidad |
|--------|----------------|
| requirement-analyst | Interroga documentos hasta alcanzar claridad suficiente para generar historias. |
| product-owner | Descubrimiento de producto, generacion de historias y validacion. |
| publisher | Publicacion en Trello: tarjetas, checklists, adjuntos, invitaciones al board. |
| sprint-planner | DoD, equipo, capacidad con factor IA y planificacion de sprint. |
| culture-guardian | Revisor de estilo: normas RAE, tono profesional, aprende del proyecto. |
| senior-auditor | Auditoria de fondo: completitud, coherencia, HU que faltan/sobran. |

## Servidor MCP

12 herramientas en Python puro (stdlib, 0 dependencias):

| Herramienta | Proposito |
|-------------|-----------|
| verify-credentials | Verificar API Key + Token |
| list-boards | Listar tableros del usuario |
| get-board | Obtener tablero con listas y etiquetas |
| create-board | Crear tablero nuevo |
| manage-lists | Crear, renombrar, reordenar, archivar listas |
| manage-labels | Crear, actualizar, eliminar etiquetas |
| create-cards | Crear tarjetas con etiquetas y miembros asignados |
| search-cards | Buscar tarjetas por titulo (deteccion de duplicados) |
| add-checklist | Anadir checklist de DoD a tarjetas |
| attach-file | Adjuntar fichero .md completo a tarjetas |
| get-board-members | Obtener miembros del tablero con sus IDs |
| invite-member | Invitar miembros al tablero por email |

## Hooks de seguridad

| Hook | Evento | Funcion |
|------|--------|---------|
| check-env.sh | PreToolUse (MCP) | Bloquea llamadas MCP si faltan credenciales en .env |
| block-trello-bash.sh | PreToolUse (Bash) | Bloquea acceso directo a Trello via curl/bash |
| check-gitignore.sh | PostToolUse (Write) | Verifica que .env esta en .gitignore |

## Configuracion

El fichero `settings.json` permite personalizar el comportamiento del plugin:

| Parametro | Defecto | Descripcion |
|-----------|---------|-------------|
| sprint.ai_agent_factor | 0.65 | Factor de productividad con agentes IA (65%) |
| sprint.ai_agent_factor_recommended | 0.70 | Factor recomendado (70%) |
| sprint.ai_agent_factor_range | [0.30, 0.80] | Rango configurable |
| sprint.duration_days | 10 | Duracion del sprint en dias |
| stories.estimation_sizes | S=1, M=2, L=3, XL=5 | Tallas t-shirt en dias |
| trello.default_lists | Backlog, Sprint actual, En progreso, En revision, Hecho | Columnas por defecto |
| trello.default_labels | Critica, Alta, Media, Baja | Etiquetas de prioridad |
| docs.date_format | DD/MM/AAAA | Formato de fechas |

## Estructura del proyecto

```
pspo-agent/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── agents/                  # 6 agentes especializados
├── skills/                  # 14 skills
├── servers/
│   └── trello-mcp.py       # Servidor MCP (Python puro, 12 herramientas, 0 dependencias)
├── hooks/
│   └── scripts/             # 3 hooks de seguridad
├── tests/                   # 239 tests (unitarios, contenido, e2e)
├── docs/                    # ADRs, arquitectura
├── .mcp.json
├── .env.example
├── settings.json
├── install.sh               # Instalador Linux/macOS
├── install.ps1              # Instalador Windows
├── uninstall.sh
└── uninstall.ps1
```

## Desinstalacion

**Linux / macOS**

```bash
bash uninstall.sh
```

**Windows (PowerShell)**

```powershell
.\uninstall.ps1
```

## Descargo de responsabilidad

PSPO Agent es una herramienta experimental que utiliza inteligencia artificial para generar
artefactos de producto. **No sustituye el criterio profesional** de un Product Owner certificado
ni de ningun rol de gestion de producto.

El contenido generado (historias de usuario, criterios de aceptacion, documentacion) es una
sugerencia automatizada que el usuario debe revisar, validar y aprobar antes de utilizarlo.
El usuario es el unico responsable de las decisiones de producto y de la informacion publicada
en Trello o cualquier otro sistema.

Este proyecto **no esta afiliado, asociado ni respaldado** por Anthropic (Claude), Atlassian
(Trello) ni Scrum.org (PSPO). Las marcas mencionadas pertenecen a sus respectivos propietarios.

El software se proporciona "tal cual", sin garantia de ningun tipo, expresa o implicita.

## Licencia

MIT

## Web

[https://pspo-agent.com](https://pspo-agent.com)
