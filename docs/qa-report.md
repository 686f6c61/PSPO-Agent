# Informe de QA: PSPO Agent -- Revision de calidad completa

| Campo | Valor |
|-------|-------|
| **Auditor** | El Rompe-cosas (QA Engineer, equipo Alfred Dev) |
| **Fecha** | 2026-03-13 |
| **Fase** | QA post-implementacion |
| **Documentos base** | docs/prd.md v1.0, docs/arquitectura.md v1.0, docs/seguridad.md |
| **Suite de tests (inicial)** | 58 tests, 9 ficheros -- todos en verde |
| **Suite de tests (tras correcciones)** | 60 tests, 9 ficheros -- todos en verde |

---

## Resumen ejecutivo

Se ha realizado una revision de calidad completa del plugin PSPO Agent: code review del servidor MCP (TypeScript), revision de la suite de tests, revision de skills (Markdown), revision de agentes, revision de hooks y verificacion de coherencia general entre todos los componentes.

La revision ha identificado **2 hallazgos bloqueantes**, **5 hallazgos importantes** y **7 hallazgos menores o sugerencias**.

Durante la revision se han aplicado 3 correcciones directas:
- **QA-02 (BLOQUEANTE):** Corregido. Se ha anadido validacion de `pos` obligatorio en `handleReorder` y 2 tests nuevos.
- **QA-09 (MENOR):** Corregido. Tests de cobertura para `reorder` sin `pos` y sin `listId`.
- **QA-11 (MENOR):** Corregido. Bug de regex en `check-gitignore.sh`.

Queda 1 hallazgo bloqueante sin resolver (QA-01) que requiere decision del equipo.

---

## Estado de los tests

```
# Antes de la revision
Test Files  9 passed (9)
     Tests  58 passed (58)

# Despues de la revision (con correcciones aplicadas)
Test Files  9 passed (9)
     Tests  60 passed (60)
  Duration  1.27s
```

Todos los tests pasan. No hay tests en rojo.

---

## Hallazgos ordenados por severidad

---

### BLOQUEANTES

---

#### QA-01: `zod` usada en produccion sin declararse como dependencia en package.json

- **Ubicacion:** `servers/trello-mcp/package.json` (secciones `dependencies` y `devDependencies`) + `servers/trello-mcp/src/index.ts:5`
- **Severidad:** BLOQUEANTE (confianza: 95)
- **Estado:** PENDIENTE -- requiere decision del equipo
- **Hallazgo:** El fichero `index.ts` importa `zod` directamente (`import { z } from "zod"`) para la validacion de esquemas de las herramientas MCP. Sin embargo, `zod` no aparece en las dependencias del `package.json`. Actualmente funciona porque `@modelcontextprotocol/sdk` tiene `zod` como peer dependency y esta presente en `node_modules`, pero esto es una dependencia implicita: si el SDK cambia su gestion de `zod` o se instala en un entorno limpio con `npm install --omit=optional`, el servidor puede fallar en runtime con `Cannot find package 'zod'`.
- **Razon:** Una dependencia usada en codigo de produccion que no esta declarada en `package.json` es invisible para cualquier herramienta de gestion de dependencias (auditoria de seguridad, actualizaciones, SBOM). Ademas, la arquitectura documenta explicitamente la intencion de no usar `zod` (doc `arquitectura.md`, seccion 13: "Dependencias rechazadas: zod -- Util pero anade peso innecesario"). Hay una contradiccion entre la decision arquitectonica documentada y la implementacion real.
- **Impacto:** El servidor MCP puede fallar en un despliegue limpio. La decision arquitectonica de rechazar `zod` queda invalidada sin documentar el cambio.
- **Solucion:** Dos opciones mutuamente excluyentes:
  - **Opcion A (recomendada):** Declarar `zod` como dependencia de produccion en `package.json` y actualizar el ADR-003 / seccion 13 de arquitectura para reflejar que se usa `zod` del SDK MCP para la validacion de esquemas de herramientas.
  - **Opcion B:** Eliminar el import de `zod` de `index.ts` y reemplazar los esquemas Zod por objetos JSON Schema nativos del SDK MCP, respetando la decision arquitectonica original.

