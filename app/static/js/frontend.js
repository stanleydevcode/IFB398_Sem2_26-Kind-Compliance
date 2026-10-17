/* Local UI previews only. No requests, persistence, invitations or database writes. */
(() => {
  document.querySelectorAll('[data-preview-role]').forEach(select => select.addEventListener('change', () => kcToast('Role selection preview only. No account permissions changed.')));
  const validate = form => {
    let valid = true;
    form.querySelectorAll('input, select, textarea').forEach(field => {
      if (field.type === 'file' && field.files.length) {
        const f = field.files[0];
        field.setCustomValidity(/\.(pdf|png|jpe?g|webp|gif|bmp)$/i.test(f.name) ? '' : 'Choose a PDF or image.');
      }
      const bad = !field.checkValidity() || (field.required && !field.value.trim());
      field.classList.toggle('is-invalid', bad);
      if (bad) valid = false;
    });
    if (!valid) form.querySelector('.is-invalid')?.focus();
    return valid;
  };
  document.querySelectorAll('[data-preview-form]').forEach(form => {
    form.addEventListener('submit', event => {
      event.preventDefault();
      if (!validate(form)) {
        kcToast('Check the required fields and file type.');
        return;
      }
      bootstrap.Modal.getInstance(form.closest('.modal'))?.hide();
      kcToast('Form preview validated. Nothing was saved, uploaded or sent.');
    });
  });
  document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('show.bs.modal', event => {
      const form = modal.querySelector('form');
      if (form) {
        form.reset();
        form.querySelectorAll('.is-invalid').forEach(field => field.classList.remove('is-invalid'));
        form.querySelectorAll('input[type=file]').forEach(field => field.setCustomValidity(''));
        modal.querySelectorAll('[data-file-selection]').forEach(label => { label.textContent = ''; });
        modal.querySelectorAll('.has-file').forEach(drop => drop.classList.remove('has-file'));
      }
      const pid = event.relatedTarget?.dataset.pid;
      const select = modal.querySelector('#nt-p, #ho-p');
      if (select && pid) select.value = pid;
      const credential = event.relatedTarget?.dataset.cred;
      const credentialSelect = modal.querySelector('#rn-cred');
      if (credentialSelect && credential) credentialSelect.value = credential;
    });
  });
  document.querySelectorAll('input[type=file]').forEach(field => {
    field.addEventListener('change', () => {
      field.setCustomValidity('');
      const drop = field.closest('.kc-drop');
      if (!drop) return;
      drop.classList.toggle('has-file', field.files.length > 0);
      let name = drop.querySelector('[data-file-selection]');
      if (!name) { name = document.createElement('span'); name.dataset.fileSelection = ''; name.className = 'small'; drop.append(name); }
      name.textContent = field.files[0]?.name || '';
    });
  });
})();
