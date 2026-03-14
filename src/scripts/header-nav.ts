// Scroll spy del header: marca como activo el enlace de la seccion visible.
// Usa IntersectionObserver con un margen que activa la seccion cuando ocupa
// el 20%-80% del viewport. Tambien gestiona el menu hamburguesa en movil
// y la transicion transparente/opaco del header al hacer scroll.
const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('[data-nav-link]');

const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        navLinks.forEach((link) => {
          const linkEl = link as HTMLElement;
          link.classList.toggle(
            'active',
            linkEl.dataset.navLink === entry.target.id
          );
        });
      }
    });
  },
  { rootMargin: '-20% 0px -80% 0px' }
);

sections.forEach((section) => observer.observe(section));

const menuButton = document.querySelector('[data-menu-toggle]');
const mobileMenu = document.querySelector('[data-mobile-menu]');

menuButton?.addEventListener('click', () => {
  const isHidden = mobileMenu?.classList.toggle('hidden');
  menuButton.setAttribute('aria-expanded', String(!isHidden));
});

document.querySelectorAll('[data-nav-link-mobile]').forEach((link) => {
  link.addEventListener('click', () => {
    mobileMenu?.classList.add('hidden');
    menuButton?.setAttribute('aria-expanded', 'false');
  });
});

// Header transparente en el hero, opaco al hacer scroll.
const header = document.querySelector('[data-header]');
if (header) {
  const onScroll = () => {
    if (window.scrollY > 50) {
      header.setAttribute('data-scrolled', '');
    } else {
      header.removeAttribute('data-scrolled');
    }
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
}
