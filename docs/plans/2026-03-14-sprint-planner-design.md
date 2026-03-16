# Diseno: agente sprint-planner

> Nota de estado (2026-03-15): este documento es un plan historico de diseno. Sirve para entender decisiones tomadas el 14/03/2026, pero no debe leerse como especificacion viva del plugin actual.

**Fecha:** 2026-03-14
**Estado:** Aprobado

## Resumen

Nuevo agente `sprint-planner` que unifica tres capacidades: Definition of Done (DoD) por proyecto, gestion de equipo con capacidad y uso de agentes IA, y planificacion de sprint con deteccion de desbordamiento.

## Componentes

### Agente: sprint-planner

- **Herramientas fichero:** Read, Grep, Glob, Write, Edit
- **Herramientas MCP:** trello-client (add-checklist)
- **No genera historias, no publica tarjetas.** Solo planifica y anade checklists DoD.

### Skills nuevas

- `/pspo-agent:team` - Cargar/editar equipo desde CSV
- `/pspo-agent:sprint-plan` - Planificar sprint: DoD + capacidad + historias

### Definition of Done

- Fichero: `docs/dod.md`
- 8 criterios por defecto: tests unitarios, code review, linter+tipado, seguridad dependencias, criterios de aceptacion verificados, documentacion, prueba manual local, rama mergeable
- Se anade como checklist en cada tarjeta de Trello al publicar

### Equipo y capacidad

- Fichero: `team.csv`
- Formato: nombre, email, rol, categoria, dedicacion (%), usa_agente_ia (si/no)
- Factor IA por defecto: 65% de reduccion de tiempo (recomendado: 70%)
- Rango configurable: 30% a 80%

### Factor IA: respaldo cientifico

| Estudio | Reduccion | Contexto |
|---------|-----------|----------|
| Amazon Q (2024) | ~97% | Migraciones Java, 79% codigo aprobado sin cambios |
| Devin/Nubank (2025) | 92% (12x) | Migracion ETL |
| Devin/Oracle (2025) | 93% (14x) | Migracion repos Java legacy |
| Devin general (2025) | 75% (4x) | Tareas de junior engineer |
| Claude Code agent (2026) | 30-40% | Desarrollo general |

Factor 65% por defecto es conservador. 70% recomendado. Configurable 30-80%.

### Calculo de capacidad

```
dias_reales = sprint_days * (dedicacion / 100)

si usa_agente_ia:
    capacidad_equiv = dias_reales / (1 - factor_ia)
sino:
    capacidad_equiv = dias_reales
```

Historias se estiman en "dias sin agente" (unidad base). Si total historias < capacidad equivalente, el sprint cabe.

### Cuando no cabe

El agente sugiere recorte por menor prioridad. El usuario aprueba, ajusta o rechaza.

### Nueva herramienta MCP: add-checklist

- Input: cardId, name, items[]
- API: POST /1/cards/{cardId}/checklists + POST /1/checklists/{id}/checkItems

### Ficheros a crear/modificar

| Fichero | Accion |
|---------|--------|
| agents/sprint-planner.md | Crear |
| skills/team/SKILL.md | Crear |
| skills/sprint-plan/SKILL.md | Crear |
| servers/trello-mcp.py | Anadir add-checklist |
| settings.json | Anadir secciones sprint y dod |
| .claude-plugin/plugin.json | Registrar agente y skills |

### Flujo integrado

```
start -> onboarding -> discovery -> generate-stories -> validate
                                                          |
                                                    sprint-plan
                                                          |
                                                    save-docs -> publish (+ DoD checklist)
```
