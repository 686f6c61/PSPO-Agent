# PRD: PSPO Agent -- Plugin de Product Owner para Claude Code

| Campo | Valor |
|-------|-------|
| **Autor** | El Buscador de Problemas (PO) |
| **Fecha** | 2026-03-15 |
| **Estado** | En revision |
| **Version** | 1.2 |

---

> Nota de estado: este PRD es la definición de producto original (baseline) y se conserva como referencia. El plugin ya publica en **Trello, Notion o GitHub Projects**; los ejemplos de este documento usan Trello por ser el primer proveedor. La fuente de verdad del comportamiento actual es `README.md` y `Documents/`.

---

## 1. Problema

Los desarrolladores independientes y equipos pequenos que usan Claude Code carecen de una figura de Product Owner dedicada. Esto provoca cinco problemas concretos:

1. **Historias de usuario mal definidas.** Traducir una idea vaga ("quiero un sistema de notificaciones") en historias de usuario bien formadas con criterios de aceptacion es un proceso que requiere experiencia en gestion de producto. Sin esa experiencia, las historias son ambiguas, demasiado grandes o carecen de criterios verificables.

2. **Perdida de tiempo en trabajo manual repetitivo.** Una vez definidas las historias, trasladarlas a un tablero de Trello (crear columnas, formatear tarjetas, asignar etiquetas, ordenar por prioridad) es trabajo mecanico que no aporta valor pero consume entre 30 y 60 minutos por sprint.

3. **Ausencia de descubrimiento de producto.** Sin un PO que haga preguntas antes de construir, los equipos saltan directamente a la implementacion. Esto genera retrabajo cuando se descubre tarde que el alcance estaba mal definido, faltaban casos de borde o no se habian considerado restricciones del negocio.

4. **Barrera de entrada en la configuracion inicial.** Conectar un plugin con una API externa (obtener credenciales, generar tokens, configurar tableros) es un proceso que intimida a usuarios sin experiencia tecnica en integraciones. Si el primer contacto con el plugin es frustrante, el usuario lo abandona antes de ver su valor.

5. **Distribucion de trabajo sin criterio ni visibilidad.** En equipos de 2-5 personas sin PO, las historias se reparten "a ojo" o por voluntariado. No hay visibilidad sobre quien tiene mas carga, que historias dependen de otras ni que pasa si una se retrasa. El tech lead pierde tiempo haciendo de coordinador manual y aun asi se descubren bloqueos a mitad de sprint.

**Resumen del dolor:** El desarrollador quiere construir producto, no gestionar producto. Pero sin gestion de producto, lo que construye no resuelve el problema correcto. Y cuando trabaja en equipo, la falta de coordinacion inteligente convierte las dependencias invisibles en bloqueos visibles demasiado tarde. Si la herramienta que deberia ayudarle le pide que "se lea la documentacion de la API de Trello" o que "haga un Excel con las asignaciones", ha fracasado antes de empezar.

---

## 2. Contexto

### Por que ahora

- **Claude Code se ha consolidado como herramienta de desarrollo** en 2025-2026, con un ecosistema de skills y plugins en expansion. La oportunidad de crear herramientas especializadas es ahora.
- **Los equipos pequenos y desarrolladores indie son el segmento de mayor crecimiento** en el uso de agentes de IA para codigo. Este segmento es precisamente el que no tiene un PO dedicado.
- **Trello sigue siendo la herramienta de gestion visual mas accesible** para equipos pequenos (plan gratuito generoso, API bien documentada, curva de aprendizaje plana).
- **La experiencia de primera ejecucion determina la retencion.** Segun datos de onboarding de herramientas SaaS, el 40-60% de los usuarios que no completan el setup inicial no vuelven a usar la herramienta. Un asistente guiado es critico para la adopcion.
- **La coordinacion de equipo es el siguiente cuello de botella.** Una vez resuelto el problema de "generar buenas historias", el siguiente dolor inmediato es "quien hace que y en que orden". Los equipos pequenos sin PO dedicado pierden hasta un 20% de su capacidad en bloqueos causados por dependencias no detectadas (fuente: datos internos de retrospectivas en equipos agiles de 3-5 personas).

### Datos que respaldan el problema

- Segun el State of Agile Report 2025, el 43% de los equipos de menos de 5 personas no tiene un rol de Product Owner definido.
- La causa principal de retrabajo en proyectos agiles es "requisitos mal definidos" (38% segun el CHAOS Report).
- Los equipos que usan criterios de aceptacion formales reducen bugs en produccion en un 25-40%.
- El 52% de los retrasos en sprints de equipos pequenos se debe a dependencias entre tareas no identificadas al inicio (fuente: encuesta VersionOne/Digital.ai 2025).

### Detalles tecnicos de la API de Trello (referencia para el equipo)

La autenticacion con Trello funciona con dos credenciales:

- **API Key:** Identifica la aplicacion. Se obtiene en https://trello.com/power-ups/admin al crear un Power-Up.
- **Token:** Autoriza al plugin a actuar en nombre del usuario. Se genera visitando una URL de autorizacion que incluye la API Key.
- **Secret:** Solo necesario para OAuth 1.0 de servidor. NO se necesita en el MVP.

URLs relevantes:

| Recurso | URL |
|---------|-----|
| Crear Power-Up / obtener API Key | https://trello.com/power-ups/admin |
| Generar token manual | `https://trello.com/1/authorize?expiration=30days&name=PSPO+Agent&scope=read,write&response_type=token&key={API_KEY}` |
| Verificar conexion | `GET https://api.trello.com/1/members/me?key={KEY}&token={TOKEN}` |
| Listar tableros del usuario | `GET https://api.trello.com/1/members/me/boards?key={KEY}&token={TOKEN}` |
| Listar miembros del tablero | `GET https://api.trello.com/1/boards/{id}/members?key={KEY}&token={TOKEN}` |
| Asignar miembro a tarjeta | `POST https://api.trello.com/1/cards/{id}/idMembers?value={memberId}&key={KEY}&token={TOKEN}` |
| Crear checklist en tarjeta | `POST https://api.trello.com/1/checklists?idCard={cardId}&name={name}&key={KEY}&token={TOKEN}` |
| Invitar miembro al tablero por email | `PUT https://api.trello.com/1/boards/{boardId}/members/{email}?type=normal&key={KEY}&token={TOKEN}` |

---

## 3. Usuario objetivo

### Persona principal: el desarrollador-emprendedor

| Atributo | Descripcion |
|----------|-------------|
| **Nombre** | Ana, desarrolladora fullstack |
| **Contexto** | Trabaja sola o en equipo de 2-3 personas |
| **Herramientas** | Claude Code, VS Code, Trello, GitHub |
| **Dolor** | Tiene ideas de producto pero no sabe traducirlas en historias accionables. Cuando lo intenta, las historias son demasiado grandes o ambiguas |
| **Comportamiento actual** | Escribe las tareas directamente en Trello sin estructura. No tiene criterios de aceptacion. Decide sobre la marcha que esta "terminado" |
| **Expectativa** | Un agente que le haga las preguntas correctas y genere la documentacion de producto que ella no sabe (o no quiere) hacer |
| **Nivel tecnico con APIs** | Sabe lo que es una API, pero nunca ha configurado tokens ni credenciales OAuth manualmente. Necesita guia paso a paso |

### Persona secundaria: el tech lead de equipo pequeno

| Atributo | Descripcion |
|----------|-------------|
| **Nombre** | Carlos, tech lead |
| **Contexto** | Equipo de 3-5 personas, sin PO dedicado |
| **Dolor** | Hace de PO a tiempo parcial ademas de su trabajo tecnico. Las historias le quedan irregulares en calidad. Reparte las tareas a ojo, sin visibilidad de dependencias ni de carga de trabajo por miembro. Descubre bloqueos a mitad de sprint cuando ya es tarde |
| **Comportamiento actual** | Manda las tareas por Slack o las asigna en Trello sin analisis previo. No tiene un mapa de dependencias. Cuando alguien se bloquea, improvisa |
| **Expectativa** | Un asistente que estandarice la calidad de las historias, le ahorre el trabajo mecanico de Trello, y ademas le diga quien deberia hacer que, en que orden, y que pasa si algo se retrasa |

---

## 4. Solucion propuesta

Un plugin de Claude Code que actua como Product Owner profesional certificado (PSPO de Scrum.org). El plugin se activa mediante un slash command y guia al usuario a traves de un flujo completo desde la primera instalacion hasta la publicacion en Trello, incluyendo la gestion del equipo y la distribucion inteligente de historias.

