// Cambered Joukowski airfoils in 2D, incompressible, inviscid potential flow.
// z = zeta + 1/zeta; the generating circle passes through the trailing-edge cusp.
// Geometry is chord-aligned and scaled to a fixed chord before applying incidence.
// States are quasi-steady; separation, viscosity and pitching transients are omitted.
export const CHORD = 2 + 1.2 + 1 / 1.2;
const DEG = Math.PI / 180;
const DEFAULT_SHAPE = {thickness: 12, camber: 0};
export const AIR_DENSITY = 1.225; // Fixed illustrative air density in kg/m^3.
let cachedKey = '', cachedGeometry;

function divide(ar, ai, br, bi) {
  const d = br * br + bi * bi;
  return [(ar * br + ai * bi) / d, (ai * br - ar * bi) / d];
}

function circleGeometry(offset, camberOffset, count = 320) {
  const radius = Math.hypot(1 + offset, camberOffset);
  const trailingAngle = Math.atan2(-camberOffset, 1 + offset);
  function mapped(t) {
    const zx = -offset + radius * Math.cos(t), zy = camberOffset + radius * Math.sin(t);
    const r2 = zx * zx + zy * zy;
    return [zx + zx / r2, zy - zy / r2];
  }
  function distance(t) {
    const [x,y] = mapped(t);
    return (x - 2) ** 2 + y * y;
  }
  // The point farthest from the cusp defines the leading edge and chord.
  let best = trailingAngle + Math.PI, maxDistance = -Infinity;
  const dt = 2 * Math.PI / 64;
  for (let i = 1; i < 64; i++) {
    const t = trailingAngle + i * dt, d = distance(t);
    if (d > maxDistance) { best = t; maxDistance = d; }
  }
  let left = best - dt, right = best + dt;
  for (let i = 0; i < 36; i++) {
    const a = left + (right - left) / 3, b = right - (right - left) / 3;
    if (distance(a) < distance(b)) left = a; else right = b;
  }
  const leadingAngle = camberOffset === 0 ? Math.PI : (left + right) / 2;
  const leading = camberOffset === 0 ? [-(1 + 2 * offset) - 1 / (1 + 2 * offset), 0] : mapped(leadingAngle);
  const chord = Math.hypot(2 - leading[0], leading[1]);
  const chordAngle = Math.atan2(-leading[1], 2 - leading[0]);
  const c = Math.cos(chordAngle), s = Math.sin(chordAngle);
  const center = [(2 + leading[0]) / 2, leading[1] / 2];
  const half = Math.floor(count / 2);
  const points = Array.from({length: count + 1}, (_, i) => {
    // Include both chord endpoints exactly and sample each surface separately.
    const t = i <= half ? trailingAngle + (leadingAngle - trailingAngle) * i / half
      : leadingAngle + (trailingAngle + 2 * Math.PI - leadingAngle) * (i - half) / (count - half);
    const p = mapped(t), x = p[0] - center[0], y = p[1] - center[1];
    return [(c * x + s * y) / chord, (-s * x + c * y) / chord];
  });
  // Measure thickness and mean-line camber at equal chord stations, rather than
  // treating circle offsets as percentages. This keeps the two controls independent.
  const upper = points.slice(0, half + 1).reverse(), lower = points.slice(half);
  let ui = 1, li = 1, thickness = 0, camber = 0;
  function ordinate(surface, index, x) {
    const a = surface[index - 1], b = surface[index];
    return a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]);
  }
  for (let i = 1; i < 160; i++) {
    const x = -0.5 + (1 - Math.cos(Math.PI * i / 160)) / 2;
    while (ui < upper.length - 1 && upper[ui][0] < x) ui++;
    while (li < lower.length - 1 && lower[li][0] < x) li++;
    const a = ordinate(upper, ui, x), b = ordinate(lower, li, x);
    thickness = Math.max(thickness, a - b);
    const mean = (a + b) / 2;
    if (Math.abs(mean) > Math.abs(camber)) camber = mean;
  }
  return {offset, camberOffset, radius, trailingAngle, chordAngle, center, chord, points, thickness, camber};
}

export function createGeometry(options = DEFAULT_SHAPE) {
  const thickness = Math.max(6, Math.min(20, Number(options.thickness ?? 12)));
  const camber = Math.max(-6, Math.min(6, Number(options.camber ?? 0)));
  const key = thickness + ':' + camber;
  if (key === cachedKey) return cachedGeometry;
  let e = thickness / 130, h = camber / 50;
  let geometry;
  // Small two-parameter Newton fit: solve actual section dimensions, not a visual warp.
  for (let i = 0; i < 8; i++) {
    geometry = circleGeometry(e, h);
    const rt = thickness / 100 - geometry.thickness, rm = camber / 100 - geometry.camber;
    if (Math.max(Math.abs(rt), Math.abs(rm)) < 2e-6) break;
    const de = circleGeometry(e + 0.0005, h), dh = circleGeometry(e, h + 0.0005);
    const a = (de.thickness - geometry.thickness) / 0.0005;
    const b = (dh.thickness - geometry.thickness) / 0.0005;
    const c = (de.camber - geometry.camber) / 0.0005;
    const d = (dh.camber - geometry.camber) / 0.0005;
    const det = a * d - b * c;
    if (Math.abs(det) < 1e-8) break;
    e = Math.max(0.02, Math.min(0.4, e + (rt * d - b * rm) / det));
    h = camber === 0 ? 0 : Math.max(-0.3, Math.min(0.3, h + (a * rm - rt * c) / det));
  }
  cachedGeometry = circleGeometry(e, h);
  cachedKey = key;
  return cachedGeometry;
}

