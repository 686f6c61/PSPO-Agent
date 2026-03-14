/**
 * Datos de instalacion del plugin por sistema operativo.
 *
 * installations[] contiene las instrucciones paso a paso para Linux, macOS
 * y Windows. Cada paso puede incluir un bloque de codigo copiable.
 * troubleshooting[] recoge los problemas mas comunes con su solucion.
 * trelloSetupSteps[] describe el proceso de configuracion de Trello que
 * el plugin guia automaticamente en la primera ejecucion.
 *
 * Todos estos datos los consume la seccion Installation.astro.
 */
export interface InstallStep {
  title: string;
  description: string;
  code?: string;
  language?: string;
}

export interface TroubleshootItem {
  problem: string;
  solution: string;
  code?: string;
}

export interface OSInstallation {
  os: 'linux' | 'macos' | 'windows';
  label: string;
  steps: InstallStep[];
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
          'Reinicia Claude Code, ábrelo en cualquier proyecto y ejecuta el comando de inicio. El plugin detectará que es tu primera ejecución y te guiará por el asistente de configuración de Trello.',
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
          'Reinicia Claude Code y ejecuta el comando de inicio para activar el asistente de configuración.',
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
          'Reinicia Claude Code y ejecuta el comando de inicio.',
        code: '/pspo-agent:start',
        language: 'powershell',
      },
    ],
  },
];

export const troubleshooting: TroubleshootItem[] = [
  {
    problem: 'Claude Code no reconoce el plugin',
    solution:
      'Asegúrate de reiniciar Claude Code después de la instalación. Los plugins se cargan al inicio de sesión.',
    code: 'claude plugin list  # Verifica que pspo-agent aparece',
  },
  {
    problem: 'Error de permisos en Linux/macOS',
    solution:
      'Si instalas manualmente, asegúrate de que los scripts tienen permisos de ejecución.',
    code: 'chmod +x install.sh\nchmod +x hooks/scripts/*.sh',
  },
  {
    problem: 'Python 3 no encontrado',
    solution:
      'Instala Python 3.8+ desde la web oficial o con tu gestor de paquetes.',
    code: '# Ubuntu/Debian\nsudo apt install python3\n\n# macOS (viene preinstalado)\npython3 --version\n\n# Windows: descarga desde https://python.org',
  },
  {
    problem: 'Las credenciales de Trello no funcionan',
    solution:
      'Verifica que la API Key tiene 32 caracteres hexadecimales y que el token empieza por ATTA. Los tokens caducan a los 30 días. Genera uno nuevo con /pspo-agent:onboarding.',
  },
  {
    problem: 'El servidor MCP no arranca',
    solution:
      'Verifica que Python 3 está en el PATH. El servidor MCP es un fichero Python puro sin dependencias externas.',
    code: 'python3 --version\n# Si falla, instala Python desde https://python.org',
  },
];

export const trelloSetupSteps = [
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
      'El plugin construye automáticamente la URL de autorización con tu API Key. Solo necesitas abrir el enlace en el navegador, autorizar a PSPO Agent y copiar el token.',
  },
  {
    step: 3,
    title: 'Seleccionar o crear tablero',
    description:
      'El plugin lista tus tableros de Trello y te permite elegir uno existente o crear uno nuevo con las columnas y etiquetas por defecto.',
  },
];