### Flujo principal (alto nivel)

```
[0] Primera ejecucion --> Onboarding guiado (credenciales + tablero)
[1] Entrada           --> /pspo-agent:start o /pspo-agent:autopilot
[2] Vision y contexto --> Analyze o discovery segun el input
[3] Generacion        --> Historias + save-docs + auditoria obligatoria
[4] Validacion        --> El usuario aprueba o corrige las HU
[5] Equipo            --> Se detecta, importa o crea un CSV de equipo compatible
[6] Asignacion        --> Ownership inicial por historia y reparto de carga
[7] Dependencias      --> Mapa confirmado de bloqueos y personas impactadas
[8] Sprint            --> DoD + estimacion en horas efectivas + sprint activo (max. 5 dias)
[9] Publicacion       --> Sync a Trello con resumen, adjunto .md, miembros y checklists
```

### Principios de diseno

- **Onboarding guiado desde el minuto cero.** Si el usuario necesita un manual para configurar el plugin, esta mal disenado. El plugin detecta que no hay configuracion y arranca un asistente que explica cada paso.
- **Descubrimiento primero.** El agente NUNCA genera historias sin antes hacer preguntas. El descubrimiento no es opcional.
- **Validacion humana obligatoria.** Ningun artefacto se publica en Trello sin aprobacion explicita del usuario.
- **Transparencia total.** El usuario ve exactamente que se va a crear en Trello antes de que se cree.
- **Reversibilidad.** Cualquier accion sobre Trello se puede deshacer.
- **El usuario manda en la distribucion.** El PSPO sugiere asignaciones y dependencias. El usuario siempre tiene la ultima palabra. Nada se asigna sin su aprobacion.

---

## 5. Historias de usuario

Priorizadas por impacto. La prioridad usa MoSCoW: Must (MVP), Should (v1.1), Could (futuro), Won't (descartado).

### MUST -- MVP

#### HU-01: Onboarding guiado de primera ejecucion

```
Como desarrollador que instala el plugin por primera vez,
quiero que el plugin detecte que no hay configuracion y me guie paso a paso
  para obtener las credenciales de Trello y configurar mi tablero,
para poder empezar a usar el plugin sin necesitar conocimientos previos sobre la API de Trello.
```

**Contexto del problema:** El usuario no sabe que es una API Key, ni donde se obtiene, ni como generar un token. El plugin debe llevarle de la mano por cada paso, explicandole que esta haciendo y por que.

**Criterios de aceptacion:**

```
ESCENARIO 1: Deteccion automatica de primera ejecucion
Given el plugin esta instalado
  And no existe un fichero .env con las variables TRELLO_API_KEY y TRELLO_TOKEN configuradas
When el usuario ejecuta cualquier comando del plugin
Then el plugin detecta que falta la configuracion
  And arranca automaticamente el asistente de onboarding
  And muestra un mensaje de bienvenida explicando que va a guiarle paso a paso

ESCENARIO 2: Paso 1 -- Obtener la API Key
Given el asistente de onboarding esta en ejecucion
When llega al paso de obtener la API Key
Then explica al usuario que necesita crear un "Power-Up" en Trello para obtener una clave de aplicacion
  And le indica que visite https://trello.com/power-ups/admin
  And le explica paso a paso:
    1. Pulsar "Nuevo" para crear un Power-Up
    2. Rellenar el nombre (sugiere "PSPO Agent") y el workspace
    3. Copiar la "API Key" que aparece en la pagina del Power-Up creado
  And le pide que pegue la API Key en el terminal
  And valida que el formato de la API Key es correcto (32 caracteres hexadecimales)

ESCENARIO 3: Paso 2 -- Generar el token de autorizacion
Given el usuario ha proporcionado una API Key con formato valido
When el asistente avanza al paso de generar el token
Then el plugin construye automaticamente la URL de autorizacion:
    https://trello.com/1/authorize?expiration=30days&name=PSPO+Agent&scope=read,write&response_type=token&key={API_KEY_DEL_USUARIO}
  And muestra al usuario una version segura de la URL o una plantilla con la API Key enmascarada
  And NUNCA vuelve a mostrar la API Key completa en pantalla ni en logs
  And le explica:
    1. Abrir esa URL en el navegador
    2. Autorizar a "PSPO Agent" cuando Trello lo pida
    3. Copiar el token que aparece en pantalla tras autorizar
  And le pide que pegue el token en el terminal

ESCENARIO 4: Verificacion de credenciales
Given el usuario ha proporcionado la API Key y el token
When el plugin verifica la conexion
Then hace una llamada a GET https://api.trello.com/1/members/me?key={KEY}&token={TOKEN}
  And si la respuesta es exitosa (HTTP 200):
    - Muestra el nombre completo y el nombre de usuario de la cuenta de Trello conectada
    - Confirma que la conexion es correcta
  And si la respuesta es un error (HTTP 401 o similar):
    - Muestra un mensaje claro indicando que las credenciales no son validas
    - Identifica cual de las dos es incorrecta si es posible (primero prueba solo la Key, luego Key+Token)
    - Ofrece reintentar desde el paso que corresponda
    - NO almacena las credenciales invalidas

ESCENARIO 5: Credenciales validas -- persistencia
Given las credenciales han sido verificadas con exito
When el plugin las almacena
Then guarda TRELLO_API_KEY y TRELLO_TOKEN en el fichero .env del proyecto
  And NO guarda el Secret (no es necesario para el MVP)
  And establece permisos 600 en el fichero .env (solo lectura/escritura para el propietario)
  And verifica que .env esta incluido en .gitignore
  And si .env no esta en .gitignore, anade la entrada y avisa al usuario
  And crea o actualiza el fichero .env.example con las variables (sin valores) como referencia
  And informa al usuario de que el token expira en 30 dias y que el plugin le avisara cuando necesite renovarlo

ESCENARIO 6: Reconfigurar credenciales existentes
Given ya existe un fichero .env con credenciales de Trello validas
When el usuario ejecuta explicitamente el comando de configuracion de credenciales
Then el plugin informa de que ya hay credenciales configuradas
  And muestra la cuenta conectada (nombre de usuario de Trello)
  And pregunta si desea reemplazarlas o mantener las actuales
  And si elige reemplazar, arranca el asistente desde el paso 1
```

---

#### HU-01b: Configuracion guiada del tablero de Trello

```
Como desarrollador que acaba de conectar sus credenciales de Trello,
quiero elegir o crear un tablero y configurar sus columnas y etiquetas,
para tener el tablero listo para recibir historias de usuario sin configuracion manual.
```

**Contexto del problema:** Despues de las credenciales, el usuario necesita un tablero donde el plugin publicara las historias. Puede querer usar uno existente o crear uno nuevo. La configuracion del tablero (columnas, etiquetas) debe ser parte del onboarding para que el plugin funcione de inmediato.

**Criterios de aceptacion:**