---

#### QA-02: `handleReorder` aceptaba llamadas sin `pos` y enviaba un PUT vacio a Trello

- **Ubicacion:** `servers/trello-mcp/src/tools/manage-lists.ts:77-98`
- **Severidad:** BLOQUEANTE (confianza: 90)
- **Estado:** CORREGIDO durante esta revision
- **Hallazgo original:** La funcion `handleReorder` construia un `body` vacio cuando `input.pos` era `undefined` y luego ejecutaba `client.put()` con ese body vacio. Una llamada PUT a `/1/lists/{id}` con body vacio es una operacion sin efecto que consume rate limit de la API de Trello sin hacer nada. El LLM podia invocar la herramienta `manage-lists` con `action: "reorder"` sin proporcionar `pos`, y el servidor no lanzaba ningun error -- simplemente ejecutaba una peticion inutil y devolvia la lista sin cambios.
- **Correccion aplicada:** Se ha anadido validacion explícita en `handleReorder`:
  ```typescript
  if (input.pos === undefined) {
    throw new Error("pos es obligatorio para reordenar una lista.");
  }
  ```
  Ademas se ha simplificado el codigo: el `body` condicional se ha sustituido por `{ pos: input.pos }` directamente, ya que `pos` esta garantizado como definido tras la validacion. Se han anadido 2 tests nuevos.

---

### IMPORTANTES

---

#### QA-03: `handleDelete` de etiquetas devuelve datos ficticios en el output

- **Ubicacion:** `servers/trello-mcp/src/tools/manage-labels.ts:77-92`
- **Severidad:** IMPORTANTE (confianza: 92)
- **Estado:** PENDIENTE
- **Hallazgo:** La funcion `handleDelete` hace la llamada DELETE correctamente, pero al construir el objeto de retorno usa `input.name ?? ""` e `input.color ?? null`. Esto significa que si el llamante no proporciono `name` o `color` (que son opcionales en `ManageLabelsInput`), la respuesta devuelve una etiqueta con `name: ""` y `color: null`, independientemente del nombre y color reales que tenia la etiqueta en Trello. El agente publisher recibira datos incorrectos y los reportara al usuario como si fueran los reales.
- **Razon:** La API de Trello devuelve un objeto vacio `{}` en las respuestas DELETE exitosas, lo que impide leer el estado anterior. La solucion correcta es hacer un `GET` previo a la etiqueta si se quieren devolver sus datos reales, o bien cambiar el contrato de la herramienta para que en `delete` solo garantice el `id`.
- **Impacto:** El reporte de la operacion de borrado puede mostrar informacion incorrecta al usuario. Bajo impacto funcional (la etiqueta se borra correctamente), pero alto impacto en la confianza del reporte.
- **Solucion:** Dos opciones:
  - **Opcion A:** Hacer GET previo para obtener el nombre y color reales antes de borrar.
  - **Opcion B (mas simple):** Cambiar `ManageLabelsOutput` para que `delete` devuelva solo `{ id, deleted: true }`, sin `name` ni `color`. Actualizar el tipo `ManageLabelsOutput` con un tipo de union o hacerlo opcional.

---

#### QA-04: El hook `check-gitignore.sh` no detectaba el patron `/.env` (con barra inicial)

- **Ubicacion:** `hooks/scripts/check-gitignore.sh:52-54`
- **Severidad:** IMPORTANTE (confianza: 88)
- **Estado:** CORREGIDO PARCIALMENTE durante esta revision (el bug de regex QA-11 fue corregido como parte de esto)
- **Hallazgo:** El patron de verificacion original `^\.env$|^\.env\s` no detectaba entradas como `/.env` (con barra inicial, patron valido en `.gitignore` para anclar al directorio raiz). Tampoco detectaba `.env # comentario` (patron con comentario inline, menos habitual).
- **Correccion aplicada:** Se ha actualizado el patron para incluir la barra inicial opcional:
  ```bash
  grep -qE "^/?\.env($|\s|#)" "$GITIGNORE_FILE"
  ```
  Y el patron glob secundario:
  ```bash
  grep -qE "^/?\.env[.*]" "$GITIGNORE_FILE"
  ```

