# Changelog

> Nota de estado (2026-03-16): este changelog se conserva como historial de releases y se mantiene en orden descendente por versión. Las entradas antiguas describen el comportamiento de cada versión en su momento y pueden mencionar términos ya sustituidos, como `Sprint actual` o `team.csv`. La fuente de verdad del estado actual es `README.md` y `Documents/`.

## v2.0.0 (22/07/2026)

### Nuevas funcionalidades

- **GitHub Projects como tercer proveedor remoto:** nuevo fallback oficial `servers/github-fallback.py` y su wrapper de runtime `.pspo-agent/runtime/github-fallback.sh`. Si el usuario tiene `gh` autenticado (con scope `project`) o un `GITHUB_TOKEN`/`GH_TOKEN`, el plugin crea un Project v2 **privado** del usuario y publica las historias como draft items con su estado.
- **Backend dual `gh` + urllib:** el cliente GraphQL usa `gh api graphql` como backend primario y cae a GraphQL directo con `urllib` usando `GITHUB_TOKEN` o `GH_TOKEN` cuando `gh` no está disponible.
- **Zero-template con esquema de campos completo:** `create-project` crea el Project v2 privado con título `PSPO · {nombre_proyecto}`, edita las opciones del campo Status nativo (`updateProjectV2Field`) con las 6 estándar y descripciones semánticas, y crea los campos Prioridad, Talla, Horas, Sprint (bajo demanda) y Responsable. Deja el proyecto autodocumentado con `shortDescription` y `readme` (tabla de estados, glosario de campos y vistas recomendadas).
- **Mapeo campo a campo:** cada metadato de la HU va a su propio campo (Status, Prioridad, Talla, Horas, Sprint, Responsable), igual que en Trello y Notion. El cuerpo del draft item lleva el markdown en bruto de la HU (GitHub renderiza Mermaid) con la DoD como task list `- [ ]`.
- **Publicación por lote en GitHub:** `sync-stories-from-folder` recorre `docs/historias/HU-*.md` + `docs/vision.md` en dos pasadas, crea o actualiza cada HU sin duplicar (dedupe por título `HU-XX`), mapea los campos, resuelve dependencias a item ids como trazabilidad y genera `docs/publish-report.md` con el mapeo campo a campo.
- **Asignación real cuando hay login:** el `Responsable` (texto) es siempre `Nombre (email)`; además, si el CSV de equipo trae una columna opcional `github` con el login, el item recibe el assignee real de GitHub. Sin login, la HU se reporta en `unresolvedAssignments`.
- **Onboarding, start, publish y ayuda hablan de tres proveedores:** nuevas rutas GitHub coherentes con las de Trello y Notion, con carril estricto que usa solo `.pspo-agent/runtime/github-fallback.sh`.
- **Guardrails al día para GitHub:** `block-trello-bash.sh`, `block-autopilot-drift.sh`, `block-autopilot-agent.sh`, `warn-sensitive-read.sh` y `persist-active-skill.py` reconocen el wrapper `github-fallback.sh`; `block-secret-prompt-leak.py` detecta y bloquea tokens de GitHub filtrados en prompts.
- **Selector de proveedor determinista:** `publish-provider.py` registra `github` y lo considera configurado por señales de proyecto (token en `.env` o targets persistidos), no por el estado global de `gh`, para no reconfigurar cada proyecto por la sesión global de la máquina.
- **Configuración y documentación de GitHub:** nueva sección `defaults.github` en `settings.json`, variables `GITHUB_*` en `.env.example`, nuevo `Documents/github-projects-integration.md` y README actualizado.

### Límites conocidos de GitHub Projects

- Los draft items de GitHub Projects no admiten adjuntos: el markdown en bruto de cada HU (incluida la DoD como task list) viaja en el cuerpo del item.
- La asignación real requiere el login de GitHub; el email no es resoluble por la API.
- Las dependencias se resuelven a item ids como trazabilidad; los draft items no admiten relaciones nativas de proyecto.
- La API pública no permite crear vistas de Project v2: el README del proyecto documenta el tablero por Status y la tabla por Sprint para crearlas a mano.

### Correccion de errores

