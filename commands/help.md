---
description: "Muestra los comandos disponibles de PSPO Agent"
---

# Ayuda de PSPO Agent

Muestra al usuario la siguiente tabla de comandos disponibles:

| Comando | Descripcion |
|---------|-------------|
| `/pspo-agent:start` | Punto de entrada recomendado: detecta configuracion y continua el flujo correcto |
| `/pspo-agent:pspo` | Alias del punto de entrada |
| `/pspo-agent:autopilot` | Lee una carpeta con instrucciones + cualquier CSV de equipo compatible y ejecuta el flujo autonomamente hasta la gate final |
| `/pspo-agent:onboarding` | Configuracion inicial: proveedor remoto (Trello, Notion o GitHub Projects) y credenciales |
| `/pspo-agent:discovery` | Descubrimiento de producto desde cero |
| `/pspo-agent:analyze` | Analizar un documento existente (brief, email, PRD) |
| `/pspo-agent:generate-stories` | Generar historias de usuario con criterios Given/When/Then |
| `/pspo-agent:validate` | Revisar y aprobar historias generadas |
| `/pspo-agent:publish` | Publicar historias aprobadas en el proveedor remoto activo (Trello, Notion o GitHub Projects) |
| `/pspo-agent:save-docs` | Guardar artefactos de producto en ficheros locales |
| `/pspo-agent:team` | Gestionar equipo del proyecto |
| `/pspo-agent:assign` | Proponer y guardar asignaciones de historias al equipo |
| `/pspo-agent:dependencies` | Detectar y guardar dependencias y bloqueantes |
| `/pspo-agent:sprint-plan` | Planificar sprint |
| `/pspo-agent:sprint-review` | Cerrar y revisar sprint |
| `/pspo-agent:audit` | Auditoria senior de las historias: completitud, coherencia, huecos |
| `/pspo-agent:export` | Exportar historias a CSV, JSON o Jira |
| `/pspo-agent:update` | Comprobar actualizaciones del plugin |
| `/pspo-agent:help` | Esta ayuda |

PSPO Agent es un plugin no oficial de Claude Code con 6 agentes especializados (product-owner, publisher, sprint-planner, culture-guardian, requirement-analyst, senior-auditor) que cubren el ciclo completo de gestion de producto: desde el descubrimiento hasta la publicacion en el proveedor remoto activo (Trello, Notion o GitHub Projects).
