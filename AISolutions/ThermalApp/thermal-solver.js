(function initThermalSolver(root, factory) {
  const solver = factory();
  if (typeof module === "object" && module.exports) module.exports = solver;
  if (root) root.KhaniThermalSolver = solver;
})(typeof globalThis !== "undefined" ? globalThis : this, function createThermalSolver() {
  "use strict";

  const DEFAULT_INPUTS = Object.freeze({
    heatW: 120,
    durationMin: 20,
    initialCoolantC: 25,
    ambientC: 25,
    thermalResistanceCW: 0.18,
    coolantVolumeL: 5,
    coolantDensityKgM3: 1070,
    coolantCpJKgK: 3400,
    solidCapacityKJK: 8,
    convectionAreaCm2: 1200,
    convectionHWm2K: 8,
  });

  function finiteNumber(value, label, minimum, maximum) {
    const number = Number(value);
    if (!Number.isFinite(number)) throw new Error(`${label} must be a number.`);
    if (number < minimum || number > maximum) {
      throw new Error(`${label} must be between ${minimum} and ${maximum}.`);
    }
    return number;
  }

  function normalizeInputs(raw = {}) {
    return {
      heatW: finiteNumber(raw.heatW, "Heat load", 0, 1000000),
      durationMin: finiteNumber(raw.durationMin, "Duration", 0.1, 10080),
      initialCoolantC: finiteNumber(raw.initialCoolantC, "Initial coolant temperature", -100, 500),
      ambientC: finiteNumber(raw.ambientC, "Ambient temperature", -100, 500),
      thermalResistanceCW: finiteNumber(raw.thermalResistanceCW, "Thermal resistance", 0.000001, 1000),
      coolantVolumeL: finiteNumber(raw.coolantVolumeL, "Coolant volume", 0, 100000),
      coolantDensityKgM3: finiteNumber(raw.coolantDensityKgM3, "Coolant density", 1, 30000),
      coolantCpJKgK: finiteNumber(raw.coolantCpJKgK, "Coolant specific heat", 1, 100000),
      solidCapacityKJK: finiteNumber(raw.solidCapacityKJK, "Solid thermal capacity", 0, 1000000),
      convectionAreaCm2: finiteNumber(raw.convectionAreaCm2, "Exposed area", 0, 100000000),
      convectionHWm2K: finiteNumber(raw.convectionHWm2K, "Convection coefficient", 0, 100000),
    };
  }

  function solvePoint(input, coolantC) {
    const convectionAreaM2 = input.convectionAreaCm2 / 10000;
    let heatToCoolantW = input.heatW;
    let convectionW = 0;

    for (let iteration = 0; iteration < 8; iteration += 1) {
      const sourceRiseC = heatToCoolantW * input.thermalResistanceCW;
      const representativeSurfaceC = coolantC + sourceRiseC / 2;
      convectionW = Math.min(
        input.heatW,
        convectionAreaM2 * input.convectionHWm2K * Math.max(representativeSurfaceC - input.ambientC, 0),
      );
      const nextHeatToCoolantW = Math.max(input.heatW - convectionW, 0);
      if (Math.abs(nextHeatToCoolantW - heatToCoolantW) < 1e-8) {
        heatToCoolantW = nextHeatToCoolantW;
        break;
      }
      heatToCoolantW = nextHeatToCoolantW;
    }

    const sourceRiseC = heatToCoolantW * input.thermalResistanceCW;
    return {
      sourceC: coolantC + sourceRiseC,
      sourceRiseC,
      convectionW,
      heatToCoolantW,
    };
  }

  function simulate(rawInputs) {
    const input = normalizeInputs(rawInputs);
    const durationS = input.durationMin * 60;
    const steps = 120;
    const dtS = durationS / steps;
    const liquidCapacityJK = input.coolantVolumeL / 1000 * input.coolantDensityKgM3 * input.coolantCpJKgK;
    const solidCapacityJK = input.solidCapacityKJK * 1000;
    const loopCapacityJK = liquidCapacityJK + solidCapacityJK;
    if (loopCapacityJK <= 0) throw new Error("Coolant and solid thermal capacity cannot both be zero.");

    const points = [];
    let storedEnergyJ = 0;
    let convectionEnergyJ = 0;

    for (let index = 0; index <= steps; index += 1) {
      const timeS = index * dtS;
      const coolantC = input.initialCoolantC + storedEnergyJ / loopCapacityJK;
      const solved = solvePoint(input, coolantC);
      points.push({
        timeS,
        timeMin: timeS / 60,
        coolantC,
        sourceC: solved.sourceC,
        sourceRiseC: solved.sourceRiseC,
        convectionW: solved.convectionW,
        heatToCoolantW: solved.heatToCoolantW,
      });
      if (index < steps) {
        storedEnergyJ += solved.heatToCoolantW * dtS;
        convectionEnergyJ += solved.convectionW * dtS;
      }
    }

    const final = points[points.length - 1];
    const peakSourceC = Math.max(...points.map((point) => point.sourceC));
    const peakCoolantC = Math.max(...points.map((point) => point.coolantC));
    return {
      inputs: input,
      points,
      summary: {
        peakSourceC,
        peakCoolantC,
        finalSourceC: final.sourceC,
        finalCoolantC: final.coolantC,
        coolantRiseC: final.coolantC - input.initialCoolantC,
        loopCapacityKJK: loopCapacityJK / 1000,
        liquidCapacityKJK: liquidCapacityJK / 1000,
        solidCapacityKJK: solidCapacityJK / 1000,
        thermalResistanceCW: input.thermalResistanceCW,
        storedEnergyKJ: storedEnergyJ / 1000,
        convectionEnergyKJ: convectionEnergyJ / 1000,
        finalConvectionW: final.convectionW,
        finalHeatToCoolantW: final.heatToCoolantW,
      },
    };
  }

  return { DEFAULT_INPUTS, normalizeInputs, simulate };
});
