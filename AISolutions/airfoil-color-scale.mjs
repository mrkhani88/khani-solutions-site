// Display-only adaptive ranges. Robust near-airfoil quantiles keep isolated
// ideal-flow peaks from washing out the rest of the field. Physics is unchanged.
const quantile = (sorted, fraction) => {
  const i = (sorted.length - 1) * fraction, lo = Math.floor(i), f = i - lo;
  return sorted[lo] * (1 - f) + sorted[Math.ceil(i)] * f;
};
export function normalizedFieldBounds(samples) {
  const valid = samples.filter(s => s && Number.isFinite(s.speed) && Number.isFinite(s.cp));
  if (!valid.length) return {velocity:[0.5,1.5], pressure:[-1,1]};
  const speed = valid.map(s => s.speed).sort((a,b) => a-b);
  const cp = valid.map(s => s.cp).sort((a,b) => a-b);
  return {
    velocity:[Math.max(0,Math.min(0.98,quantile(speed,0.02))), Math.max(1.02,quantile(speed,0.98))],
    pressure:[Math.min(-0.05,quantile(cp,0.02)), Math.max(0.05,quantile(cp,0.98))]
  };
}
export function dimensionalFieldScale(bounds, windSpeed, mode, density=1.225) {
  const wind = Math.max(0,windSpeed), pressure = mode === 'pressure';
  const factor = pressure ? 0.5*density*wind**2 : wind;
  const pair = pressure ? bounds.pressure : bounds.velocity;
  return {min:pair[0]*factor, max:pair[1]*factor, center:pressure ? 0 : null, noWind:wind===0};
}
export function fieldColorPosition(value, scale) {
  if (scale.noWind || scale.max <= scale.min) return 0.5;
  // Pressure uses a diverging map: zero pressure difference is always neutral.
  const position = scale.center === 0
    ? value < 0 ? 0.5*(1-value/scale.min) : 0.5+0.5*value/scale.max
    : (value-scale.min)/(scale.max-scale.min);
  return Math.max(0,Math.min(1,position));
}