- **Los hooks del MCP de Trello vuelven a ejecutarse:** el matcher `mcp__trello-client__.*` no coincidia con el nombre real que Claude Code asigna a las herramientas MCP de un plugin (`mcp__plugin_pspo-agent_trello-client__...`), asi que el gate de credenciales y el bloqueo de autopilot sobre Trello nunca se disparaban. El matcher acepta ahora ambos esquemas de nombre.
- **El matcher `Fetch` pasa a `WebFetch`:** la herramienta `Fetch` no existe en Claude Code; el bloqueo de accesos directos a Trello por fetch era codigo muerto.
- **El publisher puede usar de verdad el MCP:** su frontmatter restringia `tools` a Read/Grep/Bash y declaraba un campo `mcpServers` que los agentes no soportan, con lo que las 14 herramientas MCP de Trello quedaban fuera de su alcance. Se elimina la restriccion y el campo invalido (tambien en sprint-planner).
- **Las skills localizan la configuracion del plugin:** las referencias sueltas a `settings.json` en generate-stories, sprint-plan, team y sprint-planner apuntan ahora a `${CLAUDE_PLUGIN_ROOT}/settings.json`; antes buscaban el fichero en el proyecto del usuario, donde no existe.
- **`/pspo-agent:audit` aparece en la ayuda:** faltaba en la tabla de `help.md`.
- **`datetime.utcnow()` obsoleto eliminado** del launcher y del servidor MCP (aviso de deprecacion en Python 3.12+).
- **El hook de credenciales usa el esquema vigente de PreToolUse:** `block-onboarding-credential-reask.py` emitia `{"decision": "block"}`, la forma antigua que hoy solo funciona por retrocompatibilidad; ahora emite `hookSpecificOutput.permissionDecision: "deny"`.
- **El cargador de `.env` de Notion se comporta como el de Trello:** quita comillas de los valores (un `NOTION_TOKEN="ntn_..."` entre comillas rompia la autenticacion) y busca el `.env` en el directorio actual y sus padres.
- **Logs de diagnostico multiplataforma:** las rutas `/tmp/...` hardcodeadas del servidor y el launcher MCP usan ahora el directorio temporal del sistema (en Windows `/tmp` no existe y se perdia el diagnostico).

### Portabilidad y robustez de hooks

- **Los hooks funcionan en Windows nativo:** nuevo envoltorio poliglota `hooks/run-hook.cmd` (valido a la vez como batch de Windows y script sh de Unix) por el que pasan los 15 comandos de `hooks.json`. Ejecuta los `.sh` con bash (en Windows, el bash de Git) y los `.py` con `python3` o, si no existe, `python`. Antes, en Windows nativo toda la capa de guardarrailes quedaba inactiva.
- **Los guardarrailes ya no se desactivan en silencio si falta Python:** los scripts `.sh` resolvian toda la decision con `eval "$(python3 ...)"`; sin `python3` en el PATH las variables quedaban vacias y todo pasaba (fail-open silencioso). Ahora resuelven `python3` o `python`, avisan por stderr si no hay interprete y `check-env.sh` (el gate de credenciales del MCP) falla cerrado con exit 2.
- **Latencia de hooks reducida ~10x durante autopilot:** `block-autopilot-drift.sh`, `block-autopilot-agent.sh` y `block-trello-bash.sh` invocaban `autopilot-guard.py` entre 7 y 10 veces por evento (una por campo); el guard incorpora un modo `--dump-shell` que vuelca todos los campos en una sola llamada.

### Mejoras

- **Manifiesto minimo con autodescubrimiento:** `plugin.json` deja de listar comandos, skills y agentes a mano (el campo `skills` ni siquiera esta soportado); Claude Code los descubre de los directorios estandar, con lo que anadir un componente ya no exige tocar el manifiesto.
- **Divulgacion progresiva completa:** los ficheros auxiliares `templates.md`, `steps.md`, `card-format.md` y `file-templates.md` estaban huerfanos; ahora sus skills los referencian explicitamente.
- **Descripciones de skills con condicion de disparo:** las 18 skills siguen el patron "Usar cuando..." para mejorar la invocacion automatica.
- **Colores de agente dentro de la paleta soportada:** `magenta` pasa a `pink` y `amber` a `orange`.
- **Ayuda y README alineados con el multi-proveedor:** textos de Trello generalizados a proveedor remoto, tabla MCP completa con `get-card` y `update-card`, y tabla de hooks con los 14 scripts reales.

