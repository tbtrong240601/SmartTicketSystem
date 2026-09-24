document.addEventListener('submit', function(event) {
  const form = event.target;
  if (form.dataset.confirm && !window.confirm(form.dataset.confirm)) { event.preventDefault(); return; }
  const button = form.querySelector('[data-loading]');
  if (button) { button.disabled = true; button.textContent = button.dataset.loading; }
});
