# Changelog

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
