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
  version: '1.0.4',
  title: 'PSPO Agent - Plugin no oficial de Product Owner para Claude Code',
  description:
    'Plugin no oficial de Claude Code para descubrimiento de producto, historias de usuario, asignacion operativa, dependencias, planificacion de sprint con agentes y publicacion en Trello.',
  url: 'https://pspo-agent.com',
  ogImage: '/og-image.png',
  repository: 'https://github.com/686f6c61/PSPO-Agent',
  license: 'MIT',
  author: '686f6c61',
} as const;
