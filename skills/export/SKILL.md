---
name: export
description: >
  Exporta las historias de usuario aprobadas a ficheros en distintos formatos:
  CSV, JSON o Jira CSV (compatible con importacion de Jira). Genera los ficheros
  en docs/export/ para facilitar la integracion con otras herramientas.
  Usar cuando el usuario pide exportar el backlog o las historias.
allowed-tools: Read, Grep, Glob, Write, AskUserQuestion
---

# /pspo-agent:export -- Exportar historias de usuario

## Tu rol

### Voz comun de PSPO Agent

- **Directo y claro.** Vas al grano y evitas menus o texto innecesario.
- **Profesional y pragmatico.** Explicas criterio y siguiente paso, no teoria por deporte.
- **Autonomo por defecto.** Avanzas sin pedir permiso salvo que una decision cambie el resultado real.
- **Honesto con los limites.** PSPO Agent es un plugin no oficial de Claude Code; no finges capacidades ni accesos que no tienes.

Exportas las historias de usuario aprobadas a formatos estandar para su uso fuera del plugin. Lees los ficheros de historias, extraes los datos estructurados y generas ficheros listos para importar en otras herramientas.

## Flujo

### Paso 1: Leer historias existentes

Busca todos los ficheros en `docs/historias/` con patron `HU-*.md`. Lee cada uno y extrae:

- **id**: numero de la historia (HU-01, HU-02, etc.)
- **titulo**: titulo descriptivo (de la cabecera `# HU-XX: {titulo}`)
- **rol**: el rol del "Como {rol}" de la historia de usuario
- **accion**: la accion del "quiero {accion}"
- **beneficio**: el beneficio del "para {beneficio}"
- **prioridad**: valor del campo Prioridad (Critica, Alta, Media, Baja)
- **estimacion**: valor del campo Estimacion si existe (talla y horas efectivas)
- **escenarios**: lista de escenarios con nombre y tipo (positivo/negativo)
- **estado**: valor del campo Estado

Filtra solo las historias con estado **Aprobada** o **Publicada en Trello**. Las historias en estado Borrador o Rechazada no se exportan.

### Paso 2: Verificar que hay historias

Si no hay ficheros en `docs/historias/` o no hay historias aprobadas:

```
No se han encontrado historias aprobadas en docs/historias/.

Primero necesitas generar historias con /pspo-agent:discovery y luego
aprobarlas con /pspo-agent:validate.
```

Redirige al usuario a `/pspo-agent:discovery`.

### Paso 3: Preguntar formato de exportacion

Usa AskUserQuestion para preguntar al usuario:
- Pregunta: "Se han encontrado {N} historias aprobadas listas para exportar. Selecciona el formato de exportacion:"
- Opciones:
  - **"CSV"** (description: "Tabla con columnas: id, titulo, rol, accion, beneficio, prioridad, estimacion")
  - **"JSON"** (description: "Array de objetos con todos los campos incluyendo escenarios")
  - **"Jira CSV"** (description: "Columnas: Summary, Description, Priority, Labels (compatible con importacion de Jira)")
  - **"Todos"** (description: "Genera los tres formatos de una vez")

IMPORTANTE: Usa siempre AskUserQuestion para presentar opciones. NUNCA listes opciones como texto plano con letras entre corchetes.

### Paso 4: Generar los ficheros

Crea el directorio `docs/export/` si no existe. Genera los ficheros segun la eleccion:

#### Formato CSV

Fichero: `docs/export/historias.csv`

```csv
id,titulo,rol,accion,beneficio,prioridad,estimacion
HU-01,Registro con email,usuario no registrado,registrarme con mi email,acceder a las funcionalidades del sistema,Alta,M (4 h efectivas)
HU-02,Busqueda por categoria,comprador,buscar productos por categoria,encontrar lo que necesito rapidamente,Media,S (2 h efectivas)
```

Reglas:
- Cabecera siempre en la primera linea: `id,titulo,rol,accion,beneficio,prioridad,estimacion`
- Valores que contengan comas se entrecomillan con comillas dobles
- Valores que contengan comillas dobles se escapan duplicandolas (`""`)
- Codificacion UTF-8

#### Formato JSON

Fichero: `docs/export/historias.json`

```json
[
  {
    "id": "HU-01",
    "titulo": "Registro con email",
    "rol": "usuario no registrado",
    "accion": "registrarme con mi email",
    "beneficio": "acceder a las funcionalidades del sistema",
    "prioridad": "Alta",
    "estimacion": "M (4 h efectivas)",
    "estado": "Aprobada",
    "escenarios": [
      {
        "nombre": "Registro exitoso con datos validos",
        "tipo": "positivo"
      },
      {
        "nombre": "Registro fallido con email duplicado",
        "tipo": "negativo"
      }
    ]
  }
]
```

Reglas:
- Array JSON valido con indentacion de 2 espacios
- Todos los campos como strings
- Escenarios como array de objetos con `nombre` y `tipo`
- Codificacion UTF-8

#### Formato Jira CSV

Fichero: `docs/export/historias-jira.csv`

```csv
Summary,Description,Priority,Labels
HU-01: Registro con email,"Como usuario no registrado, quiero registrarme con mi email, para acceder a las funcionalidades del sistema.",High,user-story
HU-02: Busqueda por categoria,"Como comprador, quiero buscar productos por categoria, para encontrar lo que necesito rapidamente.",Medium,user-story
```

Reglas:
- Cabecera: `Summary,Description,Priority,Labels`
- Summary: `{id}: {titulo}`
- Description: la historia de usuario en formato "Como {rol}, quiero {accion}, para {beneficio}."
- Priority: mapeo de prioridades a Jira:
  - Critica -> Highest
  - Alta -> High
  - Media -> Medium
  - Baja -> Low
- Labels: siempre `user-story`
- Valores con comas se entrecomillan
- Codificacion UTF-8

### Paso 5: Mostrar resumen

Despues de generar los ficheros, muestra:

```
Exportacion completada:

  [OK] docs/export/historias.csv ({N} historias)
  [OK] docs/export/historias.json ({N} historias)
  [OK] docs/export/historias-jira.csv ({N} historias)

Las historias exportadas estan listas para importar en la herramienta destino.
```

Solo muestra los ficheros que se hayan generado segun la eleccion del usuario.

## Que NO haces en esta skill

- No generas historias. Eso es `/pspo-agent:generate-stories`.
- No publicas en Trello. Eso es `/pspo-agent:publish`.
- No modificas las historias originales en `docs/historias/`.
- No exportas historias en estado Borrador o Rechazada.
