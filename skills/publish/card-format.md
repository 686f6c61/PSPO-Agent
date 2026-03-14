# Formato de tarjetas de Trello

Define como se estructuran las tarjetas creadas por PSPO Agent en Trello.

## Estructura del titulo

```
HU-{XX}: {Titulo descriptivo breve}
```

Ejemplos:
- `HU-01: Registro de usuario con email`
- `HU-02: Busqueda de productos por categoria`
- `HU-03: Notificacion de bajada de precio`

## Estructura de la descripcion

La descripcion de cada tarjeta contiene un **resumen** de la historia, no el detalle completo. El detalle completo se adjunta como fichero.

```markdown
## Historia de usuario

Como {rol}, quiero {accion}, para {beneficio}.

## Criterios de aceptacion (resumen)

- Escenario 1: {nombre} (positivo)
- Escenario 2: {nombre} (negativo)

Prioridad: {prioridad} | Estimacion: {talla} ({dias} dias)

---
*Historia completa en el fichero adjunto.*
*Generado por PSPO Agent | {fecha}*
```

## Fichero adjunto

Cada tarjeta lleva como adjunto el fichero Markdown completo de la historia:

- **Nombre del fichero:** `HU-{XX}-{titulo-en-kebab-case}.md`
- **Contenido:** el fichero completo de `docs/historias/HU-XX-titulo.md`, con todos los escenarios Given/When/Then, notas, prioridad, estimacion y metadatos.
- **Herramienta MCP:** se usa `attach-file` para subir el contenido como adjunto a la tarjeta.

Esto permite que la tarjeta en Trello sea ligera (solo el resumen) mientras que el detalle completo esta siempre accesible en el adjunto.

## Checklist: Definition of Done

Cada tarjeta incluye un checklist llamado "Definition of Done" con los items estandar del equipo. Se crea con la herramienta `add-checklist` despues de crear la tarjeta.

## Mapeo de prioridad a etiquetas

| Prioridad | Etiqueta de Trello | Color |
|-----------|-------------------|-------|
| Critica | Critica | red |
| Alta | Alta | orange |
| Media | Media | yellow |
| Baja | Baja | blue |

Si la etiqueta no existe en el tablero (por ejemplo, si el usuario no las creo durante el onboarding), la tarjeta se crea sin etiqueta y se informa al usuario.

## Posicion en la lista

Las tarjetas se crean al final de la lista destino (`pos: "bottom"`), en el orden de prioridad definido por las historias:

1. Primero las historias de prioridad Critica.
2. Luego Alta.
3. Luego Media.
4. Por ultimo Baja.

Dentro de la misma prioridad, se respeta el orden de numeracion (HU-01 antes que HU-02).

## Longitud maxima

La API de Trello tiene limites:
- Titulo: maximo 16384 caracteres (no deberia ser un problema).
- Descripcion: maximo 16384 caracteres. Como la descripcion ahora es un resumen, no deberia alcanzar este limite. Si aun asi lo supera, truncar y anadir: "*Descripcion truncada. Ver el fichero adjunto para la historia completa.*".
