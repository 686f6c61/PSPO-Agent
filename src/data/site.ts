import { pluginMeta } from './plugin';

/**
 * Metadatos globales del sitio.
 *
 * Fuente de verdad para SEO (title, description), Open Graph (ogImage),
 * datos del proyecto (url, repository, license, author) y el nombre
 * visible del producto. BaseLayout.astro consume este objeto para
 * generar los meta tags de todas las paginas.
 */
export const site = {
  name: 'PSPO Agent',
  version: pluginMeta.version,
  title: 'PSPO Agent | Plugin no oficial de Claude Code para backlog, HU y Trello',
  description:
    'Plugin no oficial de Claude Code para descubrimiento de producto, HU amplias, asignacion operativa, dependencias, sprint con agentes y publicacion en Trello con resumen corto, adjunto .md y miembro real.',
  url: 'https://pspo-agent.com',
  ogImage: '/og-image.png',
  repository: 'https://github.com/686f6c61/PSPO-Agent',
  license: 'MIT',
  author: '686f6c61',
} as const;
