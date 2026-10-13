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

  const modal = document.getElementById('import-modal');
  if (!modal) return;
  const fileInput = document.getElementById('im-file');
  const fileNote = document.getElementById('im-file-note');
  const row5 = document.getElementById('im-row-5');
  const row9 = document.getElementById('im-row-9');
  function step(number) {
    modal.querySelectorAll('[data-im-step]').forEach(pane => {
      pane.hidden = Number(pane.dataset.imStep) !== number;
    });
    document.getElementById('im-step-label').textContent = number === 1
      ? 'Step 1 of 2: Upload your file' : 'Step 2 of 2: Review example rows';
    document.getElementById('im-confirm').hidden = number !== 2;
    document.getElementById('im-back').hidden = number !== 2;
  }
  function updateSummary() {
    const count = 10 + Number(row5.value !== 'skip') + Number(row9.value !== 'skip');
    const skipped = 12 - count;
    document.getElementById('im-summary').textContent = `${count} workers selected for import · ${skipped} ${skipped === 1 ? 'row' : 'rows'} skipped (example)`;
  }
  function selectedFile(file) {
    if (!file) return;
    const valid = /\.(csv|xlsx|xls)$/i.test(file.name);
    document.getElementById('im-drop').classList.toggle('has-file', valid);
    fileNote.classList.toggle('text-danger', !valid);
    fileNote.classList.toggle('text-secondary', valid);
    fileNote.textContent = valid
      ? `${file.name} selected. File preview will be available when importing is connected. You can try the example below.`
      : 'Choose a CSV or Excel file (.csv, .xlsx or .xls).';
    if (!valid) fileInput.value = '';
  }
  modal.addEventListener('show.bs.modal', () => {
    step(1);
    fileInput.value = '';
    row5.value = 'import';
    row9.value = 'skip';
    document.getElementById('im-drop').classList.remove('has-file');
    fileNote.classList.remove('text-danger');
    fileNote.classList.add('text-secondary');
    fileNote.textContent = 'Try the example file to preview the import steps. No records will be saved.';
    updateSummary();
  });
  fileInput.addEventListener('change', () => selectedFile(fileInput.files[0]));
  const drop = document.getElementById('im-drop');
  drop.addEventListener('dragover', event => event.preventDefault());
  drop.addEventListener('drop', event => {
    event.preventDefault();
    if (event.dataTransfer.files.length !== 1) {
      fileNote.textContent = 'Choose one file at a time.';
      return;
    }
    fileInput.files = event.dataTransfer.files;
    selectedFile(fileInput.files[0]);
  });
  document.getElementById('im-sample').addEventListener('click', () => {
    step(2);
    updateSummary();
  });
  document.getElementById('im-back').addEventListener('click', () => step(1));
  [row5, row9].forEach(select => select.addEventListener('change', updateSummary));
})();
