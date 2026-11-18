import { sanitizePose, transformPolygons } from './geometry.mjs';
import { createFieldView } from './field-view.mjs?v=20261117-r2';

const demo = document.querySelector('[data-geometry-flow]');
if (demo) mountExplorer(demo);

function mountExplorer(demo) {
  const canvas = demo.querySelector('canvas');
  const view = createFieldView(canvas);
  const picker = demo.querySelector('[data-gf-shape]');
  const poseKeys = ['x', 'y', 'size', 'angle'];
  const inputs = Object.fromEntries(poseKeys.map(key => [key, demo.querySelector(`[data-gf-${key}]`)]));
  const outputs = Object.fromEntries(poseKeys.map(key => [key, demo.querySelector(`[data-gf-${key}-value]`)]));
  const status = demo.querySelector('[data-gf-status]');
  const overlay = demo.querySelector('[data-gf-overlay]');
  const retry = demo.querySelector('[data-gf-retry]');
  const legend = demo.querySelector('[data-gf-legend]');
  const latency = demo.querySelector('[data-gf-latency]');
  const motion = demo.querySelector('[data-gf-motion]');
  const modes = [...demo.querySelectorAll('[data-gf-mode]')];
  const shapeLabels = { airfoil: 'Airfoil', car: 'Car silhouette', plane: 'Aircraft silhouette', human: 'Human silhouette' };
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  let config = null;
  let desired = null;
  let accepted = null;
  let inFlight = null;
  let worker = null;
  let errorMessage = '';
  let watchdog = 0;
  let drag = null;
  let mode = 'streamlines';
  let paused = reducedMotion.matches;
  let visible = true;
  let frame = 0;
  let previousFrame = 0;
  let flowTime = 0;
  let nextId = 0;

  const samePose = (a, b) => Boolean(a && b && a.shape === b.shape &&
    poseKeys.every(key => Math.abs(a[key] - b[key]) < 1e-7));
  const current = () => samePose(accepted?.pose, desired?.pose);
  const format = (value, digits = 2) => value.toFixed(digits).replace('-', '−');
  const family = id => config.shapes.find(shape => shape.id === id);
  const label = id => shapeLabels[id] || family(id)?.label || id;

  function updateStatus() {
    const state = errorMessage ? 'error' : current() ? 'ready' : accepted ? 'updating' : 'loading';
    const messages = {
      error: errorMessage,
      ready: 'Steady flow estimate ready.',
      updating: 'Updating the steady flow as the geometry changes…',
      loading: 'Loading the local model and estimating flow…',
    };
    demo.dataset.state = state;
    if (status.textContent !== messages[state]) status.textContent = messages[state];
    canvas.setAttribute('aria-busy', String(state === 'loading' || state === 'updating'));
    retry.hidden = state !== 'error';
    overlay.hidden = state === 'ready';
    overlay.textContent = state === 'error' ? (accepted ? 'Last computed flow' : 'Estimate unavailable')
      : accepted ? 'Updating flow' : 'Loading flow model';

    if (!desired) return;
    const pose = desired.pose;
    const poseText = `${label(pose.shape)}. X ${format(pose.x)}, Y ${format(pose.y)}, size ${format(pose.size)}, rotation ${format(pose.angle, 1)} degrees clockwise.`;
    let detail = 'Loading the first steady prediction.';
    if (current()) detail = 'Accepted steady model estimate.';
    else if (accepted) {
      const last = accepted.pose;
      detail = `Showing latest computed flow for ${label(last.shape)}, X ${format(last.x)}, Y ${format(last.y)}, size ${format(last.size)}, rotation ${format(last.angle, 1)} degrees clockwise.`;
    }
    if (errorMessage) detail += ' The current estimate could not be updated.';
    canvas.setAttribute('aria-label', `${poseText} ${detail}`);
  }

  function updateControls() {
    const pose = desired.pose;
    picker.value = pose.shape;
    const [min, max] = family(pose.shape).angle;
    inputs.angle.min = min;
    inputs.angle.max = max;
    for (const key of poseKeys) {
      inputs[key].value = pose[key];
      const text = key === 'angle' ? `${pose.angle > 0 ? '+' : ''}${format(pose.angle, 1)}°` : format(pose[key]);
      outputs[key].value = text;
      inputs[key].setAttribute('aria-valuetext', key === 'angle' ? `${pose.angle} degrees clockwise` : text);
    }
  }

  function updateLegend() {
    legend.hidden = mode === 'streamlines';
    if (legend.hidden) return;
    const range = view.getRange(mode);
    legend.querySelector('[data-gf-field-name]').textContent = mode === 'pressure' ? 'Pressure coefficient Cp' : 'Speed |u| / U∞';
    legend.querySelector('[data-gf-field-min]').textContent = range ? format(range[0]) : '—';
    legend.querySelector('[data-gf-field-max]').textContent = range ? format(range[1]) : '—';
    legend.dataset.mode = mode;
    legend.title = 'Limits show the color scale of the displayed field. Pressure zero is neutral.';
  }

  function scheduleDraw() {
    if (!frame && visible && !document.hidden) frame = requestAnimationFrame(draw);
  }

  function draw(now) {
    frame = 0;
    const animate = Boolean(accepted && !paused && visible && !document.hidden);
    if (animate && previousFrame) flowTime += Math.min(64, now - previousFrame) / 1000;
    previousFrame = animate ? now : 0;
    view.draw({
      polygons: accepted?.polygons ?? [],
      previewPolygons: current() ? [] : desired?.polygons ?? [],
      mode,
      showField: Boolean(accepted),
      time: flowTime,
    });
    if (animate) scheduleDraw();
  }

  function updateMotion() {
    motion.textContent = paused ? 'Play markers' : 'Pause markers';
    motion.setAttribute('aria-label', paused ? 'Play streamline markers' : 'Pause streamline markers');
    previousFrame = 0;
    scheduleDraw();
  }

  function fail(message) {
    errorMessage = message;
    updateStatus();
    scheduleDraw();
  }

  function stopWorker() {
    window.clearTimeout(watchdog);
    worker?.terminate();
    worker = null;
    inFlight = null;
  }

  // Keep one inference running. The single desired pose is the queue, so
  // new pointer events cannot postpone work or leave a backlog to replay.
  function dispatch() {
    if (!worker || !desired || inFlight || current() || errorMessage) return;
    const instance = worker;
    inFlight = desired;
    try {
      worker.postMessage({ id: inFlight.id, pose: inFlight.pose, config });
      watchdog = window.setTimeout(() => {
        if (worker !== instance) return;
        stopWorker();
        fail('The local model took too long. Retry to compute the current pose.');
      }, 90000);
    } catch (error) {
      console.error('Could not send geometry query:', error);
      stopWorker();
      fail('The local model could not receive the query. Retry to compute it.');
    }
  }

  function receive(event) {
    if (worker !== event.currentTarget || !inFlight || event.data?.id !== inFlight.id) return;
    const result = event.data;
    const query = inFlight;
    window.clearTimeout(watchdog);
    inFlight = null;
    const matchesDesired = samePose(query.pose, desired.pose);
    // A valid intermediate pose has value while the pointer is moving. Skip
    // old families and poses that would replace a field already at the target.
    const display = query.pose.shape === desired.pose.shape && (!current() || matchesDesired);
    if (!matchesDesired) dispatch();
    if (display) {
      try {
        if (result.error) throw new Error(result.error);
        if (!samePose(result.pose, query.pose)) throw new Error('Model returned a different pose');
        const count = config.nx * config.ny;
        for (const key of ['u', 'v', 'cp']) {
          if (!(result[key] instanceof Float32Array) || result[key].length !== count) {
            throw new Error(`Invalid ${key} field`);
          }
        }
        if (!(result.mask instanceof Uint8Array) || result.mask.length !== count) throw new Error('Invalid solid mask');
        view.setField(result, config);
        accepted = query;
        latency.textContent = Number.isFinite(result.elapsedMs) ? `${Math.round(result.elapsedMs)} ms` : 'Ready';
        updateLegend();
      } catch (error) {
        console.error('Geometry flow query failed:', error);
        if (matchesDesired) fail('The current flow estimate could not be displayed. Retry the model.');
      }
    }
    dispatch();
    updateStatus();
    scheduleDraw();
  }

  function startWorker() {
    stopWorker();
    try {
      const instance = new Worker(new URL('./inference-worker.mjs', import.meta.url), { type: 'module' });
      worker = instance;
      instance.addEventListener('message', receive);
      function handleWorkerError(event) {
        if (worker !== instance) return;
        console.error('Geometry flow worker failed:', event.message);
        stopWorker();
        fail('The local flow model could not load. Retry to compute the current pose.');
      }
      instance.addEventListener('error', handleWorkerError);
      instance.addEventListener('messageerror', handleWorkerError);
    } catch (error) {
      console.error('Geometry flow worker unavailable:', error);
      fail('This browser could not start the local flow model. Try a current browser.');
    }
  }

  function requestPose(next) {
    if (!config || !next) return;
    try {
      const pose = sanitizePose(config, next);
      if (!samePose(pose, desired?.pose)) {
        desired = { id: ++nextId, pose, polygons: transformPolygons(config, pose) };
        if (worker) errorMessage = '';
      }
      updateControls();
      updateStatus();
      dispatch();
      scheduleDraw();
    } catch (error) {
      console.error('Unsupported geometry pose:', error);
      fail('This pose is outside the model range. Reduce the size or reset the shape.');
    }
  }

  function reset() {
    if (!config) return;
    clearDrag();
    const midpoint = bounds => (bounds[0] + bounds[1]) / 2;
    requestPose({
      shape: config.shapes.find(shape => shape.id === 'airfoil')?.id ?? config.shapes[0].id,
      x: midpoint(config.centerX),
      y: midpoint(config.centerY),
      size: midpoint(config.size),
      angle: 0,
    });
  }

  picker.addEventListener('change', () => {
    clearDrag();
    requestPose({ ...desired?.pose, shape: picker.value, angle: 0 });
  });
  for (const key of poseKeys) {
    inputs[key].addEventListener('input', () => requestPose({ ...desired?.pose, [key]: Number(inputs[key].value) }));
  }
  demo.querySelector('[data-gf-reset]').addEventListener('click', reset);
  for (const button of modes) {
    button.addEventListener('click', () => {
      mode = button.dataset.gfMode;
      for (const item of modes) item.setAttribute('aria-pressed', String(item === button));
      updateLegend();
      scheduleDraw();
    });
  }
  motion.addEventListener('click', () => { paused = !paused; updateMotion(); });
  reducedMotion.addEventListener('change', event => { paused = event.matches; updateMotion(); });
  retry.addEventListener('click', () => {
    if (!config) {
      init();
      return;
    }
    errorMessage = '';
    startWorker();
    dispatch();
    updateStatus();
  });

  canvas.addEventListener('pointerdown', event => {
    if (!desired || drag || event.button !== 0) return;
    const point = view.world(event.clientX, event.clientY);
    if (!point || !view.hitTest(desired.polygons, point)) return;
    event.preventDefault();
    canvas.focus({ preventScroll: true });
    canvas.setPointerCapture(event.pointerId);
    drag = { id: event.pointerId, start: point, pose: desired.pose };
    canvas.classList.add('is-dragging');
  });
  canvas.addEventListener('pointermove', event => {
    if (event.pointerId !== drag?.id || drag.pose.shape !== desired.pose.shape) return;
    const point = view.world(event.clientX, event.clientY);
    if (!point) return;
    requestPose({
      ...desired.pose,
      x: drag.pose.x + point[0] - drag.start[0],
      y: drag.pose.y + point[1] - drag.start[1],
    });
  });
  function clearDrag() {
    if (!drag) return;
    const { id } = drag;
    drag = null;
    canvas.classList.remove('is-dragging');
    if (canvas.hasPointerCapture(id)) canvas.releasePointerCapture(id);
  }
  function endDrag(event) {
    if (event.pointerId !== drag?.id) return;
    clearDrag();
    dispatch();
  }
  for (const type of ['pointerup', 'pointercancel', 'lostpointercapture']) canvas.addEventListener(type, endDrag);

  canvas.addEventListener('keydown', event => {
    if (!desired) return;
    if (event.key === 'Home') {
      event.preventDefault();
      reset();
      return;
    }
    const moves = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, 1], ArrowDown: [0, -1] };
    if (!Object.hasOwn(moves, event.key)) return;
    event.preventDefault();
    const [x, y] = moves[event.key];
    const step = event.shiftKey ? 0.1 : 0.02;
    requestPose({ ...desired.pose, x: desired.pose.x + x * step, y: desired.pose.y + y * step });
  });

  new ResizeObserver(() => { view.resize(config); scheduleDraw(); }).observe(canvas);
  new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting;
    previousFrame = 0;
    scheduleDraw();
  }).observe(canvas);
  document.addEventListener('visibilitychange', () => { previousFrame = 0; scheduleDraw(); });

  async function init() {
    errorMessage = '';
    updateStatus();
    try {
      const response = await fetch(new URL('./model/config.json', import.meta.url));
      if (!response.ok) throw new Error(`Configuration HTTP ${response.status}`);
      const loaded = await response.json();
      if (!loaded.shapes?.length || !Number.isFinite(loaded.dx) || !(loaded.nx > 1) || !(loaded.ny > 1)) {
        throw new Error('Invalid model configuration');
      }
      config = loaded;
      picker.replaceChildren(...config.shapes.map(shape => new Option(label(shape.id), shape.id)));
      for (const [key, bounds] of [['x', config.centerX], ['y', config.centerY], ['size', config.size]]) {
        inputs[key].min = bounds[0];
        inputs[key].max = bounds[1];
      }
      for (const control of demo.querySelectorAll('[data-gf-control]')) control.disabled = false;
      view.resize(config);
      startWorker();
      reset();
    } catch (error) {
      console.error('Geometry flow initialization failed:', error);
      config = null;
      fail('The model configuration could not be loaded. Please retry.');
    }
  }

  updateMotion();
  init();
}
