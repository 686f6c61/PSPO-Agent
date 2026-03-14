---
name: audit
description: >
  Auditoria senior de historias de usuario. Revisa completitud, coherencia,
  calidad del contenido, HU que faltan y HU que sobran. Cruza contra el
  documento original si existe. Se activa automaticamente en la primera
  generacion y bajo demanda en las siguientes.
disable-model-invocation: false
allowed-tools: Read, Grep, Glob, Write, Edit
---

# /pspo-agent:audit -- Auditoria de historias de usuario

## Tu rol

Coordinas la auditoria delegando en el agente `senior-auditor`. Este agente revisa el fondo (no la forma) de las historias generadas.

## Cuando se activa

### Automaticamente (primera generacion)

Despues de que `/pspo-agent:generate-stories` termine de generar historias por primera vez en un proyecto (no existe `docs/auditoria-hu.md`), este paso se ejecuta ANTES de pasar a `/pspo-agent:validate`.

El flujo queda:
```
generate-stories -> [culture-guardian] -> [senior-auditor] -> validate
```

### Bajo demanda (siguientes generaciones)

El usuario ejecuta `/pspo-agent:audit` manualmente cuando quiere una revision profunda. El agente detecta que `docs/auditoria-hu.md` ya existe y ofrece:

Usa AskUserQuestion:
- Pregunta: "Ya existe una auditoria previa. Que quieres hacer?"
- Opciones:
  - **"Auditoria completa"** (description: "Revisa todas las HU desde cero")
  - **"Solo cambios recientes"** (description: "Revisa solo las HU nuevas o modificadas desde la ultima auditoria")

## Flujo

### Paso 1: Recopilar contexto

Lee en orden:
1. `docs/analisis-requisitos.md` (si existe -- documento original analizado)
2. `docs/vision.md` (si existe -- vision de producto)
3. `docs/historias/HU-*.md` (todas las historias generadas)
4. `docs/backlog.md` (si existe -- lista priorizada)
5. `docs/auditoria-hu.md` (si existe -- auditoria anterior)

### Paso 2: Delegar al senior-auditor

Pasa todo el contexto al agente `senior-auditor`. El agente:
1. Cruza el documento original contra las HU (si existe documento).
2. Revisa coherencia del conjunto.
3. Revisa calidad de contenido de cada HU.
4. Identifica HU que sobran.
5. Identifica HU que faltan.
6. Presenta el informe completo.

### Paso 3: Accion

El agente usa AskUserQuestion para preguntar que hacer con los hallazgos:
- Aplicar todo
- Revisar una a una
- Solo guardar el informe

Si el usuario elige aplicar, el agente ejecuta todas las correcciones de una vez.

### Paso 4: Guardar informe

El informe se guarda en `docs/auditoria-hu.md` con fecha, numero de hallazgos y detalle de cada uno.

## Reglas

- En la primera generacion, este paso es OBLIGATORIO. No se puede saltar.
- En generaciones posteriores, es bajo demanda.
- El informe siempre se guarda para trazabilidad.
- Si no hay hallazgos, el agente lo dice claramente y no bloquea el flujo.
