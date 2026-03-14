/**
 * Datos de navegacion de la onepage.
 *
 * Define los items del header (etiqueta, href de ancla e id de seccion).
 * El id de seccion se usa en header-nav.ts para activar el enlace correcto
 * segun la seccion visible. Cualquier seccion nueva que se anade a la web
 * debe tener su entrada aqui para aparecer en el menu.
 */
export interface NavItem {
  label: string;
  href: string;
  sectionId: string;
}

export const navigation: NavItem[] = [
  { label: 'Funcionalidades', href: '#funcionalidades', sectionId: 'funcionalidades' },
  { label: 'Flujo', href: '#flujo', sectionId: 'flujo' },
  { label: 'Instalación', href: '#instalacion', sectionId: 'instalacion' },
  { label: 'Arquitectura', href: '#arquitectura', sectionId: 'arquitectura' },
  { label: 'IA y productividad', href: '#estudios-ia', sectionId: 'estudios-ia' },
  { label: 'Historias', href: '#historias', sectionId: 'historias' },
];
