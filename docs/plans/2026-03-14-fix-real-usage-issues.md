# Plan: corregir problemas detectados en uso real

> Nota de estado (2026-03-15): este documento es un plan historico de correccion. Mantiene valor para trazabilidad, pero no describe necesariamente el comportamiento actual del plugin ni debe usarse como fuente de verdad operativa.

## Problemas detectados

### P1: El agente usa curl/bash en vez de MCP tools
El publisher ejecuta comandos curl directamente para crear etiquetas y listas en vez de usar
las herramientas MCP (manage-labels, manage-lists). Esto causa que Claude Code pida permiso
para cada comando bash con $() y ademas expone las credenciales en los comandos.

**Causa raiz:** El agente publisher no tiene instrucciones suficientemente explicitas de que
SOLO debe usar las herramientas MCP, NUNCA comandos bash con curl.

**Fix:** Reforzar en publisher.md que NUNCA ejecute bash/curl. Solo MCP tools.

### P2: No genera ficheros MD individuales por HU
El product-owner genera un backlog monolitico en vez de ficheros individuales en docs/historias/.

**Causa raiz:** El agente product-owner no invoca save-docs automaticamente. El save-docs
tiene las instrucciones correctas pero no se ejecuta.

**Fix:** Hacer que generate-stories invoque save-docs OBLIGATORIAMENTE antes de terminar.

### P3: No adjunta MD a las tarjetas de Trello
El publish tiene las instrucciones de attach-file pero no las ejecuta.

**Causa raiz:** Las instrucciones estan pero el agente publisher no las sigue porque son
parte de la skill publish, no del agente. Hay que reforzar en el agente.

**Fix:** Anadir al publisher.md instrucciones explicitas de los 3 pasos por tarjeta.

### P4: No pide el equipo
El plugin no pide configurar el equipo antes de planificar. Lo da por hecho.

**Causa raiz:** El flujo de start no ofrece team como opcion prominente y sprint-plan
no verifica si team.csv existe antes de empezar.

**Fix:** sprint-plan ya lo tiene pero reforzar. En start, despues de publish ofrecer team.

### P5: Boards mal configurados
Las listas y etiquetas no se crean correctamente.

**Causa raiz:** P1 -- usa curl en vez de MCP tools.

**Fix:** Mismo fix que P1.

### P6: Proximos pasos como tabla de texto
Despues de ciertas operaciones, muestra una tabla de texto con opciones.

**Causa raiz:** No hay instrucciones de usar AskUserQuestion para proximos pasos.

**Fix:** Anadir instruccion generica en TODOS los skills de usar AskUserQuestion para
proximos pasos.

### P7: Estimacion no incluida en cada HU individual
El fichero MD de cada HU no tiene campo de estimacion.

**Causa raiz:** El template de save-docs ya lo tiene pero el product-owner no lo rellena.

**Fix:** Reforzar en product-owner que incluya estimacion en cada HU.
