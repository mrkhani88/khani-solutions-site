import {createFlow, traceStreamline, pointOnStreamline} from './airfoil-flow-model.mjs';

const demo = document.querySelector('[data-airfoil-demo]');
if (demo) {
  const canvas = demo.querySelector('canvas');
  const ctx = canvas.getContext('2d');
  const slider = demo.querySelector('[data-airfoil-angle]');
  const output = demo.querySelector('output');
  const pause = demo.querySelector('[data-airfoil-pause]');
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const playIcon = '<path d="m8 5 11 7-11 7z"/>';
  const pauseIcon = '<path d="M8 5v14M16 5v14"/>';
  let width = 0, height = 0, scale = 1, paths = [], shape = [];
  let paused = motion.matches, visible = true, frame = 0, dirty = true;
  let elapsed = 0, lastTime = 0, angle = Number(slider.value);

  function formatAngle(value) {
    return (value > 0 ? '+' : '') + Number(value.toFixed(1)) + '°';
  }
  function updateLabel() {
    output.value = formatAngle(angle);
    slider.setAttribute('aria-valuetext', String(angle) + ' degrees');
    canvas.setAttribute('aria-label', 'Animated ideal airflow around an airfoil at ' + angle + ' degrees angle of attack.');
  }
  function schedule() {
    if (!frame) frame = requestAnimationFrame(render);
  }
  function setPaused(value) {
    paused = value;
    pause.setAttribute('aria-label', paused ? 'Play flow animation' : 'Pause flow animation');
    pause.setAttribute('aria-pressed', String(paused));
    pause.querySelector('svg').innerHTML = paused ? playIcon : pauseIcon;
    lastTime = 0;
    schedule();
  }
  function toScreen(point) {
    return [width * 0.5 + point.x * scale, height * 0.5 - point.y * scale];
  }
  function rebuild() {
    const box = canvas.getBoundingClientRect();
    width = Math.max(1, box.width); height = Math.max(1, box.height);
    const dpr = Math.min(devicePixelRatio || 1, 2);
    canvas.width = Math.round(width * dpr); canvas.height = Math.round(height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const halfX = width < 600 ? 4.25 : 5.65;
    scale = width / (halfX * 2);
    const halfY = height / (2 * scale);
    const flow = createFlow(angle);
    shape = flow.outline.map(p => toScreen({x: p[0], y: p[1]}));
    const count = width < 600 ? 30 : 38;
    paths = [];
    for (let i = 0; i < count; i++) {
      const y = -halfY + (i + 0.5) * 2 * halfY / count;
      const line = traceStreamline(flow, -halfX - 0.04, y, {xMin: -halfX - 0.04, xMax: halfX + 0.04, yMax: halfY});
      if (line.points.length < 12) continue;
      const path = new Path2D();
      line.points.forEach((p, index) => {
        const xy = toScreen(p);
        if (index) path.lineTo(xy[0], xy[1]); else path.moveTo(xy[0], xy[1]);
      });
      paths.push({...line, path, offset: i * 0.41});
    }
    dirty = false;
  }
  function draw() {
    ctx.clearRect(0, 0, width, height);
    const gradient = ctx.createLinearGradient(0, 0, width, 0);
    gradient.addColorStop(0, 'rgba(100,210,220,.14)');
    gradient.addColorStop(0.28, 'rgba(100,210,220,.46)');
    gradient.addColorStop(0.72, 'rgba(100,210,220,.46)');
    gradient.addColorStop(1, 'rgba(100,210,220,.14)');
    ctx.lineWidth = 1;
    ctx.strokeStyle = gradient;
    paths.forEach(line => ctx.stroke(line.path));
    ctx.strokeStyle = 'rgba(149,236,238,.9)';
    ctx.fillStyle = '#d5ffff';
    ctx.lineWidth = 1.65;
    paths.forEach(line => {
      const count = Math.max(2, Math.round(line.duration / 2.8));
      for (let i = 0; i < count; i++) {
        const t = ((elapsed * 0.85 + line.offset + i * line.duration / count) % line.duration);
        ctx.beginPath();
        for (let j = 0; j <= 5; j++) {
          const p = pointOnStreamline(line, Math.max(0, t - (5 - j) * 0.035));
          const xy = toScreen(p);
          if (j) ctx.lineTo(xy[0], xy[1]); else ctx.moveTo(xy[0], xy[1]);
        }
        ctx.stroke();
      }
    });
    // The solid is drawn last so no integration artifact appears inside it.
    ctx.beginPath();
    shape.forEach((p, i) => i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]));
    ctx.closePath();
    ctx.fillStyle = '#eff7f8';
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,.7)';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.fillStyle = 'rgba(212,232,238,.65)';
    ctx.font = '11px Inter, sans-serif';
    ctx.fillText('FLOW', 20, 29);
    ctx.beginPath();
    ctx.moveTo(62, 25); ctx.lineTo(93, 25);
    ctx.moveTo(88, 21); ctx.lineTo(93, 25); ctx.lineTo(88, 29);
    ctx.strokeStyle = 'rgba(212,232,238,.65)'; ctx.lineWidth = 1; ctx.stroke();
  }
  function render(now) {
    frame = 0;
    if (dirty) rebuild();
    if (!paused && visible && !document.hidden) {
      if (lastTime) elapsed += Math.min((now - lastTime) / 1000, 0.05);
      lastTime = now;
    } else lastTime = 0;
    draw();
    if (!paused && visible && !document.hidden) schedule();
  }
  slider.addEventListener('input', () => {
    angle = Number(slider.value);
    dirty = true; updateLabel(); schedule();
  });
  pause.addEventListener('click', () => setPaused(!paused));
  motion.addEventListener('change', e => { if (e.matches) setPaused(true); });
  new ResizeObserver(() => { dirty = true; schedule(); }).observe(canvas);
  new IntersectionObserver(entries => {
    visible = entries[0].isIntersecting;
    lastTime = 0;
    if (visible) schedule();
  }, {rootMargin: '100px'}).observe(demo);
  document.addEventListener('visibilitychange', () => { lastTime = 0; if (!document.hidden) schedule(); });
  updateLabel();
  setPaused(paused);
}
