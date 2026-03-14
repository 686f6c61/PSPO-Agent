/**
 * Script post-build: actualiza los hashes SHA-256 de scripts inline en vercel.json.
 *
 * Astro genera scripts inline de tipo module en index.html durante el build.
 * La CSP de vercel.json usa 'self' + hashes SHA-256 para autorizar solo esos
 * scripts concretos, sin necesitar 'unsafe-inline'. Este script recalcula los
 * hashes tras cada build y los reemplaza en el header Content-Security-Policy.
 *
 * Se ejecuta automaticamente via `npm run build` (astro build && node scripts/update-csp-hashes.mjs).
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join } from 'node:path';

const distDir = join(import.meta.dirname, '..', 'dist');
const vercelJsonPath = join(import.meta.dirname, '..', 'vercel.json');

const html = readFileSync(join(distDir, 'index.html'), 'utf-8');

const scriptRegex = /<script type="module">([\s\S]*?)<\/script>/g;
const hashes = [];
let match;

while ((match = scriptRegex.exec(html)) !== null) {
  const content = match[1];
  const hash = createHash('sha256').update(content).digest('base64');
  hashes.push(`'sha256-${hash}'`);
}

if (hashes.length === 0) {
  console.log('[CSP] No inline scripts found, nothing to update.');
  process.exit(0);
}

const vercelJson = JSON.parse(readFileSync(vercelJsonPath, 'utf-8'));
const allHeaders = vercelJson.headers[0].headers;
const cspHeader = allHeaders.find((h) => h.key === 'Content-Security-Policy');

if (!cspHeader) {
  console.error('[CSP] Content-Security-Policy header not found in vercel.json');
  process.exit(1);
}

const hashList = hashes.join(' ');
cspHeader.value = cspHeader.value.replace(
  /script-src\s+'self'[^;]*/,
  `script-src 'self' ${hashList}`
);

writeFileSync(vercelJsonPath, JSON.stringify(vercelJson, null, 2) + '\n');

console.log(`[CSP] Updated script-src with ${hashes.length} hash(es):`);
hashes.forEach((h) => console.log(`  ${h}`));