```
ESCENARIO 1: Seleccion de tablero -- mostrar opciones
Given las credenciales de Trello estan verificadas y el onboarding continua
  And no hay un TRELLO_BOARD_ID configurado en .env
When el asistente llega al paso de configuracion del tablero
Then consulta los tableros del usuario via GET https://api.trello.com/1/members/me/boards?key={KEY}&token={TOKEN}
  And muestra la lista de tableros disponibles (nombre y enlace)
  And ofrece dos opciones:
    a) Seleccionar un tablero existente de la lista
    b) Crear un tablero nuevo

ESCENARIO 2: Crear tablero nuevo
Given el usuario elige crear un tablero nuevo
When introduce el nombre del tablero (o acepta el nombre por defecto basado en el proyecto)
Then el plugin crea el tablero en Trello
  And crea las columnas por defecto: "Backlog", "Sprint activo", "Bloqueada", "En progreso", "En revision", "Hecho"
  And crea las etiquetas de prioridad: "Critica" (rojo), "Alta" (naranja), "Media" (amarillo), "Baja" (azul)
  And guarda el TRELLO_BOARD_ID en el fichero .env
  And muestra la URL del tablero creado para que el usuario pueda verlo

ESCENARIO 3: Usar tablero existente
Given el usuario elige un tablero existente de la lista
When confirma la seleccion
Then el plugin lee las columnas actuales del tablero
  And muestra las columnas existentes al usuario
  And pregunta si quiere:
    a) Usar las columnas tal como estan
    b) Anadir las columnas estandar que falten ("Backlog", "Sprint activo", "Bloqueada", "En progreso", "En revision", "Hecho")
  And guarda el TRELLO_BOARD_ID en el fichero .env

ESCENARIO 4: Configuracion de etiquetas en tablero existente
Given el usuario ha seleccionado un tablero existente
When el plugin analiza las etiquetas del tablero
Then muestra las etiquetas existentes
  And si no existen las etiquetas de prioridad estandar, ofrece crearlas
  And el usuario decide si anade las etiquetas estandar o usa las que ya tiene

ESCENARIO 5: Confirmacion final del onboarding
Given las credenciales estan verificadas y el tablero esta configurado
When el asistente completa el onboarding
Then muestra un resumen de la configuracion:
    - Cuenta de Trello conectada (nombre de usuario)
    - Tablero seleccionado (nombre y URL)
    - Columnas configuradas
    - Etiquetas disponibles
  And confirma que el plugin esta listo para usarse
  And guarda toda la configuracion para que en futuras sesiones no se repita el proceso

ESCENARIO 6: Sesiones posteriores -- sin repetir onboarding
Given existe un fichero .env con TRELLO_API_KEY, TRELLO_TOKEN y TRELLO_BOARD_ID validos
When el usuario ejecuta el plugin en una nueva sesion
Then el plugin verifica silenciosamente que las credenciales siguen siendo validas
  And si son validas, arranca directamente el flujo normal (descubrimiento/generacion)
  And NO muestra el asistente de onboarding

ESCENARIO 7: Credenciales validas pero tablero eliminado
Given existe un fichero .env con credenciales validas y un TRELLO_BOARD_ID
When el plugin intenta verificar el tablero y este ya no existe (eliminado en Trello)
Then informa al usuario de que el tablero configurado ya no esta disponible
  And arranca el paso de configuracion de tablero (no repite las credenciales)

ESCENARIO 8: Personalizacion de columnas por el usuario
Given el tablero esta configurado (nuevo o existente)
When el usuario quiere modificar las columnas (renombrar, anadir, eliminar o reordenar)
Then el plugin muestra las columnas actuales del tablero
  And permite al usuario:
    a) Renombrar columnas existentes
    b) Anadir columnas nuevas en la posicion que elija
    c) Eliminar columnas (con confirmacion si contienen tarjetas)
    d) Reordenar columnas
  And aplica los cambios en Trello
  And actualiza la configuracion local para reflejar la nueva estructura

ESCENARIO 9: Sugerencia de columnas por el sistema
Given el PSPO Agent detecta un patron en el flujo de trabajo del proyecto
  (por ejemplo: historias que se bloquean frecuentemente, o que necesitan validacion externa)
When analiza el estado del tablero y las historias
Then sugiere al usuario anadir o modificar columnas para mejorar el flujo
  (por ejemplo: "Detecto que varias historias estan bloqueadas. Quieres crear una columna 'Bloqueado'?")
  And el usuario decide si acepta, rechaza o modifica la sugerencia
  And el plugin NUNCA modifica columnas sin aprobacion explicita del usuario
```

---

#### HU-02: Descubrimiento de producto mediante conversacion

```
Como desarrollador con una idea de producto,
quiero que el agente me haga preguntas de descubrimiento antes de generar nada,
para asegurarme de que el problema esta bien definido antes de escribir una sola linea de codigo.
```

**Criterios de aceptacion:**

```
ESCENARIO 1: Inicio del descubrimiento
Given el usuario activa el plugin y describe una necesidad en lenguaje natural
When el agente recibe la descripcion
Then NO genera historias de usuario inmediatamente
  And formula al menos 3 preguntas de descubrimiento sobre:
    - Quien es el usuario final y que problema tiene
    - Como resuelve el problema actualmente (si lo resuelve)
    - Que restricciones existen (tiempo, tecnologia, presupuesto)
    - Que resultado se espera cuando esto funcione

ESCENARIO 2: Iteracion en descubrimiento
Given el agente ha formulado preguntas y el usuario las ha respondido
When las respuestas revelan ambiguedades o contradicciones
Then el agente hace preguntas de seguimiento para clarificar
  And no avanza a la generacion hasta que el alcance este definido

ESCENARIO 3: Descripcion suficientemente detallada
Given el usuario proporciona una descripcion con usuario, problema, contexto y restricciones
When el agente analiza la descripcion
Then puede reducir el numero de preguntas de descubrimiento
  And confirma con el usuario los puntos clave antes de avanzar
```

---

#### HU-03: Generacion de historias de usuario con criterios de aceptacion

```
Como desarrollador que ha completado el descubrimiento,
quiero recibir historias de usuario bien formadas con criterios de aceptacion,
para tener una guia clara de que construir y como verificar que esta bien hecho.
```

**Criterios de aceptacion:**

```
ESCENARIO 1: Formato correcto de historias
Given el descubrimiento esta completo y el alcance esta definido
When el agente genera las historias de usuario
Then cada historia sigue el formato "Como [rol especifico], quiero [accion concreta], para [beneficio medible]"
  And el rol nunca es generico ("usuario"), siempre es especifico
  And cada historia es independiente (se puede implementar y entregar por separado)
  And las historias estan ordenadas por prioridad de valor para el usuario

ESCENARIO 2: Criterios de aceptacion completos
Given el agente ha generado una historia de usuario
When presenta los criterios de aceptacion asociados
Then cada criterio usa formato Given/When/Then
  And incluye al menos un escenario positivo (happy path)
  And incluye al menos un escenario negativo (error, fallo, entrada invalida)
  And los valores son concretos, no genericos

ESCENARIO 3: Tamano manejable
Given el agente genera historias de usuario
When una historia es demasiado grande (estimacion superior a 3 dias de trabajo)
Then el agente la descompone en historias mas pequenas
  And explica al usuario como se relacionan entre si
```

---

#### HU-04: Validacion y aprobacion de artefactos

```
Como desarrollador que recibe los artefactos generados,
quiero revisar y aprobar cada artefacto antes de que se publique en Trello,
para mantener el control sobre lo que se gestiona en mi tablero.
```

**Criterios de aceptacion:**

```
ESCENARIO 1: Presentacion para revision
Given el agente ha generado las historias de usuario y criterios
When presenta los artefactos al usuario
Then muestra un resumen estructurado con todas las historias
  And permite al usuario aprobar, rechazar o pedir cambios en cada historia individualmente

ESCENARIO 2: Modificacion de historias
Given el usuario solicita cambios en una historia de usuario
When el agente recibe el feedback
Then modifica la historia segun el feedback
  And presenta la version revisada para nueva aprobacion
  And NO avanza a publicacion hasta aprobacion explicita

ESCENARIO 3: Aprobacion parcial
Given el usuario aprueba algunas historias pero no todas
When confirma la seleccion
Then solo las historias aprobadas se marcan como listas para publicar
  And las historias pendientes quedan en estado de revision
```

---

#### HU-05: Creacion y gestion del tablero de Trello

```
Como desarrollador que ha aprobado las historias,
quiero que el plugin publique las historias como tarjetas en el tablero de Trello configurado,
para tener la gestion visual del backlog sin trabajo manual.
```

**Criterios de aceptacion:**

```
ESCENARIO 1: Publicacion en tablero existente (configurado en onboarding)
Given el usuario tiene un tablero configurado (TRELLO_BOARD_ID en .env)
  And las historias estan aprobadas
When el usuario confirma la publicacion en Trello
Then el plugin crea o sincroniza cada historia como tarjeta en la lista que corresponda del tablero configurado
  And usa "Sprint activo" para historias del sprint sin bloqueo
  And usa "Bloqueada" para historias del sprint con dependencias no resueltas
  And usa "Backlog" para historias aun no comprometidas
  And NO duplica tarjetas que ya existan (comparacion por titulo)

ESCENARIO 2: Formato de tarjetas
Given el plugin crea una tarjeta en Trello para una historia de usuario
When la tarjeta se publica
Then el titulo de la tarjeta es la historia en formato corto
  And la descripcion incluye un resumen corto con historia, escenarios clave, prioridad y estimacion
  And la historia completa viaja como fichero Markdown adjunto a la tarjeta
  And la tarjeta tiene asignada la etiqueta de prioridad correspondiente
  And si aplica, anade checklist de DoD y checklist de dependencias

ESCENARIO 3: Vista previa antes de publicar
Given las historias estan aprobadas y listas para publicar
When el usuario da la orden de publicar
Then el plugin muestra una vista previa de lo que se va a crear:
    - Nombre del tablero destino
    - Lista de tarjetas con titulo, prioridad y columna destino
  And pide confirmacion final antes de ejecutar

ESCENARIO 4: Error de conexion
Given el plugin intenta publicar en Trello
When la API de Trello devuelve un error (red, autenticacion, limite de rate)
Then el plugin muestra un mensaje de error descriptivo
  And guarda las historias localmente para reintentar despues
  And NO pierde ningun dato
```