---

#### QA-05: `sanitizeString` se aplica a la URL pero no al body de POST/PUT

- **Ubicacion:** `servers/trello-mcp/src/trello-client.ts:69-72` y metodos `post`/`put`
- **Severidad:** IMPORTANTE (confianza: 85)
- **Estado:** PENDIENTE
- **Hallazgo:** La funcion `sanitizeString` se aplica al path y a los parametros de query, pero el contenido del body en `post` y `put` se serializa directamente con `JSON.stringify(body)` sin ninguna sanitizacion. Si un agente envia contenido malicioso en el body (por ejemplo, en el `desc` de una tarjeta o en el `name` de una lista), ese contenido llega sin filtrar a la API de Trello.
- **Razon:** Para un plugin que opera localmente con datos generados por el propio LLM, el riesgo es bajo. Sin embargo, la arquitectura declara que "el servidor MCP sanitiza todos los parametros antes de construir URLs" y esto es solo parcialmente cierto: sanitiza los parametros de URL, no los de body.
- **Impacto:** Incoherencia entre lo documentado en la arquitectura y la implementacion. Riesgo bajo en el contexto actual (datos locales), pero podria ser un vector si el plugin se expusiera a inputs externos.
- **Solucion:** Ampliar la sanitizacion para cubrir valores de string en el body antes de serializar, o documentar explicitamente que la sanitizacion del body no es necesaria en el contexto de uso actual (inputs del LLM en sesion local).

---

#### QA-06: Las skills `publish` y `start` declaran `allowed-tools` que podria bloquear la delegacion al agente publisher

- **Ubicacion:** `skills/publish/SKILL.md:8` y `skills/start/SKILL.md:9` (frontmatter)
- **Severidad:** IMPORTANTE (confianza: 85)
- **Estado:** PENDIENTE
- **Hallazgo:** El frontmatter de la skill `publish` declara `allowed-tools: Read, Grep, Glob`, pero el cuerpo de la skill instruye al LLM a "delegar al agente publisher" para ejecutar herramientas MCP (`get-board`, `search-cards`, `create-cards`). La herramienta `Write` tampoco esta en `allowed-tools`, pero el paso 1 del flujo instruye a ejecutar `/pspo-agent:save-docs` que escribe ficheros. La skill `start` tiene la misma restriccion: declara `Read, Grep, Glob` pero en los pasos 2 y 3 instruye a usar el agente `publisher`.
- **Razon:** Si Claude Code respeta estrictamente el `allowed-tools` del frontmatter para decidir que puede ejecutar la skill, las skills `publish` y `start` no podran delegar al agente publisher ni llamar a herramientas MCP. Esto podria hacer que el flujo se bloquee silenciosamente.
- **Impacto:** El flujo de publicacion podria no funcionar si Claude Code aplica las restricciones de `allowed-tools` de forma estricta.
- **Solucion:** Revisar si `allowed-tools` en el frontmatter de skills de Claude Code restringe tambien las herramientas accesibles por subagentes delegados. Si es asi, las skills `publish` y `start` deben incluir las herramientas necesarias o eliminar la restriccion del frontmatter. Consultar documentacion oficial de Claude Code sobre el alcance de `allowed-tools` en skills.

---

#### QA-07: Ausencia de `.env.example` en el repositorio del plugin

