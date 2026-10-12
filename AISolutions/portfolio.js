// Remember this website visit for the current tab across all portfolio pages.
const isFirstPortfolioVisit = (() => {
  const visitKey = 'khani-solutions-visit-v1';
  try {
    const alreadyOpened = sessionStorage.getItem(visitKey) === '1';
    sessionStorage.setItem(visitKey, '1');
    return !alreadyOpened;
  } catch {
    // Navigation still skips the intro when browser storage is unavailable.
    return !document.referrer || new URL(document.referrer).origin !== location.origin;
  }
})();

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
    const video = item.querySelector('video');
    if (video && item.hidden) video.pause();
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
  document.querySelectorAll('[data-publication-group]').forEach(group => {
    group.hidden = !Array.from(group.querySelectorAll('.paper')).some(paper => !paper.hidden);
  });
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
if (location.pathname === '/' || location.pathname === '/index.html' || location.pathname.endsWith('/AISolutions/') || location.pathname.endsWith('/AISolutions/index.html')) {
  if (location.hash === '#contact') location.replace('/AISolutions/contact.html');
  if (location.hash === '#portfolio') location.replace('/AISolutions/experience.html');
}

// Company video groups are optional. Load embeds on demand and stop on close.
function initializeCompanyDemos(container) {
  container.querySelectorAll('.company-demos').forEach(group => {
    function updateMedia() {
      group.querySelectorAll('iframe[data-demo-src]').forEach(frame => {
        if (group.open && !frame.hasAttribute('src')) frame.src = frame.dataset.demoSrc;
        else if (!group.open) frame.removeAttribute('src');
      });
      if (!group.open) group.querySelectorAll('video').forEach(player => player.pause());
    }
    group.addEventListener('toggle', () => {
      updateMedia();
    });
    updateMedia();
  });
}
initializeCompanyDemos(document);

// Overview previews use the published Experience page as their only content source.
const companyDialog = document.querySelector('#company-dialog');
if (companyDialog && typeof companyDialog.showModal === 'function') {
  const title = companyDialog.querySelector('#company-dialog-title');
  const body = companyDialog.querySelector('.company-dialog-body');
  const status = companyDialog.querySelector('.company-dialog-status');
  const sourceLink = companyDialog.querySelector('[data-company-source]');
  const retry = companyDialog.querySelector('.company-dialog-retry');
  let opener;
  let request;

  function stopMedia() {
    body.querySelectorAll('video').forEach(player => player.pause());
    body.querySelectorAll('iframe').forEach(frame => frame.removeAttribute('src'));
  }

  async function loadCompany() {
    request?.abort();
    const controller = new AbortController();
    request = controller;
    const source = new URL(opener.href);
    sourceLink.href = source.href;
    title.textContent = opener.querySelector('img').alt;
    stopMedia();
    body.replaceChildren();
    retry.hidden = true;
    status.hidden = false;
    status.textContent = 'Loading experience…';
    companyDialog.setAttribute('aria-busy', 'true');
    try {
      const response = await fetch(source.origin + source.pathname, {cache: 'no-store', signal: controller.signal});
      if (!response.ok) throw new Error('Experience page unavailable');
      const documentSource = new DOMParser().parseFromString(await response.text(), 'text/html');
      const section = documentSource.getElementById(source.hash.slice(1));
      if (!section?.matches('.company-experience')) throw new Error('Company section unavailable');
      if (controller.signal.aborted || !companyDialog.open) return;
      const preview = document.importNode(section, true);
      preview.id = 'preview-' + section.id;
      // Keep imported content passive and resolve any relative links to its source page.
      preview.querySelectorAll('script,style,link,base').forEach(element => element.remove());
      preview.querySelectorAll('*').forEach(element => {
        for (const attribute of [...element.attributes]) {
          if (attribute.name.startsWith('on')) element.removeAttribute(attribute.name);
        }
        for (const attribute of ['href','src','poster']) {
          if (element.hasAttribute(attribute)) element.setAttribute(attribute, new URL(element.getAttribute(attribute), response.url).href);
        }
      });
      const companyHeading = preview.querySelector('.company-heading h2');
      title.textContent = companyHeading.textContent;
      companyHeading.remove();
      const demos = preview.querySelector('.company-demos');
      if (demos) {
        preview.querySelector('.company-heading').after(demos);
        demos.open = true;
      }
      const firstRole = preview.querySelector('.company-position');
      if (firstRole) {
        const workHeading = document.createElement('p');
        workHeading.className = 'eyebrow company-dialog-work';
        workHeading.textContent = 'Work & responsibilities';
        firstRole.before(workHeading);
      }
      body.append(preview);
      initializeCompanyDemos(preview);
      status.hidden = true;
    } catch (error) {
      if (controller.signal.aborted) return;
      status.textContent = 'The company details could not load. Try again or open the full Experience page below.';
      retry.hidden = false;
    } finally {
      if (request === controller) companyDialog.removeAttribute('aria-busy');
    }
  }

  document.querySelectorAll('[data-company-preview]').forEach(link => {
    link.setAttribute('aria-haspopup', 'dialog');
    link.setAttribute('aria-controls', 'company-dialog');
    link.addEventListener('click', event => {
      // Modified clicks retain the normal Experience-page link behavior.
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      opener = link;
      companyDialog.showModal();
      document.body.classList.add('company-modal-open');
      companyDialog.scrollTop = 0;
      loadCompany();
    });
  });
  companyDialog.querySelector('.company-dialog-close').addEventListener('click', () => companyDialog.close());
  retry.addEventListener('click', loadCompany);
  companyDialog.addEventListener('click', event => {
    if (event.target !== companyDialog) return;
    const bounds = companyDialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) companyDialog.close();
  });
  companyDialog.addEventListener('close', () => {
    request?.abort();
    stopMedia();
    body.replaceChildren();
    document.body.classList.remove('company-modal-open');
    opener?.focus({preventScroll: true});
  });
}
