/**
 * Datos de instalacion del plugin por sistema operativo.
 *
 * installations[] contiene las instrucciones paso a paso para Linux, macOS
 * y Windows. Cada paso puede incluir un bloque de codigo copiable.
 * remoteSetupGroups[] describe los proveedores remotos activos que el plugin
 * puede guiar automaticamente en la primera ejecucion.
 *
 * Todos estos datos los consume la seccion Installation.astro.
 */
export interface InstallStep {
  title: string;
  description: string;
  code?: string;
  language?: string;
}

export interface OSInstallation {
  os: 'linux' | 'macos' | 'windows';
  label: string;
  steps: InstallStep[];
}

export interface RemoteSetupStep {
  step: number;
  title: string;
  description: string;
  link?: string;
}

export interface RemoteSetupGroup {
  provider: string;
  badge: string;
  summary: string;
  steps: RemoteSetupStep[];
}

export const installations: OSInstallation[] = [
  {
    os: 'linux',
    label: 'Linux',
    steps: [
      {
        title: 'Requisitos previos',
        description:
          'Necesitas tener instalados Claude Code y Python 3.8+. Verifica que están disponibles en tu terminal.',
        code: 'claude --version\npython3 --version  # Debe ser >= 3.8',
        language: 'bash',
      },
      {
        title: 'Instalar el plugin',
        description:
          'Ejecuta el instalador con un solo comando. Registra el marketplace y el plugin en Claude Code automáticamente.',
        code: 'curl -fsSL https://raw.githubusercontent.com/686f6c61/PSPO-Agent/main/install.sh | bash',
        language: 'bash',
      },
      {
        title: 'Primera ejecución',
        description:
          'Reinicia Claude Code, ábrelo en cualquier proyecto y ejecuta /pspo-agent:start. Si faltan las credenciales, el onboarding se lanza solo; si ya tienes un brief en .pspo-agent/inbox, después puedes seguir con /pspo-agent:autopilot.',
        code: '/pspo-agent:start',
        language: 'bash',
      },
    ],
  },
  {
    os: 'macos',
    label: 'macOS',
    steps: [
      {
        title: 'Requisitos previos',
        description:
          'Necesitas Claude Code y Python 3 (viene preinstalado en macOS).',
        code: 'claude --version\npython3 --version  # Debe ser >= 3.8',
        language: 'bash',
      },
      {
        title: 'Instalar el plugin',
        description:
          'Ejecuta el instalador con un solo comando.',
        code: 'curl -fsSL https://raw.githubusercontent.com/686f6c61/PSPO-Agent/main/install.sh | bash',
        language: 'bash',
      },
      {
        title: 'Primera ejecución',
        description:
          'Reinicia Claude Code y ejecuta /pspo-agent:start. El plugin lanza onboarding automáticamente si aún no existe .env y deja listo el camino para autopilot.',
        code: '/pspo-agent:start',
        language: 'bash',
      },
    ],
  },
  {
    os: 'windows',
    label: 'Windows',
    steps: [
      {
        title: 'Requisitos previos',
        description:
          'Necesitas Claude Code y Python 3.8+. Usa PowerShell como terminal.',
        code: 'claude --version\npython3 --version  # Debe ser >= 3.8',
        language: 'powershell',
      },
      {
        title: 'Instalar el plugin',
        description:
          'Ejecuta el instalador con un solo comando en PowerShell.',
        code: 'irm https://raw.githubusercontent.com/686f6c61/PSPO-Agent/main/install.ps1 | iex',
        language: 'powershell',
      },
      {
        title: 'Primera ejecución',
        description:
          'Reinicia Claude Code y ejecuta /pspo-agent:start. Si faltan credenciales, el plugin te guía sin pedir comandos extra.',
        code: '/pspo-agent:start',
        language: 'powershell',
      },
    ],
  },
];

export const remoteSetupGroups: RemoteSetupGroup[] = [
  {
    provider: 'Trello',
    badge: 'MCP + fallback',
    summary:
      'Ideal si quieres tablero operativo, tarjetas, adjuntos, DoD y asignaciones reales sobre un flujo Kanban visible.',
    steps: [
      {
        step: 1,
        title: 'Obtener API Key',
        description:
          'Visita la página de administración de Power-Ups de Trello, crea un nuevo Power-Up y copia la API Key.',
        link: 'https://trello.com/power-ups/admin',
      },
      {
        step: 2,
        title: 'Generar token de autorización',
        description:
          'El plugin construye la URL de autorización con tu API Key sin exponerla completa en pantalla. Solo necesitas autorizar a PSPO Agent y pegar el token.',
      },
      {
        step: 3,
        title: 'Seleccionar o crear tablero',
        description:
          'El plugin lista tus tableros y te permite elegir uno existente o crear uno nuevo con Backlog, Sprint activo, Bloqueada, En progreso, En revision y Hecho.',
      },
    ],
  },
  {
    provider: 'Notion',
    badge: 'Zero-template',
    summary:
      'Ideal si quieres proyecto, HU-00, backlog y paginas largas dentro de un workspace, sin depender de una plantilla previa.',
    steps: [
      {
        step: 1,
        title: 'Crear integración interna',
        description:
          'Crea una internal integration en Notion y copia el token. El plugin usa ese token como proveedor remoto sin exponerlo en logs.',
        link: 'https://www.notion.so/profile/integrations',
      },
      {
        step: 2,
        title: 'Compartir la página padre',
        description:
          'Conecta la integración a una página vacía o existente de tu workspace para que PSPO Agent pueda crear desde cero el proyecto y la base de backlog.',
      },
      {
        step: 3,
        title: 'Dejar que el plugin cree la estructura',
        description:
          'El onboarding guarda el parent page, crea proyecto, HU-00, backlog y luego publish sincroniza las HU, adjuntos y asignaciones people.',
      },
    ],
  },
];
