---
name: analyze
description: >
  Analiza un documento crudo (brief, email, PRD, mensaje) y lo interroga hasta
  alcanzar un 80% de claridad en 8 categorias. Sustituye al discovery cuando el
  usuario aporta un documento como punto de partida. Usar cuando el usuario pega
  texto o referencia un documento existente.
disable-model-invocation: false
allowed-tools: Read, Grep, Glob, Write, Edit
---

# /pspo-agent:analyze -- Analisis de requisitos

## Tu rol

Coordinas el analisis de un documento crudo delegando en el agente `requirement-analyst`. Este flujo **sustituye** a `/pspo-agent:discovery` cuando el usuario aporta un documento de partida.

## Cuando se activa

- El usuario ejecuta `/pspo-agent:analyze` explicitamente.
- El usuario pega un bloque de texto largo (mas de 100 palabras) durante `/pspo-agent:start` o al describir su idea.
- El usuario referencia un fichero ("analiza este documento", "mira este brief").

## Flujo

### Paso 1: Recibir el documento

Si el usuario ya ha pegado texto, usarlo directamente. Si no:

```
Pega el documento que quieres analizar.

Puede ser cualquier cosa: un brief, un email, un mensaje de Slack,
un PRD, una lista de funcionalidades o una descripcion informal.

Pega el texto aqui:
```

### Paso 2: Delegar al requirement-analyst

Pasa el documento completo al agente `requirement-analyst`. El agente:

1. Lee el documento completo sin interrumpir.
2. Evalua la claridad inicial de las 8 categorias.
3. Muestra el indicador de claridad con porcentajes.
4. Hace preguntas priorizadas por impacto (una a la vez).
5. Actualiza el indicador tras cada respuesta.
6. Cuando alcanza el 80%, presenta el resumen de validacion.

### Paso 3: Transicion a historias

Cuando el usuario confirma el resumen de validacion:

Usa AskUserQuestion para preguntar al usuario:
- Pregunta: "Analisis completado. El documento esta listo para generar historias. Quieres continuar?"
- Opciones:
  - **"Generar historias de usuario"** (description: "Lanza /pspo-agent:generate-stories con el contexto del analisis")
  - **"Hacer descubrimiento adicional"** (description: "Lanza /pspo-agent:discovery con el analisis como base para preguntas mas enfocadas")
  - **"Parar aqui"** (description: "El analisis queda guardado en docs/analisis-requisitos.md para usarlo mas tarde")

IMPORTANTE: Usa siempre AskUserQuestion para presentar opciones. NUNCA listes opciones como texto plano con letras entre corchetes.

Si elige "Generar historias de usuario", el agente `product-owner` recibe el contexto del analisis (lee `docs/analisis-requisitos.md`) y genera historias directamente, sin repetir preguntas de descubrimiento.

Si elige "Hacer descubrimiento adicional", el discovery arranca con el contexto del analisis como base, haciendo preguntas mas enfocadas.

## Reglas

- NUNCA generes historias desde esta skill. Solo analiza y pregunta.
- Si el usuario pega menos de 50 palabras, sugiere usar `/pspo-agent:discovery` en su lugar.
- El documento original se guarda siempre en `docs/analisis-requisitos.md` para trazabilidad.
- Respeta el flujo del agente `requirement-analyst`: no saltees el indicador de claridad.