## v1.0.8 (16/03/2026)

### Nuevas funcionalidades

- **Capa de proveedores remotos:** el plugin deja de asumir Trello como unico destino y resuelve el proveedor activo (`trello`, `notion` o `local`) desde runtime con `publish-provider.py`.
- **Onboarding zero-template para Notion:** se incorpora `notion-fallback.py`, su wrapper de runtime y la ruta guiada para validar credenciales, leer la pagina padre y crear proyecto, HU-00 y backlog sin plantilla previa.
- **Seleccion de proveedor en tiempo de ejecucion:** si solo hay un proveedor listo se elige automaticamente; si hay varios, el flujo pregunta una sola vez antes de planificar o publicar.

### Mejoras

- **Start, onboarding y publish hablan ya de proveedor remoto activo:** comandos, skills y mensajes de estado dejan de estar acoplados a Trello y enrutan por el carril oficial correspondiente.
- **Guardrails mas finos para autopilot y onboarding:** los hooks aceptan `trello-fallback`, `notion-fallback` y `publish-provider`, bloquean Bash/Fetch genericos y evitan preguntas redundantes cuando Notion ya esta autenticado o configurado.
- **Documentacion viva alineada con Notion:** `Documents/`, `.env.example` y la configuracion del plugin documentan variables, arquitectura y flujo zero-template del nuevo proveedor.

### Correccion de errores

- **Publish deja de apoyarse en contexto lateral inseguro:** los hooks bloquean `.claude`, `*.local.md` y rutas ajenas a `docs/`, wrappers oficiales y runtime como fuente de verdad durante la publicacion.
- **La decision del siguiente paso tras auditoria ya no fuerza Trello:** el runtime comprueba el proveedor listo antes de mandar de vuelta a onboarding y puede continuar hacia `team` cuando la publicacion ya esta resuelta.

### Infraestructura

- **Cobertura ampliada para routing y runtime de proveedores:** se añaden tests para `publish-provider`, fallback de Notion, bootstrap de wrappers y nuevas reglas de hooks.

## v1.0.7 (15/03/2026)

### Mejoras

- **Autopilot todavia mas directo:** el comando y la skill ya dejan negro sobre blanco que, una vez existe el runtime, no se vuelve a leer `brief.md`, `vision.md`, `contexto.md`, `config*` ni el CSV desde `autopilot`.
- **Delegaciones de `product-phase` mas cerradas:** requirement-analyst, product-owner, culture-guardian y senior-auditor deben trabajar con prompts autosuficientes, sin explorar el workspace.
- **Documentacion tecnica consolidada:** la documentacion viva del plugin pasa a `Documents/`, y `docs/` queda reservado para artefactos generados por el flujo de producto.
- **Desinstalacion alineada con el runtime actual:** los desinstaladores limpian `docs/` completo como salida generada y conservan el codigo fuente y la configuracion del plugin.

### Correccion de errores

- **Recuperacion floja tras el bootstrap:** se refuerza la instruccion para que un bloqueo de lectura en inbox se interprete como señal de saltar inmediatamente a `Skill("pspo-agent:product-phase")`.
- **Subagentes con deriva lateral en product-phase:** se corrige la especificacion para prohibir `Read`, `Glob`, `Grep`, `ToolSearch`, `TodoWrite` y `Bash` cuando ya reciben el contexto completo en el prompt.

## v1.0.6 (15/03/2026)

### Mejoras

- **Autopilot mas fino y menos improvisable:** la skill `autopilot` reduce su presupuesto de herramientas a `Glob + Read + AskUserQuestion` y empuja el carril exacto `Glob(".pspo-agent/inbox/*") -> Skill("pspo-agent:product-phase")`.
- **Importacion automatica del CSV desde la inbox:** `autopilot-bootstrap.py` ya no solo detecta el CSV compatible; si hace falta lo importa a la raiz del proyecto para que las fases de asignacion, sprint y publicacion puedan continuar sin pasos manuales.
- **Mensajes de recuperacion mas accionables:** los hooks de drift y Bash ya indican la siguiente accion valida en vez de limitarse a bloquear.
- **Gate de Stop para autopilot:** nuevo hook `autopilot-stop.py` que impide cerrar el flujo antes de materializar el runtime o antes de persistir los artefactos de producto.

