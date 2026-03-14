---
name: team
description: >
  Gestiona el equipo del proyecto: cargar miembros desde CSV o mediante
  asistente guiado, con dedicacion y uso de agentes IA. Los datos se
  persisten en team.csv para futuras sesiones y planificacion de sprint.
disable-model-invocation: false
allowed-tools: Read, Grep, Glob, Write, Edit
---

# /pspo-agent:team -- Gestion de equipo

## Tu rol

Coordinas la definicion del equipo del proyecto delegando en el agente `sprint-planner`. El equipo se persiste en `team.csv` y se usa para la planificacion de sprint.

## Flujo

### Si existe `team.csv`

Lee el fichero y muestra el equipo actual:

Muestra el equipo actual en tabla:

```
Equipo del proyecto (team.csv):

| # | Nombre       | Rol       | Categoria | Dedicacion | Agente IA |
|---|-------------|-----------|-----------|------------|-----------|
| 1 | Ana Garcia  | frontend  | Senior    | 100%       | si        |
| 2 | Pedro Lopez | backend   | Mid       | 50%        | no        |
| 3 | Laura Ruiz  | fullstack | Junior    | 80%        | si        |
```

Luego usa AskUserQuestion para preguntar:
- Pregunta: "Que quieres hacer con el equipo?"
- Opciones:
  - **"Anadir un miembro"** (description: "Registra un nuevo miembro del equipo paso a paso")
  - **"Editar un miembro"** (description: "Modifica los datos de un miembro existente (indica el numero)")
  - **"Eliminar un miembro"** (description: "Quita un miembro del equipo (indica el numero)")
  - **"Volver"** (description: "El equipo esta correcto, continuar sin cambios")

IMPORTANTE: Usa siempre AskUserQuestion para presentar opciones. NUNCA listes opciones como texto plano con letras entre corchetes.

### Si no existe `team.csv`

Muestra este mensaje:

```
Para planificar el sprint necesito conocer al equipo.

Los datos que necesito de cada miembro son:
  - Nombre completo
  - Email (para invitarle al tablero de Trello)
  - Rol (frontend, backend, fullstack, QA, devops...)
  - Categoria (Junior, Mid, Senior)
  - Dedicacion al proyecto (% de tiempo: 100 = completo, 50 = media jornada)
  - Usa agente de IA para desarrollar? (si/no) -- esto aplica un factor de
    productividad del 65% en la planificacion
```

Usa AskUserQuestion:
- Pregunta: "Como quieres configurar el equipo?"
- Opciones:
  - **"Tengo la plantilla CSV"** (description: "Ya he descargado y rellenado la plantilla desde pspo-agent.com/team-template.csv. Indicame la ruta del fichero.")
  - **"Definir miembro a miembro"** (description: "Te digo los datos de cada persona y tu generas el CSV")
  - **"Descargar plantilla primero"** (description: "Dame el enlace para descargar la plantilla CSV y rellenarla")

IMPORTANTE: Usa siempre AskUserQuestion para presentar opciones. NUNCA listes opciones como texto plano con letras entre corchetes.

Si el usuario elige **"Descargar plantilla primero"**:

```
Descarga la plantilla desde:

  https://pspo-agent.com/team-template.csv

El formato del CSV es:

  nombre,email,rol,categoria,dedicacion,usa_agente_ia

Ejemplo:
  Ana Garcia,ana@empresa.com,frontend,Senior,100,si
  Pedro Lopez,pedro@empresa.com,backend,Mid,50,no

Cuando la tengas rellena, ejecuta /pspo-agent:team y elige "Tengo la plantilla CSV".
```

Si el usuario elige **"Definir miembro a miembro"**, pregunta primero:

```
Cuantas personas componen el equipo?
```

Con el numero, pregunta los datos de cada uno en secuencia (nombre, email, rol, categoria, dedicacion, usa agente IA). Al terminar cada miembro, muestra el resumen y pregunta si anadir otro o confirmar.

### Modo guiado

Para cada miembro, pregunta en secuencia:

1. **Nombre completo**
2. **Email**
3. **Rol** (texto libre, ej: frontend, backend, fullstack, QA, devops)
4. **Categoria:** Junior, Mid o Senior
5. **Dedicacion al proyecto:** porcentaje de 0 a 100 (100 = tiempo completo)
6. **Usa agente de IA para desarrollar?** (si/no)
   - Si responde "si", informa brevemente: "Se aplicara un factor de correccion del 65% en la planificacion de sprint (configurable en settings.json)."

Tras cada miembro:

```
Miembro anadido: Ana Garcia (frontend, Senior, 100%, agente IA: si)

Anadir otro miembro? (s/n)
```

### Confirmacion y guardado

Al terminar, muestra el resumen completo y pide confirmacion:

```
Resumen del equipo ({N} miembros):

| # | Nombre       | Email             | Rol       | Categoria | Dedicacion | Agente IA |
|---|-------------|-------------------|-----------|-----------|------------|-----------|
| 1 | Ana Garcia  | ana@empresa.com   | frontend  | Senior    | 100%       | si        |
| 2 | Pedro Lopez | pedro@empresa.com | backend   | Mid       | 50%        | no        |

Guardar equipo? (s/n)
```

Si confirma, escribe `team.csv` con cabecera:

```csv
nombre,email,rol,categoria,dedicacion,usa_agente_ia
Ana Garcia,ana@empresa.com,frontend,Senior,100,si
Pedro Lopez,pedro@empresa.com,backend,Mid,50,no
```

### Transicion automatica al terminar

Al terminar de guardar team.csv, informa:

"Equipo configurado: {N} miembros. Continuando con la planificacion."

Y vuelve automaticamente al flujo que lo invoco (sprint-plan normalmente). No preguntes al usuario que quiere hacer. El equipo ya esta listo, el siguiente paso es continuar con lo que se estaba haciendo.

### Modo importacion CSV

Puedes descargar la plantilla CSV desde https://pspo-agent.com/team-template.csv

1. Lee el fichero indicado por el usuario.
2. Valida que tiene las columnas necesarias (nombre, email, rol, categoria, dedicacion, usa_agente_ia).
3. Si faltan columnas, informa cuales y ofrece completarlas interactivamente.
4. Muestra el equipo importado y pide confirmacion antes de guardar.

## Reglas

- NUNCA inventes miembros del equipo. Solo registra lo que el usuario proporciona.
- Valida el email con formato basico (contiene @ y punto).
- Dedicacion debe estar entre 0 y 100.
- usa_agente_ia solo acepta "si" o "no".
- Si el usuario no sabe la dedicacion, sugiere 100% como valor por defecto.
