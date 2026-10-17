"use strict";
document.getElementById("migration-select-all")?.addEventListener("change", event => {
  document.querySelectorAll('input[name="rows"]').forEach(box => { box.checked = event.target.checked; });
});