---

#### HU-06: Generacion de documentacion de producto local

```
Como desarrollador que trabaja en el proyecto,
quiero que los artefactos de producto se guarden como ficheros en el repositorio,
para tener la documentacion versionada junto al codigo.
```

**Criterios de aceptacion:**

```
ESCENARIO 1: Estructura de ficheros
Given el agente ha generado y el usuario ha aprobado los artefactos
When se guardan en el sistema de ficheros
Then se crean en la carpeta docs/ del proyecto con la siguiente estructura:
    - docs/vision.md (vision de producto)
    - docs/historias/ (una historia por fichero, nombrada HU-XX-titulo-corto.md)
    - docs/backlog.md (lista priorizada de todas las historias)
  And cada fichero usa formato Markdown limpio y legible

ESCENARIO 2: Actualizacion sin perdida
Given ya existen artefactos de producto en docs/
When el agente genera nuevos artefactos o modifica existentes
Then actualiza los ficheros correspondientes
  And NO sobreescribe historias que no han cambiado
  And registra la fecha de ultima modificacion en el fichero
```

---

#### HU-07: Gestion de equipo del proyecto

```
Como tech lead de un equipo pequeno sin PO dedicado,
quiero definir los miembros de mi equipo con sus roles dentro del plugin,
para que el PSPO tenga la informacion necesaria para distribuir historias de forma inteligente.
```

**Contexto del problema:** El tech lead conoce a su equipo pero no tiene una forma estructurada de comunicarselo al plugin. Necesita poder definir el equipo de forma rapida (importar CSV si ya lo tiene en otro sitio) o de forma guiada (anadir miembros uno a uno si parte de cero). Los roles son libres porque cada equipo tiene su propia estructura. Ademas del rol, la categoria (nivel de experiencia) es crucial: no es lo mismo asignar una historia critica a un Backend Junior que a un Backend Senior.

**Criterios de aceptacion:**

```
ESCENARIO 1: Deteccion de equipo no definido
Given el usuario tiene historias aprobadas y listas para distribuir
  And no existe ningun CSV de equipo compatible en la raiz del proyecto
When el usuario solicita distribuir historias al equipo
Then el plugin detecta que no hay equipo definido
  And pregunta al usuario si tiene un equipo definido en algun formato (CSV, lista)
  And ofrece tres opciones:
    a) Importar miembros desde un fichero CSV
    b) Rellenar una plantilla CSV que el plugin genera
    c) Anadir miembros uno a uno de forma guiada

ESCENARIO 2: Importacion desde CSV
Given el usuario elige importar un CSV existente
When proporciona la ruta del fichero
Then el plugin lee el fichero CSV
  And espera las columnas: nombre, email, rol, categoria, dedicacion, usa_agente_ia
  And valida que cada fila tiene los seis campos rellenos
  And valida que los emails tienen formato correcto
  And valida que la dedicacion esta entre 0 y 100
  And valida que usa_agente_ia sea "si" o "no"
  And muestra un resumen del equipo importado:
    - Numero de miembros
    - Lista con nombre, email, rol, categoria, dedicacion y uso de agente IA de cada uno
  And pide confirmacion antes de guardar
  And si hay filas invalidas, las muestra y permite corregirlas o descartarlas

ESCENARIO 3: Generacion de plantilla CSV con ejemplos
Given el usuario elige rellenar una plantilla
When el plugin genera la plantilla
Then crea un fichero CSV compatible (por defecto `team.csv` si el usuario no indica otro nombre) con la cabecera: nombre,email,rol,categoria,dedicacion,usa_agente_ia
  And anade filas de ejemplo comentadas para que quede claro el formato:
    # Los siguientes son ejemplos. Borralos y anade los datos reales de tu equipo.
    # nombre,email,rol,categoria,dedicacion,usa_agente_ia
    # Ana Garcia,ana@equipo.com,Frontend,Senior,100,si
    # Carlos Lopez,carlos@equipo.com,Backend,Junior,100,no
    # Maria Ruiz,maria@equipo.com,QA,Mid,50,si
  And indica al usuario que borre los ejemplos, rellene con datos reales y vuelva a ejecutar el comando
  And muestra la ruta absoluta del fichero generado

ESCENARIO 4: Alta guiada de miembros uno a uno
Given el usuario elige anadir miembros de forma guiada
When el plugin inicia el asistente
Then para cada miembro pregunta:
    1. Nombre completo
    2. Email
    3. Rol en el equipo (texto libre, con sugerencias: Frontend, Backend, QA, UX, Fullstack, DevOps)
    4. Categoria o nivel (texto libre, con sugerencias: Junior, Mid, Senior, Lead)
    5. Dedicacion al proyecto (0-100)
    6. Usa agente de IA para desarrollar? (si/no)
  And tras cada miembro, pregunta si quiere anadir otro
  And al terminar, muestra el resumen del equipo completo con nombre, email, rol, categoria, dedicacion y uso de agente IA
  And pide confirmacion antes de guardar

ESCENARIO 5: Roles y categorias de texto libre
Given el usuario introduce el rol y la categoria de un miembro
When el plugin recibe los textos
Then acepta cualquier texto como rol valido (no hay lista cerrada)
  And sugiere roles comunes (Frontend, Backend, QA, UX, Fullstack, DevOps) solo como ayuda
  And el usuario puede escribir cualquier rol personalizado (por ejemplo: "Datos", "Movil", "Seguridad")
  And acepta cualquier texto como categoria valida (no hay lista cerrada)
  And sugiere categorias comunes (Junior, Mid, Senior, Lead) solo como ayuda
  And el usuario puede escribir cualquier categoria personalizada (por ejemplo: "Trainee", "Principal", "Staff")
  And la categoria es importante para la distribucion: no es lo mismo asignar una historia critica a un Backend Junior que a un Backend Senior

ESCENARIO 6: Persistencia del equipo
Given el usuario ha confirmado la composicion del equipo
When el plugin guarda los datos
Then escribe el fichero CSV del equipo en la raiz del proyecto respetando el nombre original si el usuario venia de un fichero existente
  And si el equipo se creo desde cero y no hay nombre previo, usa `team.csv` como convencion por defecto
  And el formato es CSV con cabecera: nombre,email,rol,categoria,dedicacion,usa_agente_ia
  And el fichero se puede editar manualmente con cualquier editor de texto
  And en futuras sesiones, el plugin lee cualquier CSV de equipo compatible automaticamente sin repetir el proceso de alta

ESCENARIO 7: Modificacion del equipo existente
Given existe un CSV de equipo compatible con miembros definidos
When el usuario solicita modificar el equipo
Then el plugin muestra el equipo actual en formato tabla
  And permite:
    a) Anadir nuevos miembros
    b) Eliminar miembros existentes (con confirmacion)
    c) Modificar el rol de un miembro existente
    d) Ajustar dedicacion o uso de agente IA de un miembro existente
  And actualiza el mismo CSV tras la confirmacion del usuario

ESCENARIO 8: Equipo vacio o fichero corrupto
Given existe un CSV de equipo compatible pero esta vacio o tiene formato invalido
When el plugin intenta leerlo
Then muestra un mensaje descriptivo del problema
  And ofrece recrear el fichero desde cero (genera plantilla nueva)
  And NO pierde el fichero original (lo renombra a {nombre_original}.bak)
```

---

#### HU-08: Distribucion inteligente de historias al equipo

```
Como tech lead que tiene historias aprobadas y un equipo definido,
quiero que el PSPO sugiera una distribucion de historias entre los miembros del equipo,
para no tener que repartir el trabajo a ojo y asegurarme de que la carga esta equilibrada.
```

**Contexto del problema:** El tech lead pierde tiempo decidiendo quien hace cada historia. Lo hace sin datos: no analiza la carga total por miembro, ni tiene en cuenta que ciertas historias son mas adecuadas para ciertos roles. El PSPO puede hacer ese analisis en segundos, pero el tech lead siempre debe tener la ultima palabra.

**Criterios de aceptacion:**

