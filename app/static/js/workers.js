/* Workers presentation only. No worker, login or migration writes happen here. */
(() => {
  const tabs = [...document.querySelectorAll('[data-tab]')];
  function showTab(name, updateHash = true) {
    if (!tabs.some(tab => tab.dataset.tab === name)) name = 'register';
    tabs.forEach(tab => {
      const active = tab.dataset.tab === name;
      tab.classList.toggle('active', active);
      tab.setAttribute('aria-selected', String(active));
      tab.tabIndex = active ? 0 : -1;
    });
    document.querySelectorAll('[data-pane]').forEach(pane => {
      pane.hidden = pane.dataset.pane !== name;
    });
    if (updateHash) history.replaceState(null, '', '#' + name);
  }
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => showTab(tab.dataset.tab));
    tab.addEventListener('keydown', event => {
      let next;
      if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      if (event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = tabs.length - 1;
      if (next !== undefined) {
        event.preventDefault();
        showTab(tabs[next].dataset.tab);
        tabs[next].focus();
      }
    });
  });
  showTab(location.hash.slice(1), false);
  window.addEventListener('hashchange', () => showTab(location.hash.slice(1), false));

  const filters = ['w-search', 'w-cred', 'w-status', 'w-position'].map(id => document.getElementById(id));
  function filterWorkers() {
    const [search, credential, status, position] = filters.map(input => input.value.trim().toLowerCase());
    const rows = [...document.querySelectorAll('#workers-body tr[data-q]')];
    rows.forEach(row => {
      row.hidden = !((row.dataset.q || '').toLowerCase().includes(search)
        && (!credential || ['bad', 'warn', 'missing'].includes(row.dataset['c' + credential[0].toUpperCase() + credential.slice(1)]))
        && (!status || (status === 'soon' ? row.dataset.soon === '1' : row.dataset.status === status))
        && (!position || (row.dataset.position || '').toLowerCase() === position));
    });
    document.getElementById('workers-empty').hidden = rows.some(row => !row.hidden);
    document.querySelector('#workers-empty .fw-medium').textContent = rows.length ? 'No matching workers' : 'No workers yet';
    const filtered = filters.some(input => input.value);
    document.getElementById('workers-empty-help').textContent = filtered
      ? 'No records match these filters. Clear the filters to view all workers.'
      : 'Worker records will appear here once they are added.';
  }
  filters.forEach(input => input.addEventListener('input', filterWorkers));
  document.querySelectorAll('[data-filter-status]').forEach(counter => {
    counter.addEventListener('click', event => {
      event.preventDefault();
      filters.forEach(input => { input.value = ''; });
      document.getElementById('w-status').value = counter.dataset.filterStatus;
      showTab('register');
      filterWorkers();
    });
  });
  document.getElementById('add-form').addEventListener('submit', event => event.preventDefault());
})();
