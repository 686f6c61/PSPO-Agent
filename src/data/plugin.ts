/**
 * Metadatos operativos del plugin que la web usa para no desalinearse.
 *
 * Esta capa evita que version, contadores y changelog visible queden
 * repartidos entre varios componentes con valores distintos.
 */
export const pluginMeta = {
  version: '1.0.8',
  counts: {
    commands: 19,
    skills: 18,
    agents: 6,
    mcpTools: 14,
    hookEvents: 3,
    hookGuards: 19,
  },
  docsUrl: 'https://github.com/686f6c61/PSPO-Agent/tree/main/Documents',
  skillNames: [
    'start',
    'autopilot',
    'product-phase',
    'onboarding',
    'discovery',
    'generate-stories',
    'validate',
    'publish',
    'save-docs',
    'update',
    'team',
    'assign',
    'dependencies',
    'sprint-plan',
    'export',
    'sprint-review',
    'analyze',
    'audit',
  ],
  changelog: [
    {
      version: 'v1.0.8',
      date: '16/03/2026',
      sections: [
        {
          title: 'Capa de proveedores',
          icon: 'M3.75 5.25h16.5M3.75 12h16.5m-16.5 6.75h16.5',
          items: [
            'Runtime con publish-provider para elegir Trello, Notion o modo local sin acoplar el flujo a un único destino',
            'Onboarding zero-template de Notion con proyecto, HU-00 y backlog creados desde la página padre',
            'Selección automática cuando solo hay un proveedor listo y una sola pregunta si hay varios',
          ],
        },
        {
          title: 'Guardrails y documentación',
          icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
          items: [
            'Hooks de start, onboarding y publish guiados por trello-fallback, notion-fallback y publish-provider',
            'Bloqueos extra para evitar Bash o lecturas laterales inseguras durante publish y onboarding',
            'Web y documentación alineadas con Notion, variables nuevas y routing por proveedor remoto',
          ],
        },
      ],
    },
    {
      version: 'v1.0.7',
      date: '15/03/2026',
      sections: [
        {
          title: 'Autopilot más cerrado',
          icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
          items: [
            'Autopilot deja aún menos margen para reabrir la inbox o pensar por libre',
            'product-phase delega con prompts autosuficientes y menos deriva lateral',
            'recuperación más clara cuando un bloqueo debe llevar a la siguiente skill',
          ],
        },
      ],
    },
    {
      version: 'v1.0.6',
      date: '15/03/2026',
      sections: [
        {
          title: 'Runtime de autopilot',
          icon: 'M12 4v16m8-8H4',
          items: [
            'Bootstrap automático del CSV desde la inbox al runtime del proyecto',
            'Mensajes de bloqueo más accionables para no improvisar con Bash',
            'Nuevo gate Stop para impedir cerrar el flujo antes de persistir artefactos',
          ],
        },
      ],
    },
    {
      version: 'v1.0.5',
      date: '15/03/2026',
      sections: [
        {
          title: 'Carril de producto',
          icon: 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6',
          items: [
            'Bootstrap determinista de autopilot con contexto materializado en runtime',
            'Scaffold automático de docs/ y docs/historias/ para evitar mkdir improvisados',
            'Bloqueo estricto de Bash y Fetch cuando el flujo ya está en modo autónomo',
          ],
        },
      ],
    },
    {
      version: 'v1.0.4',
      date: '15/03/2026',
      sections: [
        {
          title: 'Flujo actual del producto',
          icon: 'M12 4v16m8-8H4',
          items: [
            'Nuevo /pspo-agent:start para encadenar el flujo correcto automáticamente',
            'Modo carpeta /pspo-agent:autopilot con gate final y CSV flexible',
            'Fases assign y dependencies antes de sprint-plan y publish',
            'Mermaid operativo en la visión/HU-00 y sincronización incremental en Trello',
          ],
        },
        {
          title: 'Trello y seguridad',
          icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
          items: [
            'Launcher MCP dedicado y fallback oficial de Trello',
            'Resumen corto + adjunto .md + miembros reales + DoD + dependencias',
            'Bloqueo reforzado de Bash, Fetch y lecturas sensibles para secretos',
          ],
        },
      ],
    },
    {
      version: 'v1.0.3',
      date: '15/03/2026',
      sections: [
        {
          title: 'Publicación sólida',
          icon: 'M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z',
          items: [
            'Asignación real de miembros a tarjetas',
            'Verificación post-publicación y lotes de trabajo',
            'Primer endurecimiento contra atajos inseguros con Trello',
          ],
        },
      ],
    },
    {
      version: 'v1.0.0',
      date: '14/03/2026',
      sections: [
        {
          title: 'Release inicial',
          icon: 'M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z',
          items: [
            'Base del plugin en Python puro con instalador pipeable',
            'Primer flujo de historias y publicación en Trello',
          ],
        },
      ],
    },
  ],
} as const;
