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
          'crea el tablero con columnas: Backlog, Sprint actual, En progreso, En revisión, Hecho',
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
        when: 'una historia es demasiado grande (más de 3 días de trabajo)',
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
    title: 'Gestión de equipo del proyecto [planificada]',
    role: 'tech lead de un equipo pequeño sin PO dedicado',
    action:
      'definir los miembros de mi equipo con sus roles dentro del plugin',
    benefit:
      'que el PSPO tenga la información necesaria para distribuir historias de forma inteligente',
    context:
      'El tech lead necesita poder definir el equipo rápidamente: importar CSV o añadir miembros uno a uno. Los roles son libres. La categoría (Junior, Mid, Senior) es crucial para la distribución.',
    scenarios: [
      {
        name: 'Detección de equipo no definido',
        given: 'el usuario tiene historias aprobadas y no existe team.csv',
        when: 'solicita distribuir historias al equipo',
        then: [
          'detecta que no hay equipo definido',
          'ofrece: importar CSV, rellenar plantilla, o añadir miembros uno a uno',
        ],
      },
      {
        name: 'Alta guiada de miembros',
        given: 'el usuario elige añadir miembros de forma guiada',
        when: 'el plugin inicia el asistente',
        then: [
          'para cada miembro pregunta: nombre, email, rol y categoria',
          'sugiere roles comunes pero acepta texto libre',
          'al terminar, muestra el resumen y pide confirmación',
        ],
      },
      {
        name: 'Persistencia del equipo',
        given: 'el usuario ha confirmado la composición del equipo',
        when: 'el plugin guarda los datos',
        then: [
          'escribe team.csv con cabecera: nombre,email,rol,categoria,dedicacion,usa_agente_ia',
          'en futuras sesiones, lee team.csv automáticamente',
        ],
      },
    ],
    priority: 'should',
    status: 'v1.1',
  },
  {
    id: 'HU-08',
    title: 'Distribución inteligente de historias al equipo [planificada]',
    role: 'tech lead que tiene historias aprobadas y un equipo definido',
    action:
      'que el PSPO sugiera una distribución de historias entre los miembros del equipo',
    benefit:
      'no tener que repartir el trabajo a ojo y asegurarme de que la carga está equilibrada',
    context:
      'El tech lead pierde tiempo decidiendo quién hace cada historia. El PSPO puede analizar roles y carga, pero el tech lead siempre debe tener la última palabra.',
    scenarios: [
      {
        name: 'Propuesta de distribución basada en roles',
        given: 'hay historias aprobadas y equipo definido',
        when: 'el PSPO analiza las historias y el equipo',
        then: [
          'identifica el tipo de trabajo de cada historia',
          'cruza el tipo de trabajo con los roles del equipo',
          'genera una propuesta de asignación en formato tabla',
          'muestra la carga total por miembro y señala desequilibrios',
        ],
      },
      {
        name: 'Aprobación del usuario sobre la distribución',
        given: 'el PSPO presenta la propuesta completa',
        when: 'el usuario la revisa',
        then: [
          'puede aprobar la distribución tal como está',
          'puede modificar asignaciones individuales',
          'puede rechazar y pedir nuevo análisis con criterios distintos',
        ],
      },
    ],
    priority: 'should',
    status: 'v1.1',
  },
  {
    id: 'HU-09',
    title: 'Mapa de dependencias y bloqueantes entre historias [planificada]',
    role: 'tech lead que coordina el trabajo de un equipo pequeño',
    action:
      'que el PSPO identifique dependencias y bloqueantes entre historias',
    benefit:
      'saber en qué orden deben ejecutarse y qué impacto tiene un retraso',
    context:
      'Las dependencias son invisibles hasta que alguien se bloquea. El PSPO puede analizar el contenido de las historias para detectar relaciones, pero el usuario siempre debe confirmar.',
    scenarios: [
      {
        name: 'Análisis automático de dependencias',
        given: 'hay al menos 3 historias aprobadas',
        when: 'el usuario solicita el mapa de dependencias',
        then: [
          'analiza el contenido de cada historia buscando relaciones técnicas, de datos y de UX',
          'genera una lista de dependencias con nivel de confianza (alta, media, baja)',
        ],
      },
      {
        name: 'Visualización del grafo de dependencias',
        given: 'el mapa está confirmado por el usuario',
        when: 'el plugin genera la visualización',
        then: [
          'crea un diagrama Mermaid en docs/dependencias.md',
          'cada historia es un nodo con ID y título',
          'las historias bloqueantes se resaltan visualmente',
        ],
      },
      {
        name: 'Análisis de impacto de retrasos',
        given: 'el mapa está confirmado y las historias están asignadas',
        when: 'el usuario pregunta qué pasa si una historia se retrasa',
        then: [
          'recorre la cadena de dependencias desde esa historia',
          'muestra historias y miembros afectados directa e indirectamente',
          'calcula el radio de impacto total',
        ],
      },
    ],
    priority: 'should',
    status: 'v1.1',
  },
  {
    id: 'HU-10',
    title: 'Integración de asignaciones y dependencias con Trello [planificada]',
    role: 'tech lead que gestiona su equipo a través de Trello',
    action:
      'que las asignaciones y dependencias se reflejen en las tarjetas del tablero',
    benefit:
      'que todo el equipo vea quién hace qué y qué depende de qué sin salir de Trello',
    context:
      'El mapa de dependencias y las asignaciones son útiles localmente, pero el equipo trabaja en Trello. La sincronización debe reflejar asignaciones y dependencias en las tarjetas.',
    scenarios: [
      {
        name: 'Asignación de miembros a tarjetas',
        given: 'las historias están publicadas y las asignaciones aprobadas',
        when: 'el plugin sincroniza con Trello',
        then: [
          'busca cada miembro asignado por email en el tablero',
          'si existe, lo asigna a la tarjeta correspondiente',
          'si no existe, ofrece invitarle al tablero o registrar la asignación localmente',
        ],
      },
      {
        name: 'Checklists de dependencias',
        given: 'el mapa de dependencias está confirmado y las tarjetas existen en Trello',
        when: 'el plugin sincroniza las dependencias',
        then: [
          'crea un checklist "Dependencias" en cada tarjeta afectada',
          'cada item es una dependencia con enlace a la tarjeta de la que depende',
        ],
      },
      {
        name: 'Vista previa antes de sincronizar',
        given: 'el plugin va a sincronizar asignaciones y dependencias',
        when: 'el usuario solicita la sincronización',
        then: [
          'muestra una vista previa completa de los cambios',
          'pide confirmación explícita antes de ejecutar',
          'NUNCA modifica tarjetas sin confirmación del usuario',
        ],
      },
    ],
    priority: 'should',
    status: 'v1.1',
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
];
