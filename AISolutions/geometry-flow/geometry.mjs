// Shared geometry and frozen preprocessing for the trained fixed-grid surrogate.
// Rows increase with world y; positive pose.angle rotates the body clockwise.
const preparedConfigs = new WeakMap();
const clamp = (value, low, high) => Math.max(low, Math.min(high, value));

function finitePair(value, name, positive = false) {
  if (!Array.isArray(value) || value.length !== 2 || !value.every(Number.isFinite) ||
      value[0] > value[1] || (positive && value[0] <= 0)) {
    throw new Error(`Invalid ${name} bounds`);
  }
  return value;
}

function prepare(config) {
  if (!config || typeof config !== 'object') throw new Error('Model configuration is required');
  if (preparedConfigs.has(config)) return preparedConfigs.get(config);
  const {nx, ny, dx, xmin, xmax, ymin, ymax, sdfScale} = config;
  if (!Number.isInteger(nx) || !Number.isInteger(ny) || nx < 2 || ny < 2 ||
      nx > 1024 || ny > 1024 || ![dx, xmin, xmax, ymin, ymax, sdfScale].every(Number.isFinite) ||
      dx <= 0 || sdfScale <= 0 || xmax <= xmin || ymax <= ymin ||
      Math.abs(nx * dx - (xmax - xmin)) > 1e-9 ||
      Math.abs(ny * dx - (ymax - ymin)) > 1e-9) {
    throw new Error('Invalid fixed Cartesian grid');
  }
  finitePair(config.centerX, 'center x');
  finitePair(config.centerY, 'center y');
  finitePair(config.size, 'size', true);
  if (!Array.isArray(config.shapeBounds) || config.shapeBounds.length !== 4 ||
      !config.shapeBounds.every(Number.isFinite) ||
      config.shapeBounds[0] >= config.shapeBounds[1] || config.shapeBounds[2] >= config.shapeBounds[3] ||
      config.shapeBounds[0] < xmin || config.shapeBounds[1] > xmax ||
      config.shapeBounds[2] < ymin || config.shapeBounds[3] > ymax) {
    throw new Error('Invalid geometry placement envelope');
  }
  if (!Array.isArray(config.outputScales) || config.outputScales.length !== 3 ||
      !config.outputScales.every(value => Number.isFinite(value) && value > 0)) {
    throw new Error('Invalid frozen output scales');
  }
  if (!Array.isArray(config.shapes) || !config.shapes.length) throw new Error('No supported shapes');
  const shapes = new Map();
  for (const shape of config.shapes) {
    if (!shape || typeof shape.id !== 'string' || shapes.has(shape.id)) throw new Error('Invalid shape identifier');
    finitePair(shape.angle, 'shape angle');
    if (!Array.isArray(shape.polygons) || shape.polygons.some(polygon =>
      !Array.isArray(polygon) || polygon.length < 3 || polygon.some(point =>
        !Array.isArray(point) || point.length !== 2 || !point.every(Number.isFinite)))) {
      throw new Error(`Invalid polygons for ${shape.id}`);
    }
    shapes.set(shape.id, shape);
  }
  const value = {nx, ny, n: nx * ny, shapes, scales: new Float32Array(config.outputScales)};
  preparedConfigs.set(config, value);
  return value;
}

function transformed(shape, pose) {
  const radians = -pose.angle * Math.PI / 180;
  const cosine = Math.cos(radians), sine = Math.sin(radians);
  return shape.polygons.map(polygon => polygon.map(([px, py]) => {
    // Multiply before rotating, matching the source NumPy geometry builder.
    const x = pose.size * px, y = pose.size * py;
    return [cosine * x - sine * y + pose.x, sine * x + cosine * y + pose.y];
  }));
}

function relativeBounds(shape, size, angle) {
  const polygons = transformed(shape, {x: 0, y: 0, size, angle});
  const bounds = [Infinity, -Infinity, Infinity, -Infinity];
  for (const polygon of polygons) for (const [x, y] of polygon) {
    bounds[0] = Math.min(bounds[0], x); bounds[1] = Math.max(bounds[1], x);
    bounds[2] = Math.min(bounds[2], y); bounds[3] = Math.max(bounds[3], y);
  }
  return polygons.length ? bounds : [0, 0, 0, 0];
}

