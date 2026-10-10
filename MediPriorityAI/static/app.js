document.addEventListener('DOMContentLoaded', () => {
  const date = document.getElementById('todayDate');
  if (date) date.textContent = new Intl.DateTimeFormat('en-IN', {weekday:'short', day:'2-digit', month:'short', year:'numeric'}).format(new Date());
  document.querySelectorAll('[data-toggle-password]').forEach(btn => btn.addEventListener('click', () => {
    const input = btn.parentElement.querySelector('input');
    if (!input) return;
    input.type = input.type === 'password' ? 'text' : 'password';
    btn.textContent = input.type === 'password' ? 'Show' : 'Hide';
  }));
  const fillDemo = document.querySelector('[data-fill-demo]');
  if (fillDemo) fillDemo.addEventListener('click', () => {
    const email = document.querySelector('input[name="email"]');
    const password = document.querySelector('input[name="password"]');
    if (email && password) { email.value = 'demo@medipriority.ai'; password.value = 'Demo@123'; }
  });
  const search = document.getElementById('patientSearch');
  const urgency = document.getElementById('urgencyFilter');
  const status = document.getElementById('statusFilter');
  const rows = [...document.querySelectorAll('#patientRows tr')];
  const visibleCount = document.getElementById('visibleCount');
  const emptyState = document.getElementById('emptyState');
  function filterRows() {
    const q = (search?.value || '').toLowerCase().trim();
    let shown = 0;
    rows.forEach(row => {
      const text = `${row.dataset.name} ${row.dataset.code} ${row.dataset.symptoms}`;
      const visible = text.includes(q) && (!urgency?.value || row.dataset.urgency === urgency.value) && (!status?.value || row.dataset.status === status.value);
      row.hidden = !visible;
      if (visible) shown++;
    });
    if (visibleCount) visibleCount.textContent = shown;
    if (emptyState) emptyState.hidden = shown !== 0;
  }
  [search, urgency, status].forEach(el => el?.addEventListener('input', filterRows));
  document.querySelectorAll('.flash').forEach(el => setTimeout(() => { if (el.isConnected) el.classList.add('fade-out'); }, 6500));
});