### Correccion de errores

- **Autopilot dejaba demasiado margen para “pensar por libre”:** el carril temprano ahora depende menos de instrucciones blandas y mas de reglas de negocio en codigo, siguiendo el patron que tan bien funciona en Alfred.
- **El contexto runtime quedaba util pero no suficiente para fases posteriores:** el bootstrap ya deja tambien el CSV del equipo disponible en la raiz cuando no existia uno compatible.

## v1.0.5 (15/03/2026)

### Mejoras

- **Bootstrap determinista de autopilot:** nuevo helper `autopilot-bootstrap.py` que materializa `.pspo-agent/runtime/autopilot-context.md` en cuanto detecta un brief valido en la inbox, sin depender de exploracion lateral ni de Bash.
- **Scaffold operativo automatico:** los hooks preparan `.pspo-agent/runtime`, `docs/` y `docs/historias/` para que el carril de producto no improvise `mkdir` ni bootstrap manual.
- **Bloqueo estricto de Bash/Fetch en autopilot:** durante `prepare-context`, `delegate-product-phase` y `product-phase-active`, cualquier Bash/Fetch queda bloqueado con recuperacion guiada hacia `Skill("pspo-agent:product-phase")`.
- **Carril mas parecido a Alfred:** el flujo de producto se apoya mas en reglas de negocio del sistema y menos en que el modelo “elija bien” el siguiente paso.

### Correccion de errores

- **La cache del plugin ya invalida correctamente el paquete de release:** la version interna sube a `1.0.5` para evitar pruebas mezcladas contra una cache parcial de `1.0.4`.
- **Autopilot deja de quedarse en bootstrap blando:** se reduce el espacio para derivas como `.pspo-agent/**/*`, `docs/**/*` o `CLAUDE.md` antes de delegar en `product-phase`.

## v1.0.4 (15/03/2026)

### Nuevas funcionalidades

- **Nuevo punto de entrada `/pspo-agent:start`:** detecta credenciales, tablero y estado del proyecto, y encadena automaticamente el siguiente artefacto que falta.
- **Modo carpeta-autopilot:** nuevo comando `/pspo-agent:autopilot` para leer una carpeta de entrada con instrucciones, vision opcional y cualquier CSV de equipo compatible, ejecutar el flujo de producto y detenerse solo en la gate final.
- **Asignacion operativa y dependencias como fases propias:** nuevos comandos `/pspo-agent:assign` y `/pspo-agent:dependencies` para generar ownership claro, carga por persona y mapa de bloqueos antes de planificar o publicar.
- **Sincronizacion incremental de tarjetas en Trello:** el MCP incorpora `get-card` y `update-card`, y `publish` ya no solo crea tarjetas; tambien sincroniza descripcion, lista, miembros, etiquetas y checklists sin duplicar.
- **Mermaid operativo en la vision del proyecto:** la vision/HU-0 puede incluir mapa de dependencias y ownership para anticipar bloqueos desde el inicio.
- **Launcher MCP dedicado:** nuevo `trello-mcp-launcher.py` para cargar credenciales desde `.env` antes de arrancar el servidor MCP y evitar configuraciones frágiles del entorno.

### Mejoras