/** Clamp a supported family pose, including its complete rotated silhouette. */
export function sanitizePose(config, pose = {}) {
  const metadata = prepare(config);
  const shape = metadata.shapes.get(pose.shape) || config.shapes[0];
  const number = (value, fallback) => typeof value === 'number' && Number.isFinite(value) ? value : fallback;
  const size = clamp(number(pose.size, (config.size[0] + config.size[1]) / 2), ...config.size);
  const angle = clamp(number(pose.angle, clamp(0, ...shape.angle)), ...shape.angle);
  const bounds = relativeBounds(shape, size, angle);
  const [left, right, bottom, top] = config.shapeBounds;
  const xlow = Math.max(config.centerX[0], left - bounds[0]);
  const xhigh = Math.min(config.centerX[1], right - bounds[1]);
  const ylow = Math.max(config.centerY[0], bottom - bounds[2]);
  const yhigh = Math.min(config.centerY[1], top - bounds[3]);
  if (xlow > xhigh + 1e-12 || ylow > yhigh + 1e-12) {
    throw new Error('This size and angle do not fit the supported geometry envelope');
  }
  return {
    shape: shape.id,
    x: clamp(number(pose.x, (config.centerX[0] + config.centerX[1]) / 2), xlow, Math.max(xlow, xhigh)),
    y: clamp(number(pose.y, (config.centerY[0] + config.centerY[1]) / 2), ylow, Math.max(ylow, yhigh)),
    size, angle
  };
}

/** Return the same sanitized world-space polygons used to rasterize the input. */
export function transformPolygons(config, pose) {
  const accepted = sanitizePose(config, pose);
  return transformed(prepare(config).shapes.get(accepted.shape), accepted);
}

