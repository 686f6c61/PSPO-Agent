// Inicializa todos los widgets de pestanas de la pagina.
// Activa la pestana correcta segun el User-Agent (linux/macos/windows) y
// gestiona la navegacion por teclado con flechas izquierda/derecha (ARIA Tabs).
document.querySelectorAll('[data-tab-group]').forEach((group) => {
  const buttons = group.querySelectorAll('[data-tab-button]');
  const panels = group.querySelectorAll('[data-tab-panel]');

  const ua = navigator.userAgent.toLowerCase();
  let defaultTab = 'linux';
  if (ua.includes('mac')) defaultTab = 'macos';
  if (ua.includes('win')) defaultTab = 'windows';

  function activate(tabId: string) {
    buttons.forEach((btn) => {
      const isActive = (btn as HTMLElement).dataset.tabButton === tabId;
      btn.setAttribute('aria-selected', String(isActive));
    });
    panels.forEach((panel) => {
      const panelEl = panel as HTMLElement;
      panelEl.hidden = panelEl.dataset.tabPanel !== tabId;
    });
  }

  buttons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const tabId = (btn as HTMLElement).dataset.tabButton;
      if (tabId) activate(tabId);
    });

    btn.addEventListener('keydown', (e) => {
      const key = (e as KeyboardEvent).key;
      if (key !== 'ArrowLeft' && key !== 'ArrowRight') return;
      const btnsArray = Array.from(buttons);
      const currentIndex = btnsArray.indexOf(btn);
      let nextIndex: number;
      if (key === 'ArrowRight') {
        nextIndex = (currentIndex + 1) % btnsArray.length;
      } else {
        nextIndex = (currentIndex - 1 + btnsArray.length) % btnsArray.length;
      }
      const nextBtn = btnsArray[nextIndex] as HTMLElement;
      const nextTabId = nextBtn.dataset.tabButton;
      if (nextTabId) {
        activate(nextTabId);
        nextBtn.focus();
      }
    });
  });

  activate(defaultTab);
});
