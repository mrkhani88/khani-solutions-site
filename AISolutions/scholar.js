/* Same-origin, last-verified snapshot. Visitors never scrape Scholar. */
(() => {
  const summaries = [...document.querySelectorAll('[data-scholar-summary]')];
  if (!summaries.length && !document.querySelector('[data-scholar-paper]')) return;
  let snapshot = null;
  const integer = n => Number.isSafeInteger(n) && n >= 0;
  const safeLink = value => {
    try { const u = new URL(value); return u.protocol === 'https:' && u.hostname === 'scholar.google.com' && !u.username && !u.password && !u.port && ['/citations', '/scholar'].includes(u.pathname); }
    catch { return false; }
  };
  function valid(data) {
    return data?.schema_version === 1 && data.profile_id === 'ipaKdZ4AAAAJ' && safeLink(data.profile_url)
      && Number.isFinite(Date.parse(data.checked_at)) && /^Since \d{4}$/.test(data.recent_label)
      && ['citations', 'h_index', 'i10_index'].every(k => integer(data.metrics?.[k]?.all) && integer(data.metrics?.[k]?.recent) && data.metrics[k].recent <= data.metrics[k].all)
      && Array.isArray(data.annual_citations) && data.annual_citations.length > 0
      && data.annual_citations.every((p, i, a) => integer(p.year) && p.year >= 1900 && p.year <= 2200 && integer(p.citations) && (!i || p.year > a[i-1].year))
      && Array.isArray(data.coauthors) && data.coauthors.every(p => typeof p.name === 'string' && typeof p.affiliation === 'string' && safeLink(p.url))
      && (!data.public_access || (integer(data.public_access.available) && integer(data.public_access.not_available) && safeLink(data.public_access.url)))
      && data.articles && Object.values(data.articles).every(p => integer(p.citations) && safeLink(p.record_url) && (!p.cited_by_url || safeLink(p.cited_by_url)));
  }
  function textNode(tag, text, className) {
    const node = document.createElement(tag); node.textContent = text;
    if (className) node.className = className;
    return node;
  }
  function paintChart(section) {
    const chart = section.querySelector('[data-scholar-chart]');
    if (!chart || !snapshot) return;
    const recent = section.querySelector('[data-scholar-chart-period="recent"][aria-pressed="true"]');
    const start = Number(snapshot.recent_label.match(/\d{4}/)[0]);
    const rows = snapshot.annual_citations.filter(p => !recent || p.year >= start);
    const peak = Math.max(1, ...rows.map(p => p.citations));
    chart.replaceChildren(...rows.map(p => {
      const li = document.createElement('li'), bar = document.createElement('button');
      bar.type = 'button'; bar.className = 'scholar-bar';
      bar.dataset.scholarYear = p.year; bar.dataset.citations = p.citations;
      bar.setAttribute('aria-label', `${p.year}: ${p.citations} citations`);
      bar.setAttribute('aria-pressed', 'false');
      const fill = textNode('span', '', 'scholar-bar-fill');
      fill.style.setProperty('--bar-height', `${100 * p.citations / peak}%`);
      bar.append(textNode('span', p.citations, 'scholar-bar-count'), fill, textNode('span', p.year, 'scholar-bar-year'));
      li.append(bar); return li;
    }));
  }
  function patchPapers(root = document) {
    if (!snapshot) return;
    root.querySelectorAll('[data-scholar-paper]').forEach(a => {
      const record = snapshot.articles[a.dataset.scholarPaper];
      if (!record) return;
      const label = `Cited by ${record.citations}${record.estimated ? '*' : ''} ↗`;
      const decoratedLabel = a.querySelector('.action-label');
      if ((decoratedLabel || a).textContent !== label) (decoratedLabel || a).textContent = label;
      if (a.href !== (record.cited_by_url || record.record_url)) a.href = record.cited_by_url || record.record_url;
    });
  }
  summaries.forEach(section => section.addEventListener('click', event => {
    const period = event.target.closest('[data-scholar-chart-period]');
    const bar = event.target.closest('[data-scholar-year]');
    if (period) {
      section.querySelectorAll('[data-scholar-chart-period]').forEach(b => b.setAttribute('aria-pressed', String(b === period)));
      if (snapshot) paintChart(section);
      else {
        const start = Number(section.querySelector('[data-scholar-recent-label]').textContent.match(/\d{4}/)[0]);
        section.querySelectorAll('[data-scholar-year]').forEach(b => { b.closest('li').hidden = period.dataset.scholarChartPeriod === 'recent' && Number(b.dataset.scholarYear) < start; });
      }
      section.querySelector('[data-scholar-chart-status]').textContent = `${period.textContent} · Select a year to inspect its citation count. The current year is still in progress.`;
    }
    if (bar) {
      section.querySelectorAll('[data-scholar-year]').forEach(b => b.setAttribute('aria-pressed', String(b === bar)));
      const partial = Number(bar.dataset.scholarYear) === new Date().getUTCFullYear() ? ' · Year in progress.' : '.';
      section.querySelector('[data-scholar-chart-status]').textContent = `${bar.dataset.scholarYear}: ${bar.dataset.citations} citations${partial}`;
    }
  }));
  function freshness(section, data) {
    const date = new Date(data.checked_at);
    const time = textNode('time', date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' }));
    time.dateTime = data.checked_at; time.dataset.scholarChecked = '';
    const stale = Date.now() - date.getTime() > 72 * 3600 * 1000;
    section.querySelector('[data-scholar-freshness]').replaceChildren('Google Scholar · Last verified ', time, stale ? ' · Check Scholar for the latest counts.' : ' · Refreshes daily.');
  }
  // Also make the embedded timestamp honest when the JSON request is unavailable.
  summaries.forEach(section => {
    const time = section.querySelector('[data-scholar-checked]');
    if (time && Date.now() - Date.parse(time.dateTime) > 72 * 3600 * 1000)
      freshness(section, {checked_at: time.dateTime});
  });
  fetch('/assets/scholar/profile.json', {cache: 'no-cache'})
    .then(r => { if (!r.ok) throw new Error('Snapshot unavailable'); return r.json(); })
    .then(data => {
      if (!valid(data)) throw new Error('Invalid snapshot');
      snapshot = data;
      summaries.forEach(section => {
        section.querySelectorAll('[data-scholar-metric]').forEach(node => { node.textContent = data.metrics[node.dataset.scholarMetric][node.dataset.period]; });
        section.querySelectorAll('[data-scholar-recent-label], [data-scholar-chart-period="recent"]').forEach(node => { node.textContent = data.recent_label; });
        freshness(section, data); paintChart(section);
        const access = section.querySelector('[data-scholar-access]');
        if (access) {
          access.hidden = !data.public_access;
          if (data.public_access) {
            const p = data.public_access, total = p.available + p.not_available;
            access.querySelector('[data-scholar-available]').textContent = p.available;
            access.querySelector('[data-scholar-unavailable]').textContent = `${p.not_available}${p.recused ? '*' : ''}`;
            access.querySelector('[data-scholar-access-fill]').style.width = `${total ? 100*p.available/total : 0}%`;
            access.querySelector('.scholar-access-link').href = p.url;
          }
        }
        const coauthors = section.querySelector('[data-scholar-coauthors]');
        if (coauthors) coauthors.replaceChildren(...data.coauthors.map(p => {
          const li = document.createElement('li'), a = document.createElement('a');
          a.href = p.url; a.target = '_blank'; a.rel = 'noopener';
          const arrow = textNode('span', '↗', 'coauthor-arrow'); arrow.setAttribute('aria-hidden', 'true');
          a.append(textNode('strong', p.name), textNode('span', p.affiliation), arrow); li.append(a); return li;
        }));
      });
      patchPapers();
    }).catch(() => { /* Keep the dated, server-rendered snapshot. */ });
  const popup = document.querySelector('.company-dialog');
  if (popup) new MutationObserver(() => patchPapers(popup)).observe(popup, {childList: true, subtree: true});
})();
