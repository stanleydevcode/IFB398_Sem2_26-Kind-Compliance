// Shared scripts: toasts, search and countdown timers

// small popup message in the corner
function kcToast(message) {
  const toastEl = document.getElementById('kc-toast');
  if (!toastEl) return;
  toastEl.querySelector('.toast-body span').textContent = message;
  bootstrap.Toast.getOrCreateInstance(toastEl, { delay: 2600 }).show();
}

// any element with data-toast="..." shows that message when clicked
document.addEventListener('click', function (e) {
  const el = e.target.closest('[data-toast]');
  if (!el) return;
  if (el.tagName === 'A' && el.getAttribute('href') === '#') e.preventDefault();
  kcToast(el.dataset.toast);
});

// search box
const searchInput = document.getElementById('kc-search-input');
const searchResults = document.getElementById('kc-search-results');
const searchData = document.getElementById('kc-search-index');

if (searchInput && searchResults && searchData) {
  const items = JSON.parse(searchData.textContent);

  function showResults() {
    const query = searchInput.value.trim().toLowerCase();
    if (query === '') {
      searchResults.classList.remove('show');
      return;
    }
    let html = '';
    let count = 0;
    items.forEach(function (item) {
      if (count < 8 && item.label.toLowerCase().includes(query)) {
        html += '<a class="dropdown-item" href="' + item.url + '"><span>' + item.label + '</span><small>' + item.kind + '</small></a>';
        count++;
      }
    });
    if (count === 0) {
      html = '<span class="dropdown-item-text small text-secondary">No results</span>';
    }
    searchResults.innerHTML = html;
    searchResults.classList.add('show');
  }

  searchInput.addEventListener('input', showResults);
  searchInput.addEventListener('focus', showResults);
  searchInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
      const first = searchResults.querySelector('a');
      if (first) window.location.href = first.href;
    }
    if (e.key === 'Escape') {
      searchResults.classList.remove('show');
      searchInput.blur();
    }
  });
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.kc-search')) searchResults.classList.remove('show');
  });
}

// countdown timers: <span data-countdown="seconds">
document.querySelectorAll('[data-countdown]').forEach(function (el) {
  let secondsLeft = parseInt(el.dataset.countdown);

  function draw() {
    const h = Math.floor(secondsLeft / 3600);
    const m = Math.floor((secondsLeft % 3600) / 60);
    const s = secondsLeft % 60;
    el.textContent = String(h).padStart(2, '0') + ':' + String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
  }

  draw();
  setInterval(function () {
    if (secondsLeft > 0) {
      secondsLeft--;
      draw();
    }
  }, 1000);
});
