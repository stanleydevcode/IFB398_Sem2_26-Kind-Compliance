(() => {
  const tabs = [...document.querySelectorAll('[data-tab]')];
  function show(name, hash = true) {
    if (!tabs.some(tab => tab.dataset.tab === name)) name = 'people';
    tabs.forEach(tab => {
      const active = tab.dataset.tab === name;
      tab.classList.toggle('active', active); tab.setAttribute('aria-selected', String(active)); tab.tabIndex = active ? 0 : -1;
    });
    document.querySelectorAll('[data-pane]').forEach(pane => { pane.hidden = pane.dataset.pane !== name; });
    if (hash) history.replaceState(null, '', '#' + name);
  }
  tabs.forEach((tab, i) => {
    tab.addEventListener('click', () => show(tab.dataset.tab));
    tab.addEventListener('keydown', event => {
      let next;
      if (event.key === 'ArrowRight') next = (i + 1) % tabs.length;
      if (event.key === 'ArrowLeft') next = (i + tabs.length - 1) % tabs.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = tabs.length - 1;
      if (next !== undefined) { event.preventDefault(); show(tabs[next].dataset.tab); tabs[next].focus(); }
    });
  });
  show(location.hash.slice(1), false);
  window.addEventListener('hashchange', () => show(location.hash.slice(1), false));
  document.getElementById('p-search').addEventListener('input', event => {
    const q = event.target.value.trim().toLowerCase();
    const rows = [...document.querySelectorAll('[data-pane=people] tbody tr[data-q]')];
    rows.forEach(row => { row.hidden = !row.dataset.q.includes(q); });
    document.getElementById('p-empty').hidden = rows.some(row => !row.hidden);
  });
  let filter = 'all';
  function filterNotes(value = filter) {
    filter = value;
    document.querySelectorAll('[data-nf]').forEach(button => button.classList.toggle('active', button.dataset.nf === value));
    const rows = [...document.querySelectorAll('[data-pane=notes] tbody tr[data-type]')];
    rows.forEach(row => { row.hidden = !(value === 'all' || (value === 'follow' ? row.dataset.follow === '1' : value === 'incident' ? row.dataset.incident === '1' : row.dataset.type === value)); });
    document.getElementById('n-empty').hidden = rows.some(row => !row.hidden);
  }
  document.querySelectorAll('[data-nf]').forEach(button => button.addEventListener('click', () => filterNotes(button.dataset.nf)));
  document.querySelectorAll('[data-resolve]').forEach(button => button.addEventListener('click', () => {
    const row = button.closest('tr'); row.dataset.follow = '0'; row.querySelector('.kc-pill.warn')?.remove(); button.remove(); filterNotes();
    kcToast('Example marked as followed up in this page only. No record was saved.');
  }));
})();
