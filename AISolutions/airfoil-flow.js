import {createFlow, dimensionalSample, traceStreamline, pointOnStreamline} from './airfoil-flow-model.mjs?v=20261015-drag';

const demo = document.querySelector('[data-airfoil-demo]');
if (demo) {
  const canvas = demo.querySelector('canvas');
  const ctx = canvas.getContext('2d');
  const slider = demo.querySelector('[data-airfoil-angle]');
  const output = demo.querySelector('[data-angle-output]');
  const thicknessSlider = demo.querySelector('[data-airfoil-thickness]');
  const camberSlider = demo.querySelector('[data-airfoil-camber]');
  const thicknessOutput = demo.querySelector('[data-thickness-output]');
  const camberOutput = demo.querySelector('[data-camber-output]');
  const windSlider = demo.querySelector('[data-airfoil-wind]');
  const windOutput = demo.querySelector('[data-wind-output]');
  const liftOutput = demo.querySelector('[data-lift-output]');
  const dragOutput = demo.querySelector('[data-drag-output]');
  const pause = demo.querySelector('[data-airfoil-pause]');
  const modes = [...demo.querySelectorAll('[data-airfoil-mode]')];
  const legend = demo.querySelector('[data-airfoil-legend]');
  const fieldCanvas = document.createElement('canvas');
  const fieldCtx = fieldCanvas.getContext('2d');
  const palette = [[19,53,109],[26,122,162],[59,176,169],[238,202,111],[218,87,63]];
  let mode = 'streamlines', fieldSamples = [], fieldDirty = true;
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const playIcon = '<path d="m8 5 11 7-11 7z"/>';
  const pauseIcon = '<path d="M8 5v14M16 5v14"/>';
  let width = 0, height = 0, scale = 1, paths = [], shape = [];
  let paused = motion.matches, visible = true, frame = 0, dirty = true;
  let elapsed = 0, lastTime = 0, angle = Number(slider.value);
  let thickness = Number(thicknessSlider.value), camber = Number(camberSlider.value);
  let windSpeed = Number(windSlider.value);
  let liftCoefficient = 0, liftOrigin = [0, 0, 0];
  let dragCoefficient = 0;

  function formatAngle(value) {
    return (value > 0 ? '+' : '') + Number(value.toFixed(1)) + '°';
  }
  function updateLabel() {
    output.value = formatAngle(angle);
    slider.setAttribute('aria-valuetext', String(angle) + ' degrees');
    thicknessOutput.value = thickness + '%';
    camberOutput.value = (camber > 0 ? '+' : '') + camber + '%';
    thicknessSlider.setAttribute('aria-valuetext', thickness + ' percent of chord');
    camberSlider.setAttribute('aria-valuetext', camber + ' percent of chord');
    windOutput.value = windSpeed + ' m/s';
    windSlider.setAttribute('aria-valuetext', windSpeed + ' meters per second');
    const cl = Math.abs(liftCoefficient) < 0.005 ? 0 : liftCoefficient;
    const liftText = (cl > 0 ? '+' : '') + cl.toFixed(2);
    liftOutput.value = windSpeed > 0 ? liftText : '—';
    liftOutput.title = windSpeed > 0 ? 'Ideal 2D section lift coefficient; arrow length is capped for display.' : 'No lift at zero wind. The coefficient is undefined because dynamic pressure is zero.';
    liftOutput.setAttribute('aria-label', windSpeed > 0 ? 'Lift coefficient ' + liftText : 'Lift coefficient undefined at zero wind; no lift force');
    dragOutput.value = windSpeed > 0 ? dragCoefficient.toFixed(2) : '—';
    dragOutput.setAttribute('aria-label', windSpeed > 0 ? 'Ideal drag coefficient 0.00; viscous drag not modeled' : 'Drag coefficient undefined at zero wind; no drag force');
    const view = mode === 'streamlines' ? 'streamlines' : mode === 'velocity' ? 'velocity magnitude colors and streamlines' : 'pressure difference colors and streamlines';
    canvas.setAttribute('aria-label', 'Ideal airflow: ' + view + ', wind speed ' + windSpeed + ' meters per second, at ' + angle + ' degrees angle of attack, ' + thickness + ' percent thickness and ' + camber + ' percent camber. ' + (windSpeed > 0 ? 'Lift coefficient ' + liftText + '; solid arrow indicates coefficient direction and relative magnitude. Ideal drag coefficient 0.00; dashed arrow indicates drag direction only, not force.' : 'No lift or drag at zero wind.'));
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
  function sampleField(flow) {
    // A bounded raster is cached per angle/resize, never recomputed per frame.
    fieldCanvas.width = Math.min(480, Math.ceil(width));
    fieldCanvas.height = Math.max(1, Math.round(height * fieldCanvas.width / width));
    fieldSamples = [];
    for (let y = 0; y < fieldCanvas.height; y++) {
      for (let x = 0; x < fieldCanvas.width; x++) {
        fieldSamples.push(flow.sample(((x + 0.5) / fieldCanvas.width - 0.5) * width / scale,
          (0.5 - (y + 0.5) / fieldCanvas.height) * height / scale));
      }
    }
    fieldDirty = true;
  }
  function colorField() {
    const raster = fieldCtx.createImageData(fieldCanvas.width, fieldCanvas.height);
    fieldSamples.forEach((sample, i) => {
      if (!sample) return; // Solid interior is not assigned a fluid value.
      const physical = dimensionalSample(sample, windSpeed);
      // Fixed scales make changes in wind speed visible; capped ends are labeled.
      const value = mode === 'velocity' ? physical.speed / 100 : (physical.deltaPressure + 1500) / 2000;
      const t = Math.max(0, Math.min(1, value)) * (palette.length - 1);
      const lo = Math.min(palette.length - 2, Math.floor(t)), f = t - lo;
      for (let c = 0; c < 3; c++) raster.data[i * 4 + c] = Math.round(palette[lo][c] * (1 - f) + palette[lo + 1][c] * f);
      raster.data[i * 4 + 3] = 255;
    });
    fieldCtx.putImageData(raster, 0, 0);
    fieldDirty = false;
  }
  function setMode(next) {
    mode = next;
    modes.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.airfoilMode === mode)));
    legend.hidden = mode === 'streamlines';
    legend.querySelector('[data-field-label]').textContent = mode === 'velocity' ? 'Speed · m/s' : 'Pressure Δp · Pa';
    legend.querySelector('[data-field-min]').textContent = mode === 'velocity' ? '0' : '≤ −1500';
    legend.querySelector('[data-field-max]').textContent = mode === 'velocity' ? '≥ 100' : '≥ +500';
    legend.title = mode === 'velocity' ? 'Local air speed in meters per second. Fixed color scale, capped at 100 m/s.' : 'Static pressure relative to freestream: Δp = p − p∞ = ½ρV∞² Cp. Air density 1.225 kg/m³. Fixed color scale capped below −1500 Pa and above +500 Pa.';
    fieldDirty = true; updateLabel(); schedule();
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
    const flow = createFlow(angle, {thickness, camber});
    liftCoefficient = flow.liftCoefficient;
    dragCoefficient = flow.dragCoefficient;
    sampleField(flow);
    shape = flow.outline.map(p => toScreen({x: p[0], y: p[1]}));
    // Anchor within the section at a vertical surface intersection. Its position
    // is illustrative, not an assertion about the aerodynamic center or moment.
    const arrowX = Math.max(width * 0.56, Math.min(width * 0.65, 185));
    const intersections = [];
    for (let i = 1; i < shape.length; i++) {
      const a = shape[i - 1], b = shape[i];
      if ((a[0] <= arrowX && b[0] > arrowX) || (b[0] <= arrowX && a[0] > arrowX))
        intersections.push(a[1] + (b[1] - a[1]) * (arrowX - a[0]) / (b[0] - a[0]));
    }
    liftOrigin = [arrowX, intersections.length ? Math.min(...intersections) : height / 2,
      intersections.length ? Math.max(...intersections) : height / 2];
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
    updateLabel();
  }
  function drawLiftArrow() {
    // A coefficient indicator, not a dimensional force vector. No arrow at zero wind.
    if (windSpeed === 0 || Math.abs(liftCoefficient) < 0.005) return;
    const direction = liftCoefficient > 0 ? -1 : 1;
    const x = liftOrigin[0], y = liftOrigin[direction < 0 ? 1 : 2] + direction * 3;
    const length = Math.min(Math.abs(liftCoefficient) * 52, height * 0.28);
    if (length < 7) return;
    const end = y + direction * length, head = Math.min(9, length * 0.35);
    ctx.save();
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.moveTo(x, y); ctx.lineTo(x, end);
    ctx.moveTo(x - head * 0.6, end - direction * head); ctx.lineTo(x, end); ctx.lineTo(x + head * 0.6, end - direction * head);
    ctx.strokeStyle = '#0b263b'; ctx.lineWidth = 7; ctx.stroke();
    ctx.strokeStyle = '#ffdb89'; ctx.lineWidth = 3; ctx.stroke();
    ctx.beginPath(); ctx.arc(x, y, 3, 0, Math.PI * 2);
    ctx.fillStyle = '#ffdb89'; ctx.fill();
    ctx.restore();
  }
  function drawDragDirection(color) {
    if (windSpeed === 0) return;
    // A reference direction, deliberately dashed and detached from the surface:
    // there is no nonzero drag-force vector in this ideal solution.
    const start = Math.max(...shape.map(p => p[0])) + 12;
    const end = Math.min(width - 18, start + 68), y = shape[0][1];
    if (end - start < 20) return;
    ctx.save();
    ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.beginPath(); ctx.moveTo(start, y); ctx.lineTo(end, y); ctx.stroke();
    ctx.setLineDash([]);
    ctx.beginPath(); ctx.moveTo(end - 6, y - 4); ctx.lineTo(end, y); ctx.lineTo(end - 6, y + 4); ctx.stroke();
    ctx.font = '10px Inter, sans-serif'; ctx.textAlign = 'center';
    const labelWidth = ctx.measureText('Drag direction').width;
    const labelX = Math.min((start + end) / 2, width - 8 - labelWidth / 2);
    ctx.fillText('Drag direction', labelX, y + 18);
    ctx.restore();
  }
  function draw() {
    ctx.clearRect(0, 0, width, height);
    const colored = mode !== 'streamlines';
    if (colored) {
      if (fieldDirty) colorField();
      ctx.drawImage(fieldCanvas, 0, 0, width, height);
    }
    const gradient = ctx.createLinearGradient(0, 0, width, 0);
    gradient.addColorStop(0, 'rgba(100,210,220,.14)');
    gradient.addColorStop(0.28, 'rgba(100,210,220,.46)');
    gradient.addColorStop(0.72, 'rgba(100,210,220,.46)');
    gradient.addColorStop(1, 'rgba(100,210,220,.14)');
    ctx.lineWidth = 1;
    ctx.strokeStyle = colored ? 'rgba(6,28,43,.32)' : gradient;
    const flowingPaths = windSpeed > 0 ? paths : [];
    flowingPaths.forEach(line => ctx.stroke(line.path));
    ctx.strokeStyle = colored ? 'rgba(255,255,255,.72)' : 'rgba(149,236,238,.9)';
    ctx.fillStyle = '#d5ffff';
    ctx.lineWidth = 1.65;
    flowingPaths.forEach(line => {
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
    ctx.strokeStyle = colored ? '#163449' : 'rgba(255,255,255,.7)';
    ctx.lineWidth = 1;
    ctx.stroke();
    drawLiftArrow();
    const darkLabel = colored && (mode === 'pressure' || windSpeed >= 35);
    const flowLabelColor = darkLabel ? 'rgba(6,28,43,.85)' : 'rgba(225,245,249,.85)';
    drawDragDirection(flowLabelColor);
    ctx.fillStyle = flowLabelColor;
    ctx.font = '11px Inter, sans-serif';
    const labelY = width < 700 ? 77 : 29;
    ctx.fillText(windSpeed > 0 ? 'FLOW' : 'NO WIND', 20, labelY);
    if (windSpeed > 0) {
      ctx.beginPath();
      ctx.moveTo(62, labelY - 4); ctx.lineTo(93, labelY - 4);
      ctx.moveTo(88, labelY - 8); ctx.lineTo(93, labelY - 4); ctx.lineTo(88, labelY);
      ctx.strokeStyle = flowLabelColor; ctx.lineWidth = 1; ctx.stroke();
    }
  }
  function render(now) {
    frame = 0;
    if (dirty) rebuild();
    if (!paused && windSpeed > 0 && visible && !document.hidden) {
      // Deliberate display slow motion: travel rate remains proportional to wind.
      if (lastTime) elapsed += Math.min((now - lastTime) / 1000, 0.05) * windSpeed / 20;
      lastTime = now;
    } else lastTime = 0;
    draw();
    if (!paused && windSpeed > 0 && visible && !document.hidden) schedule();
  }
  slider.addEventListener('input', () => {
    angle = Number(slider.value);
    dirty = true; updateLabel(); schedule();
  });
  [thicknessSlider, camberSlider].forEach(control => control.addEventListener('input', () => {
    thickness = Number(thicknessSlider.value); camber = Number(camberSlider.value);
    dirty = true; updateLabel(); schedule();
  }));
  windSlider.addEventListener('input', () => {
    windSpeed = Number(windSlider.value);
    fieldDirty = true; lastTime = 0; updateLabel(); schedule();
  });
  pause.addEventListener('click', () => setPaused(!paused));
  modes.forEach(button => button.addEventListener('click', () => setMode(button.dataset.airfoilMode)));
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