- **Flujo autonomo completo y coherente:** onboarding -> vision -> analyze/discovery -> generate-stories -> save-docs -> audit -> validate -> team -> assign -> dependencies -> sprint-plan -> publish.
- **Sprint con agentes redefinido:** un solo sprint activo, maximo 5 dias laborables, backlog futuro en documentacion local y no en columnas separadas.
- **Estimacion realista para equipos con agentes:** `sprint-plan` propone horas efectivas autonomamente, evita inflar historias sencillas y usa recorte por prioridad cuando el sprint no cabe.
- **Tablero Trello normalizado:** columnas estables en castellano (`Backlog`, `Sprint activo`, `Bloqueada`, `En progreso`, `En revision`, `Hecho`) y etiquetas operativas `Asignada`, `Bloqueada`, `Bloqueante`.
- **Publicacion completa de historias:** cada tarjeta se crea o sincroniza con resumen corto, adjunto `.md`, checklist DoD, checklist `Dependencias` cuando aplica y miembros reales en `idMembers`.
- **CSV de equipo flexible:** el plugin ya no depende rigidamente de `team.csv`; acepta cualquier CSV compatible con cabecera `nombre,email,rol,categoria,dedicacion,usa_agente_ia`.
- **Voz comun del plugin:** skills y agentes comparten una personalidad base consistente, sin cambiar de tono entre fases.
- **Autopilot mas util:** acepta una carpeta de trabajo, detecta el documento principal automaticamente y sigue sin menus intermedios hasta la decision final de revisar o planificar/publicar.

### Correccion de errores

- **API keys ya no se exponen en onboarding:** se deja de mostrar la URL resuelta con la API Key real y se usan plantillas seguras con placeholders.
- **Bloqueo reforzado de accesos directos a Trello:** los hooks ahora cubren Bash y Fetch, y ademas avisan en lecturas sensibles para evitar fugas accidentales de secretos.
- **El publisher deja de depender de alias legacy:** `Sprint actual` ya no se usa como columna valida; si aparece en un tablero viejo, se renombra a `Sprint activo`.
- **El onboarding y el MCP arrancan en orden correcto:** primero se materializan credenciales utilizables y despues se valida Trello, evitando fallos por entorno no inicializado.
- **La publicacion ya no arranca sin HUs individuales:** `publish` valida `docs/historias/HU-*.md` y fuerza `save-docs` si solo existe un backlog monolitico.
- **Las tarjetas asignadas ya no se dan por buenas sin miembro real:** si una HU tiene responsable pero no se obtiene `memberId`, la tarjeta queda reportada como incompleta y requiere revision manual.
- **La desinstalacion ya no borra solo `team.csv`:** `uninstall.sh` y `uninstall.ps1` detectan y limpian cualquier CSV de equipo compatible en la raiz del proyecto.
- **Compatibilidad macOS en desinstalacion:** el script bash evita `mapfile` para seguir funcionando en el bash antiguo de macOS.

### Documentacion

- **README actualizado:** refleja que PSPO Agent es un plugin no oficial, expone el flujo actual, los comandos nuevos y las 14 herramientas MCP.
- **PRD alineado con la implementacion real:** equipo flexible, flujo autonomo, sprint con agentes, columnas actuales de Trello y sincronizacion incremental.
- **Documentos historicos marcados como tales:** el `CHANGELOG` avisa cuando es referencia historica y no especificacion viva; la documentacion viva del plugin vive en `README.md` y `Documents/`.
- **Ayuda y comandos revisados:** `help`, `autopilot` y el resto de descripciones ya usan el lenguaje actual del producto.

### Infraestructura

- **17 skills y 14 herramientas MCP registradas y cubiertas por tests.**
- **Suite ampliada a 278 tests** entre contenido, configuracion, skills, MCP unitario y end-to-end.
- **Tests nuevos para regresiones clave:** voz comun, CSV de equipo flexible, renombrado de `Sprint actual`, hooks de seguridad y desinstalacion de CSVs compatibles.

## v1.0.3 (15/03/2026)

### Nuevas funcionalidades

- **MCP get-board-members:** obtiene miembros del tablero con sus IDs para mapear email a memberId.
- **invite-member devuelve memberId:** despues de invitar, busca el ID del miembro en el tablero y lo devuelve. El publisher construye el mapeo email->memberId directamente desde las invitaciones sin necesidad de fuzzy matching de nombres.
- **Asignacion real de miembros a tarjetas:** create-cards soporta idMembers. Las tarjetas se crean con miembros asignados en Trello (columna Miembros visible). Los miembros ghost (invitados pendientes de aceptar) tambien se pueden asignar.
- **Hook anti-curl:** bloquea automaticamente cualquier comando bash que intente acceder a la API de Trello directamente. Obliga a usar MCP tools.
- **Verificacion post-publicacion:** despues de crear tarjetas, verifica que cada una existe y tiene adjuntos.
- **Enrutamiento por sprint:** las HUs del sprint se publican en "Sprint actual", las demas en "Backlog".

