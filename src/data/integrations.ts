export interface IntegrationItem {
  id: string;
  name: string;
  logo?: string;
  summary: string;
}

export const activeIntegrations: IntegrationItem[] = [
  {
    id: 'trello',
    name: 'Trello',
    logo: '/integrations/trello.svg',
    summary: 'MCP + fallback oficial para tablero, tarjetas, adjuntos y asignacion real.',
  },
  {
    id: 'notion',
    name: 'Notion',
    logo: '/Logo.svg',
    summary: 'Zero-template desde API: proyecto, HU-00, backlog, paginas, adjuntos y people.',
  },
];

export const upcomingIntegrations: IntegrationItem[] = [
  {
    id: 'obsidian',
    name: 'Obsidian',
    summary: 'Modo local-first con pequenos ajustes sobre el contrato Markdown actual.',
  },
  {
    id: 'jira',
    name: 'Jira',
    summary: 'Proximo proveedor remoto para equipos que ya viven en Atlassian.',
  },
  {
    id: 'github',
    name: 'GitHub',
    summary: 'Proxima capa para issues, tracking tecnico y sync con desarrollo.',
  },
];