```
ESCENARIO 1: Condiciones previas para la distribucion
Given el usuario solicita distribuir historias
When el plugin verifica el estado
Then comprueba que existen historias aprobadas (en docs/historias/ o en memoria)
  And comprueba que existe un equipo definido (CSV de equipo compatible con al menos 2 miembros)
  And si falta alguna de las dos condiciones, informa al usuario de que necesita primero:
    - Historias aprobadas (si no las hay): ejecutar el flujo de descubrimiento/generacion
    - Equipo definido (si no lo hay): ejecutar la gestion de equipo (HU-07)

ESCENARIO 2: Propuesta de distribucion basada en roles
Given hay historias aprobadas y equipo definido
When el PSPO analiza las historias y el equipo
Then para cada historia, identifica que tipo de trabajo implica (frontend, backend, datos, testing, etc.)
  And cruza el tipo de trabajo con los roles de los miembros del equipo
  And genera una propuesta de asignacion en formato tabla:
    | Historia | Miembro asignado | Rol | Horas efectivas | Razon de la asignacion |
  And muestra la carga total por miembro en horas efectivas
  And si hay desequilibrio operativo claro, lo senala explicitamente

ESCENARIO 3: Equilibrio de carga
Given el PSPO ha generado una propuesta de distribucion
When la carga esta desequilibrada entre miembros
Then senala el desequilibrio con datos concretos:
    "Ana tiene 14 h efectivas asignadas y Carlos tiene 6 h. Quieres reequilibrar?"
  And sugiere una redistribucion alternativa moviendo historias de perfil compatible
  And el usuario decide si acepta la redistribucion o mantiene la propuesta original

ESCENARIO 4: Historias sin encaje claro de rol
Given hay historias que no encajan claramente con ningun rol del equipo
When el PSPO intenta asignarlas
Then las marca como "asignacion sugerida con baja confianza"
  And explica por que no tiene claro a quien asignarla
  And pide al usuario que decida manualmente para esas historias

ESCENARIO 5: Aprobacion del usuario sobre la distribucion
Given el PSPO presenta la propuesta completa de distribucion
When el usuario la revisa
Then puede:
    a) Aprobar la distribucion tal como esta
    b) Modificar asignaciones individuales (reasignar una historia a otro miembro)
    c) Rechazar toda la distribucion y pedir un nuevo analisis con criterios distintos
  And el PSPO NO ejecuta ninguna asignacion hasta que el usuario apruebe explicitamente

ESCENARIO 6: Persistencia de las asignaciones
Given el usuario ha aprobado la distribucion de historias
When el plugin guarda las asignaciones
Then crea o actualiza el fichero docs/asignaciones.md con:
    - Fecha de la asignacion
    - Tabla historia -> miembro -> rol -> estado
    - Resumen de carga por miembro
  And si ya existia el fichero, anade las nuevas asignaciones sin borrar las anteriores
```

---

#### HU-09: Mapa de dependencias y bloqueantes entre historias

```
Como tech lead que coordina el trabajo de un equipo pequeno,
quiero que el PSPO identifique dependencias y bloqueantes entre historias,
para saber en que orden deben ejecutarse y que impacto tiene un retraso en el resto del plan.
```

**Contexto del problema:** Las dependencias entre historias son invisibles hasta que alguien se bloquea. El tech lead las lleva en la cabeza, pero se le escapan. El PSPO puede analizar el contenido de las historias y sus criterios de aceptacion para detectar relaciones (por ejemplo: "la HU-03 usa el API que se construye en la HU-01"). Pero como este analisis es inferido, el usuario siempre debe confirmar.

**Criterios de aceptacion:**

```
ESCENARIO 1: Analisis automatico de dependencias
Given hay al menos 3 historias aprobadas
When el usuario solicita el mapa de dependencias
  Or el PSPO inicia la distribucion de historias (HU-08)
Then el PSPO analiza el contenido de cada historia y sus criterios de aceptacion
  And busca relaciones de dependencia:
    - Tecnica: "HU-03 necesita el endpoint que crea HU-01"
    - De datos: "HU-05 necesita datos que genera HU-02"
    - De UX: "HU-04 usa el componente que disena HU-06"
  And genera una lista de dependencias detectadas en formato:
    | Historia origen | Depende de | Tipo de dependencia | Confianza |
  And marca el nivel de confianza de cada dependencia (alta, media, baja)

ESCENARIO 2: Confirmacion de dependencias por el usuario
Given el PSPO ha detectado dependencias entre historias
When presenta las dependencias al usuario
Then para cada dependencia, el usuario puede:
    a) Confirmar: "Si, esa dependencia es real"
    b) Rechazar: "No, esas historias son independientes"
    c) Anadir dependencias que el PSPO no detecto
  And el PSPO actualiza el mapa con las correcciones del usuario
  And el PSPO NUNCA trata como bloqueante una dependencia no confirmada

ESCENARIO 3: Identificacion de bloqueantes
Given el mapa de dependencias esta confirmado
When el PSPO analiza las cadenas de dependencia
Then identifica historias bloqueantes: aquellas de las que dependen otras
  And ordena las historias bloqueantes por impacto (cuantas historias desbloquean)
  And muestra la informacion de forma clara:
    "HU-01 bloquea a HU-03 y HU-05. Si HU-01 se retrasa, 2 historias se ven afectadas."
  And recomienda que las historias bloqueantes se prioricen al inicio del sprint

ESCENARIO 4: Visualizacion del grafo de dependencias
Given el mapa de dependencias esta confirmado por el usuario
When el plugin genera la visualizacion
Then crea un diagrama en formato Mermaid dentro de docs/dependencias.md:
    - Cada historia es un nodo con su ID y titulo corto
    - Cada dependencia es una flecha del origen al destino
    - Las historias bloqueantes se resaltan (color o forma diferente)
    - Los miembros asignados aparecen junto a cada nodo (si ya hay asignaciones)
  And el diagrama se puede visualizar en cualquier visor de Markdown con soporte Mermaid
  And debajo del diagrama incluye la lista en formato texto para lectores sin soporte Mermaid

ESCENARIO 5: Analisis de impacto de retrasos
Given el mapa de dependencias esta confirmado
  And las historias estan asignadas a miembros
When el usuario pregunta "que pasa si HU-XX se retrasa?"
Then el PSPO recorre la cadena de dependencias desde esa historia
  And muestra todas las historias afectadas directa e indirectamente
  And muestra los miembros afectados (los que trabajan en historias dependientes)
  And calcula el "radio de impacto": numero total de historias y miembros afectados
  And si el impacto es alto (mas de 3 historias afectadas), recomienda acciones:
    - Reasignar mas recursos a la historia retrasada
    - Buscar un camino alternativo (historias que puedan avanzar en paralelo)

ESCENARIO 6: Persistencia del mapa de dependencias
Given el usuario ha confirmado el mapa de dependencias
When el plugin guarda los datos
Then crea o actualiza el fichero docs/dependencias.md con:
    - Diagrama Mermaid del grafo
    - Tabla de dependencias confirmadas
    - Lista de historias bloqueantes ordenadas por impacto
    - Fecha de ultima actualizacion
  And en futuras sesiones, el plugin carga el mapa existente como punto de partida
  And si se anaden nuevas historias, ofrece analizar solo las nuevas contra el mapa existente

ESCENARIO 7: Dependencia circular detectada
Given el PSPO analiza las dependencias
When detecta una dependencia circular (HU-01 -> HU-03 -> HU-01)
Then lo senala como un problema critico
  And muestra la cadena circular de forma clara
  And pide al usuario que resuelva la circularidad (eliminando o reformulando alguna dependencia)
  And NO permite confirmar un mapa con dependencias circulares
```

---

#### HU-10: Integracion de asignaciones y dependencias con Trello

```
Como tech lead que gestiona su equipo a traves de Trello,
quiero que las asignaciones de historias y las dependencias se reflejen en las tarjetas del tablero,
para que todo el equipo vea quien hace que y que depende de que sin salir de Trello.
```

**Contexto del problema:** El mapa de dependencias y las asignaciones son utiles localmente, pero el equipo trabaja en Trello. Si esa informacion no llega a las tarjetas, el equipo no la ve. La sincronizacion con Trello debe reflejar asignaciones (miembros en tarjetas) y dependencias (checklists y etiquetas).

**Criterios de aceptacion:**