- **Ubicacion:** Raiz del proyecto `/home/r/Escritorio/PSPO_AI/`
- **Severidad:** IMPORTANTE (confianza: 90)
- **Estado:** PENDIENTE
- **Hallazgo:** El PRD (seccion 7) especifica que debe existir un fichero `.env.example` con las tres variables de configuracion (`TRELLO_API_KEY`, `TRELLO_TOKEN`, `TRELLO_BOARD_ID`). El informe de seguridad (SEC-02) confirma que se creo en el commit `5d20d42`. Sin embargo, al revisar el directorio raiz del proyecto, no hay un `.env.example` presente.
- **Razon:** Este fichero es necesario como plantilla de referencia para nuevos desarrolladores y como parte del criterio de aceptacion de HU-01 Escenario 5.
- **Impacto:** Un desarrollador que clone el repositorio no tiene referencia de que variables configurar. El criterio de aceptacion HU-01 Escenario 5 no esta cubierto en el repositorio actual.
- **Solucion:** Crear el fichero `.env.example` en la raiz del proyecto con el contenido especificado en la seccion 7 del PRD, con `expiration=30days` (no `expiration=never`). Ver tambien SEC-10 del informe de seguridad.

---

### MENORES

---

#### QA-08: `plugin.json` omite el campo `repository` presente en la arquitectura

- **Ubicacion:** `.claude-plugin/plugin.json`
- **Severidad:** MENOR (confianza: 82)
- **Estado:** PENDIENTE
- **Hallazgo:** La arquitectura (seccion 5.1) especifica que el `plugin.json` debe incluir el campo `"repository": "https://github.com/pspo-ai/pspo-agent"`. El fichero real no lo incluye.
- **Razon:** El campo `repository` es informativo pero ayuda a la trazabilidad del plugin en el ecosistema de Claude Code.
- **Solucion:** Anadir el campo `repository` al `plugin.json`.

---

#### QA-09: Tests de `manage-lists` no cubrian `reorder` sin `pos`

- **Ubicacion:** `servers/trello-mcp/tests/tools/manage-lists.test.ts`
- **Severidad:** MENOR (confianza: 90)
- **Estado:** CORREGIDO durante esta revision
- **Hallazgo original:** El test de `action: reorder` siempre pasaba `pos: "top"`. No existia ningun test que verificara el comportamiento cuando `pos` es `undefined` en una accion de reordenacion. Este hueco de cobertura fue directamente responsable de que el bug QA-02 no fuera detectado antes.
- **Correccion aplicada:** Se han anadido 2 tests nuevos en `describe("action: reorder")`:
  - `"lanza error si falta pos al reordenar"`
  - `"lanza error si falta listId al reordenar"`

---

#### QA-10: Tests de `manage-labels` no cubren `delete` con etiqueta sin nombre ni color en el input

- **Ubicacion:** `servers/trello-mcp/tests/tools/manage-labels.test.ts`
- **Severidad:** MENOR (confianza: 85)
- **Estado:** PENDIENTE
- **Hallazgo:** El test de `action: delete` no verifica que el output de la operacion de borrado es correcto (o incorrecto) cuando `name` o `color` no son proporcionados en el input. Este hueco de cobertura esta relacionado con el bug QA-03.
- **Solucion:** Anadir tests que verifiquen el comportamiento de delete cuando el input no incluye `name` ni `color`. Estos tests deberan actualizarse una vez que QA-03 sea corregido para reflejar el comportamiento nuevo.

---

#### QA-11: Bug de regex en `check-gitignore.sh` para detectar `.env*`

- **Ubicacion:** `hooks/scripts/check-gitignore.sh:53`
- **Severidad:** MENOR (confianza: 82)
- **Estado:** CORREGIDO durante esta revision
- **Hallazgo original:** El patron de grep usaba `^\.env\*` para detectar `.env*` en `.gitignore`. El caracter `*` en ERE no significa "cualquier cosa" -- significa "cero o mas repeticiones del caracter anterior (el `v`)". La intencion era detectar el patron glob `.env*` de gitignore, pero la regex no lo hacia correctamente. Solo detectaba `.env*` literalmente (con asterisco literal en el fichero).
- **Correccion aplicada:** Se ha cambiado el patron a `^/?\.env[.*]` que detecta cualquier caracter tras `.env` (punto o asterisco como primer caracter de un patron glob).

---

#### QA-12: El test de rate limiting es potencialmente fragil (timing-dependent)

