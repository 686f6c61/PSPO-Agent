# ADR-003: TypeScript como lenguaje del servidor MCP

| Campo | Valor |
|-------|-------|
| **Estado** | Sustituido por ADR-007 |
| **Fecha** | 2026-03-13 |
| **Autor** | El Dibujante de Cajas |

## Contexto

El servidor MCP necesita un lenguaje de implementacion. El SDK oficial de MCP (`@modelcontextprotocol/sdk`) esta disponible para TypeScript y Python. La eleccion del lenguaje afecta a las dependencias, la experiencia de desarrollo y la compatibilidad con el ecosistema.

## Opciones consideradas

### Opcion A: TypeScript (Node.js)

| Criterio | Puntuacion (1-10) |
|----------|-------------------|
| SDK MCP maduro | 9 -- SDK de referencia, desarrollado por Anthropic |
| Ecosistema Claude Code | 9 -- Claude Code esta escrito en TypeScript. La mayoria de plugins usan Node.js |
| Fetch nativo | 9 -- Node.js 18+ incluye fetch global. Sin dependencias HTTP |
| Tipado | 9 -- Tipos de la API de Trello bien definidos |
| Disponibilidad runtime | 7 -- La mayoria de desarrolladores tienen Node.js instalado |
| Peso de dependencias | 8 -- Solo `@modelcontextprotocol/sdk` como dep de produccion |

### Opcion B: Python

| Criterio | Puntuacion (1-10) |
|----------|-------------------|
| SDK MCP maduro | 8 -- SDK oficial disponible, algo menos documentado |
| Ecosistema Claude Code | 5 -- No es el lenguaje del ecosistema Claude Code |
| Fetch nativo | 6 -- Requiere `httpx` o `aiohttp` (no incluido en stdlib) |
| Tipado | 7 -- Tipado con type hints, menos estricto que TS |
| Disponibilidad runtime | 8 -- Python suele estar preinstalado |
| Peso de dependencias | 5 -- Mas dependencias transitivas para HTTP + MCP |

### Opcion C: Go (binario compilado)

| Criterio | Puntuacion (1-10) |
|----------|-------------------|
| SDK MCP maduro | 4 -- No hay SDK oficial de MCP para Go |
| Ecosistema Claude Code | 3 -- Fuera del ecosistema |
| Fetch nativo | 9 -- net/http incluido en stdlib |
| Tipado | 9 -- Tipado estatico fuerte |
| Disponibilidad runtime | 10 -- Binario compilado, sin runtime |
| Peso de dependencias | 10 -- Sin dependencias externas |

## Matriz de decision

| Criterio | Peso | TypeScript | Python | Go |
|----------|------|-----------|--------|-----|
| SDK MCP maduro | 0.30 | 9 | 8 | 4 |
| Ecosistema Claude Code | 0.25 | 9 | 5 | 3 |
| Fetch nativo / HTTP | 0.15 | 9 | 6 | 9 |
| Tipado | 0.10 | 9 | 7 | 9 |
| Disponibilidad runtime | 0.10 | 7 | 8 | 10 |
| Peso de dependencias | 0.10 | 8 | 5 | 10 |
| **TOTAL PONDERADO** | | **8.65** | **6.45** | **5.65** |

## Decision

**TypeScript (Node.js).**

Gana por la madurez del SDK MCP oficial y la alineacion con el ecosistema de Claude Code. El uso de `fetch` nativo (Node.js 18+) elimina la necesidad de librerias HTTP externas, manteniendo el plugin ligero.

## Consecuencias

- **Ganancia:** SDK MCP de referencia. Ecosistema alineado. Fetch nativo. Tipado fuerte.
- **Coste:** Requiere Node.js 18+ en la maquina del usuario.
- **Deuda tecnica:** Si Node.js deja de ser el runtime estandar del ecosistema Claude Code, habria que migrar. Riesgo bajo a medio plazo.

---

> **Nota:** Esta decision fue sustituida el 2026-03-14 por ADR-007 (Python puro para el servidor MCP). El servidor TypeScript fue eliminado del repositorio.
