---
name: sprint-plan
description: >
  Planifica un sprint: configura la Definition of Done, calcula la capacidad
  del equipo (con factor de correccion por agentes IA) y evalua si las
  historias aprobadas caben en el sprint. Sugiere recortes si se desborda.
disable-model-invocation: false
allowed-tools: Read, Grep, Glob, Write, Edit
---

# /pspo-agent:sprint-plan -- Planificacion de sprint

## Tu rol

Coordinas la planificacion de un sprint delegando en el agente `sprint-planner`. Unes tres piezas: la Definition of Done, la capacidad del equipo, y las historias aprobadas.

## Flujo

### Paso 1: Verificar prerequisitos

Comprueba en orden:

1. **Equipo definido:** existe `team.csv`?
   - Si no existe, NO continues con la planificacion. Muestra:
     ```
     Para planificar el sprint necesito conocer al equipo: quienes son,
     cuanto tiempo dedican al proyecto y si usan agentes de IA.

     Puedes descargar la plantilla CSV desde: https://pspo-agent.com/team-template.csv
     ```
     El equipo es OBLIGATORIO para planificar. Redirige automaticamente a /pspo-agent:team:
     "Para planificar necesito conocer al equipo. Vamos a configurarlo."
     -> Redirige a /pspo-agent:team automaticamente, luego vuelve aqui.
2. **Historias aprobadas:** existe al menos un fichero en `docs/historias/`?
   - Si no: "No hay historias aprobadas. Empieza por el descubrimiento." -> redirige a `/pspo-agent:discovery`.
3. **Definition of Done:** existe `docs/dod.md`?
   - Si no: ofrece configurarla (ver paso 1b).

### Paso 1b: Configurar DoD (si no existe)

Usa AskUserQuestion para preguntar al usuario:
- Pregunta: "No tienes una Definition of Done configurada para este proyecto. La DoD define los criterios minimos que toda historia debe cumplir para considerarse terminada. Que quieres hacer?"
- Opciones:
  - **"Usar DoD por defecto"** (description: "Aplica 8 criterios estandar: tests, code review, linter, seguridad, criterios de aceptacion, documentacion, pruebas manuales y rama mergeable")
  - **"Definir mi propia DoD"** (description: "Te preguntare criterio a criterio hasta que digas que has terminado")
  - **"Saltar por ahora"** (description: "Continua sin Definition of Done, podras configurarla mas adelante")

IMPORTANTE: Usa siempre AskUserQuestion para presentar opciones. NUNCA listes opciones como texto plano con letras entre corchetes.

**DoD por defecto (8 criterios):**

```markdown
# Definition of Done

Ultima actualizacion: {fecha}

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

**DoD personalizada:** pregunta al usuario criterio a criterio hasta que diga "ya esta".

Guarda en `docs/dod.md`.

### Paso 2: Leer configuracion

Lee de `settings.json`:
- `sprint.duration_days` (defecto: 10)
- `sprint.ai_agent_factor` (defecto: 0.65)

Lee de `team.csv`: los miembros y su capacidad.

Lee de `docs/historias/`: las historias aprobadas.

### Paso 3: Estimar historias con tallas (t-shirt sizing)

Lee de `settings.json` la tabla de conversion `stories.estimation_sizes`:
- S = 1 dia, M = 2 dias, L = 3 dias, XL = 5 dias (valores por defecto, configurables en settings.json).

Presenta las historias aprobadas y pide al usuario que asigne una talla a cada una:

```
Estimacion por tallas (t-shirt sizing)

Conversion (configurable en settings.json):
  S = 1 dia | M = 2 dias | L = 3 dias | XL = 5 dias

Asigna una talla (S/M/L/XL) a cada historia:

  1. HU-01: Login
  2. HU-02: Dashboard
  3. HU-03: Perfil usuario
  ...

Formato: numero=talla (ej: "1=M 2=XL 3=S") o una por linea:
```

Espera a que el usuario asigne tallas. Cuando lo haga, muestra la tabla completa:

```
| #  | Historia              | Talla | Dias equiv. | Prioridad |
|----|-----------------------|-------|-------------|-----------|
| 1  | HU-01: Login          | M     | 2           | Alta      |
| 2  | HU-02: Dashboard      | XL    | 5           | Alta      |
| 3  | HU-03: Perfil usuario | S     | 1           | Media     |
| 4  | HU-04: Busqueda       | L     | 3           | Media     |
| 5  | HU-05: Reportes       | M     | 2           | Baja      |
|    | Total                 |       | 13 dias     |           |

Quieres ajustar alguna talla antes de confirmar? (indica numero=talla o "ok"):
```

Si el usuario ajusta tallas, recalcula el total y vuelve a mostrar la tabla.
Espera confirmacion explicita ("ok", "si", "confirmo") antes de continuar.

### Paso 3b: Priorizacion asistida

Tras confirmar las estimaciones, ofrece la priorizacion asistida:

```
Quieres priorizar las historias antes de calcular capacidad? (s/n)
```

**Si el usuario acepta (s):**

1. Para cada historia, el agente sugiere:
   - **Valor de negocio:** Alto/Medio/Bajo (pregunta al usuario).
   - **Riesgo tecnico:** Alto/Medio/Bajo (el agente lo sugiere basandose en los criterios de aceptacion y la complejidad).
   - **Dependencias:** Bloqueante/Dependiente/Independiente (el agente analiza si otras historias dependen de esta).

2. Presenta la matriz completa en tabla ordenada por puntuacion descendente:

```
Priorizacion asistida (formula: Valor*3 + Riesgo*2 + Dependencia*1):