- **Ubicacion:** `servers/trello-mcp/tests/trello-client.test.ts:283-313`
- **Severidad:** MENOR (confianza: 80)
- **Estado:** PENDIENTE (no corregido, requiere evaluacion del equipo)
- **Hallazgo:** El test verifica que con 5 peticiones y un limite de 3/segundo, el tiempo total sea mayor de 800ms. Este test depende del tiempo de ejecucion del entorno. En una maquina muy cargada, podria tardar mas de lo esperado incluso sin rate limiting real, o pasar incorrectamente si el scheduler del sistema operativo introduce latencia. El margen de 800ms (en lugar de 1000ms) da cierta tolerancia, pero es un test fragil por naturaleza.
- **Solucion:** Considerar complementar este test con una verificacion del numero de llamadas en la ventana de tiempo, que es mas determinista. Como alternativa, usar `vi.useFakeTimers()` para controlar el tiempo en el test.

---

#### QA-13: La skill `discovery/SKILL.md` tiene instrucciones contradictorias sobre el uso del agente PO

- **Ubicacion:** `skills/discovery/SKILL.md:16-18` y `skills/generate-stories/SKILL.md:14-18`
- **Severidad:** MENOR (confianza: 80)
- **Estado:** PENDIENTE
- **Hallazgo:** Las skills `discovery` y `generate-stories` dicen "Actuas como el agente `product-owner` durante esta skill" y tambien "Delega el trabajo al agente `product-owner`". Estas dos instrucciones son contradictorias: o la skill asume directamente el rol del PO, o delega en el subagente. La ambiguedad puede provocar que el LLM adopte uno u otro comportamiento de forma inconsistente entre sesiones.
- **Razon:** La arquitectura define claramente que la skill delega en el agente. La instruccion "actuas como" es un patron de rol que puede hacer que el LLM no utilice el subagente formal.
- **Solucion:** Elegir una de las dos instrucciones y eliminar la otra. Si la intencion es usar el subagente formal, mantener solo "Delega el trabajo al agente `product-owner`" y eliminar la instruccion de "actuas como".

---

#### QA-14: Ausencia de `settings.json` en el repositorio

- **Ubicacion:** Raiz del proyecto `/home/r/Escritorio/PSPO_AI/`
- **Severidad:** MENOR (confianza: 88)
- **Estado:** PENDIENTE
- **Hallazgo:** La arquitectura menciona un fichero `settings.json` en la raiz del plugin. La skill `generate-stories/SKILL.md` (paso 1) instruye al agente a "lee `settings.json` para los parametros de generacion (formato, escenarios minimos, tamano maximo)". Ese fichero no existe en el repositorio.
- **Impacto:** Si el LLM sigue la instruccion de leer `settings.json` y no lo encuentra, puede generar un error o simplemente ignorar la instruccion. El comportamiento es indeterminado.
- **Solucion:** Crear `settings.json` con valores por defecto, o modificar la instruccion en `generate-stories/SKILL.md` para indicar que si el fichero no existe se usan los valores por defecto embebidos en la skill.

---

## Notas de baja confianza (60-79)

Estas notas no son hallazgos confirmados pero merecen atencion:

1. **(Confianza: 72) La skill `onboarding/SKILL.md` valida el token con longitud 64 hex, pero los tokens modernos de Trello tienen el prefijo `ATTA` y longitud variable.** La validacion estricta de `^[0-9a-fA-F]{64}$` podria rechazar tokens validos si Trello cambia el formato. Contrastar con la especificacion actual de la API de Trello antes de afirmarlo como bug.

2. **(Confianza: 70) El agente `publisher` declara `tools: Read, Grep` en el frontmatter, pero sus instrucciones menciona que puede leer `.env` para las credenciales.** Si `.env` no esta en el path accesible con `Read`, o si Claude Code restringe `Read` a ciertos directorios, el agente podria no poder leer las credenciales. Verificar si las credenciales llegan al agente via variables de entorno (como indica el `.mcp.json`) o si realmente se leen del `.env`.

