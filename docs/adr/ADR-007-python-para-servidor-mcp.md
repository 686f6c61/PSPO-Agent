# ADR-007: Python puro para el servidor MCP

| Campo | Valor |
|-------|-------|
| **Estado** | Aceptado (sustituye a ADR-003) |
| **Fecha** | 2026-03-14 |
| **Autor** | El Dibujante de Cajas |

## Contexto

El servidor MCP se implemento inicialmente en TypeScript con el SDK oficial `@modelcontextprotocol/sdk` (ADR-003). Esto requeria Node.js >= 18, npm, compilacion con `tsc`, y generaba 78 MB de `node_modules` con 311 dependencias transitivas.

## Decision

Reescribir el servidor MCP en Python puro usando solo la biblioteca estandar (stdlib). Implementar el protocolo JSON-RPC 2.0 directamente sobre stdio, sin frameworks ni dependencias externas.

## Justificacion

- **Cero dependencias:** solo Python 3.8+ (stdlib). Elimina npm, `node_modules`, compilacion.
- **Python esta preinstalado** en macOS y Linux. Node.js no.
- **Superficie de protocolo minima:** el plugin solo usa `tools/list` y `tools/call` del protocolo MCP. No necesita resources, prompts ni subscriptions.
- **Fichero unico de ~700 lineas** frente a 11 ficheros + 78 MB de dependencias.
- **Consistente con el patron del plugin alfred-dev** (mismo autor), que usa Python puro para su servidor MCP.

## Riesgos aceptados

- Si la spec MCP evoluciona, hay que actualizar manualmente. Mitigado porque solo se usan 4 metodos del protocolo.
- Sin SDK oficial, la responsabilidad del protocolo es nuestra. Mitigado con tests.

## Consecuencias

- **Ganancia:** instalacion trivial (sin `npm install`), arranque mas rapido, cero superficie de ataque por dependencias transitivas.
- **Coste:** mantenimiento manual del subconjunto JSON-RPC 2.0 implementado.
- **Deuda tecnica:** si en el futuro se necesitan resources o subscriptions, habra que ampliar la implementacion del protocolo o volver a un SDK.

## ADR sustituida

ADR-003 queda con estado "Sustituido por ADR-007".
