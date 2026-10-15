// Symmetric Joukowski airfoil in 2D, incompressible, inviscid potential flow.
// Circle center = (-e, 0), radius = 1 + e, map z = zeta + 1/zeta.
// Kutta circulation (clockwise convention): Gamma = 4*pi*R*U*sin(alpha).
// Angles are quasi-steady states; this is not a viscous or unsteady CFD solver.
export const OFFSET = 0.10;
export const RADIUS = 1 + OFFSET;
export const CHORD = 2 + (1 + 2 * OFFSET) + 1 / (1 + 2 * OFFSET);
const DEG = Math.PI / 180;

function divide(ar, ai, br, bi) {
  const d = br * br + bi * bi;
  return [(ar * br + ai * bi) / d, (ai * br - ar * bi) / d];
}

export function outline(angleDegrees, count = 240) {
  const a = angleDegrees * DEG, c = Math.cos(a), s = Math.sin(a);
  return Array.from({length: count + 1}, (_, i) => {
    const t = 2 * Math.PI * i / count;
    const zx = -OFFSET + RADIUS * Math.cos(t), zy = RADIUS * Math.sin(t);
    const r2 = zx * zx + zy * zy;
    const x = zx + zx / r2, y = zy - zy / r2;
    // Positive incidence pitches the leading edge upward into horizontal flow.
    return [c * x + s * y, -s * x + c * y];
  });
}

export function createFlow(angleDegrees) {
  const alpha = angleDegrees * DEG, ca = Math.cos(alpha), sa = Math.sin(alpha);
  const circulation = 4 * Math.PI * RADIUS * sa;
  const k = circulation / (2 * Math.PI);

  function velocity(x, y) {
    // Rotate the world point back into the fixed airfoil coordinates.
    const bx = ca * x - sa * y, by = sa * x + ca * y;
    // Invert z = zeta + 1/zeta; retain the root exterior to the generating circle.
    const dr = bx * bx - by * by - 4, di = 2 * bx * by;
    const magnitude = Math.hypot(dr, di);
    const sr = Math.sqrt(Math.max(0, (magnitude + dr) / 2));
    const si = (di < 0 ? -1 : 1) * Math.sqrt(Math.max(0, (magnitude - dr) / 2));
    let zx = (bx + sr) / 2, zy = (by + si) / 2;
    const ox = (bx - sr) / 2, oy = (by - si) / 2;
    if ((ox + OFFSET) ** 2 + oy * oy > (zx + OFFSET) ** 2 + zy * zy) {
      zx = ox; zy = oy;
    }
    const wx = zx + OFFSET, wy = zy;
    if (wx * wx + wy * wy < RADIUS * RADIUS * (1 - 1e-10)) return null;

    const w2r = wx * wx - wy * wy, w2i = 2 * wx * wy;
    const doublet = divide(RADIUS * RADIUS * ca, RADIUS * RADIUS * sa, w2r, w2i);
    const vortex = divide(0, k, wx, wy);
    const nr = ca - doublet[0] + vortex[0];
    const ni = -sa - doublet[1] + vortex[1];
    const inverseZ2 = divide(1, 0, zx * zx - zy * zy, 2 * zx * zy);
    const mr = 1 - inverseZ2[0], mi = -inverseZ2[1];
    // Removable singularity at the cusp: use the analytic Kutta limit.
    const q = mr * mr + mi * mi < 1e-14 ? [ca / RADIUS, 0] : divide(nr, ni, mr, mi);
    const u = q[0] * ca - q[1] * sa;
    const v = -(q[0] * sa + q[1] * ca);
    return Number.isFinite(u) && Number.isFinite(v) ? [u, v] : null;
  }

  function sample(x, y) {
    const v = velocity(x, y);
    if (!v) return null;
    const speed = Math.hypot(...v); // V / V_infinity, with U_infinity = 1.
    // Bernoulli: Cp = (p - p_infinity) / (0.5 rho U_infinity^2).
    return {speed, cp: 1 - speed * speed};
  }
  return {velocity, sample, circulation, outline: outline(angleDegrees)};
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
