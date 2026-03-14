import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import rehypeMermaid from 'rehype-mermaid';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  site: 'https://pspo-agent.onrender.com',
  output: 'static',
  integrations: [sitemap()],
  build: {
    inlineStylesheets: 'auto',
  },
  markdown: {
    rehypePlugins: [
      [rehypeMermaid, {
        strategy: 'inline-svg',
        mermaidConfig: {
          theme: 'neutral',
          securityLevel: 'strict',
        },
      }],
    ],
  },
  vite: {
    plugins: [tailwindcss()],
  },
});
