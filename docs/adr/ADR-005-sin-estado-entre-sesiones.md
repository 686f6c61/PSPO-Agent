# ADR-005: Sin estado propio entre sesiones

| Campo | Valor |
|-------|-------|
| **Estado** | Aceptado |
| **Fecha** | 2026-03-13 |
| **Autor** | El Dibujante de Cajas |

## Contexto

El plugin necesita recordar ciertas cosas entre sesiones: credenciales de Trello, ID del tablero, historias generadas. La pregunta es donde y como persistir esta informacion.

Las opciones van desde una base de datos local (SQLite, JSON) hasta simplemente usar ficheros planos que ya existen por otras razones (.env, docs/).

## Opciones consideradas

### Opcion A: Base de datos local (SQLite o JSON estructurado)

- **Pros:** Consultas estructuradas. Historial completo. Estado de sesion (que historias se publicaron, cuales estan pendientes).
- **Contras:** Dependencia adicional (SQLite) o fichero JSON que puede corromperse. Mas logica de sincronizacion. El usuario no puede leer/editar facilmente el estado. Oculta informacion que deberia ser transparente.

### Opcion B: Sin estado propio -- usar .env y docs/

- **Pros:** Cero dependencias. Transparencia total (el usuario puede leer y editar todo). Los artefactos de producto (docs/) ya son la "base de datos" de historias. Las credenciales ya estan en .env. No hay sincronizacion que romper.
- **Contras:** No se recuerda que historias ya se publicaron (se verifica contra Trello en tiempo real). No hay historial de sesiones. No se puede deshacer una publicacion sin ir a Trello.

### Opcion C: Estado en memoria persistente de subagente (`memory` en frontmatter)

- **Pros:** Los agentes recuerdan contexto entre sesiones. Aprendizaje progresivo.
- **Contras:** El estado no es legible por el usuario. Dependencia del mecanismo de memoria de Claude Code que puede cambiar. No es adecuado para datos estructurados (credenciales, IDs).

## Decision

**Opcion B: Sin estado propio.** La configuracion vive en `.env`. Los artefactos de producto viven en `docs/`. La verificacion de duplicados se hace en tiempo real contra Trello.

## Consecuencias

- **Ganancia:** Cero dependencias. Transparencia total. El usuario tiene control absoluto sobre todos los datos. Alineado con el principio de "si no esta en un fichero legible, no existe".
- **Coste:** No hay historial de sesiones. Cada nueva sesion parte de cero (lee .env y docs/).
- **Deuda tecnica:** Si en futuras versiones se necesita estado complejo (metricas de flujo HU-10, sincronizacion bidireccional HU-11), habra que introducir algun tipo de almacenamiento. Pero para el MVP, es un problema que no existe todavia.