### Mejoras

- **Procesamiento en lotes de 5:** evita perdida de contexto con muchas HUs. Cada lote ejecuta las 3 operaciones (card + MD + DoD) para cada tarjeta.
- **AskUserQuestion en TODOS los puntos de decision:** eliminados todos los (s/n) residuales en onboarding, team, validate, sprint-plan, sprint-review y publish.
- **Seleccion de tablero interactiva:** onboarding usa AskUserQuestion con los tableros como opciones seleccionables.
- **Verificacion de listas antes de crear:** el publisher comprueba que la lista no existe antes de crearla. Evita columnas duplicadas.
- **Orden de pasos clarificado en generate-stories:** secuencia 6a-6e sin ambiguedad (save-docs, culture-guardian, audit, presentar, validate).
- **12 herramientas MCP listadas en publisher:** tabla completa con todas las herramientas incluidas attach-file, add-checklist, get-board-members e invite-member.

### Correccion de errores

- Columnas duplicadas al ejecutar onboarding mas de una vez.
- Miembros no asignados a tarjetas (solo texto en descripcion).
- Agente usando bash/curl con API keys visibles en terminal.
- Checklists de DoD no anadidos a tarjetas del Backlog (solo Sprint Backlog).
- Ficheros MD no adjuntados en tarjetas finales con muchas HUs (>10).
- Opciones de onboarding (seleccion de tablero, columnas, etiquetas) no seleccionables con flechas.
- Servidor MCP muere con JSON malformado (ahora descarta y continua).
- Servidor MCP muere con timeout de red/DNS (ahora reintenta con backoff).
- attach-file e invite-member sin rate limiter ni reintentos (ahora pasan por el rate limiter).
- fileName sin sanitizar en attach-file (inyeccion de cabeceras multipart).
- Validacion de email laxa en invite-member ("@@" pasaba como valido).
- member_type invalido silenciado a "normal" sin avisar (ahora lanza error).
- Body de errores de Trello reenviado sin truncar al usuario.

### Infraestructura

- 239 tests (89 MCP unitarios, 23 config, 14 skills, 69 contenido, 44 e2e).
- Tests e2e reales: arrancan servidor MCP como subproceso, validan protocolo completo, resiliencia a JSON malformado, integridad del plugin.
- Hook PreToolUse para Bash con script block-trello-bash.sh.
- .env.example con variable TRELLO_TOKEN_CREATED documentada.

## v1.0.2 (14/03/2026)

### Nuevas funcionalidades

- **Agente senior-auditor:** auditoria de fondo de las HU (completitud, coherencia, huecos, HU que faltan/sobran). Cruza contra documento original. Automatico en primera generacion, bajo demanda despues.
- **Skill audit:** `/pspo-agent:audit` para auditorias bajo demanda.
- **MCP invite-member:** invita miembros al tablero de Trello por email. Trello envia la invitacion automaticamente.
- **Invitacion automatica al board:** antes de publicar tarjetas, invita a los miembros del equipo (team.csv) al tablero.
- **Sprint y asignacion en cada HU:** campos Sprint y Asignado a (nombre + email) en la tabla de metadatos de cada fichero MD.

### Mejoras

- **Flujo autonomo entre fases:** el plugin avanza automaticamente sin preguntar "quieres pasar a la siguiente fase". Solo se detiene para preguntas de contenido.
- **Equipo conversacional:** explica campos necesarios, ofrece descargar plantilla CSV, pregunta cuantos miembros o carga CSV existente.
- **Equipo obligatorio en sprint-plan:** redirige a /pspo-agent:team si falta team.csv.
- **AskUserQuestion en todas las skills:** selectores interactivos en vez de texto plano con letras.
- **3 reglas inquebrantables del publisher:** create-card + attach-file + add-checklist siempre.
- **Listas en castellano obligatorio:** el publisher renombra listas si estan en ingles.
- **Estimacion en descripcion de tarjeta:** prioridad, talla, sprint y asignado visibles.

