/* Foco del menú nativo de Streamlit. No lee credenciales ni modifica la sesión. */
(() => {
  window.__upcFocoCuenta?.disconnect();
  let anterior = null;
  const visible = (e) => e.getClientRects().length && getComputedStyle(e).visibility === 'visible';
  const ajustar = () => {
    const activador = [...document.querySelectorAll('.st-key-menu_cuenta [data-testid="stPopoverButton"]')].find(visible);
    const cuerpo = [...document.querySelectorAll('[data-testid="stPopoverBody"]')].find(visible);
    if (!activador || activador.getAttribute('aria-expanded') !== 'true' || !cuerpo) {
      anterior = null;
      return;
    }
    if (cuerpo === anterior) return;
    const opcion = [...cuerpo.querySelectorAll('button:not(:disabled)')].find(visible);
    if (opcion) {
      anterior = cuerpo;
      opcion.focus({preventScroll: true});
    }
  };
  const observador = new MutationObserver(ajustar);
  observador.observe(document.body, {
    childList: true, subtree: true, attributes: true, attributeFilter: ['aria-expanded'],
  });
  window.__upcFocoCuenta = observador;
  ajustar();
})();
