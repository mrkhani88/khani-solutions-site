#!/usr/bin/env node

const assert = require("node:assert/strict");
const {
  DEFAULT_INPUTS,
  simulate,
  simulateNetwork,
  simulateHydraulics,
  simulateCellHeat,
} = require("./AISolutions/ThermalApp/thermal-solver.js");

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

const networkModel = {
  materials: [
    { id: "solid", name: "Solid", type: "solid", k: 10, density: 1000, cp: 1000 },
    { id: "fluid", name: "Fluid", type: "liquid", k: 0.5, density: 1000, cp: 4000 },
  ],
  blocks: [
    { id: "source", name: "Source", materialId: "solid", initialC: 20, heatW: 100, xMm: 100, yMm: 100, zMm: 100 },
    { id: "sink", name: "Sink", materialId: "fluid", initialC: 20, heatW: 0, xMm: 100, yMm: 100, zMm: 100 },
  ],
  connections: [
    { id: "source-sink", fromId: "source", toId: "sink", type: "conduction", resistanceCW: 0.1 },
    { id: "sink-ambient", fromId: "sink", toId: "ambient", type: "heat rejection", resistanceCW: 0.5 },
  ],
};
const networkResult = simulateNetwork(networkModel, { mode: "transient", durationMin: 10, outputStepS: 5, ambientC: 20 });
assert.equal(networkResult.points.length, 121);
assert.ok(networkResult.summary.peakSourceC > networkResult.summary.finalTemperatures.sink);
assert.ok(networkResult.summary.finalTemperatures.sink > 20);
assert.ok(Math.abs(networkResult.summary.energyBalanceKJ) < 1e-6);
const steadyNetworkResult = simulateNetwork(networkModel, { mode: "steady", durationMin: 10, outputStepS: 5, ambientC: 20 });
assert.equal(steadyNetworkResult.points.length, 2);
assert.ok(Math.abs(steadyNetworkResult.summary.finalTemperatures.source - 80) < 1e-9);
assert.ok(Math.abs(steadyNetworkResult.summary.finalTemperatures.sink - 70) < 1e-9);
assert.ok(Math.abs(steadyNetworkResult.summary.steadyEnergyBalanceW) < 1e-9);
assert.throws(
  () => simulateNetwork({ ...networkModel, connections: [networkModel.connections[0]] }, { durationMin: 1, outputStepS: 1, ambientC: 20 }),
  /Ambient/,
);

const hydraulicResult = simulateHydraulics({
  flowLpm: 10,
  density: 1000,
  viscosityMpas: 1,
  components: [{ name: "Pipe", lengthM: 2, diameterMm: 15, minorK: 2 }],
});
assert.ok(hydraulicResult.summary.totalPressureDropKPa > 0);
assert.ok(hydraulicResult.summary.pumpPowerW > 0);

const cellResult = simulateCellHeat({ currentA: 10, resistanceMOhm: 20, cellCount: 100, durationMin: 30 });
assert.equal(cellResult.points.length, 121);
assert.equal(cellResult.summary.perCellW, 2);
assert.equal(cellResult.summary.peakHeatW, 200);
assert.ok(cellResult.summary.energyKJ > 0);

console.log("Thermal solver tests passed.");