```
ESCENARIO 1: Asignacion de miembros a tarjetas
Given las historias estan publicadas en Trello como tarjetas
  And las asignaciones estan aprobadas por el usuario
  And el plugin dispone de un CSV de equipo compatible con emails validos
When el plugin sincroniza las asignaciones con Trello
Then para cada tarjeta, busca el miembro del equipo asignado por email
  And si el miembro existe como miembro del tablero en Trello, lo asigna a la tarjeta
  And si el miembro NO existe en el tablero, intenta invitarlo automaticamente como parte de la sincronizacion confirmada
  And si despues de invitarlo no consigue `memberId`, marca la tarjeta como incompleta y la incluye en el reporte final para revision manual

ESCENARIO 2: Invitacion de miembros al tablero de Trello
Given las asignaciones estan aprobadas
  And hay miembros del equipo que NO son miembros del tablero en Trello
When el plugin detecta miembros no vinculados
Then incluye esas invitaciones en la vista previa final antes de sincronizar
  And tras la confirmacion del usuario, envia invitacion via PUT /1/boards/{boardId}/members/{email} para cada miembro no vinculado
  And si la invitacion se envia correctamente, el plugin lo confirma:
    "Invitacion enviada a ana@equipo.com para unirse al tablero."
  And si la API devuelve error (email invalido, limite alcanzado), lo informa sin detener el resto
  And las invitaciones se envian con rol "normal" (miembro, no admin)
  And esta accion requiere que el token tenga permisos de escritura en el tablero

ESCENARIO 3: Checklists de dependencias en tarjetas
Given el mapa de dependencias esta confirmado
  And las tarjetas existen en Trello
When el plugin sincroniza las dependencias con Trello
Then para cada tarjeta que tiene dependencias, crea un checklist llamado "Dependencias"
  And cada item del checklist es una dependencia en formato:
    "[ ] Requiere: HU-XX - [titulo corto] (enlace a la tarjeta)"
  And cuando la tarjeta de la que depende se mueve a "Hecho", el item se marca como completado
    (solo si hay sincronizacion activa; en MVP, el marcado es manual o bajo demanda)

ESCENARIO 4: Etiquetas de estado de asignacion
Given las asignaciones estan sincronizadas con Trello
When el plugin actualiza las tarjetas
Then crea o reutiliza etiquetas adicionales para visualizar el estado:
    - "Asignada" (verde): la historia tiene miembro asignado
    - "Bloqueada" (rojo): la historia tiene dependencias no resueltas
    - "Bloqueante" (morado): la historia bloquea a otras
  And asigna las etiquetas correspondientes a cada tarjeta

ESCENARIO 5: Vista previa antes de sincronizar con Trello
Given el plugin va a sincronizar asignaciones y dependencias con Trello
When el usuario solicita la sincronizacion
Then el plugin muestra una vista previa de los cambios:
    - Tarjetas a las que se asignaran miembros (nombre del miembro + tarjeta)
    - Invitaciones pendientes de enviar (si las hay)
    - Checklists de dependencias que se crearan
    - Etiquetas que se anadiran
  And pide confirmacion explicita antes de ejecutar cualquier cambio
  And el plugin NUNCA modifica tarjetas en Trello sin confirmacion del usuario

ESCENARIO 6: Sincronizacion incremental
Given ya se han sincronizado asignaciones previamente
When el usuario hace cambios en la distribucion o en las dependencias
Then el plugin detecta solo los cambios (nuevas asignaciones, dependencias modificadas)
  And muestra los cambios incrementales, no toda la sincronizacion de nuevo
  And aplica solo los cambios confirmados por el usuario

ESCENARIO 7: Error de permisos en Trello
Given el plugin intenta asignar un miembro o crear un checklist en Trello
When la API devuelve un error de permisos (el token no tiene permisos suficientes, o el miembro no pertenece al tablero)
Then muestra un mensaje de error claro con la causa especifica
  And no detiene la sincronizacion del resto de tarjetas
  And al final, muestra un resumen de lo que se sincronizo y lo que fallo
  And las acciones fallidas se guardan para reintentar
```

---

### SHOULD -- Version 1.1

#### HU-11s: Definition of Done configurable

```
Como tech lead de un equipo pequeno,
quiero definir una Definition of Done (DoD) para el proyecto,
para que todas las historias tengan un estandar minimo de calidad verificable.
```

**Criterios de aceptacion:**

```
ESCENARIO 1: DoD por defecto
Given el usuario no ha configurado una DoD personalizada
When el agente genera historias
Then aplica una DoD por defecto que incluye:
    - Criterios de aceptacion cumplidos
    - Codigo revisado
    - Tests escritos y pasando
    - Documentacion actualizada

ESCENARIO 2: DoD personalizada
Given el usuario define una DoD personalizada
When el agente genera historias
Then aplica la DoD personalizada a todas las historias
  And incluye la DoD en cada tarjeta de Trello como checklist
```

---

#### HU-12s: Priorizacion asistida por valor

```
Como desarrollador que tiene muchas historias en el backlog,
quiero que el agente me ayude a priorizar por valor de negocio,
para trabajar primero en lo que mas impacto tiene.
```

**Criterios de aceptacion:**

```
ESCENARIO 1: Sugerencia de priorizacion
Given hay mas de 5 historias en el backlog sin priorizar
When el usuario pide ayuda para priorizar
Then el agente pregunta por criterios de valor (impacto en usuario, esfuerzo estimado, riesgo)
  And sugiere un orden de priorizacion con justificacion para cada historia
  And el usuario tiene la ultima palabra sobre el orden final
```

---

#### HU-13s: Niveles PSPO II -- Estrategia de producto

```
Como tech lead que necesita alinear al equipo,
quiero que el agente me ayude a definir la vision de producto y el roadmap,
para tener un norte claro mas alla del sprint actual.
```

**Criterios de aceptacion:**

```
ESCENARIO 1: Vision de producto
Given el usuario solicita definir la vision de producto
When el agente inicia el flujo de vision
Then hace preguntas sobre publico objetivo, propuesta de valor, diferenciacion y metricas de exito
  And genera un documento de vision conciso (1 pagina)
  And lo guarda en docs/vision.md

ESCENARIO 2: Roadmap basico
Given la vision de producto esta definida y hay historias priorizadas
When el usuario solicita un roadmap
Then el agente agrupa las historias en releases logicas
  And sugiere un orden temporal basado en dependencias y valor
  And genera un documento de roadmap en docs/roadmap.md
```

---

### COULD -- Futuro

#### HU-14c: Metricas de flujo del tablero

```
Como tech lead que gestiona el backlog en Trello,
quiero ver metricas basicas del flujo de trabajo (lead time, throughput),
para detectar cuellos de botella y mejorar la previsibilidad.
```

#### HU-15c: Sincronizacion bidireccional con Trello

```
Como desarrollador que mueve tarjetas en Trello manualmente,
quiero que los cambios en Trello se reflejen en la documentacion local,
para mantener la coherencia entre el tablero y el repositorio.
```

#### HU-16c: Niveles PSPO III -- Gestion de stakeholders

```
Como tech lead de un producto con multiples interesados,
quiero que el agente me ayude a gestionar expectativas y comunicacion con stakeholders,
para alinear la estrategia de producto con las necesidades del negocio.
```

---

### WON'T -- Descartado para este producto

- **Integracion con Jira.** Jira es para equipos mas grandes que ya tienen PO. No es nuestro usuario.
- **Estimacion de esfuerzo automatica.** Estimar es responsabilidad del equipo de desarrollo, no del PO.
- **Gestion de sprints completa.** Trello no es la herramienta ideal para ceremonias de Scrum. El plugin se limita al backlog y la publicacion.
- **Interfaz grafica propia.** El plugin opera dentro de Claude Code. No se construye UI separada.
- **Autenticacion OAuth 1.0 de servidor.** El MVP usa autenticacion manual (API Key + Token generado por el usuario). OAuth server-side anade complejidad sin beneficio para el caso de uso de un plugin local.
- **Gestion de disponibilidad y capacidad del equipo.** El PSPO no gestiona vacaciones, jornadas parciales ni capacidad por sprint. La distribucion se basa en roles, no en horas disponibles. Si esto se necesita en el futuro, sera una historia aparte.

---

## 6. Alcance del MVP

El MVP incluye las historias HU-01, HU-01b, HU-02 a HU-06, y HU-07 a HU-10. Con esto, el usuario puede:

1. **Instalar y configurar el plugin en menos de 5 minutos** gracias al asistente de onboarding guiado que le lleva de la mano desde cero (HU-01).
2. **Tener un tablero de Trello listo** sin configuracion manual, eligiendo uno existente o creando uno nuevo con la estructura adecuada (HU-01b).
3. **Describir una necesidad y ser guiado** por un proceso de descubrimiento profesional (HU-02).
4. **Recibir historias de usuario** con criterios de aceptacion de calidad profesional (HU-03).
5. **Revisar y aprobar cada historia** antes de publicar (HU-04).
6. **Publicar automaticamente** en el tablero de Trello configurado (HU-05).
7. **Tener la documentacion versionada** en el repositorio (HU-06).
8. **Definir su equipo** importando un CSV, rellenando una plantilla o anadiendo miembros uno a uno de forma guiada (HU-07).
9. **Distribuir historias al equipo de forma inteligente**, con sugerencias basadas en rol, equilibrio de carga y aprobacion del usuario (HU-08).
10. **Visualizar dependencias y bloqueantes** entre historias con un mapa que identifica cadenas criticas y analiza el impacto de retrasos (HU-09).
11. **Reflejar asignaciones y dependencias en Trello**, con miembros en tarjetas, checklists de dependencias y etiquetas de estado (HU-10).

