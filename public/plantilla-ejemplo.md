# Ejemplo de salida de PSPO Agent

Este archivo muestra los artefactos que PSPO Agent genera para tu proyecto.

---

## Vision del producto

**Producto:** App de gestion de tareas para equipos remotos
**Usuario objetivo:** Equipos de desarrollo de 3-10 personas que trabajan en remoto
**Problema:** Falta de visibilidad sobre quien hace que y cuando se entrega
**Propuesta de valor:** Un tablero compartido con historias bien definidas, asignaciones claras y dependencias visibles

---

## Historia de usuario: HU-01

**Como** desarrollador del equipo,
**quiero** ver mis tareas asignadas en un tablero organizado por estado,
**para** saber en que debo trabajar sin preguntar al tech lead.

### Prioridad
- **MoSCoW:** Must have
- **Fase:** MVP

### Criterios de aceptacion

**Escenario positivo: Ver tareas asignadas**
```gherkin
Given que estoy autenticado en el tablero
When accedo a la vista "Mis tareas"
Then veo solo las tarjetas asignadas a mi
And estan organizadas por columnas: Pendiente, En progreso, En revision, Hecho
```

**Escenario positivo: Mover tarea de estado**
```gherkin
Given que tengo una tarea en "Pendiente"
When arrastro la tarjeta a "En progreso"
Then la tarjeta cambia de columna
And se registra la fecha del cambio de estado
```

**Escenario negativo: Tarea sin asignar**
```gherkin
Given que existe una tarea sin miembro asignado
When accedo a la vista "Mis tareas"
Then la tarea sin asignar no aparece en mi vista
```

---

## Historia de usuario: HU-02

**Como** tech lead,
**quiero** ver un resumen de capacidad del equipo para el sprint,
**para** saber si las historias planificadas caben en el tiempo disponible.

### Prioridad
- **MoSCoW:** Must have
- **Fase:** MVP

### Criterios de aceptacion

**Escenario positivo: Sprint viable**
```gherkin
Given que el equipo tiene 3 miembros definidos en team.csv
And hay 5 historias aprobadas estimadas en 18 dias
When ejecuto /pspo-agent:sprint-plan
Then veo la capacidad del equipo con y sin agentes IA
And el veredicto indica que el sprint cabe
```

**Escenario negativo: Sprint desbordado**
```gherkin
Given que las historias suman mas dias que la capacidad del equipo
When ejecuto /pspo-agent:sprint-plan
Then veo el porcentaje de desbordamiento
And el agente sugiere que historias recortar por prioridad
```

---

## Equipo (team.csv)

```csv
nombre,email,rol,categoria,dedicacion,usa_agente_ia
Ana Garcia,ana@empresa.com,frontend,Senior,100,si
Pedro Lopez,pedro@empresa.com,backend,Mid,50,no
Laura Ruiz,laura@empresa.com,fullstack,Junior,80,si
```

---

## Definition of Done (docs/dod.md)

```markdown
# Definition of Done

## Criterios

- [ ] Tests unitarios escritos y en verde
- [ ] Code review aprobado por al menos 1 persona
- [ ] Sin errores de linter ni de tipado
- [ ] Sin warnings de seguridad en dependencias
- [ ] Criterios de aceptacion (Given/When/Then) verificados
- [ ] Documentacion actualizada si hay cambios en API o configuracion
- [ ] Probado manualmente en el entorno local
- [ ] Rama mergeable sin conflictos
```

---

## Backlog priorizado

| ID    | Historia                              | Prioridad | Dias est. | Estado    |
|-------|---------------------------------------|-----------|-----------|-----------|
| HU-01 | Tablero de tareas por estado          | Must      | 3         | Pendiente |
| HU-02 | Capacidad del equipo por sprint       | Must      | 2         | Pendiente |
| HU-03 | Notificaciones de cambio de estado    | Should    | 4         | Pendiente |
| HU-04 | Filtro por etiqueta y miembro         | Could     | 2         | Pendiente |

---

*Generado por PSPO Agent - Plugin de Claude Code*
