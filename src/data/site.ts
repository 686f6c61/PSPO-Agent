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
  title: 'PSPO Agent - Product Owner con IA para Claude Code',
  description:
    'Plugin de Claude Code que actúa como Product Owner profesional. Descubrimiento de producto, historias de usuario con criterios de aceptación y publicación en Trello.',
  url: 'https://pspo-agent.com',
  ogImage: '/og-image.png',
  repository: 'https://github.com/686f6c61/PSPO-Agent',
  license: 'MIT',
  author: '686f6c61',
} as const;