### Correccion de errores

- Publisher usaba curl/bash en vez de MCP tools.
- No generaba ficheros MD individuales por HU.
- No adjuntaba MD a tarjetas de Trello.
- No pedia equipo antes de planificar.
- Pedia permiso tarjeta por tarjeta en vez de una sola vez.
- Update mostraba codigo Python al usuario.
- API keys se guardaban en local.md en vez de .env.
- Proximos pasos como tabla de texto en vez de selectores.

## v1.0.1 (14/03/2026)

### Nuevas funcionalidades

- **Agente requirement-analyst:** analiza documentos crudos (briefs, emails, PRDs) con indicador de claridad progresiva (0-100%) en 8 categorias. Sustituye al discovery cuando hay documento de partida.
- **Agente culture-guardian:** revisor de estilo automatico. Aplica normas RAE, castellano neutro, tono profesional (CTO). Aprende de las correcciones del usuario via memoria de Claude Code.
- **Agente sprint-planner:** planificacion de sprint con DoD, equipo y capacidad. Factor de productividad por agentes IA (65% por defecto, 70% recomendado).
- **Skill analyze:** punto de entrada para analisis de documentos. Activa el requirement-analyst.
- **Skill team:** gestion de equipo desde CSV con dedicacion y uso de agentes IA.
- **Skill sprint-plan:** estimacion por tallas (S/M/L/XL), calculo de capacidad, priorizacion asistida (valor/riesgo/dependencias).
- **Skill sprint-review:** revision de sprint con estado de tarjetas y cumplimiento de DoD.
- **Skill export:** exportacion a CSV, JSON y Jira CSV.
- **MCP add-checklist:** anade checklists de DoD a las tarjetas de Trello.
- **MCP attach-file:** adjunta ficheros .md completos a las tarjetas de Trello.
- **Vision de producto:** se pide antes del primer descubrimiento/analisis. Se guarda en docs/vision.md.
- **Edge cases:** deteccion automatica de 5 categorias con tabla de impacto.
- **Estimacion t-shirt:** S=1, M=2, L=3, XL=5 dias (configurable en settings.json).
- **Fechas en formato espanol:** DD/MM/AAAA en toda la documentacion generada.

### Mejoras

- **Personalidad JARVIS** en product-owner y requirement-analyst: tecnico, ironico, exigente.
- **HU enriquecidas:** contexto narrativo, diagramas Mermaid, tablas de datos, referencias externas, notas de implementacion.
- **Criterios de aceptacion detallados:** parrafos explicativos en vez de bullets de una frase.
- **Tarjetas de Trello resumidas:** descripcion escaneable + fichero .md adjunto con detalle completo + checklist DoD.
- **Confirmacion unica en publish:** se pide una sola vez en la vista previa, no por cada tarjeta.
- **Onboarding visual:** barras de progreso ASCII, mensajes cortos.
- **Colores por agente:** blue (PO), cyan (analyst), green (publisher), amber (planner), magenta (guardian).
- **Plantilla CSV de equipo** descargable desde la web.
- **Priorizacion asistida** con matriz valor/riesgo/dependencias.

### Correccion de errores

- El culture-guardian no se invocaba en generate, validate ni publish.
- Los ficheros .md no se adjuntaban a las tarjetas de Trello.
- Se pedia confirmacion individual por cada tarjeta en vez de una sola vez.
- Validacion de token en onboarding incompatible con formato real de Trello (ATTA*).
- stdin/stdout del servidor MCP en modo texto en vez de binario (corrupcion con UTF-8).
- IDs de Trello sin validar (riesgo de path traversal).

### Infraestructura

- Servidor MCP migrado de TypeScript a Python puro (stdlib, 0 dependencias).
- 152 tests (unitarios, configuracion, estructura, contenido, end-to-end).
- Directorio TypeScript legacy eliminado (79 MB).
- ADR-007: documentada la migracion a Python.

## v1.0.0 (14/03/2026)

- Release inicial del plugin.
- 8 skills, 2 agentes, 8 herramientas MCP.
- Servidor MCP en Python puro.
- Instalador pipeable para Linux/macOS/Windows.
