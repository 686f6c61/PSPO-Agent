# Changelog

> Nota de estado (2026-03-16): este changelog se conserva como historial de releases y se mantiene en orden descendente por versión. Las entradas antiguas describen el comportamiento de cada versión en su momento y pueden mencionar términos ya sustituidos, como `Sprint actual` o `team.csv`. La fuente de verdad del estado actual es `README.md` y `Documents/`.

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
- **Documentos historicos marcados como tales:** `CHANGELOG`, `docs/arquitectura.md`, `docs/seguridad.md`, `docs/qa-report.md` y `docs/plans/*` avisan cuando son referencia historica y no especificacion viva.
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
