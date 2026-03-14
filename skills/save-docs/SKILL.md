---
name: save-docs
description: >
  Guarda los artefactos de producto (vision, historias de usuario, backlog) en
  el sistema de ficheros local en formato Markdown. Garantiza la persistencia
  de todo el trabajo del plugin independientemente de Trello.
disable-model-invocation: false
allowed-tools: Read, Grep, Glob, Write, Edit
---

# /pspo-agent:save-docs -- Persistencia local de artefactos

## Tu rol

Guardas todos los artefactos de producto generados por el plugin en el sistema de ficheros local. Eres la red de seguridad: aunque Trello no este disponible, el trabajo del usuario siempre esta persistido en ficheros Markdown legibles dentro del repositorio.

## Estructura de ficheros

Todos los artefactos se guardan en la carpeta `docs/` del proyecto:

```
docs/
  vision.md                    # Vision de producto
  backlog.md                   # Lista priorizada de todas las historias
  historias/                   # Directorio con una historia por fichero
    HU-01-titulo-corto.md
    HU-02-titulo-corto.md
    HU-03-titulo-corto.md
```

## Proceso de guardado

### Paso 1: Crear estructura de directorios

Si no existe `docs/` o `docs/historias/`, crealos.

### Paso 2: Guardar vision de producto (si aplica)

Si el descubrimiento ha generado una vision de producto, guardala en `docs/vision.md`:

```markdown
# Vision de producto

> {Resumen de la vision en una frase}

## Usuario principal

{Descripcion del usuario principal y su contexto}

## Problema

{Descripcion del problema que se resuelve}

## Solucion propuesta

{Resumen de la solucion}

## Resultado esperado

{Que pasara cuando esto funcione}

## Restricciones

{Limitaciones identificadas}

## Fuera de alcance

{Que NO se incluye}

---
*Generado por PSPO Agent | Ultima actualizacion: {fecha}*
```

### Paso 3: Guardar cada historia como fichero individual

Para cada historia aprobada, crea (o actualiza) un fichero en `docs/historias/`.

**Nombre del fichero:** `HU-{XX}-{titulo-en-kebab-case}.md`

Reglas para el nombre:
- El numero tiene dos digitos con cero a la izquierda: `HU-01`, `HU-02`, ..., `HU-10`.
- El titulo se convierte a kebab-case: minusculas, guiones en vez de espacios, sin caracteres especiales.
- Maximo 50 caracteres en el titulo del fichero.
- Ejemplos: `HU-01-registro-con-email.md`, `HU-02-busqueda-por-categoria.md`.

**Contenido del fichero:**

```markdown
# HU-{XX}: {Titulo descriptivo}

| Campo | Valor |
|-------|-------|
| **Prioridad** | {Critica / Alta / Media / Baja} |
| **Estado** | {Aprobada / Publicada en Trello / Borrador} |
| **Creada** | {fecha de creacion} |
| **Ultima modificacion** | {fecha de ultima modificacion} |

## Historia de usuario

Como {rol especifico},
quiero {accion concreta},
para {beneficio medible}.

## Criterios de aceptacion

### Escenario 1: {nombre del escenario}

Given {contexto}
  And {condicion adicional}
When {accion}
Then {resultado}
  And {resultado adicional}

### Escenario 2: {nombre del escenario}

Given {contexto}
When {accion}
Then {resultado}

## Notas

{Contexto adicional, dependencias, restricciones}

---
*Generado por PSPO Agent*
```

### Paso 4: Actualizar el backlog

Crea o actualiza `docs/backlog.md` con la lista priorizada de todas las historias:

```markdown
# Product backlog

Ultima actualizacion: {fecha}

## Historias priorizadas

| # | Historia | Prioridad | Estado | Fichero |
|---|----------|-----------|--------|---------|
| HU-01 | {titulo} | Alta | Aprobada | [HU-01](historias/HU-01-titulo.md) |
| HU-02 | {titulo} | Alta | Publicada | [HU-02](historias/HU-02-titulo.md) |
| HU-03 | {titulo} | Media | Aprobada | [HU-03](historias/HU-03-titulo.md) |

## Resumen

- **Total:** {N} historias
- **Aprobadas:** {X}
- **Publicadas en Trello:** {Y}
- **Pendientes de revision:** {Z}

---
*Generado por PSPO Agent*
```

## Reglas de actualizacion

### No sobreescribir sin cambios

Antes de escribir un fichero de historia, lee el fichero existente (si existe) y compara:
- Si el contenido es identico, no escribas. Evita cambiar la fecha de modificacion del fichero sin razon.
- Si hay cambios, actualiza el campo "Ultima modificacion" con la fecha actual.

### Preservar historias existentes

Si existen historias previas en `docs/historias/` que no forman parte del lote actual:
- NO las elimines.
- NO las modifiques.
- Incluye sus referencias en `docs/backlog.md` para mantener la lista completa.

### Numeracion coherente

- Lee las historias existentes para determinar el proximo numero disponible.
- Si existen HU-01 a HU-05, las nuevas empiezan en HU-06.
- Nunca reutilices un numero, aunque la historia haya sido rechazada.

### Estado de las historias

Los estados posibles son:

| Estado | Significado |
|--------|-------------|
| Borrador | Generada pero no revisada |
| Aprobada | Revisada y aprobada por el usuario |
| Publicada en Trello | Aprobada y publicada como tarjeta en Trello |
| Rechazada | Descartada por el usuario durante la revision |

### Fechas

Las fechas se muestran en formato espanol: DD/MM/AAAA (ejemplo: 14/03/2026). Usa este formato en todos los artefactos generados: historias, backlog, vision y cualquier otro documento.

## Confirmacion al usuario

Despues de guardar, muestra un resumen:

```
Artefactos guardados en docs/:

  [OK] docs/vision.md (actualizado)
  [OK] docs/historias/HU-01-registro-con-email.md (nuevo)
  [OK] docs/historias/HU-02-busqueda-por-categoria.md (nuevo)
  [OK] docs/historias/HU-03-notificacion-precio.md (nuevo)
  [OK] docs/backlog.md (actualizado)

Total: {N} ficheros creados/actualizados.
```
