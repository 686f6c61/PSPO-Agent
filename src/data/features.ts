/**
 * Datos de las funcionalidades del plugin PSPO Agent.
 *
 * Cada Feature representa una funcionalidad con su categoria, descripcion,
 * comando de activacion, icono SVG (path de Heroicons) y referencia a la
 * historia de usuario que la define. La lista de categorias (featureCategories)
 * controla el orden de agrupacion en la seccion Features.
 *
 * Para anadir una funcionalidad nueva: anadir un objeto a features[] con
 * categoria existente o nueva, y si la categoria es nueva, incluirla en
 * featureCategories para que aparezca como grupo.
 */
export interface Feature {
  id: string;
  category: 'configuracion' | 'producto' | 'publicacion' | 'planificacion' | 'calidad' | 'analisis';
  categoryLabel: string;
  title: string;
  description: string;
  command: string;
  icon: string;
  huReference: string;
}

export const features: Feature[] = [
  {
    id: 'analyze',
    category: 'analisis',
    categoryLabel: 'Análisis de requisitos',
    title: 'Analista de requisitos',
    description:
      'Pega un documento (brief, email, PRD, mensaje de Slack) y el agente lo interroga hasta alcanzar un 80% de claridad. Evalúa 8 categorías: usuario final, problema, contexto, alcance, restricciones, criterios de éxito, dependencias y fuera de alcance. Sustituye al descubrimiento cuando hay documento de partida.',
    command: '/pspo-agent:analyze',
    icon: 'M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m5.231 13.481L15 17.25m-4.5-15H5.625c-.621 0-1.125.504-1.125 1.125v16.5c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Zm3.75 11.625a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z',
    huReference: '',
  },
  {
    id: 'onboarding',
    category: 'configuracion',
    categoryLabel: 'Configuración',
    title: 'Onboarding guiado',
    description:
      'Empieza con /pspo-agent:start. El plugin detecta si faltan credenciales o tablero y te guía paso a paso para dejar Trello listo sin tocar ficheros a mano.',
    command: '/pspo-agent:start',
    icon: 'M15.59 14.37a6 6 0 0 0-5.84 7.38c.06.3.15.59.27.86M12 2a10 10 0 0 0-6.88 17.23l1.17-1.17A8 8 0 1 1 20 12a7.95 7.95 0 0 1-2.32 5.64l1.17 1.17A10 10 0 0 0 12 2zm0 4a6 6 0 0 0-4.24 10.24l1.17-1.17A4 4 0 1 1 16 12a3.98 3.98 0 0 1-1.17 2.83l1.17 1.17A6 6 0 0 0 12 6zm0 4a2 2 0 1 0 0 4 2 2 0 0 0 0-4z',
    huReference: 'HU-01',
  },
  {
    id: 'autopilot',
    category: 'configuracion',
    categoryLabel: 'Configuración',
    title: 'Autopilot por carpeta',
    description:
      'Deja un brief, una visión opcional y un CSV de equipo compatible en una carpeta. /pspo-agent:autopilot analiza, genera, guarda y audita sin menús intermedios hasta la gate final.',
    command: '/pspo-agent:autopilot',
    icon: 'M3.75 13.5l7.5-7.5m0 0 7.5 7.5m-7.5-7.5v18',
    huReference: '',
  },
  {
    id: 'discovery',
    category: 'producto',
    categoryLabel: 'Producto',
    title: 'Descubrimiento conversacional',
    description:
      'El agente formula preguntas de descubrimiento antes de generar nada. Identifica al usuario final, el problema, las restricciones y el alcance. No genera historias sin antes entender el contexto.',
    command: '/pspo-agent:discovery',
    icon: 'M21 21l-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607z',
    huReference: 'HU-02',
  },
  {
    id: 'generate',
    category: 'producto',
    categoryLabel: 'Producto',
    title: 'Generación de historias',
    description:
      'Produce historias de usuario en formato "Como [rol], quiero [acción], para [beneficio]" con criterios de aceptación Given/When/Then. Cada historia es independiente y de tamaño manejable.',
    command: '/pspo-agent:generate-stories',
    icon: 'M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9z',
    huReference: 'HU-03',
  },
  {
    id: 'validate',
    category: 'producto',
    categoryLabel: 'Producto',
    title: 'Validación y aprobación',
    description:
      'El usuario revisa cada historia individualmente. Puede aprobar, rechazar o pedir cambios. Nada se publica sin aprobación explícita. Soporta aprobación parcial del lote.',
    command: '/pspo-agent:validate',
    icon: 'M9 12.75L11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z',
    huReference: 'HU-04',
  },
  {
    id: 'publish',
    category: 'publicacion',
    categoryLabel: 'Publicación',
    title: 'Publicación en Trello',
    description:
      'Publica o sincroniza historias en Trello con resumen corto, adjunto .md, DoD, dependencias y miembros reales. Detecta duplicados, muestra vista previa y guarda siempre en local antes de tocar Trello.',
    command: '/pspo-agent:publish',
    icon: 'M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5',
    huReference: 'HU-05',
  },
  {
    id: 'save-docs',
    category: 'publicacion',
    categoryLabel: 'Publicación',
    title: 'Documentación local',
    description:
      'Guarda los artefactos de producto en docs/ del repositorio: vision.md, una historia por fichero en docs/historias/, y backlog.md con la lista priorizada. Todo versionado junto al código.',
    command: '/pspo-agent:save-docs',
    icon: 'M2.25 12.75V12A2.25 2.25 0 0 1 4.5 9.75h15A2.25 2.25 0 0 1 21.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 0 0-1.061-.44H4.5A2.25 2.25 0 0 0 2.25 6v12a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9a2.25 2.25 0 0 0-2.25-2.25h-5.379a1.5 1.5 0 0 1-1.06-.44z',
    huReference: 'HU-06',
  },
  {
    id: 'update',
    category: 'configuracion',
    categoryLabel: 'Configuración',
    title: 'Actualización automática',
    description:
      'Comprueba si hay una versión nueva del plugin comparando con las releases de GitHub. Descarga e instala la actualización verificando el checksum SHA-256 del instalador.',
    command: '/pspo-agent:update',
    icon: 'M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182',
    huReference: '',
  },
  {
    id: 'team',
    category: 'planificacion',
    categoryLabel: 'Planificación',
    title: 'Gestión de equipo',
    description:
      'Define los miembros del equipo con rol, categoría, dedicación y uso de agentes IA. Acepta cualquier CSV compatible, no solo team.csv, o usa el asistente guiado.',
    command: '/pspo-agent:team',
    icon: 'M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0z',
    huReference: '',
  },
  {
    id: 'assign',
    category: 'planificacion',
    categoryLabel: 'Planificación',
    title: 'Asignación operativa',
    description:
      'Reparte ownership del backlog con criterio: encaje de rol, carga real en horas efectivas, continuidad funcional y reducción de bloqueos entre personas.',
    command: '/pspo-agent:assign',
    icon: 'M17.25 6.75v10.5m-10.5-10.5v10.5m-3-7.5h16.5',
    huReference: '',
  },
  {
    id: 'dependencies',
    category: 'planificacion',
    categoryLabel: 'Planificación',
    title: 'Mapa de dependencias',
    description:
      'Detecta dependencias confirmadas e inferidas, genera docs/dependencias.md con Mermaid y deja visibles las personas impactadas antes de que aparezcan bloqueos en mitad del sprint.',
    command: '/pspo-agent:dependencies',
    icon: 'M7.5 6h9m-9 12h9M6 6a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Zm12 9a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3ZM6 15a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Zm12-9a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Z',
    huReference: '',
  },
  {
    id: 'sprint-plan',
    category: 'planificacion',
    categoryLabel: 'Planificación',
    title: 'Planificación de sprint con estimación',
    description:
      'Propone horas efectivas con agentes (XS=1, S=2, M=4, L=8, XL=16), calcula capacidad real del equipo y no infla trabajo sencillo por costumbre. Si no cabe, recorta con criterio.',
    command: '/pspo-agent:sprint-plan',
    icon: 'M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5',
    huReference: '',
  },
  {
    id: 'dod',
    category: 'planificacion',
    categoryLabel: 'Planificación',
    title: 'Definition of Done',
    description:
      'Configura los criterios mínimos que toda historia debe cumplir: tests, code review, linter, seguridad, documentación. Se añade automáticamente como checklist en las tarjetas de Trello.',
    command: '/pspo-agent:sprint-plan',
    icon: 'M11.35 3.836c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m8.9-4.414c.376.023.75.05 1.124.08 1.131.094 1.976 1.057 1.976 2.192V16.5A2.25 2.25 0 0 1 18 18.75h-2.25m-7.5-10.5H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V18.75m-7.5-10.5h6.375c.621 0 1.125.504 1.125 1.125v9.375m-8.25-3l1.5 1.5 3-3.75',
    huReference: '',
  },
  {
    id: 'export',
    category: 'publicacion',
    categoryLabel: 'Publicación',
    title: 'Exportación a CSV, JSON y Jira',
    description:
      'Exporta las historias aprobadas a tres formatos: CSV para hojas de cálculo, JSON para integraciones programáticas, y CSV compatible con la importación de Jira para equipos que migran.',
    command: '/pspo-agent:export',
    icon: 'M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3',
    huReference: '',
  },
  {
    id: 'sprint-review',
    category: 'planificacion',
    categoryLabel: 'Planificación',
    title: 'Revisión de sprint',
    description:
      'Consulta el estado de las tarjetas en Trello, evalúa el cumplimiento de la Definition of Done y genera un informe de cierre de sprint con métricas de completitud.',
    command: '/pspo-agent:sprint-review',
    icon: 'M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25Z',
    huReference: '',
  },
  {
    id: 'culture-guardian',
    category: 'calidad',
    categoryLabel: 'Calidad',
    title: 'Guardián de cultura',
    description:
      'Agente revisor de estilo que corrige todo el contenido antes de mostrarlo: normas RAE, castellano neutro, tono profesional (CTO), detallista con los criterios de aceptación. Aprende de las correcciones del usuario.',
    command: '',
    icon: 'M12 18v-5.25m0 0a6.01 6.01 0 0 0 1.5-.189m-1.5.189a6.01 6.01 0 0 1-1.5-.189m3.75 7.478a12.06 12.06 0 0 1-4.5 0m3.75 2.383a14.406 14.406 0 0 1-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 1 0-7.517 0c.85.493 1.509 1.333 1.509 2.316V18',
    huReference: '',
  },
  {
    id: 'audit',
    category: 'calidad',
    categoryLabel: 'Calidad',
    title: 'Auditoría senior de HU',
    description:
      'Agente auditor que revisa completitud, coherencia y calidad de las historias generadas. Cruza contra el documento original, detecta HU que faltan o sobran, y propone correcciones. Automático en la primera generación.',
    command: '/pspo-agent:audit',
    icon: 'M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z',
    huReference: '',
  },
  {
    id: 'invite-members',
    category: 'publicacion',
    categoryLabel: 'Publicación',
    title: 'Invitación al tablero por email',
    description:
      'Invita automáticamente a los miembros del equipo al tablero de Trello usando los emails del CSV compatible y reutiliza el memberId devuelto para asignar tarjetas reales.',
    command: '',
    icon: 'M21.75 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25h-15a2.25 2.25 0 0 1-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25m19.5 0v.243a2.25 2.25 0 0 1-1.07 1.916l-7.5 4.615a2.25 2.25 0 0 1-2.36 0L3.32 8.91a2.25 2.25 0 0 1-1.07-1.916V6.75',
    huReference: '',
  },
];

export const featureCategories = [
  { id: 'analisis', label: 'Análisis de requisitos' },
  { id: 'configuracion', label: 'Configuración' },
  { id: 'producto', label: 'Producto' },
  { id: 'publicacion', label: 'Publicación' },
  { id: 'planificacion', label: 'Planificación de sprint' },
  { id: 'calidad', label: 'Calidad' },
] as const;