| Historia | Valor | Riesgo | Depend.  | Punt. | Orden |
|----------|-------|--------|----------|-------|-------|
| HU-01    | Alto  | Medio  | Bloq.    | 16    | 1     |
| HU-02    | Alto  | Bajo   | Indep.   | 13    | 2     |
| HU-03    | Medio | Medio  | Dep.     | 11    | 3     |
| HU-04    | Medio | Bajo   | Indep.   | 10    | 4     |
| HU-05    | Bajo  | Bajo   | Indep.   | 7     | 5     |

Pesos: Valor (Alto=3, Medio=2, Bajo=1), Riesgo (Alto=3, Medio=2, Bajo=1),
Dependencia (Bloqueante=3, Independiente=2, Dependiente=1).

Puedes ajustar cualquier valor (indica historia y campo, ej: "HU-03 Valor=Alto"):
```

3. Espera confirmacion o ajustes del usuario. Si el usuario modifica valores, recalcula puntuaciones y reordena.

4. El orden priorizado se usa en el paso 5 para el recorte: si el sprint no cabe, se recortan las historias de menor puntuacion primero.

**Si el usuario rechaza (n):**

Se mantiene la prioridad original (Alta/Media/Baja) como criterio de recorte, igual que antes.

### Paso 4: Calcular capacidad

Calcula la capacidad del equipo para el sprint:

```
Sprint de {N} dias ({N/5} semanas)
Factor IA: {factor}% de reduccion de tiempo

Equipo:
| Miembro          | Dedicacion | Agente IA | Dias reales | Capacidad equiv. |
|------------------|-----------|-----------|-------------|------------------|
| Ana (Senior)     | 100%      | si        | 10          | 28.6 dias        |
| Pedro (Mid)      | 50%       | no        | 5           | 5 dias           |
| Laura (Junior)   | 80%       | si        | 8           | 22.9 dias        |
| Total            |           |           | 23 dias     | 56.5 dias        |
```

Donde:
- `dias_reales = duracion_sprint * (dedicacion / 100)`
- `capacidad_equiv = dias_reales / (1 - factor_ia)` si usa agente IA
- `capacidad_equiv = dias_reales` si no usa agente IA

La primera vez que presentes el factor IA, explica brevemente:

```
El factor de correccion por agente IA (65%) esta respaldado por estudios
con agentes autonomos (Devin/Cognition 2025, Amazon Q 2024, Claude Code 2026).
Significa que una tarea de 10 dias sin agente se completa en 3.5 dias con agente.
Es configurable en settings.json (recomendado: 70%, rango: 30-80%).
```

### Paso 5: Veredicto

Compara el total de historias contra la capacidad equivalente.

**Si cabe (historias <= capacidad):**

```
Resultado:
  Historias:  22 dias de trabajo
  Capacidad:  56.5 dias equivalentes
  Ocupacion:  39%

  [OK] El sprint cabe holgadamente.

Quieres continuar con la publicacion? -> /pspo-agent:publish
```

**Si no cabe (historias > capacidad):**

```
Resultado:
  Historias:  65 dias de trabajo
  Capacidad:  56.5 dias equivalentes
  Ocupacion:  115% (excede en 8.5 dias)

  [!] El sprint esta desbordado.

Sugerencia de recorte (por menor puntuacion o prioridad):
  [-] HU-05: Reportes (4 dias, Punt. 7) -> siguiente sprint
  [-] HU-04: Busqueda (8 dias, Punt. 10) -> siguiente sprint

Con este recorte:
  Historias:  53 dias
  Capacidad:  56.5 dias
  Ocupacion:  94%
  [OK] Sprint viable.

Aceptas esta sugerencia? (s/n/ajustar)
```

Si el usuario rechaza la sugerencia, permite seleccionar manualmente que historias quitar.

### Paso 6: Guardar planificacion

Tras la aprobacion del sprint, guarda un resumen en `docs/sprint-plan.md`:

```markdown
# Sprint plan

Fecha: {fecha}
Duracion: {N} dias
Factor IA: {factor}%

## Equipo

| Miembro | Dedicacion | Agente IA | Capacidad equiv. |
|---------|-----------|-----------|------------------|
| ... | ... | ... | ... |

## Historias incluidas

| Historia | Talla | Dias | Asignado a | Prioridad |
|----------|-------|------|-----------|-----------|
| ... | ... | ... | ... | ... |

## Historias excluidas (siguiente sprint)

| Historia | Talla | Dias | Prioridad | Motivo |
|----------|-------|------|-----------|--------|
| ... | ... | ... | ... | Desbordamiento de capacidad |

## Resumen

- Total historias: {N} dias
- Capacidad equipo: {N} dias equiv.
- Ocupacion: {N}%
```

### Paso 7: Actualizar ficheros de HU con sprint y asignacion

Despues de guardar el sprint-plan, actualiza cada fichero de `docs/historias/HU-XX-*.md` que este incluido en el sprint:

1. Establece el campo **Sprint** en la tabla de metadatos (ej: "Sprint 1").
2. Si se ha asignado un miembro, establece el campo **Asignado a** con su nombre.
3. Actualiza el campo **Ultima modificacion** con la fecha actual.

Esto garantiza que cada HU individual tiene la informacion de planificacion unitaria: a que sprint pertenece y quien la va a desarrollar.

## Reglas

- NUNCA estimes historias que no esten aprobadas.
- NUNCA fuerces un sprint desbordado. Presenta datos y deja que el usuario decida.
- Las estimaciones son orientativas. Siempre permite al usuario ajustarlas.
- Al recortar, si se uso priorizacion asistida, empieza por las historias de menor puntuacion. Si no se uso, empieza por las de menor prioridad (Alta/Media/Baja).
- Si dos historias tienen la misma puntuacion o prioridad, sugiere recortar la de mas dias (libera mas capacidad).
- No repitas la tabla de estudios del factor IA cada vez. Solo la primera vez.