### Lo que NO incluye el MVP

- Definition of Done configurable (HU-11s, v1.1).
- Priorizacion asistida por valor (HU-12s, v1.1).
- Vision de producto y roadmap (HU-13s, v1.1).
- Metricas de flujo (HU-14c, futuro).
- Sincronizacion bidireccional (HU-15c, futuro).
- Gestion de stakeholders (HU-16c, futuro).
- Gestion de disponibilidad y capacidad del equipo (descartado).

---

## 7. Configuracion del entorno -- .env.example

El fichero `.env.example` del proyecto debe contener las siguientes variables (sin valores reales):

```
# Credenciales de Trello
# Se configuran automaticamente mediante el asistente de onboarding del plugin
# Para obtenerlas manualmente: https://trello.com/power-ups/admin

# API Key: identifica la aplicacion (32 caracteres hexadecimales)
TRELLO_API_KEY=

# Token: autoriza al plugin a actuar en nombre del usuario
# Se genera en: https://trello.com/1/authorize?expiration=30days&name=PSPO+Agent&scope=read,write&response_type=token&key=TU_API_KEY
TRELLO_TOKEN=

# ID del tablero de Trello donde se publican las historias
# Se configura automaticamente durante el onboarding
TRELLO_BOARD_ID=
```

**Nota importante:** El campo `TRELLO_API_SECRET` se ha eliminado. No es necesario para el MVP. La autenticacion funciona exclusivamente con API Key + Token manual.

---

## 8. Persistencia -- Ficheros del equipo y distribucion

Ademas de los artefactos de producto (docs/), el MVP genera los siguientes ficheros de equipo y distribucion:

| Fichero | Contenido | Formato | Creado por |
|---------|-----------|---------|-----------|
| `team.csv` (por defecto) o cualquier CSV de equipo compatible | Miembros del equipo | CSV con cabecera: nombre,email,rol,categoria,dedicacion,usa_agente_ia | HU-07 (gestion de equipo) |
| `docs/asignaciones.md` | Mapeo historia -> miembro con tabla y resumen de carga | Markdown | HU-08 (distribucion) |
| `docs/dependencias.md` | Grafo de dependencias (Mermaid), tabla de relaciones, bloqueantes | Markdown | HU-09 (dependencias) |

### Ejemplo de CSV de equipo compatible

```csv
nombre,email,rol,categoria,dedicacion,usa_agente_ia
Ana Garcia,ana@equipo.com,Frontend,Senior,100,si
Carlos Lopez,carlos@equipo.com,Backend,Junior,100,no
Maria Ruiz,maria@equipo.com,QA,Mid,50,si
```

### Ejemplo de docs/asignaciones.md

```markdown
# Asignaciones de historias

Fecha: 2026-03-13

| Historia | Responsable | Email | Rol | Horas | Estado |
|----------|-------------|-------|-----|-------|--------|
| HU-01: Onboarding guiado | Carlos Lopez | carlos@equipo.com | Backend | 4 h | Pendiente |
| HU-02: Descubrimiento | Ana Garcia | ana@equipo.com | Frontend | 2 h | Pendiente |
| HU-03: Generacion de HU | Carlos Lopez | carlos@equipo.com | Backend | 6 h | Pendiente |

## Carga por miembro

| Miembro | Horas efectivas asignadas |
|---------|--------------------------|
| Carlos Lopez | 10 h |
| Ana Garcia | 2 h |
| Maria Ruiz | 0 h |
```

### Ejemplo de docs/dependencias.md

```markdown
# Mapa de dependencias

Fecha: 2026-03-13

## Grafo

(diagrama Mermaid aqui)

## Dependencias confirmadas

| Historia | Depende de | Tipo | Confirmada |
|----------|-----------|------|-----------|
| HU-03 | HU-01 | Tecnica | Si |
| HU-05 | HU-03 | De datos | Si |

## Bloqueantes (ordenados por impacto)

1. HU-01 -- Bloquea: HU-03, HU-05 (2 historias afectadas)
```

---

## 9. Metricas de exito

| Metrica | Objetivo MVP | Como se mide |
|---------|-------------|--------------|
| Tiempo de onboarding completo | < 5 minutos | Desde la primera ejecucion hasta tener credenciales verificadas y tablero configurado |
| Tasa de completitud del onboarding | > 90% | Porcentaje de usuarios que inician el asistente y lo completan sin abandonar |
| Calidad de historias | 100% con formato correcto | Todas las historias tienen rol especifico, accion concreta, beneficio medible y criterios Given/When/Then |
| Tasa de aprobacion a la primera | > 70% | Porcentaje de historias que el usuario aprueba sin pedir cambios |
| Tiempo de descubrimiento a publicacion | < 30 minutos | Desde que el usuario describe la necesidad hasta que las tarjetas estan en Trello |
| Tarjetas sin retrabajo | > 80% | Porcentaje de tarjetas que no se modifican despues de publicarse en Trello |
| Tiempo de definicion de equipo | < 3 minutos | Desde que el usuario inicia la gestion de equipo hasta que el CSV compatible queda guardado (para equipos de hasta 5 miembros) |
| Tasa de aceptacion de distribucion sugerida | > 60% | Porcentaje de asignaciones propuestas por el PSPO que el usuario acepta sin modificar |
| Dependencias detectadas correctamente | > 80% | Porcentaje de dependencias reales que el PSPO identifica automaticamente (confirmadas por el usuario) |
| Bloqueos evitados | Cualitativa | El usuario reporta que se evito al menos un bloqueo por sprint gracias al mapa de dependencias |
| Tasa de vinculacion Trello del equipo | > 70% | Porcentaje de miembros del equipo que se vinculan correctamente con sus cuentas de Trello |

---

## 10. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| **Limites de la API de Trello** (rate limiting, cambios en endpoints) | Media | Alto | Implementar retry con backoff exponencial. Guardar siempre local antes de publicar. Usar la API REST estable, no experimental |
| **Calidad del descubrimiento depende del LLM** (preguntas irrelevantes o genericas) | Media | Alto | Disenar prompts de descubrimiento con estructura fija. Incluir ejemplos de preguntas buenas y malas. Permitir al usuario saltar preguntas irrelevantes |
| **Resistencia del usuario al descubrimiento** ("solo dame las historias") | Alta | Medio | Hacer el descubrimiento breve (3-5 preguntas). Mostrar el valor con un ejemplo antes/despues. Permitir modo rapido para usuarios experimentados |
| **Credenciales de Trello comprometidas** (leak del .env) | Baja | Critico | .env siempre en .gitignore. Verificacion automatica en cada sesion. .env.example como plantilla sin valores reales |
| **Desalineacion entre doc local y Trello** (ediciones manuales en Trello) | Alta | Medio | En MVP, la sincronizacion es unidireccional (local -> Trello). Avisar al usuario de esta limitacion. La bidireccional queda para futuro (HU-15c) |
| **Dependencia del ecosistema de Claude Code** (cambios en el sistema de skills/plugins) | Baja | Alto | Seguir las convenciones oficiales del formato SKILL.md. Minimizar el acoplamiento con APIs internas no documentadas |
| **Abandono durante el onboarding** (usuario se pierde o se frustra) | Media | Alto | Cada paso del asistente es explicativo y reversible. Si el usuario cierra el terminal, el progreso parcial se guarda. El asistente retoma desde donde se quedo |
| **Cambios en la pagina de Power-Ups de Trello** (la URL o el flujo para obtener la API Key cambia) | Baja | Medio | Las instrucciones del onboarding se mantienen en un fichero separado facil de actualizar. El plugin valida el formato de la Key para detectar problemas temprano |
| **Deteccion incorrecta de dependencias** (falsos positivos/negativos del LLM) | Alta | Medio | TODAS las dependencias detectadas son sugerencias que requieren confirmacion del usuario. El PSPO indica el nivel de confianza de cada deteccion. Las dependencias no confirmadas NO se tratan como bloqueantes |
| **Miembros del equipo no vinculados en Trello** (emails no coinciden con cuentas de Trello) | Media | Medio | El plugin busca por email. Si no encuentra coincidencia, ofrece alternativas (nota en tarjeta, invitacion). Las asignaciones locales en docs/asignaciones.md siempre funcionan aunque Trello no las refleje |
| **Equipo cambia con frecuencia** (altas y bajas frecuentes) | Media | Bajo | El CSV de equipo compatible es editable manualmente. El plugin permite modificar el equipo en cualquier momento. Las asignaciones de historias ya distribuidas no se pierden si un miembro sale |
| **Dependencias circulares** (A depende de B, B depende de A) | Baja | Alto | El PSPO detecta ciclos en el grafo de dependencias y los senala como error critico. No permite confirmar mapas con ciclos. El usuario debe reformular las historias para romper la circularidad |