function contains(polygon, x, y) {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [xi, yi] = polygon[i], [xj, yj] = polygon[j];
    if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

function rasterize(config, polygons) {
  const {nx, ny, n} = prepare(config);
  const mask = new Uint8Array(n);
  for (const polygon of polygons) {
    let left = Infinity, right = -Infinity, bottom = Infinity, top = -Infinity;
    for (const [x, y] of polygon) {
      left = Math.min(left, x); right = Math.max(right, x);
      bottom = Math.min(bottom, y); top = Math.max(top, y);
    }
    const ix0 = Math.max(0, Math.ceil((left - config.xmin) / config.dx - .5));
    const ix1 = Math.min(nx - 1, Math.floor((right - config.xmin) / config.dx - .5));
    const iy0 = Math.max(0, Math.ceil((bottom - config.ymin) / config.dx - .5));
    const iy1 = Math.min(ny - 1, Math.floor((top - config.ymin) / config.dx - .5));
    for (let iy = iy0; iy <= iy1; iy++) {
      const y = config.ymin + (iy + .5) * config.dx;
      for (let ix = ix0; ix <= ix1; ix++) {
        const index = iy * nx + ix;
        if (!mask[index] && contains(polygon, config.xmin + (ix + .5) * config.dx, y)) mask[index] = 1;
      }
    }
  }
  return mask;
}

// Exact squared Euclidean distance transform, separable lower-envelope method.
// Infinite rows are skipped explicitly, avoiding large-number cancellation.
function distanceLine(f, length, result, sites, breaks) {
  let first = 0;
  while (first < length && !Number.isFinite(f[first])) first++;
  if (first === length) { result.fill(Infinity, 0, length); return; }
  let count = 0;
  sites[0] = first; breaks[0] = -Infinity; breaks[1] = Infinity;
  for (let q = first + 1; q < length; q++) {
    if (!Number.isFinite(f[q])) continue;
    let site = sites[count];
    let crossing = ((f[q] + q * q) - (f[site] + site * site)) / (2 * (q - site));
    while (crossing <= breaks[count]) {
      count--; site = sites[count];
      crossing = ((f[q] + q * q) - (f[site] + site * site)) / (2 * (q - site));
    }
    count++; sites[count] = q; breaks[count] = crossing; breaks[count + 1] = Infinity;
  }
  count = 0;
  for (let q = 0; q < length; q++) {
    while (breaks[count + 1] < q) count++;
    const delta = q - sites[count];
    result[q] = delta * delta + f[sites[count]];
  }
}

function squaredDistance(mask, nx, ny, featureValue) {
  const height = ny * 3, length = Math.max(nx, height);
  const intermediate = new Float64Array(nx * height), result = new Float64Array(nx * height);
  const f = new Float64Array(length), line = new Float64Array(length);
  const sites = new Int32Array(length), breaks = new Float64Array(length + 1);
  for (let y = 0; y < height; y++) {
    const offset = y * nx, maskOffset = (y % ny) * nx;
    for (let x = 0; x < nx; x++) f[x] = mask[maskOffset + x] === featureValue ? 0 : Infinity;
    distanceLine(f, nx, line, sites, breaks);
    intermediate.set(line.subarray(0, nx), offset);
  }
  for (let x = 0; x < nx; x++) {
    for (let y = 0; y < height; y++) f[y] = intermediate[y * nx + x];
    distanceLine(f, height, line, sites, breaks);
    for (let y = 0; y < height; y++) result[y * nx + x] = line[y];
  }
  return result;
}

/** Periodic-y signed distance in model units; positive fluid, negative solid. */
export function periodicSignedDistance(mask, nx, ny, spacing) {
  if (!(mask instanceof Uint8Array) || mask.length !== nx * ny || !Number.isFinite(spacing) || spacing <= 0) {
    throw new Error('Invalid occupancy grid for signed distance');
  }
  let solids = 0;
  for (const value of mask) { if (value !== 0 && value !== 1) throw new Error('Occupancy must be binary'); solids += value; }
  if (!solids) return new Float32Array(mask.length).fill(4);
  if (solids === mask.length) throw new Error('The entire prediction domain cannot be solid');
  const toSolid = squaredDistance(mask, nx, ny, 1), toFluid = squaredDistance(mask, nx, ny, 0);
  const sdf = new Float32Array(mask.length), offset = nx * ny;
  for (let i = 0; i < mask.length; i++) sdf[i] = spacing * (Math.sqrt(toSolid[offset + i]) - Math.sqrt(toFluid[offset + i]));
  return sdf;
}

/** Build NCHW [mask, clipped periodic SDF, cell-center x, cell-center y]. */
export function buildInputs(config, pose) {
  const {nx, ny, n} = prepare(config);
  const polygons = transformPolygons(config, pose), mask = rasterize(config, polygons);
  let solids = 0;
  for (const value of mask) solids += value;
  if (polygons.length && solids < 20) throw new Error('Geometry has fewer than 20 resolved solid cells');
  const sdf = periodicSignedDistance(mask, nx, ny, config.dx), data = new Float32Array(4 * n);
  const x0 = config.xmin + .5 * config.dx, y0 = config.ymin + .5 * config.dx;
  const xrange = (nx - 1) * config.dx, yrange = (ny - 1) * config.dx;
  for (let y = 0; y < ny; y++) for (let x = 0; x < nx; x++) {
    const i = y * nx + x;
    data[i] = mask[i];
    data[n + i] = clamp(Math.fround(sdf[i] / config.sdfScale), -4, 4);
    data[2 * n + i] = 2 * ((config.xmin + (x + .5) * config.dx) - x0) / xrange - 1;
    data[3 * n + i] = 2 * ((config.ymin + (y + .5) * config.dx) - y0) / yrange - 1;
  }
  return {data, mask, polygons};
}

/** Recover u/Uin, v/Uin and Cp from raw NCHW [du,dv,Cp] network output. */
export function recoverFields(config, response, mask) {
  const {nx, ny, n, scales} = prepare(config);
  if (!(response instanceof Float32Array) || response.length !== 3 * n ||
      !(mask instanceof Uint8Array) || mask.length !== n) throw new Error('Unexpected model response dimensions');
  let sum = 0;
  for (let y = 0; y < ny; y++) sum += response[2 * n + y * nx + nx - 1];
  const outletMean = Math.fround(sum / ny);
  const u = new Float32Array(n), v = new Float32Array(n), cp = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    if (![response[i], response[n + i], response[2 * n + i]].every(Number.isFinite)) throw new Error('Nonfinite model response');
    if (mask[i]) continue;
    const du = i % nx === 0 ? 0 : Math.fround(response[i] * scales[0]);
    u[i] = Math.fround(1 + du);
    v[i] = i % nx === 0 ? 0 : Math.fround(response[n + i] * scales[1]);
    cp[i] = Math.fround(Math.fround(response[2 * n + i] - outletMean) * scales[2]);
    if (![u[i], v[i], cp[i]].every(Number.isFinite)) throw new Error('Nonfinite recovered field');
  }
  return {u, v, cp};
}
