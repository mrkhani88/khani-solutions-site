#!/usr/bin/env node

const assert = require("node:assert/strict");
const { DEFAULT_INPUTS, simulate } = require("./AISolutions/ThermalApp/thermal-solver.js");

const baseline = simulate(DEFAULT_INPUTS);
assert.equal(baseline.points.length, 121);
assert.ok(Math.abs(baseline.summary.loopCapacityKJK - 26.19) < 1e-9);
assert.ok(baseline.summary.peakSourceC > baseline.summary.peakCoolantC);
assert.ok(baseline.summary.finalCoolantC > DEFAULT_INPUTS.initialCoolantC);
assert.ok(Math.abs(
  baseline.summary.storedEnergyKJ + baseline.summary.convectionEnergyKJ
  - DEFAULT_INPUTS.heatW * DEFAULT_INPUTS.durationMin * 60 / 1000,
) < 1e-6);

const noHeat = simulate({ ...DEFAULT_INPUTS, heatW: 0 });
assert.equal(noHeat.summary.peakSourceC, DEFAULT_INPUTS.initialCoolantC);
assert.equal(noHeat.summary.finalCoolantC, DEFAULT_INPUTS.initialCoolantC);

const resistanceCase = simulate({
  ...DEFAULT_INPUTS,
  heatW: 100,
  durationMin: 1,
  initialCoolantC: 20,
  thermalResistanceCW: 0.25,
  convectionAreaCm2: 0,
});
assert.ok(Math.abs(resistanceCase.points[0].sourceC - 45) < 1e-9);
assert.ok(Math.abs(resistanceCase.points[0].sourceRiseC - 25) < 1e-9);

assert.throws(
  () => simulate({ ...DEFAULT_INPUTS, coolantVolumeL: 0, solidCapacityKJK: 0 }),
  /cannot both be zero/,
);
assert.throws(() => simulate({ ...DEFAULT_INPUTS, thermalResistanceCW: -1 }), /Thermal resistance/);

console.log("Thermal solver tests passed.");