---

## 11. Dependencias

| Dependencia | Tipo | Estado |
|-------------|------|--------|
| API REST de Trello (v1) | Externa | Disponible, documentada, estable |
| API de Trello: miembros del tablero (`/1/boards/{id}/members`) | Externa | Disponible. Necesaria para vincular miembros del equipo con cuentas de Trello (HU-10) |
| API de Trello: asignacion de miembros a tarjetas (`/1/cards/{id}/idMembers`) | Externa | Disponible. Necesaria para HU-10 |
| API de Trello: checklists (`/1/checklists`) | Externa | Disponible. Necesaria para dependencias en tarjetas (HU-10) |
| API de Trello: invitacion de miembros (`PUT /1/boards/{id}/members/{email}`) | Externa | Disponible. Necesaria para invitar miembros al tablero (HU-10) |
| Sistema de skills de Claude Code | Plataforma | Disponible, en evolucion activa |
| Pagina de administracion de Power-Ups de Trello | Externa | Disponible en https://trello.com/power-ups/admin |
| Navegador del usuario | Entorno | Necesario para crear el Power-Up y autorizar el token (dos interacciones puntuales durante el onboarding) |
| Capacidad de analisis del LLM para detectar dependencias | Plataforma | Las dependencias se detectan por inferencia del contenido de las historias. La calidad depende del modelo y de los prompts |

---

## 12. Fuera de alcance (explicito)

- **No se gestiona la ejecucion del sprint.** El plugin crea el backlog y distribuye historias, no gestiona el flujo diario.
- **No se sustituye al criterio tecnico del equipo.** El plugin propone estimaciones iniciales en horas efectivas con agentes, pero el equipo puede corregirlas.
- **No se integra con otras herramientas** mas alla de Trello en el MVP.
- **No se genera codigo.** El plugin es de producto, no de desarrollo.
- **No se reemplazan ceremonias de Scrum.** El plugin asiste con artefactos, no facilita reuniones.
- **No se implementa OAuth 1.0 de servidor.** La autenticacion es manual (API Key + Token). Suficiente para un plugin local.
- **No se integra con calendarios, vacaciones ni festivos externos.** La capacidad se calcula con la dedicacion declarada en el CSV del equipo.
- **No se hace seguimiento en tiempo real del progreso.** El mapa de dependencias es una foto del momento. No hay polling continuo a Trello.
- **No se crean columnas por sprint futuro en Trello.** Solo existe un sprint activo en el tablero; la planificacion futura se mantiene en documentacion local.

---

## 13. Glosario

| Termino | Definicion |
|---------|-----------|
| **PSPO** | Professional Scrum Product Owner, certificacion de Scrum.org en tres niveles |
| **Historia de usuario** | Descripcion de una funcionalidad desde la perspectiva del usuario, formato "Como X quiero Y para Z" |
| **Criterio de aceptacion** | Condicion verificable que debe cumplirse para que una historia se considere completada |
| **Definition of Done (DoD)** | Lista de criterios que todo incremento debe cumplir antes de considerarse terminado |
| **Backlog** | Lista priorizada de todo el trabajo pendiente del producto |
| **Descubrimiento** | Fase de preguntas y analisis para entender el problema antes de proponer soluciones |
| **MoSCoW** | Metodo de priorizacion: Must, Should, Could, Won't |
| **Onboarding** | Proceso de primera configuracion guiada que lleva al usuario desde la instalacion hasta el uso efectivo del producto |
| **API Key** | Clave que identifica la aplicacion ante la API de Trello. Se obtiene al crear un Power-Up |
| **Token** | Credencial que autoriza al plugin a actuar en nombre del usuario en Trello. Se genera visitando una URL de autorizacion |
| **Power-Up** | Extension o aplicacion registrada en Trello. Necesaria para obtener una API Key |
| **Dependencia (entre historias)** | Relacion en la que una historia necesita que otra este completada antes de poder empezar. Puede ser tecnica, de datos o de UX |
| **Bloqueante** | Historia de la que dependen otras. Si se retrasa, las historias dependientes no pueden avanzar |
| **Grafo de dependencias** | Representacion visual de las relaciones de dependencia entre historias, donde cada historia es un nodo y cada dependencia es una flecha |
| **Radio de impacto** | Numero total de historias y miembros afectados si una historia especifica se retrasa |
| **Distribucion de historias** | Asignacion de historias de usuario a miembros del equipo basada en el rol de cada miembro y el tipo de trabajo de cada historia |
| **CSV de equipo compatible** | Fichero CSV que contiene la definicion del equipo del proyecto. Puede llamarse como quiera el usuario si mantiene la cabecera `nombre,email,rol,categoria,dedicacion,usa_agente_ia` |

---

**Estado del documento: EN REVISION v1.2 -- Actualizado el 2026-03-15.**

**Cambios respecto a v1.0:**
- Nuevo problema (5) en la seccion 1: distribucion de trabajo sin criterio ni visibilidad.
- Ampliada la persona secundaria (Carlos) con dolor y comportamiento especificos de coordinacion de equipo.
- Anadido paso [6] equipo, [7] distribucion y [8] sincronizacion al flujo principal.
- Nuevo principio de diseno: "El usuario manda en la distribucion".
- Nuevas historias MUST para el MVP:
  - HU-07: Gestion de equipo del proyecto (definir, importar CSV, plantilla, alta guiada).
  - HU-08: Distribucion inteligente de historias al equipo (sugerencia por rol, equilibrio de carga).
  - HU-09: Mapa de dependencias y bloqueantes (deteccion, confirmacion, grafo, impacto).
  - HU-10: Integracion de asignaciones y dependencias con Trello (miembros, checklists, etiquetas).
- Renumeracion de historias SHOULD: HU-07 -> HU-11s, HU-08 -> HU-12s, HU-09 -> HU-13s.
- Renumeracion de historias COULD: HU-10 -> HU-14c, HU-11 -> HU-15c, HU-12 -> HU-16c.
- Alcance del MVP ampliado con puntos 8, 9, 10 y 11.
- Nueva seccion 8: persistencia de ficheros de equipo y distribucion (CSV de equipo compatible, asignaciones.md, dependencias.md).
- Cinco nuevas metricas de exito para las funcionalidades de equipo.
- Cuatro nuevos riesgos: deteccion incorrecta de dependencias, miembros no vinculados en Trello, equipo que cambia, dependencias circulares.
- Nuevas dependencias de API de Trello: miembros del tablero, asignacion a tarjetas, checklists.
- Tres nuevas exclusiones de alcance: gestion de disponibilidad, seguimiento en tiempo real, sprints multiples.
- Nuevo item en WON'T: gestion de disponibilidad y capacidad del equipo.
- Glosario ampliado con 6 terminos nuevos.
- URLs nuevas de la API de Trello en la seccion de contexto.

**Cambios respecto a v1.1:**
- El flujo principal refleja ya el recorrido real: equipo -> asignacion -> dependencias -> sprint -> publicacion.
- El onboarding y la publicacion usan listas estables en Trello: `Backlog`, `Sprint activo`, `Bloqueada`, `En progreso`, `En revision`, `Hecho`.
- La gestion de equipo pasa de `team.csv` rigido a **CSV de equipo compatible** con 6 columnas y nombre libre.
- La publicacion en Trello queda descrita como resumen corto + adjunto `.md` + checklists + sync incremental.
- La estimacion de sprint se define en horas efectivas con agentes y sprints de hasta 5 dias laborables.
- El alcance fuera de scope se alinea con el producto actual: sin calendarios externos ni columnas por sprint futuro.

*Este PRD ha sido generado por El Buscador de Problemas (PO del equipo Alfred Dev). Ninguna historia se mueve a arquitectura ni desarrollo sin aprobacion explicita.*
