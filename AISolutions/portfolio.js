const toggle = document.querySelector('.nav-toggle');
const nav = document.querySelector('#site-nav');
function closeMenu(restoreFocus = false) {
  nav.classList.remove('is-open');
  toggle.setAttribute('aria-expanded', 'false');
  if (restoreFocus) toggle.focus();
}
toggle.addEventListener('click', () => {
  const open = toggle.getAttribute('aria-expanded') !== 'true';
  nav.classList.toggle('is-open', open);
  toggle.setAttribute('aria-expanded', String(open));
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') closeMenu(true);
});
document.addEventListener('click', event => {
  if (!event.target.closest('.header-inner')) closeMenu();
});
nav.addEventListener('click', event => { if (event.target.closest('a')) closeMenu(); });
window.matchMedia('(min-width: 861px)').addEventListener('change', event => { if (event.matches) closeMenu(); });
const filters = document.querySelectorAll('[data-filter]');
filters.forEach(button => button.addEventListener('click', () => {
  const category = button.dataset.filter;
  filters.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  let visible = 0;
  document.querySelectorAll('.filter-item').forEach(item => {
    item.hidden = category !== 'All' && item.dataset.category !== category;
    if (!item.hidden) visible++;
    const frame = item.querySelector('iframe');
    if (frame && item.hidden && frame.hasAttribute('src')) {
      frame.dataset.source = frame.src;
      frame.removeAttribute('src');
    } else if (frame && !item.hidden && !frame.hasAttribute('src') && frame.dataset.source) {
      frame.src = frame.dataset.source;
    }
  });
  document.querySelector('[data-filter-status]').textContent = `${visible} simulations shown.`;
}));
const search = document.querySelector('[data-search]');
search?.addEventListener('input', () => {
  const query = search.value.trim().toLocaleLowerCase();
  let visible = 0;
  document.querySelectorAll('.paper').forEach(item => {
    item.hidden = !item.textContent.toLocaleLowerCase().includes(query);
    if (!item.hidden) visible++;
  });
  document.querySelector('[data-empty]').hidden = visible > 0;
  document.querySelector('[data-search-status]').textContent = `${visible} publications shown.`;
});
document.querySelector('.contact-form')?.addEventListener('submit', event => {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  const subject = `${data.get('topic')} — ${data.get('name')}`;
  const body = `Name: ${data.get('name')}\nEmail: ${data.get('email')}\nOrganization: ${data.get('organization') || 'Not provided'}\n\n${data.get('message')}`;
  window.location.href = `mailto:mkhani.phd@gmail.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  document.querySelector('[data-form-status]').textContent = 'Your email app should open with a draft. If it does not, email mkhani.phd@gmail.com directly.';
});
// Preserve old contact links when visitors arrive at the former single-page site.
if (location.pathname.endsWith('/AISolutions/') || location.pathname.endsWith('/AISolutions/index.html')) {
  if (location.hash === '#contact') location.replace('contact.html');
  if (location.hash === '#portfolio') location.replace('experience.html');
}
