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

```
Equipo del proyecto (team.csv):

| # | Nombre       | Rol       | Categoria | Dedicacion | Agente IA |
|---|-------------|-----------|-----------|------------|-----------|
| 1 | Ana Garcia  | frontend  | Senior    | 100%       | si        |
| 2 | Pedro Lopez | backend   | Mid       | 50%        | no        |
| 3 | Laura Ruiz  | fullstack | Junior    | 80%        | si        |

Que quieres hacer?
  [A] Anadir un miembro
  [E] Editar un miembro (indica el numero)
  [D] Eliminar un miembro (indica el numero)
  [V] Volver (equipo correcto)
```

### Si no existe `team.csv`

```
No hay equipo configurado para este proyecto.

Como quieres definirlo?
  [G] Guiado (te pregunto miembro a miembro)
  [C] Importar desde CSV (indica la ruta del fichero)
```

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

### Modo importacion CSV

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
