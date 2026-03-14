# ADR-002: Servidor MCP propio para la API de Trello

| Campo | Valor |
|-------|-------|
| **Estado** | Aceptado |
| **Fecha** | 2026-03-13 |
| **Autor** | El Dibujante de Cajas |

## Contexto

El plugin necesita comunicarse con la API REST de Trello para: verificar credenciales, listar tableros, crear tableros, gestionar listas y etiquetas, crear tarjetas y buscar tarjetas existentes.

Claude Code puede ejecutar comandos bash (y por tanto `curl`), usar herramientas MCP de servidores externos, o usar un servidor MCP bundled en el plugin. Necesitamos decidir como se estructura esta comunicacion.

## Opciones consideradas

### Opcion A: Llamadas directas con curl/fetch via Bash

- **Pros:** Sin dependencias adicionales. Implementacion trivial.
- **Contras:** Las credenciales se pasan como argumentos de comando (visibles en logs y historial de bash). Sin tipado. Sin reintentos automaticos. Sin abstraccion: cada skill tiene que construir URLs. Acoplamiento temporal entre skills y la API de Trello.
- **Riesgo de seguridad:** Las credenciales aparecen en el historial de herramientas de Claude Code.

### Opcion B: Servidor MCP existente de la comunidad para Trello

- **Pros:** Sin desarrollo propio. Ya probado.
- **Contras:** No hay un servidor MCP de Trello maduro y verificado en el ecosistema. Los que existen tienen APIs genericas (demasiado abiertas) o estan abandonados. Dependencia de mantenimiento externo. No se ajusta a las operaciones especificas del plugin (crear tarjetas con formato especifico, verificar duplicados por titulo).

### Opcion C: Servidor MCP propio empaquetado en el plugin

- **Pros:** Credenciales inyectadas via variables de entorno (nunca en argumentos). Herramientas especificas para las operaciones del plugin (no genericas). Reintentos con backoff integrados. Tipado completo. Control total sobre el formato de respuestas. Se distribuye con el plugin.
- **Contras:** Codigo que hay que desarrollar y mantener (~500-800 lineas). Requiere Node.js en la maquina del usuario.

## Decision

**Opcion C: Servidor MCP propio.**

La seguridad de las credenciales es la razon principal. Un servidor MCP recibe las variables de entorno a traves de la configuracion de `.mcp.json`, sin exponerlas en argumentos de bash ni en el contexto del LLM. Ademas, nos da control total sobre las herramientas expuestas, los formatos de respuesta y la gestion de errores.

El coste de desarrollo es moderado (~500-800 lineas de TypeScript) y se justifica por:
1. Seguridad de credenciales.
2. Abstraccion limpia de la API de Trello.
3. Reintentos y gestion de errores centralizada.
4. Herramientas especificas en lugar de genericas.

## Consecuencias

- **Ganancia:** Credenciales seguras. API limpia para los agentes. Errores bien gestionados.
- **Coste:** Desarrollo de ~500-800 lineas de TypeScript. Dependencia de Node.js en el usuario.
- **Deuda tecnica:** Minima si se mantiene el servidor delgado (solo las 8 operaciones necesarias para el MVP).
