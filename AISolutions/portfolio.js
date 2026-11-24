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

const preparedVideos = new WeakSet();
const conserveVideoData = navigator.connection?.saveData || /2g/.test(navigator.connection?.effectiveType ?? '');
function warmVideo(video) {
  if (video.preload === 'auto' || video.error || !video.paused) return;
  video.preload = conserveVideoData ? 'metadata' : 'auto';
  if (video.networkState === HTMLMediaElement.NETWORK_EMPTY) video.load();
}
const videoObserver = typeof IntersectionObserver === 'function' && new IntersectionObserver(entries => {
  entries.forEach(({target, isIntersecting}) => {
    if (!isIntersecting) return;
    warmVideo(target);
    videoObserver.unobserve(target);
  });
}, {rootMargin: '120px 0px'});

function initializeProjectMedia(container) {
  container.querySelectorAll('.simulation-card, .company-demo').forEach(card => {
    const video = card.querySelector('video[controls]');
    if (!video) return;
    let media = video;
    while (media.parentElement !== card) media = media.parentElement;
    if (media !== card.firstElementChild) card.prepend(media);
  });

  container.querySelectorAll('video[controls][playsinline]').forEach(video => {
    if (preparedVideos.has(video)) return;
    preparedVideos.add(video);
    const player = document.createElement('div');
    player.className = 'portfolio-video-player';
    video.before(player);
    player.append(video);

    const play = document.createElement('button');
    play.type = 'button';
    play.className = 'portfolio-video-play';
    const heading = video.closest('.simulation-card, .company-demo')?.querySelector('h2, h4');
    const labelledBy = document.getElementById(video.getAttribute('aria-labelledby'));
    const name = heading?.textContent || labelledBy?.textContent || video.getAttribute('aria-label');
    play.setAttribute('aria-label', name ? `Play ${name}` : 'Play video');
    player.append(play);

    const status = document.createElement('p');
    status.className = 'portfolio-video-status';
    status.setAttribute('role', 'status');
    status.hidden = true;
    player.append(status);

    function showVideoError(message) {
      status.replaceChildren(message);
      const source = video.querySelector('source[type="video/mp4"]')?.src || video.src;
      if (source) {
        const link = document.createElement('a');
        link.href = source;
        link.textContent = 'Open MP4';
        status.append(link);
      }
      status.hidden = false;
      play.classList.remove('is-playing');
    }
    play.addEventListener('click', () => {
      video.play().catch(error => {
        if (error.name !== 'AbortError') showVideoError('Playback could not start. ');
      });
    });
    video.addEventListener('playing', () => {
      play.classList.add('is-playing');
      status.hidden = true;
    });
    video.addEventListener('pause', () => play.classList.remove('is-playing'));
    video.addEventListener('ended', () => play.classList.remove('is-playing'));
    video.addEventListener('error', () => showVideoError('Video unavailable. '));
    player.addEventListener('pointerenter', () => warmVideo(video), {once: true});
    play.addEventListener('focus', () => warmVideo(video), {once: true});
    videoObserver && videoObserver.observe(video);
  });
}

initializeProjectMedia(document);

document.addEventListener('play', event => {
  if (!event.target.matches?.('.portfolio-video-player video')) return;
  document.querySelectorAll('.portfolio-video-player video').forEach(video => {
    if (video !== event.target && !video.paused) video.pause();
  });
}, true);

// Company video groups are optional. Stop playback when a group closes.
function initializeCompanyDemos(container) {
  container.querySelectorAll('.company-demos').forEach(group => {
    group.addEventListener('toggle', () => {
      if (!group.open) group.querySelectorAll('video').forEach(player => player.pause());
    });
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
      const response = await fetch(source.origin + source.pathname, {signal: controller.signal});
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
      initializeProjectMedia(preview);
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
      document.querySelectorAll('[data-analysis-grid] video').forEach(player => player.pause());
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

// Analysis filters combine modeling method with the shared Experience identifier.
const analysisGrid = document.querySelector('[data-analysis-grid]');
if (analysisGrid) {
  const methodButtons = [...document.querySelectorAll('[data-analysis-method]')];
  const companySelect = document.querySelector('[data-analysis-company]');
  const entries = [...analysisGrid.querySelectorAll('.filter-item')];
  function updateAnalysis() {
    const method = methodButtons.find(b => b.getAttribute('aria-pressed') === 'true').dataset.analysisMethod;
    const company = companySelect.value;
    let count = 0;
    entries.forEach(entry => {
      entry.hidden = !((method === 'all' || entry.dataset.method === method) && (company === 'all' || (entry.dataset.analysisCompanyIds || '').split(' ').includes(company)));
      if (!entry.hidden) count++;
      else {
        entry.querySelectorAll('video').forEach(video => video.pause());
      }
    });
    document.querySelector('[data-analysis-status]').textContent = `${count} ${count === 1 ? 'entry' : 'entries'} shown.`;
    document.querySelector('[data-analysis-empty]').hidden = count > 0;
  }
  methodButtons.forEach(button => button.addEventListener('click', () => {
    methodButtons.forEach(b => b.setAttribute('aria-pressed', String(b === button)));
    updateAnalysis();
  }));
  companySelect.addEventListener('change', updateAnalysis);
  document.querySelector('[data-analysis-reset]').addEventListener('click', () => {
    methodButtons.forEach(b => b.setAttribute('aria-pressed', String(b.dataset.analysisMethod === 'all')));
    companySelect.value = 'all'; updateAnalysis(); methodButtons[0].focus();
  });
}
