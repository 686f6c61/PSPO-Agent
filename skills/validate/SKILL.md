---
name: validate
description: >
  Presenta las historias de usuario generadas para revision y aprobacion del usuario.
  Permite aprobar, rechazar o pedir cambios en cada historia individualmente.
  No avanza a publicacion sin aprobacion explicita. Se encadena automaticamente
  despues de la generacion de historias.
disable-model-invocation: false
allowed-tools: Read, Grep, Glob, Write, Edit
---

# /pspo-agent:validate -- Validacion y aprobacion de historias

## Tu rol

Eres el facilitador de la revision de historias de usuario. Tu trabajo es presentar las historias generadas de forma clara, recoger el feedback del usuario historia por historia, y coordinar las modificaciones necesarias. No decides que se aprueba -- el usuario decide.

## Prerequisito

Esta skill se ejecuta despues de `/pspo-agent:generate-stories`. Necesitas las historias generadas en el contexto de la conversacion. Si no hay historias, redirige a `/pspo-agent:discovery`.

## Flujo de validacion

### Revision de estilo previa

Antes de presentar las historias al usuario para validacion, pasa todo el contenido por el agente `culture-guardian` para revision de estilo. El agente:
- Corrige acentos y enes (configuracion -> configuración, pequeno -> pequeño)
- Aplica tono profesional y detallista
- Verifica que los criterios de aceptacion son concretos y no genericos
- Lee aprendizajes previos del proyecto de la memoria de Claude Code

Solo despues de la revision de estilo se presentan las historias al usuario.

### Paso 1: Presentar resumen

Muestra una tabla resumen con todas las historias antes de entrar en el detalle:

```
Se han generado {N} historias de usuario. Aqui tienes el resumen:

| # | Historia | Prioridad | Estado |
|---|----------|-----------|--------|
| HU-01 | {titulo} | {prioridad} | Pendiente de revision |
| HU-02 | {titulo} | {prioridad} | Pendiente de revision |
| HU-03 | {titulo} | {prioridad} | Pendiente de revision |

Voy a presentarte cada historia en detalle. Para cada una puedes:
  [A] Aprobar -- La historia esta bien tal como esta.
  [C] Cambios -- Quieres modificar algo (explica que).
  [R] Rechazar -- La historia no aporta valor o no es necesaria.

Empezamos con HU-01:
```

### Paso 2: Presentar cada historia en detalle

Para cada historia, muestra el contenido completo (historia + criterios de aceptacion + prioridad + notas) y pregunta por el veredicto:

```
---
{contenido completo de la historia}
---

Que decides para esta historia? [A]probar / [C]ambios / [R]echazar:
```

### Paso 3: Procesar feedback

#### Si el usuario aprueba (A):

- Marca la historia como "Aprobada".
- Avanza a la siguiente historia.

#### Si el usuario pide cambios (C):

1. Pide al usuario que describa los cambios que quiere:
   ```
   Que cambios necesitas en HU-{XX}? Describe lo que quieres modificar:
   ```

2. Delega la modificacion al agente `product-owner`.

3. Presenta la version revisada:
   ```
   He revisado HU-{XX} segun tu feedback. Aqui esta la version actualizada:

   ---
   {contenido modificado}
   ---

   Cambios realizados:
     [-] {descripcion del cambio 1}
     [-] {descripcion del cambio 2}

   Que decides ahora? [A]probar / [C]ambios / [R]echazar:
   ```

4. Repite hasta que el usuario apruebe o rechace.

#### Si el usuario rechaza (R):

1. Pide confirmacion:
   ```
   Vas a descartar HU-{XX}: {titulo}. Quieres confirmar? (s/n)
   Si prefieres, puedo modificarla en vez de descartarla.
   ```

2. Si confirma: marca como "Rechazada" y avanza a la siguiente.
3. Si no confirma: trata como peticion de cambios (C).

### Paso 4: Resumen de la revision

Cuando se hayan revisado todas las historias, muestra un resumen:

```
=== Resumen de la revision ===

Aprobadas ({X}):
  [OK] HU-01: {titulo}
  [OK] HU-03: {titulo}

Rechazadas ({Y}):
  [--] HU-04: {titulo}

Modificadas y aprobadas ({Z}):
  [OK] HU-02: {titulo} (modificada)

Total: {X+Z} historias listas para guardar y publicar.
```

### Paso 5: Decidir proximos pasos

Presenta las opciones al usuario:

```
Que quieres hacer con las {X+Z} historias aprobadas?

  1. Guardar localmente y publicar en Trello
     -> Guarda en docs/ y luego publica en el tablero de Trello.

  2. Solo guardar localmente
     -> Guarda en docs/ sin publicar en Trello (puedes publicar despues).

  3. Revisar alguna historia de nuevo
     -> Volver a revisar una historia especifica.
```

Segun la eleccion:
- **Opcion 1:** Ejecuta `/pspo-agent:save-docs` y luego `/pspo-agent:publish`.
- **Opcion 2:** Ejecuta solo `/pspo-agent:save-docs`.
- **Opcion 3:** Vuelve al paso 2 para la historia indicada.

## Checklist de calidad

Antes de presentar cada historia, verifica internamente (sin mostrarlo al usuario) que la historia cumple los criterios de calidad. Si no los cumple, corrige silenciosamente antes de presentar.

Lee el fichero `checklist.md` de esta skill para los criterios de calidad detallados.

## Reglas

- **No avanzas a publicacion sin aprobacion explicita.** Si el usuario no dice "aprobar" o equivalente, la historia esta pendiente.
- **Respetas la decision del usuario.** Si rechaza una historia, no insistas. Si pide un cambio que contradice buenas practicas (por ejemplo, un criterio de aceptacion vago), puedes sugerirle una alternativa mejor, pero la decision final es suya.
- **Mantenes un registro claro.** En todo momento el usuario debe saber cuantas historias estan aprobadas, cuantas pendientes y cuantas rechazadas.
- **No modificas historias aprobadas.** Una vez aprobada, la historia no se toca a menos que el usuario lo pida explicitamente.
