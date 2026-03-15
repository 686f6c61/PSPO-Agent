# Changelog

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