3. **(Confianza: 65) El ordenamiento de tarjetas por prioridad al publicar podria no funcionar correctamente.** La skill `publish/SKILL.md` indica que las tarjetas se crean con `pos: "bottom"` en orden de prioridad. Sin embargo, `create-cards` crea las tarjetas de forma secuencial, lo que significa que la ultima en crearse quedara al final. Si las historias se envian en orden Critica -> Alta -> Media -> Baja con `pos: "bottom"`, el orden resultante en Trello sera el correcto. Pero si el LLM invierte el orden por algun motivo, quedaran al reves. No es un bug confirmado, depende del comportamiento del LLM.

---

## Revision de coherencia general

### Nombres de herramientas MCP

| Herramienta en arquitectura | Herramienta en servidor MCP | Herramienta en agente publisher | Coherente |
|-----------------------------|-----------------------------|---------------------------------|-----------|
| `verify-credentials` | `verify-credentials` | `verify-credentials` | SI |
| `list-boards` | `list-boards` | `list-boards` | SI |
| `get-board` | `get-board` | `get-board` | SI |
| `create-board` | `create-board` | `create-board` | SI |
| `manage-lists` | `manage-lists` | `manage-lists` | SI |
| `manage-labels` | `manage-labels` | `manage-labels` | SI |
| `create-cards` | `create-cards` | `create-cards` | SI |
| `search-cards` | `search-cards` | `search-cards` | SI |

Los 8 nombres de herramientas son coherentes en todos los documentos y en el codigo.

### Comandos de skill

| Comando en arquitectura | Directorio en skills/ | SKILL.md presente | Coherente |
|-------------------------|-----------------------|-------------------|-----------|
| `/pspo-agent:start` | `skills/start/` | SI | SI |
| `/pspo-agent:onboarding` | `skills/onboarding/` | SI | SI |
| `/pspo-agent:discovery` | `skills/discovery/` | SI | SI |
| `/pspo-agent:generate-stories` | `skills/generate-stories/` | SI | SI |
| `/pspo-agent:validate` | `skills/validate/` | SI | SI |
| `/pspo-agent:publish` | `skills/publish/` | SI | SI |
| `/pspo-agent:save-docs` | `skills/save-docs/` | SI | SI |

Todos los comandos son coherentes entre arquitectura y directorio de skills.

### Configuracion MCP

El `.mcp.json` referencia `${CLAUDE_PLUGIN_ROOT}/servers/trello-mcp/dist/index.js`. El servidor MCP se compila desde `src/index.ts` con `npm run build`. La referencia es correcta. Las variables de entorno `TRELLO_API_KEY` y `TRELLO_TOKEN` se inyectan correctamente desde el entorno, en linea con lo que especifica la arquitectura.

### Separacion de responsabilidades en agentes

| Responsabilidad | Agente PO | Agente Publisher | Correcto |
|-----------------|-----------|------------------|----------|
| Herramientas MCP de Trello | NO (sin mcpServers) | SI (trello-client) | SI |
| Write/Edit en sistema de ficheros | SI | NO | SI |
| Descubrimiento y generacion de HU | SI | NO | SI |
| Publicacion en Trello | NO | SI | SI |

La separacion de responsabilidades entre agentes es correcta y coherente con la arquitectura.

---

## Cobertura de criterios de aceptacion del PRD

