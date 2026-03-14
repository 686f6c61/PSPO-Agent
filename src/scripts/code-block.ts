// Activa los botones de copiar en todos los bloques de codigo de la pagina.
// Usa la Clipboard API y muestra feedback visual transitorio (2 segundos).
document.querySelectorAll('[data-copy-button]').forEach((btn) => {
  btn.addEventListener('click', async () => {
    const codeBlock = btn.closest('[data-code-block]');
    if (!codeBlock) return;
    const code = codeBlock.querySelector('code');
    if (!code) return;
    try {
      await navigator.clipboard.writeText(code.textContent || '');
      const originalText = btn.textContent;
      btn.textContent = 'Copiado';
      setTimeout(() => {
        btn.textContent = originalText;
      }, 2000);
    } catch {
      btn.textContent = 'Error';
      setTimeout(() => {
        btn.textContent = 'Copiar';
      }, 2000);
    }
  });
});