export function outline(angleDegrees, count = 240, options = DEFAULT_SHAPE) {
  const geometry = createGeometry(options);
  const points = circleGeometry(geometry.offset, geometry.camberOffset, count).points;
  const a = angleDegrees * DEG, c = Math.cos(a), s = Math.sin(a);
  return points.map(([x,y]) => [CHORD * (c * x + s * y), CHORD * (-s * x + c * y)]);
}

export function createFlow(angleDegrees, options = DEFAULT_SHAPE) {
  const geometry = createGeometry(options);
  const {offset, camberOffset, radius, trailingAngle, chordAngle, center, chord} = geometry;
  const alpha = angleDegrees * DEG + chordAngle, ca = Math.cos(alpha), sa = Math.sin(alpha);
  const size = CHORD / chord;
  const rawCirculation = 4 * Math.PI * radius * Math.sin(alpha - trailingAngle);
  const k = rawCirculation / (2 * Math.PI);

  function velocity(x, y) {
    // Undo the chord scaling, incidence rotation and centering before inverting the map.
    const bx = (ca * x - sa * y) / size + center[0];
    const by = (sa * x + ca * y) / size + center[1];
    const dr = bx * bx - by * by - 4, di = 2 * bx * by;
    const magnitude = Math.hypot(dr, di);
    const sr = Math.sqrt(Math.max(0, (magnitude + dr) / 2));
    const si = (di < 0 ? -1 : 1) * Math.sqrt(Math.max(0, (magnitude - dr) / 2));
    let zx = (bx + sr) / 2, zy = (by + si) / 2;
    const ox = (bx - sr) / 2, oy = (by - si) / 2;
    if ((ox + offset) ** 2 + (oy - camberOffset) ** 2 > (zx + offset) ** 2 + (zy - camberOffset) ** 2) {
      zx = ox; zy = oy;
    }
    const wx = zx + offset, wy = zy - camberOffset;
    if (wx * wx + wy * wy < radius * radius * (1 - 1e-10)) return null;
    const w2r = wx * wx - wy * wy, w2i = 2 * wx * wy;
    const doublet = divide(radius * radius * ca, radius * radius * sa, w2r, w2i);
    const vortex = divide(0, k, wx, wy);
    const nr = ca - doublet[0] + vortex[0], ni = -sa - doublet[1] + vortex[1];
    const inverseZ2 = divide(1, 0, zx * zx - zy * zy, 2 * zx * zy);
    const mr = 1 - inverseZ2[0], mi = -inverseZ2[1];
    // Analytic removable-singularity limit at zeta=1, including camber.
    const limit = Math.cos(alpha - trailingAngle) / radius;
    const q = mr * mr + mi * mi < 1e-14
      ? [limit * Math.cos(2 * trailingAngle), -limit * Math.sin(2 * trailingAngle)] : divide(nr, ni, mr, mi);
    const u = q[0] * ca - q[1] * sa, v = -(q[0] * sa + q[1] * ca);
    return Number.isFinite(u) && Number.isFinite(v) ? [u, v] : null;
  }
  function sample(x, y) {
    const v = velocity(x, y);
    if (!v) return null;
    const speed = Math.hypot(...v);
    return {speed, cp: 1 - speed * speed}; // Bernoulli with U_infinity = 1.
  }
  const circulation = size * rawCirculation;
  // Kutta-Joukowski for a 2D section: Cl = 2 Gamma / (U_infinity c).
  // This flow solution is normalized to U_infinity = 1, so Cl is speed-independent.
  const liftCoefficient = 2 * circulation / CHORD;
  // d'Alembert's paradox: this attached, incompressible 2D potential-flow model
  // has zero net drag. No skin friction, separation, induced or wave drag is added.
  const dragCoefficient = 0;
  return {velocity, sample, circulation, liftCoefficient, dragCoefficient, outline: outline(angleDegrees, 240, options), geometry};
}

// Bernoulli scaling of the normalized ideal solution. The geometry and Cp are
// independent of wind speed; dimensional velocity is linear and delta-p quadratic.
// https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/bernoullis-equation/
export function dimensionalSample(sample, windSpeed, density = AIR_DENSITY) {
  if (!sample) return null;
  return {speed: sample.speed * windSpeed, deltaPressure: 0.5 * density * windSpeed ** 2 * sample.cp};
}

export function traceStreamline(flow, x, y, bounds, maxSteps = 1400) {
  const points = [{x, y, t: 0}];
  let t = 0;
  for (let step = 0; step < maxSteps; step++) {
    const v = flow.velocity(x, y);
    if (!v) break;
    const speed = Math.hypot(v[0], v[1]);
    if (speed < 0.012) break;
    const dt = Math.min(0.055, 0.035 / speed);
    const mid = flow.velocity(x + v[0] * dt / 2, y + v[1] * dt / 2);
    if (!mid) break;
    const nx = x + mid[0] * dt, ny = y + mid[1] * dt;
    // Reject steps into the solid rather than drawing a streamline through it.
    if (!flow.velocity(nx, ny)) break;
    x = nx; y = ny; t += dt;
    points.push({x, y, t});
    if (x > bounds.xMax || x < bounds.xMin - 0.2 || Math.abs(y) > bounds.yMax + 0.2) break;
  }
  return {points, duration: t};
}

export function pointOnStreamline(line, time) {
  const p = line.points;
  if (time <= 0) return p[0];
  if (time >= line.duration) return p[p.length - 1];
  let lo = 0, hi = p.length - 1;
  while (hi - lo > 1) {
    const mid = (hi + lo) >> 1;
    if (p[mid].t < time) lo = mid; else hi = mid;
  }
  const f = (time - p[lo].t) / (p[hi].t - p[lo].t);
  return {x: p[lo].x + f * (p[hi].x - p[lo].x), y: p[lo].y + f * (p[hi].y - p[lo].y)};
}