| HU | Criterio | Cubierto por tests | Cubierto por implementacion |
|----|----------|-------------------|----------------------------|
| HU-01 | Deteccion de primera ejecucion (credenciales ausentes) | Indirectamente (hook check-env.sh) | SI (skill start) |
| HU-01 | Validacion formato API Key (32 hex) | NO (comportamiento del LLM, no testeable en unitarios) | SI (skill onboarding) |
| HU-01 | Validacion formato Token (64 hex) | NO (comportamiento del LLM, no testeable en unitarios) | SI (skill onboarding) |
| HU-01 | Verificacion de credenciales via API | SI (verify-credentials.test.ts) | SI |
| HU-01 | Persistencia en .env con permisos 600 | NO (comportamiento del LLM, no testeable en unitarios) | SI (skill onboarding) |
| HU-01 | Verificacion de .gitignore | Parcialmente (check-gitignore.sh -- corregido) | SI |
| HU-01b | Listar tableros | SI (list-boards.test.ts) | SI |
| HU-01b | Crear tablero nuevo | SI (create-board.test.ts) | SI |
| HU-01b | Crear columnas por defecto | SI (manage-lists.test.ts) | SI |
| HU-01b | Crear etiquetas de prioridad | SI (manage-labels.test.ts) | SI |
| HU-05 | Publicar tarjetas en Backlog | SI (create-cards.test.ts) | SI |
| HU-05 | Detectar duplicados antes de publicar | SI (search-cards.test.ts) | SI |
| HU-05 | Operacion atomica (continuar si una falla) | SI (create-cards: partial failure) | SI |
| HU-05 | Error de conexion: no perder datos | NO test especifico | SI (arquitectura ADR-006) |

Los tests del servidor MCP cubren correctamente los escenarios criticos de la integracion con Trello. Los criterios no cubiertos por tests unitarios corresponden a comportamientos del LLM (validacion de formato en skills) que son propios de la capa de prompts y no de la capa TypeScript.

---

## Resumen de correcciones aplicadas

| ID | Severidad original | Fichero(s) modificado(s) | Descripcion |
|----|-------------------|--------------------------|-------------|
| QA-02 | BLOQUEANTE | `src/tools/manage-lists.ts` | Validacion de `pos` obligatorio en `handleReorder`. Simplificacion del body condicional. |
| QA-09 | MENOR | `tests/tools/manage-lists.test.ts` | 2 tests nuevos: `reorder` sin `pos` y `reorder` sin `listId`. |
| QA-11 | MENOR | `hooks/scripts/check-gitignore.sh` | Correccion del patron regex y ampliacion para detectar `/.env`. |

Estado de la suite tras correcciones: **60 tests, 9 ficheros, todos en verde.**

---

## VEREDICTO

---

**VEREDICTO: RECHAZADO**

**Resumen:** El servidor MCP pasa todos los tests (60/60 en verde tras correcciones) y la estructura general del plugin es coherente y bien construida. Se han corregido 3 bugs durante la revision (QA-02 bloqueante, QA-09 y QA-11 menores). Sin embargo, queda 1 hallazgo bloqueante sin resolver (QA-01): la dependencia implicita de `zod` en produccion sin declararse en `package.json`, con contradiccion directa respecto a la decision arquitectonica documentada. Esto no es negociable para un plugin que se va a distribuir.

**Hallazgos bloqueantes:**
- QA-01: `zod` usada en produccion sin declararse en `package.json` -- PENDIENTE (requiere decision del equipo: opcion A declarar dependencia, opcion B eliminar uso de zod)
- ~~QA-02: `handleReorder` sin validacion de `pos` -- CORREGIDO~~

**Condiciones pendientes (IMPORTANTES, no bloqueantes por si solas):**
- QA-03: `handleDelete` de etiquetas devuelve datos ficticios en el output
- QA-04/QA-11: Patrones del hook `check-gitignore.sh` -- CORREGIDOS
- QA-05: Sanitizacion de body de POST/PUT no implementada
- QA-06: `allowed-tools` en skills `publish` y `start` podria bloquear el flujo MCP
- QA-07: Fichero `.env.example` ausente del repositorio

**Proxima accion recomendada:** El senior-dev debe resolver QA-01 (elegir entre opcion A -- declarar `zod` en `package.json` y actualizar el ADR -- u opcion B -- eliminar el import de `zod` y usar JSON Schema nativo). Una vez resuelto QA-01, el veredicto puede cambiar a APROBADO CON CONDICIONES si se acepta postergar QA-03, QA-05 y QA-06 como deuda tecnica documentada.

---

*Informe generado por El Rompe-cosas (QA Engineer, equipo Alfred Dev). He roto tu codigo en varios sitios. Sorpresa: ninguna.*
