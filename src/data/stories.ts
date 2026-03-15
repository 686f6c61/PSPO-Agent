/**
 * Historias de usuario del plugin PSPO Agent.
 *
 * Son los requisitos del propio plugin, escritos con la misma metodologia
 * que el plugin aplica a los proyectos de sus usuarios. Sirven como ejemplo
 * en la seccion Stories de la web.
 *
 * Cada UserStory sigue el formato "Como [rol], quiero [accion], para [beneficio]"
 * con escenarios Given/When/Then, prioridad MoSCoW y estado de version.
 *
 * Para anadir una historia: agregar un objeto a stories[] con un id unico
 * (HU-XX), completar todos los campos obligatorios y al menos un escenario.
 */
export interface Scenario {
  name: string;
  given: string;
  when: string;
  then: string[];
}

export interface UserStory {
  id: string;
  title: string;
  role: string;
  action: string;
  benefit: string;
  context?: string;
  scenarios: Scenario[];
  priority: 'must' | 'should' | 'could';
  status: 'mvp' | 'v1.1' | 'futuro';
}

export const stories: UserStory[] = [
  {
    id: 'HU-00',
    title: 'Visión de producto',
    role: 'desarrollador que empieza un proyecto nuevo',
    action:
      'definir la filosofía y el norte del producto en 2-3 frases antes de generar ninguna historia',
    benefit:
      'que todas las historias de usuario estén alineadas con una visión común y que las decisiones de producto tengan un criterio compartido',
    context:
      'La visión se pide una sola vez, al inicio del primer flujo de descubrimiento o análisis. Se guarda en docs/vision.md y se usa como contexto en toda la generación posterior. No son requisitos, es la filosofía: por qué existe este producto, qué lo hace diferente y cuál es el norte.',
    scenarios: [
      {
        name: 'Solicitud de visión en el primer uso',
        given: 'el usuario ejecuta el flujo de descubrimiento o análisis por primera vez y no existe docs/vision.md',
        when: 'el plugin detecta que falta la visión',
        then: [
          'muestra un mensaje explicando qué es la visión y por qué importa, con un ejemplo concreto',
          'pide al usuario que describa la visión de su producto en 2-3 frases',
          'no avanza al descubrimiento ni al análisis hasta que el usuario responda',
        ],
      },
      {
        name: 'Persistencia en docs/vision.md',
        given: 'el usuario ha escrito la visión de su producto',
        when: 'el plugin la guarda',
        then: [
          'crea el directorio docs/ si no existe',
          'escribe docs/vision.md con la visión del usuario en formato blockquote, fecha de última actualización y firma de PSPO Agent',
          'en sesiones futuras, detecta que docs/vision.md ya existe y no vuelve a preguntar',
        ],
      },
      {
        name: 'Uso como contexto en generación de historias',
        given: 'docs/vision.md existe y el agente product-owner va a generar historias de usuario',
        when: 'el agente lee el contexto del proyecto antes de generar',
        then: [
          'incluye la visión como contexto de alto nivel para alinear las historias',
          'si una historia generada contradice la visión, el agente lo señala al usuario antes de presentarla',
          'la visión aparece referenciada en docs/backlog.md como contexto del conjunto de historias',
        ],
      },
    ],
    priority: 'must',
    status: 'mvp',
  },
  {
    id: 'HU-01',
    title: 'Onboarding guiado de primera ejecución',
    role: 'desarrollador que instala el plugin por primera vez',
    action:
      'que el plugin detecte que no hay configuración y me guíe paso a paso para obtener las credenciales de Trello y configurar mi tablero',
    benefit:
      'poder empezar a usar el plugin sin necesitar conocimientos previos sobre la API de Trello',
    context:
      'El usuario no sabe qué es una API Key, ni dónde se obtiene, ni cómo generar un token. El plugin debe llevarle de la mano por cada paso.',
    scenarios: [
      {
        name: 'Detección automática de primera ejecución',
        given: 'el plugin está instalado y no existe un fichero .env con las variables TRELLO_API_KEY y TRELLO_TOKEN',
        when: 'el usuario ejecuta cualquier comando del plugin',
        then: [
          'el plugin detecta que falta la configuración',
          'arranca automáticamente el asistente de onboarding',
          'muestra un mensaje de bienvenida explicando que va a guiarle paso a paso',
        ],
      },
      {
        name: 'Paso 1 -- Obtener la API Key',
        given: 'el asistente de onboarding está en ejecución',
        when: 'llega al paso de obtener la API Key',
        then: [
          'explica al usuario que necesita crear un Power-Up en Trello',
          'le indica que visite https://trello.com/power-ups/admin',
          'le pide que pegue la API Key en el terminal',
          'valida que el formato es correcto (32 caracteres hexadecimales)',
        ],
      },
      {
        name: 'Verificación de credenciales',
        given: 'el usuario ha proporcionado la API Key y el token',
        when: 'el plugin verifica la conexión',
        then: [
          'hace una llamada a GET /1/members/me con las credenciales',
          'si la respuesta es exitosa, muestra el nombre del usuario de Trello',
          'si la respuesta es un error, identifica cuál credencial es incorrecta',
          'NO almacena las credenciales inválidas',
        ],
      },
    ],
    priority: 'must',
    status: 'mvp',
  },
  {
    id: 'HU-01b',
    title: 'Configuración guiada del tablero de Trello',
    role: 'desarrollador que acaba de conectar sus credenciales de Trello',
    action:
      'elegir o crear un tablero y configurar sus columnas y etiquetas',
    benefit:
      'tener el tablero listo para recibir historias de usuario sin configuración manual',
    context:
      'Después de las credenciales, el usuario necesita un tablero donde publicar las historias. La configuración del tablero debe ser parte del onboarding.',
    scenarios: [
      {
        name: 'Selección de tablero',
        given: 'las credenciales de Trello están verificadas y no hay TRELLO_BOARD_ID configurado',
        when: 'el asistente llega al paso de configuración del tablero',
        then: [
          'consulta los tableros del usuario vía la API de Trello',
          'muestra la lista de tableros disponibles',
          'ofrece seleccionar un tablero existente o crear uno nuevo',
        ],
      },
      {
        name: 'Crear tablero nuevo',
        given: 'el usuario elige crear un tablero nuevo',
        when: 'introduce el nombre del tablero',
        then: [
          'crea el tablero con columnas: Backlog, Sprint activo, Bloqueada, En progreso, En revision, Hecho',
          'crea etiquetas de prioridad: Crítica (rojo), Alta (naranja), Media (amarillo), Baja (azul)',
          'guarda el TRELLO_BOARD_ID en .env',
          'muestra la URL del tablero creado',
        ],
      },
    ],
    priority: 'must',
    status: 'mvp',
  },
  {
    id: 'HU-02',
    title: 'Descubrimiento de producto mediante conversación',
    role: 'desarrollador con una idea de producto',
    action:
      'que el agente me haga preguntas de descubrimiento antes de generar nada',
    benefit:
      'asegurarme de que el problema está bien definido antes de escribir una sola línea de código',
    scenarios: [
      {
        name: 'Inicio del descubrimiento',
        given: 'el usuario activa el plugin y describe una necesidad en lenguaje natural',
        when: 'el agente recibe la descripción',
        then: [
          'NO genera historias de usuario inmediatamente',
          'formula al menos 3 preguntas de descubrimiento',
          'pregunta sobre el usuario final, el problema actual, las restricciones y el resultado esperado',
        ],
      },
      {
        name: 'Iteración en descubrimiento',
        given: 'el agente ha formulado preguntas y el usuario las ha respondido',
        when: 'las respuestas revelan ambigüedades o contradicciones',
        then: [
          'hace preguntas de seguimiento para clarificar',
          'no avanza a la generación hasta que el alcance esté definido',
        ],
      },
      {
        name: 'Descripción suficientemente detallada',
        given: 'el usuario proporciona una descripción con usuario, problema, contexto y restricciones',
        when: 'el agente analiza la descripción',
        then: [
          'puede reducir el número de preguntas de descubrimiento',
          'confirma con el usuario los puntos clave antes de avanzar',
        ],
      },
    ],
    priority: 'must',
    status: 'mvp',
  },
  {
    id: 'HU-03',
    title: 'Generación de historias de usuario con criterios de aceptación',
    role: 'desarrollador que ha completado el descubrimiento',
    action:
      'recibir historias de usuario bien formadas con criterios de aceptación',
    benefit:
      'tener una guía clara de qué construir y cómo verificar que está bien hecho',
    scenarios: [
      {
        name: 'Formato correcto de historias',
        given: 'el descubrimiento está completo y el alcance está definido',
        when: 'el agente genera las historias de usuario',
        then: [
          'cada historia sigue el formato "Como [rol específico], quiero [acción concreta], para [beneficio medible]"',
          'el rol nunca es genérico ("usuario"), siempre es específico',
          'cada historia es independiente y se puede entregar por separado',
          'las historias están ordenadas por prioridad de valor',
        ],
      },
      {
        name: 'Criterios de aceptación completos',
        given: 'el agente ha generado una historia de usuario',
        when: 'presenta los criterios de aceptación',
        then: [
          'cada criterio usa formato Given/When/Then',
          'incluye al menos un escenario positivo (happy path)',
          'incluye al menos un escenario negativo (error, entrada inválida)',
          'los valores son concretos, no genéricos',
        ],
      },
      {
        name: 'Tamaño manejable',
        given: 'el agente genera historias de usuario',
        when: 'una historia es demasiado grande (más de 16 horas efectivas de trabajo)',
        then: [
          'la descompone en historias más pequeñas',
          'explica cómo se relacionan entre sí',
        ],
      },
    ],
    priority: 'must',
    status: 'mvp',
  },
  {
    id: 'HU-04',
    title: 'Validación y aprobación de artefactos',
    role: 'desarrollador que recibe los artefactos generados',
    action:
      'revisar y aprobar cada artefacto antes de que se publique en Trello',
    benefit:
      'mantener el control sobre lo que se gestiona en mi tablero',
    scenarios: [
      {
        name: 'Presentación para revisión',
        given: 'el agente ha generado las historias de usuario y criterios',
        when: 'presenta los artefactos al usuario',
        then: [
          'muestra un resumen estructurado con todas las historias',
          'permite aprobar, rechazar o pedir cambios en cada historia individualmente',
        ],
      },
      {
        name: 'Aprobación parcial',
        given: 'el usuario aprueba algunas historias pero no todas',
        when: 'confirma la selección',
        then: [
          'solo las historias aprobadas se marcan como listas para publicar',
          'las historias pendientes quedan en estado de revisión',
        ],
      },
    ],
    priority: 'must',
    status: 'mvp',
  },
  {
    id: 'HU-05',
    title: 'Creación y gestión del tablero de Trello',
    role: 'desarrollador que ha aprobado las historias',
    action:
      'que el plugin publique las historias como tarjetas en el tablero de Trello configurado',
    benefit:
      'tener la gestión visual del backlog sin trabajo manual',
    scenarios: [
      {
        name: 'Publicación en tablero existente',
        given: 'el usuario tiene un tablero configurado y las historias están aprobadas',
        when: 'confirma la publicación en Trello',
        then: [
          'publica cada historia como una tarjeta en la columna Backlog',
          'NO duplica tarjetas que ya existan (comparación por título)',
        ],
      },
      {
        name: 'Formato de tarjetas',
        given: 'el plugin crea una tarjeta en Trello',
        when: 'la tarjeta se publica',
        then: [
          'el título es la historia en formato corto',
          'la descripción incluye la historia completa y los criterios Given/When/Then',
          'la tarjeta tiene la etiqueta de prioridad correspondiente',
        ],
      },
      {
        name: 'Vista previa antes de publicar',
        given: 'las historias están aprobadas y listas para publicar',
        when: 'el usuario da la orden de publicar',
        then: [
          'muestra una vista previa de las tarjetas a crear',
          'pide confirmación final antes de ejecutar',
        ],
      },
    ],
    priority: 'must',
    status: 'mvp',
  },
  {
    id: 'HU-06',
    title: 'Generación de documentación de producto local',
    role: 'desarrollador que trabaja en el proyecto',
    action:
      'que los artefactos de producto se guarden como ficheros en el repositorio',
    benefit:
      'tener la documentación versionada junto al código',
    scenarios: [
      {
        name: 'Estructura de ficheros',
        given: 'el agente ha generado y el usuario ha aprobado los artefactos',
        when: 'se guardan en el sistema de ficheros',
        then: [
          'crea docs/vision.md con la visión de producto',
          'crea docs/historias/HU-XX-titulo.md para cada historia',
          'crea docs/backlog.md con la lista priorizada',
          'cada fichero usa formato Markdown limpio y legible',
        ],
      },
    ],
    priority: 'must',
    status: 'mvp',
  },
  {
    id: 'HU-07',
    title: 'Gestión de equipo del proyecto',
    role: 'tech lead de un equipo pequeño sin PO dedicado',
    action:
      'definir los miembros de mi equipo con sus roles, dedicación y uso de agentes IA dentro del plugin',
    benefit:
      'que el PSPO tenga la información necesaria para calcular la capacidad real del sprint y distribuir historias de forma inteligente',
    context:
      'El tech lead necesita poder definir el equipo rápidamente: importar CSV o añadir miembros uno a uno. Los roles son libres. La categoría (Junior, Mid, Senior), la dedicación y el uso de agente IA son cruciales para la planificación de sprint.',
    scenarios: [
      {
        name: 'Detección de equipo no definido',
        given: 'el usuario tiene historias aprobadas y no existe ningún CSV de equipo compatible en la raíz del proyecto ni en .pspo-agent/inbox',
        when: 'solicita planificar un sprint o distribuir historias al equipo',
        then: [
          'detecta que no hay equipo definido',
          'ofrece dos opciones: modo guiado (pregunta miembro a miembro) o importar desde CSV',
        ],
      },
      {
        name: 'Alta guiada de miembros',
        given: 'el usuario elige añadir miembros de forma guiada',
        when: 'el plugin inicia el asistente para cada miembro',
        then: [
          'pregunta en secuencia: nombre, email, rol (texto libre), categoría (Junior/Mid/Senior), dedicación (0-100%) y si usa agente de IA (sí/no)',
          'si el miembro usa agente IA, informa del factor de corrección del 65% configurable en settings.json',
          'tras cada miembro muestra un resumen y pregunta si quiere añadir otro',
        ],
      },
      {
        name: 'Persistencia del equipo con 6 campos',
        given: 'el usuario ha confirmado la composición del equipo',
        when: 'el plugin guarda los datos',
        then: [
          'escribe o actualiza un CSV compatible con cabecera de 6 campos: nombre,email,rol,categoria,dedicacion,usa_agente_ia',
          'valida el email (contiene @ y punto), la dedicación (entre 0 y 100) y usa_agente_ia (solo sí o no)',
          'en futuras sesiones, lee ese CSV automáticamente y muestra el equipo con opciones de editar, añadir o eliminar',
        ],
      },
    ],
    priority: 'must',
    status: 'mvp',
  },
  {
    id: 'HU-08',
    title: 'Distribución inteligente de historias al equipo',
    role: 'tech lead que tiene historias aprobadas y un equipo definido',
    action:
      'que el PSPO estime las historias por tallas (XS/S/M/L/XL), calcule la capacidad del equipo en horas efectivas con factor IA y sugiera una distribución equilibrada',
    benefit:
      'no tener que repartir el trabajo a ojo y saber si el sprint es viable antes de empezar',
    context:
      'El tech lead pierde tiempo decidiendo quién hace cada historia y si cabe en un sprint de una semana. El PSPO calcula la capacidad equivalente del equipo con foco real y factor de corrección del 65% para quienes usan agentes IA, y cruza ese dato con estimaciones por tallas.',
    scenarios: [
      {
        name: 'Estimación por tallas con conversión configurable',
        given: 'hay historias aprobadas en docs/historias/ y el usuario ejecuta la planificación de sprint',
        when: 'el agente presenta las historias para estimar',
        then: [
          'muestra la tabla de conversión configurable en settings.json: XS=1 h, S=2 h, M=4 h, L=8 h, XL=16 h',
          'permite asignar tallas en formato rápido (ej: "1=M 2=XL 3=S")',
          'recalcula el total en horas efectivas tras cada ajuste y espera confirmación explícita',
        ],
      },
      {
        name: 'Propuesta de distribución basada en roles y factor IA',
        given: 'las historias están estimadas y el equipo está definido en un CSV compatible con dedicación y usa_agente_ia',
        when: 'el PSPO calcula la capacidad del equipo para el sprint',
        then: [
          'calcula horas reales de foco por miembro según duración del sprint, dedicación y horas de foco por día',
          'aplica el factor IA a los miembros que usan agente: capacidad_equiv = horas_reales / (1 - factor_ia)',
          'compara el total de historias contra la capacidad equivalente y muestra el porcentaje de ocupación',
          'si el sprint desborda, sugiere recortar las historias de menor prioridad o puntuación',
        ],
      },
      {
        name: 'Aprobación del usuario sobre la distribución',
        given: 'el PSPO presenta la propuesta completa con tabla de capacidad y veredicto',
        when: 'el usuario la revisa',
        then: [
          'puede aprobar la distribución tal como está',
          'puede modificar asignaciones individuales o ajustar tallas',
          'puede rechazar y pedir nuevo análisis con criterios distintos',
        ],
      },
    ],
    priority: 'must',
    status: 'mvp',
  },
  {
    id: 'HU-09',
    title: 'Mapa de dependencias y bloqueantes',
    role: 'tech lead que coordina el trabajo de un equipo pequeño',
    action:
      'que el PSPO identifique dependencias y bloqueantes entre historias como parte de la priorización asistida del sprint',
    benefit:
      'saber en qué orden deben ejecutarse las historias y que las bloqueantes se prioricen automáticamente',
    context:
      'Las dependencias son invisibles hasta que alguien se bloquea. El agente sprint-planner analiza las historias y clasifica cada una como Bloqueante, Dependiente o Independiente. Esto alimenta la fórmula de priorización: Valor*3 + Riesgo*2 + Dependencia*1.',
    scenarios: [
      {
        name: 'Análisis automático de dependencias en la priorización',
        given: 'hay al menos 3 historias aprobadas y el usuario acepta la priorización asistida durante la planificación de sprint',
        when: 'el agente sprint-planner analiza cada historia',
        then: [
          'clasifica cada historia como Bloqueante (otras dependen de ella, peso 3), Independiente (sin relaciones, peso 2) o Dependiente (necesita que otra se complete, peso 1)',
          'integra la clasificación en la matriz de priorización junto con Valor de negocio y Riesgo técnico',
          'las historias bloqueantes suben automáticamente en la puntuación final',
        ],
      },
      {
        name: 'Visualización del grafo de dependencias',
        given: 'la priorización asistida está confirmada por el usuario',
        when: 'el plugin guarda la planificación del sprint en docs/sprint-plan.md',
        then: [
          'genera un diagrama Mermaid en docs/dependencias.md con cada historia como nodo',
          'las flechas indican la dirección de dependencia (A bloquea a B)',
          'las historias bloqueantes se resaltan visualmente y aparecen primero en el orden del sprint',
        ],
      },
      {
        name: 'Análisis de impacto de retrasos',
        given: 'el mapa está confirmado y las historias están asignadas a miembros del equipo',
        when: 'el usuario pregunta qué pasa si una historia concreta se retrasa',
        then: [
          'recorre la cadena de dependencias hacia abajo desde esa historia',
          'muestra las historias afectadas directa e indirectamente con sus asignaciones',
          'calcula el radio de impacto total en horas efectivas de trabajo bloqueado',
        ],
      },
    ],
    priority: 'must',
    status: 'mvp',
  },
  {
    id: 'HU-10',
    title: 'Integración de asignaciones y dependencias con Trello',
    role: 'tech lead que gestiona su equipo a través de Trello',
    action:
      'que las historias se publiquen con ficheros .md adjuntos, checklists de Definition of Done y asignaciones de miembros',
    benefit:
      'que todo el equipo vea quién hace qué, qué criterios debe cumplir y tenga la historia completa sin salir de Trello',
    context:
      'El plugin publica cada tarjeta con una descripción resumida, adjunta el fichero .md completo como documento de referencia, añade un checklist con los criterios de la DoD y asigna miembros por email. Las dependencias se reflejan como checklist adicional.',
    scenarios: [
      {
        name: 'Publicación con fichero adjunto y checklist DoD',
        given: 'las historias están aprobadas, la DoD está configurada en docs/dod.md y el usuario confirma la publicación',
        when: 'el plugin crea cada tarjeta en Trello',
        then: [
          'crea la tarjeta con descripción resumida (historia + criterios + prioridad + estimación)',
          'adjunta el fichero HU-XX-titulo.md completo como archivo adjunto usando attach-file',
          'añade un checklist "Definition of Done" con los criterios de docs/dod.md usando add-checklist',
          'la descripción termina con "Historia completa en el fichero adjunto"',
        ],
      },
      {
        name: 'Asignación de miembros a tarjetas',
        given: 'las historias están publicadas y las asignaciones del sprint están aprobadas',
        when: 'el plugin sincroniza con Trello',
        then: [
          'busca cada miembro asignado por email en los miembros del tablero',
          'si existe, lo asigna a la tarjeta correspondiente',
          'si no existe en el tablero, lo invita por email y reutiliza el memberId devuelto antes de dar la sincronización por completada',
        ],
      },
      {
        name: 'Checklists de dependencias',
        given: 'el mapa de dependencias está confirmado y las tarjetas existen en Trello',
        when: 'el plugin sincroniza las dependencias',
        then: [
          'crea un checklist "Dependencias" en cada tarjeta afectada',
          'cada ítem es un enlace a la tarjeta de la que depende (formato: "HU-XX: título - url")',
          'muestra vista previa completa de los cambios y pide confirmación explícita antes de ejecutar',
        ],
      },
    ],
    priority: 'must',
    status: 'mvp',
  },
  {
    id: 'HU-11s',
    title: 'Definition of Done configurable',
    role: 'tech lead de un equipo pequeño',
    action:
      'definir una Definition of Done para el proyecto',
    benefit:
      'que todas las historias tengan un estándar mínimo de calidad verificable',
    scenarios: [
      {
        name: 'DoD por defecto',
        given: 'el usuario no ha configurado una DoD personalizada',
        when: 'el agente genera historias',
        then: [
          'aplica una DoD por defecto: criterios cumplidos, código revisado, tests pasando, documentación actualizada',
        ],
      },
    ],
    priority: 'should',
    status: 'v1.1',
  },
  {
    id: 'HU-12s',
    title: 'Priorización asistida por valor',
    role: 'desarrollador con muchas historias en el backlog',
    action:
      'que el agente me ayude a priorizar por valor de negocio',
    benefit:
      'trabajar primero en lo que más impacto tiene',
    scenarios: [
      {
        name: 'Sugerencia de priorización',
        given: 'hay más de 5 historias en el backlog sin priorizar',
        when: 'el usuario pide ayuda para priorizar',
        then: [
          'pregunta por criterios de valor (impacto, esfuerzo, riesgo)',
          'sugiere un orden con justificación para cada historia',
          'el usuario tiene la última palabra sobre el orden final',
        ],
      },
    ],
    priority: 'should',
    status: 'v1.1',
  },
  {
    id: 'HU-13',
    title: 'Análisis de requisitos desde documento',
    role: 'desarrollador que recibe un brief, email o especificación como punto de partida',
    action:
      'pegar el documento y que el agente requirement-analyst lo analice mediante preguntas priorizadas hasta alcanzar un 80% de claridad',
    benefit:
      'no empezar a generar historias de usuario sin haber entendido bien los requisitos, evitando sprints de trabajo basura por ambigüedades',
    context:
      'El agente requirement-analyst sustituye al flujo de descubrimiento cuando el usuario aporta un documento de partida. Evalúa 8 categorías de claridad (usuario final, problema, contexto de negocio, alcance, restricciones técnicas, criterios de éxito, dependencias, fuera de alcance) y hace preguntas una a una hasta alcanzar el umbral.',
    scenarios: [
      {
        name: 'Indicador de claridad 0-100% por categorías',
        given: 'el usuario pega un documento de más de 50 palabras (brief, PRD, mensaje de Slack o lista de funcionalidades)',
        when: 'el agente requirement-analyst lee el documento completo sin interrumpir',
        then: [
          'evalúa la claridad inicial de las 8 categorías con un porcentaje individual para cada una',
          'muestra el indicador global (media de las 8 categorías) y el desglose por categoría',
          'informa de cuántas preguntas estima necesarias para llegar al 80%',
        ],
      },
      {
        name: 'Preguntas priorizadas por impacto',
        given: 'el indicador de claridad muestra categorías por debajo del 80%',
        when: 'el agente formula preguntas al usuario',
        then: [
          'pregunta una sola pregunta por mensaje, empezando por la categoría con menor claridad',
          'tras cada respuesta, actualiza el indicador mostrando solo las categorías que han cambiado (ej: "Restricciones técnicas: 45% -> 75% [+30]")',
          'si una categoría ya está al 80% o más, no pregunta más sobre ella salvo contradicción',
        ],
      },
      {
        name: 'Validación final con resumen estructurado',
        given: 'la claridad media alcanza el 80%',
        when: 'el agente presenta el resumen de validación',
        then: [
          'muestra un resumen de una línea por cada una de las 8 categorías',
          'pide confirmación explícita al usuario antes de avanzar a la generación de historias',
          'guarda el documento original y el análisis completo en docs/analisis-requisitos.md para trazabilidad',
        ],
      },
    ],
    priority: 'must',
    status: 'mvp',
  },
  {
    id: 'HU-14',
    title: 'Estimación por tallas en horas efectivas',
    role: 'tech lead que planifica un sprint',
    action:
      'asignar tallas XS, S, M, L o XL a las historias aprobadas con conversión configurable a horas efectivas',
    benefit:
      'saber si el sprint es viable comparando el total estimado contra la capacidad equivalente del equipo asistido por agentes',
    context:
      'Las tallas se configuran en settings.json (por defecto XS=1 h, S=2 h, M=4 h, L=8 h, XL=16 h). La estimación se integra en sprint-plan y permite ajustar el sprint a una ventana máxima de 5 días.',
    scenarios: [
      {
        name: 'Asignación rápida de tallas',
        given: 'hay historias aprobadas en docs/historias/ y el usuario ejecuta la planificación de sprint',
        when: 'el agente presenta las historias para estimar',
        then: [
          'muestra la tabla de conversión actual (XS=1, S=2, M=4, L=8, XL=16 horas por defecto)',
          'permite asignar tallas en formato rápido con una sola línea (ej: "1=M 2=XL 3=S")',
          'calcula el total en horas efectivas y muestra una tabla resumen con historia, talla, horas y prioridad',
        ],
      },
      {
        name: 'Conversión configurable en settings.json',
        given: 'el usuario ha modificado los valores de conversión en settings.json (ej: XS=2, S=3, M=6, L=10, XL=16)',
        when: 'el agente lee la configuración al iniciar la estimación',
        then: [
          'usa los valores personalizados del usuario en lugar de los valores por defecto',
          'muestra la tabla de conversión activa para que el usuario sepa qué escala se está aplicando',
          'si settings.json no existe o no tiene el campo stories.estimation_sizes, usa los valores por defecto sin error',
        ],
      },
      {
        name: 'Integración con capacidad del equipo',
        given: 'las tallas están asignadas y confirmadas, y el equipo está definido en un CSV compatible',
        when: 'el agente calcula el veredicto del sprint',
        then: [
          'compara el total de horas efectivas de las historias contra la capacidad equivalente del equipo (con factor IA aplicado)',
          'muestra el porcentaje de ocupación del sprint',
          'si la ocupación supera el 100%, sugiere recortar las historias de menor prioridad o puntuación hasta que el sprint sea viable',
        ],
      },
    ],
    priority: 'must',
    status: 'mvp',
  },
  {
    id: 'HU-15',
    title: 'Revisión de estilo automática (culture guardian)',
    role: 'tech lead que quiere comunicación profesional y consistente en todo el proyecto',
    action:
      'que todo el contenido generado por el plugin pase por un revisor de estilo automático antes de mostrarse al usuario o publicarse en Trello',
    benefit:
      'tono consistente en todas las historias, acentos y eñes correctos, criterios de aceptación concretos y detallistas, y aprendizaje de las correcciones del usuario entre sesiones',
    context:
      'El agente culture-guardian actúa como corrector de estilo exigente. Revisa historias de usuario, documentación local, descripciones de tarjetas y cualquier texto que el plugin genera. Aplica normas RAE, castellano neutro (España), tono profesional y criterios detallistas.',
    scenarios: [
      {
        name: 'Revisión antes de mostrar al usuario',
        given: 'el agente product-owner ha generado historias de usuario con sus criterios de aceptación',
        when: 'el contenido pasa por el agente culture-guardian antes de presentarse',
        then: [
          'corrige acentos y eñes (configuracion -> configuración, pequeno -> pequeño)',
          'aplica títulos en minúsculas según la RAE (solo primera letra mayúscula)',
          'verifica que los criterios de aceptación usan valores concretos (no "formato válido", sino "32 caracteres hexadecimales")',
          'si faltan escenarios negativos, lo señala al usuario sin inventar contenido',
        ],
      },
      {
        name: 'Revisión antes de publicar en Trello',
        given: 'las historias aprobadas van a publicarse como tarjetas en Trello',
        when: 'el plugin prepara las descripciones de las tarjetas',
        then: [
          'pasa cada descripción por el culture-guardian para asegurar tono profesional y ortografía correcta',
          'verifica que no hay muros de texto: la información clave debe ser visible de un vistazo',
          'los comentarios de código se mantienen sin acentos por compatibilidad, pero el contenido visible sí los lleva',
        ],
      },
      {
        name: 'Aprendizaje de correcciones del usuario',
        given: 'el usuario corrige un texto generado por el plugin durante la sesión (ej: "no uses X, prefiero Y")',
        when: 'el culture-guardian detecta la corrección',
        then: [
          'registra el aprendizaje en la memoria de Claude Code como tipo feedback',
          'en sesiones futuras, lee los aprendizajes almacenados antes de revisar cualquier contenido',
          'aplica automáticamente las preferencias del usuario sin que tenga que repetir la corrección',
        ],
      },
    ],
    priority: 'must',
    status: 'mvp',
  },
  {
    id: 'HU-16',
    title: 'Detección de edge cases en generación de historias',
    role: 'desarrollador que quiere cubrir todos los escenarios posibles antes de implementar',
    action:
      'que el agente detecte edge cases potenciales en cada historia generada y los presente en una tabla de impacto',
    benefit:
      'no descubrir en producción problemas que se podían prever durante la definición del producto',
    context:
      'Después de generar los criterios de aceptación básicos (happy path y errores), el agente product-owner analiza cada historia buscando edge cases en 5 categorías: límites de datos, concurrencia, estado inconsistente, permisos e integraciones externas.',
    scenarios: [
      {
        name: 'Detección automática en 5 categorías',
        given: 'el agente product-owner ha generado una historia con sus escenarios positivos y negativos',
        when: 'ejecuta el análisis de edge cases',
        then: [
          'analiza la historia buscando edge cases en: límites de datos (strings vacíos, valores nulos, textos de 10000 caracteres), concurrencia (dos usuarios haciendo lo mismo a la vez), estado inconsistente (proceso interrumpido a mitad), permisos (acceso sin autorización) e integraciones (servicio externo no responde)',
          'genera una lista de edge cases detectados con nombre descriptivo para cada uno',
        ],
      },
      {
        name: 'Tabla de impacto para decisión del usuario',
        given: 'se han detectado edge cases para una historia',
        when: 'el agente los presenta al usuario',
        then: [
          'muestra una tabla con columnas: número, descripción del edge case, impacto (Alto/Medio/Bajo) y recomendación de cobertura (Sí/No para el MVP)',
          'los edge cases de impacto Alto se recomiendan siempre',
          'los de impacto Bajo se sugieren para futuras iteraciones',
        ],
      },
      {
        name: 'Integración opcional en criterios de aceptación',
        given: 'el usuario selecciona los edge cases que quiere cubrir',
        when: 'confirma la selección',
        then: [
          'genera criterios de aceptación adicionales en formato Given/When/Then para cada edge case seleccionado',
          'los edge cases no seleccionados se documentan como nota al final de la historia para futuras iteraciones',
          'si el usuario rechaza todos, no se añade nada pero quedan registrados en las notas',
        ],
      },
    ],
    priority: 'must',
    status: 'mvp',
  },
];
