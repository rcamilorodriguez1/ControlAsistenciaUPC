/* Ancho útil del área de contenido, incluida la reserva de scroll de cada motor. */
(() => {
  window.__upcAnchoContenido?.disconnect();
  const contenido = document.querySelector('[data-testid="stMain"]');
  if (!contenido) return;
  const ajustar = () => {
    const ancho = contenido.clientWidth;
    if (!ancho) return;
    const valor = `${ancho}px`;
    if (contenido.style.getPropertyValue('--upc-ancho-contenido') !== valor) {
      contenido.style.setProperty('--upc-ancho-contenido', valor);
    }
  };
  const observador = new ResizeObserver(ajustar);
  observador.observe(contenido);
  window.__upcAnchoContenido = observador;
  ajustar();
})();
