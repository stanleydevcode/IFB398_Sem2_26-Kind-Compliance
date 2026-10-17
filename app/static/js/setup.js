(() => {

const today = new Date();
const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const stepOrder = ['profile', 'insurance', 'groups', 'people', 'rules'];

function formatDate(value) {
  const d = new Date(value + 'T00:00:00');
  return d.getDate() + ' ' + months[d.getMonth()] + ' ' + d.getFullYear();
}

function expiryPill(value) {
  const days = Math.round((new Date(value + 'T00:00:00') - today) / 86400000);
  if (days < 0) return '<span class="kc-pill bad">Lapsed</span>';
  if (days <= 60) return '<span class="kc-pill warn">' + days + ' days</span>';
  return '<span class="kc-pill ok">Valid</span>';
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// returns true if a required field is empty or invalid
function hasErrors(form) {
  let errors = false;
  form.querySelectorAll('[required]').forEach(function (field) {
    const bad = field.value.trim() === '' || !field.checkValidity() || (field.id === 'o-abn' && field.value.replace(/\s/g, '').length !== 11);
    field.classList.toggle('is-invalid', bad);
    if (bad) errors = true;
  });
  return errors;
}

// step status
function setStatus(step, status) {
  const pill = document.querySelector('#step-' + step + ' [data-pill]');
  const tracker = document.querySelector('[data-step-link="' + step + '"]');
  if (status === 'done') {
    pill.className = 'kc-pill ok';
    pill.textContent = 'Done';
  } else if (status === 'now') {
    pill.className = 'kc-pill warn';
    pill.textContent = 'In progress';
  }
  tracker.classList.toggle('done', status === 'done');
  tracker.classList.toggle('now', status === 'now');

  const doneCount = document.querySelectorAll('#steps li.done').length;
  if (doneCount === stepOrder.length) {
    document.getElementById('setup-sub').textContent = 'All steps done in this preview; no data saved';
  } else {
    document.getElementById('setup-sub').textContent = doneCount + ' of ' + stepOrder.length + ' steps done (preview)';
  }
}



// edit buttons (steps 1 and 3)
document.querySelectorAll('.kc-step').forEach(function (section) {
  const view = section.querySelector('[data-view]');
  const form = section.querySelector('[data-form]');
  const editButton = section.querySelector('[data-edit]');
  if (!form || !editButton) return;

  function showForm(show) {
    view.hidden = show;
    form.hidden = !show;
    editButton.hidden = show;
    if (section.id === 'step-groups') updateDocuments();
  }

  editButton.addEventListener('click', function () { showForm(true); });

  form.querySelector('[data-cancel]').addEventListener('click', function () {
    form.reset();
    form.querySelectorAll('.is-invalid').forEach(function (f) { f.classList.remove('is-invalid'); });
    showForm(false);
  });

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (hasErrors(form)) return;
    if (section.id === 'step-groups' && !countDocuments().codes.length) { kcToast('Choose at least one group.'); return; }
    if (section.id === 'step-profile') {
      form.querySelectorAll('[name]').forEach(function (field) {
        const target = section.querySelector('[data-show="' + field.name + '"]');
        if (target) target.textContent = field.value || '—';
      });
      setStatus('profile', 'done'); kcToast('Profile preview updated; no data saved.');
    } else {
      saveGroups();
    }
    // Keep the in-page preview values if the form is opened again.
    form.querySelectorAll('input:not([type=checkbox]), select, textarea').forEach(function (field) {
      field.defaultValue = field.value;
    });
    form.querySelectorAll('input[type=checkbox]').forEach(function (box) {
      box.defaultChecked = box.checked;
    });
    showForm(false);
  });
});

// Step 3: preview the user's group choices. Requirement counts need backend rules.
const groupBoxes = document.querySelectorAll('#groups-form input[type=checkbox]');

function countDocuments() {
  return { codes: [...groupBoxes].filter(box => box.checked).map(box => box.value) };
}

function updateDocuments() {
  const result = countDocuments();
  document.getElementById('u-groups').textContent = result.codes.length;
  document.getElementById('u-pathway').textContent = 'Not assessed';
  document.getElementById('u-total').textContent = 'Not assessed';
  document.getElementById('u-rows').innerHTML = '';
}

function saveGroups() {
  const result = countDocuments();
  const summary = document.getElementById('step-groups');
  summary.querySelector('[data-sum="groups"]').textContent = result.codes.length;
  summary.querySelector('[data-sum="pathway"]').textContent = 'Not assessed';
  summary.querySelector('[data-sum="total"]').textContent = 'Not assessed';
  summary.querySelector('[data-sum="missing"]').textContent = 'Not assessed';

  let chips = '';
  result.codes.forEach(function (code) {
    const box = [...groupBoxes].find(item => item.value === code);
    const name = box.closest('.kc-reg').querySelector('.nm').textContent;
    chips += '<span class="kc-chip"><b>' + code + '</b>' + escapeHtml(name) + '</span>';
  });
  summary.querySelector('[data-sum="chips"]').innerHTML = chips;
  setStatus('groups', 'done'); kcToast('Group preview updated; no data saved. Requirement counts are pending.');
}

groupBoxes.forEach(function (box) { box.addEventListener('change', updateDocuments); });
updateDocuments();

// step 2: insurance
const insModal = document.getElementById('ins-modal');
const insForm = document.getElementById('ins-form');
let editingRow = null;

insModal.addEventListener('show.bs.modal', function (e) {
  insForm.reset();
  insForm.querySelectorAll('.is-invalid').forEach(function (f) { f.classList.remove('is-invalid'); });
  document.getElementById('in-file-name').textContent = 'Upload the certificate of currency';
  document.getElementById('in-drop').classList.remove('has-file');

  editingRow = null;
  if (e.relatedTarget && e.relatedTarget.hasAttribute('data-row')) {
    editingRow = e.relatedTarget.closest('tr');
  }

  if (editingRow) {
    document.getElementById('in-title').textContent = 'Update policy';
    document.getElementById('in-type').value = editingRow.querySelector('[data-c="type"]').textContent;
    document.getElementById('in-insurer').value = editingRow.querySelector('[data-c="insurer"]').textContent;
    document.getElementById('in-policy').value = editingRow.querySelector('[data-c="policy"]').textContent;
    document.getElementById('in-cover').value = editingRow.querySelector('[data-c="cover"]').textContent;
    document.getElementById('in-exp').value = editingRow.querySelector('[data-c="expires"]').dataset.iso;
  } else {
    document.getElementById('in-title').textContent = 'Add a policy';
  }
});

document.getElementById('in-file').addEventListener('change', function (e) {
  if (!e.target.files[0]) return;
  document.getElementById('in-file-name').textContent = e.target.files[0].name;
  document.getElementById('in-drop').classList.add('has-file');
});

insForm.addEventListener('submit', function (e) {
  e.preventDefault();
  if (hasErrors(insForm)) return;

  let row = editingRow;
  if (!row) {
    row = document.createElement('tr');
    row.innerHTML =
      '<td class="fw-medium" data-c="type"></td><td data-c="insurer"></td><td data-c="policy"></td><td data-c="cover"></td>' +
      '<td><span data-c="expires"></span> <span class="ms-1" data-c="pill"></span></td>' +
      '<td><a href="#" class="kc-doc-link small" data-toast="Selected file preview only. No certificate is stored."><i class="bi bi-file-earmark-pdf me-1"></i><span data-c="file">Certificate pending</span></a></td>' +
      '<td class="text-end"><button class="btn btn-sm btn-outline-kc" data-bs-toggle="modal" data-bs-target="#ins-modal" data-row>Update</button></td>';
    document.querySelector('#ins-table tbody').appendChild(row);
  }

  const emptyRow = document.querySelector('#ins-table [data-empty-row]'); if (emptyRow) emptyRow.remove();
  const expiry = document.getElementById('in-exp').value;
  row.querySelector('[data-c="type"]').textContent = document.getElementById('in-type').value;
  row.querySelector('[data-c="insurer"]').textContent = document.getElementById('in-insurer').value;
  row.querySelector('[data-c="policy"]').textContent = document.getElementById('in-policy').value;
  row.querySelector('[data-c="cover"]').textContent = document.getElementById('in-cover').value || '—';
  row.querySelector('[data-c="expires"]').textContent = formatDate(expiry);
  row.querySelector('[data-c="expires"]').dataset.iso = expiry;
  row.querySelector('[data-c="pill"]').innerHTML = expiryPill(expiry);
  const file = document.getElementById('in-file').files[0];
  if (file) row.querySelector('[data-c="file"]').textContent = file.name;

  bootstrap.Modal.getInstance(insModal).hide();
  setStatus('insurance', 'done'); kcToast('Policy preview updated; no certificate uploaded.');
});

// step 4: key personnel
const peopleForm = document.getElementById('kp-form');
const screening = document.getElementById('k-scr');

screening.addEventListener('change', function () {
  document.getElementById('k-exp-wrap').hidden = screening.value !== 'Cleared';
  document.getElementById('k-exp').required = screening.value === 'Cleared';
});
document.getElementById('k-exp').required = screening.value === 'Cleared';

peopleForm.addEventListener('submit', function (e) {
  e.preventDefault();
  if (hasErrors(peopleForm)) return;

  const name = document.getElementById('k-name').value.trim();
  const parts = name.split(' ');
  let initials = parts[0][0];
  if (parts.length > 1) initials += parts[parts.length - 1][0];

  const expiry = document.getElementById('k-exp').value;
  let screeningCell = '<span class="kc-pill neutral">' + screening.value + '</span>';
  if (screening.value === 'Cleared' && expiry) {
    screeningCell = formatDate(expiry) + ' <span class="ms-1">' + expiryPill(expiry) + '</span>';
  }

  const row = document.createElement('tr');
  row.innerHTML =
    '<td><span class="d-flex align-items-center gap-2"><span class="kc-avatar" style="width:30px;height:30px">' + escapeHtml(initials.toUpperCase()) + '</span>' +
    '<span class="fw-medium">' + escapeHtml(name) + '</span></span></td>' +
    '<td>' + escapeHtml(document.getElementById('k-pos').value) + '</td>' +
    '<td>' + document.getElementById('k-role').value + '</td>' +
    '<td>' + screeningCell + '</td>' +
    '<td><span class="kc-pill info">Preview only</span></td>';
  const emptyRow = document.querySelector('#kp-table [data-empty-row]'); if (emptyRow) emptyRow.remove();
  document.querySelector('#kp-table tbody').appendChild(row);
  ['r-sign', 'r-esc'].forEach(id => { const option = new Option(name, name); document.getElementById(id).add(option); });

  kcToast('Person preview added; no invitation sent.');
  peopleForm.reset();
  screening.dispatchEvent(new Event('change'));
});

document.getElementById('people-done').addEventListener('click', function () {
  if (!document.querySelector('#kp-table tbody tr:not([data-empty-row])')) { kcToast('Add a person before continuing.'); return; }
  setStatus('people', 'done');
  setStatus('rules', 'now');
  document.getElementById('step-rules').scrollIntoView({ behavior: 'smooth' });
});

// step 5: finish
document.getElementById('rules-form').addEventListener('submit', function (e) {
  e.preventDefault();
  if (hasErrors(e.target)) return;
  const incomplete = stepOrder.slice(0,4).filter(step => !document.querySelector('[data-step-link="' + step + '"]').classList.contains('done'));
  if (incomplete.length) { kcToast('Complete the first four sections before finishing the preview.'); document.getElementById('step-' + incomplete[0]).scrollIntoView(); return; }
  setStatus('rules', 'done');
  kcToast('Setup preview complete. Nothing has been saved.');
});

})();
