# ADR-004: Dos agentes especializados (PO + Publisher)

| Campo | Valor |
|-------|-------|
| **Estado** | Aceptado |
| **Fecha** | 2026-03-13 |
| **Autor** | El Dibujante de Cajas |

## Contexto

El plugin tiene dos tipos de trabajo fundamentalmente diferentes:

1. **Trabajo de producto:** Hacer preguntas de descubrimiento, generar historias de usuario, validar calidad de criterios de aceptacion. Requiere creatividad, conocimiento de Scrum y razonamiento sobre negocio.

2. **Trabajo tecnico con Trello:** Verificar credenciales, crear tableros, publicar tarjetas, buscar duplicados. Requiere acceso a herramientas MCP y precision en las operaciones HTTP.

Mezclar ambos en un unico agente crea un problema: el agente de producto tendria acceso a las herramientas de Trello (riesgo de publicaciones accidentales) y el agente de Trello tendria acceso a Write/Edit (riesgo de modificaciones no deseadas en ficheros).

## Opciones consideradas

### Opcion A: Un unico agente con todos los permisos

- **Pros:** Simplicidad. Un solo prompt de sistema. Sin coordinacion entre agentes.
- **Contras:** Viola principio de minimo privilegio. Un error en el prompt de producto podria disparar publicaciones en Trello. El contexto del agente se sobrecarga con instrucciones de ambos dominios. Mas dificil de depurar.

### Opcion B: Dos agentes especializados con permisos segregados

- **Pros:** Cada agente tiene solo los permisos que necesita. El agente PO no puede tocar Trello. El agente Publisher no puede modificar ficheros. Prompts mas enfocados. Mas facil de depurar y evolucionar por separado.
- **Contras:** Coordinacion entre agentes (las skills orquestan quien hace que). Ligeramente mas complejo.

### Opcion C: Tres o mas agentes (PO, validador, publisher, docwriter)

- **Pros:** Maximo granularidad en permisos.
- **Contras:** Sobreingenieria para el MVP. La coordinacion entre 4 agentes anade complejidad sin beneficio proporcional. Las skills ya encapsulan la logica de validacion y documentacion.

## Decision

**Opcion B: Dos agentes especializados.**

El agente `product-owner` tiene permisos de lectura/escritura en ficheros pero NO tiene acceso a herramientas MCP de Trello. El agente `publisher` tiene acceso al servidor MCP de Trello pero NO tiene permisos de escritura en ficheros.

Las skills actuan como orquestadores: deciden cuando delegar al PO (descubrimiento, generacion) y cuando delegar al Publisher (verificacion, publicacion).

## Consecuencias

- **Ganancia:** Separacion de responsabilidades clara. Minimo privilegio. Prompts enfocados. Auditoria facil (si se publico en Trello, fue el Publisher).
- **Coste:** Las skills deben coordinar la delegacion entre agentes. Ligeramente mas complejo que un agente unico.
- **Deuda tecnica:** Si en futuras versiones (v1.1+) se necesitan mas agentes (por ejemplo, para priorizacion), la arquitectura ya soporta la adicion sin refactorizar.
