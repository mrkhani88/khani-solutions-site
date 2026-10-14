(() => {
  const initialized = new WeakSet();
  function init(root) {
    if (initialized.has(root)) return;
    initialized.add(root);
    const video = root.querySelector('video');
    const timeline = JSON.parse(root.dataset.timeline);
    const cases = [...root.querySelectorAll('[data-sweep-case]')];
    const modes = [...root.querySelectorAll('[data-sweep-mode]')];
    const cuts = [...root.querySelectorAll('[data-sweep-cut]')];
    const output = root.querySelector('[data-sweep-active]');
    const status = root.querySelector('[data-sweep-status]');
    const download = root.querySelector('[data-sweep-download]');
    let mode = 'Lift', cut = 3, pendingSeek = null, revision = 0, switching = false, desiredPhase = 0;
    const frame = () => Math.min(timeline.length - 1, Math.floor((switching || pendingSeek !== null ? desiredPhase : video.currentTime / cut) * timeline.length));
    function update() {
      const f = frame(), selected = timeline[f];
      cases.forEach((b, i) => b.setAttribute('aria-pressed', String(i === selected)));
      output.textContent = `${2 * selected}° · ${f < timeline.length / 2 ? 'increasing' : 'returning'}`;
    }
    function seek(target) {
      desiredPhase = target / cut;
      if (video.readyState >= 1 && !switching) {
        pendingSeek = null;
        video.currentTime = Math.min(target, video.duration - .001);
        update();
      } else {pendingSeek = target; update();}
    }
    function load(nextMode, nextCut) {
      const phase = switching || pendingSeek !== null ? desiredPhase : video.currentTime / cut;
      const playing = !video.paused;
      const currentRevision = ++revision;
      mode = nextMode; cut = nextCut; desiredPhase = phase; switching = true;
      modes.forEach(b => b.setAttribute('aria-pressed', String(b.dataset.sweepMode === mode)));
      cuts.forEach(b => b.setAttribute('aria-pressed', String(Number(b.dataset.sweepCut) === cut)));
      status.hidden = true;
      video.poster = `${root.dataset.assets}/${mode}_Poster.png`;
      const src = `${root.dataset.assets}/Midnight_0_to_20_${mode}_${cut}s.mp4`;
      download.href = src;
      video.src = src;
      video.addEventListener('loadedmetadata', () => {
        if (currentRevision !== revision) return;
        switching = false;
        seek(desiredPhase * cut);
        if (playing) video.play().catch(() => {});
      }, {once: true});
    }
    cases.forEach((b, i) => b.addEventListener('click', () => {
      video.pause();
      seek((timeline.indexOf(i) + .25) / timeline.length * cut);
    }));
    modes.forEach(b => b.addEventListener('click', () => {
      if (mode !== b.dataset.sweepMode) load(b.dataset.sweepMode, cut);
    }));
    cuts.forEach(b => b.addEventListener('click', () => {
      if (cut !== Number(b.dataset.sweepCut)) load(mode, Number(b.dataset.sweepCut));
    }));
    video.addEventListener('loadedmetadata', () => {
      if (switching) return;
      if (pendingSeek !== null) {const t = pendingSeek; pendingSeek = null; seek(t);}
      update();
    });
    video.addEventListener('timeupdate', update);
    video.addEventListener('seeked', update);
    video.addEventListener('error', () => {
      status.hidden = false;
      status.textContent = 'Video could not load. Try the download link or refresh the page.';
    });
    update();
  }
  function scan(node) {
    if (node.nodeType !== 1 && node.nodeType !== 9) return;
    if (node.matches?.('[data-midnight-sweep]')) init(node);
    node.querySelectorAll('[data-midnight-sweep]').forEach(init);
  }
  scan(document);
  new MutationObserver(records => records.forEach(r => r.addedNodes.forEach(scan)))
    .observe(document.body, {childList: true, subtree: true});
})();
