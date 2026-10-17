(() => {
  const tabs = [...document.querySelectorAll('[data-tab]')];
  const panes = [...document.querySelectorAll('[data-pane]')];
  if (!tabs.length) return;
  tabs.forEach(tab => tab.addEventListener('click', () => {
    tabs.forEach(other => {
      const active = other === tab;
      other.classList.toggle('active', active);
      other.setAttribute('aria-selected', String(active));
    });
    if (panes.length) panes.forEach(pane => { pane.hidden = pane.dataset.pane !== tab.dataset.tab; });
  }));
})();
