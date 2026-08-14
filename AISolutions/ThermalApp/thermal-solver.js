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

  function normalizeNetworkModel(rawModel = {}) {
    const materials = Array.isArray(rawModel.materials) ? rawModel.materials : [];
    const blocks = Array.isArray(rawModel.blocks) ? rawModel.blocks : [];
    const connections = Array.isArray(rawModel.connections) ? rawModel.connections : [];
    if (!materials.length) throw new Error("Add at least one material.");
    if (!blocks.length) throw new Error("Add at least one thermal block.");

    const normalizedMaterials = materials.map((material, index) => ({
      id: String(material.id || `material-${index}`),
      name: String(material.name || `Material ${index + 1}`),
      type: String(material.type || "solid"),
      k: finiteNumber(material.k, `${material.name || "Material"} conductivity`, 0.000001, 1000000),
      density: finiteNumber(material.density, `${material.name || "Material"} density`, 0.000001, 100000),
      cp: finiteNumber(material.cp, `${material.name || "Material"} specific heat`, 0.000001, 1000000),
    }));
    const materialMap = new Map(normalizedMaterials.map((material) => [material.id, material]));
    const ids = new Set();
    const normalizedBlocks = blocks.map((block, index) => {
      const id = String(block.id || `block-${index}`);
      if (ids.has(id)) throw new Error("Thermal block identifiers must be unique.");
      ids.add(id);
      const material = materialMap.get(String(block.materialId));
      if (!material) throw new Error(`${block.name || "Block"} needs a valid material.`);
      const xMm = finiteNumber(block.xMm, `${block.name || "Block"} X dimension`, 0.001, 1000000);
      const yMm = finiteNumber(block.yMm, `${block.name || "Block"} Y dimension`, 0.001, 1000000);
      const zMm = finiteNumber(block.zMm, `${block.name || "Block"} Z dimension`, 0.001, 1000000);
      const volumeM3 = xMm * yMm * zMm * 1e-9;
      return {
        id,
        name: String(block.name || `Block ${index + 1}`),
        materialId: material.id,
        initialC: finiteNumber(block.initialC, `${block.name || "Block"} initial temperature`, -273.15, 2000),
        heatW: finiteNumber(block.heatW, `${block.name || "Block"} heat`, -10000000, 10000000),
        xMm,
        yMm,
        zMm,
        volumeM3,
        capacityJK: volumeM3 * material.density * material.cp,
      };
    });
    const blockMap = new Map(normalizedBlocks.map((block) => [block.id, block]));
    const normalizedConnections = connections.map((connection, index) => {
      const fromId = String(connection.fromId || "");
      const toId = String(connection.toId || "");
      if (!blockMap.has(fromId)) throw new Error(`Connection ${index + 1} needs a valid source block.`);
      if (toId !== "ambient" && !blockMap.has(toId)) throw new Error(`Connection ${index + 1} needs a valid destination.`);
      if (fromId === toId) throw new Error(`Connection ${index + 1} cannot connect a block to itself.`);
      return {
        id: String(connection.id || `connection-${index}`),
        fromId,
        toId,
        type: String(connection.type || "conduction"),
        resistanceCW: finiteNumber(connection.resistanceCW, `Connection ${index + 1} resistance`, 0.000001, 1000000),
      };
    });
    if (!normalizedConnections.some((connection) => connection.toId === "ambient")) {
      throw new Error("Add at least one connection to Ambient.");
    }
    return { materials: normalizedMaterials, blocks: normalizedBlocks, connections: normalizedConnections };
  }

  function solveLinearSystem(matrix, values) {
    const size = values.length;
    const a = matrix.map((row) => [...row]);
    const b = [...values];
    for (let column = 0; column < size; column += 1) {
      let pivot = column;
      for (let row = column + 1; row < size; row += 1) {
        if (Math.abs(a[row][column]) > Math.abs(a[pivot][column])) pivot = row;
      }
      if (Math.abs(a[pivot][column]) < 1e-12) throw new Error("The steady-state network is not connected to Ambient.");
      [a[column], a[pivot]] = [a[pivot], a[column]];
      [b[column], b[pivot]] = [b[pivot], b[column]];
      const divisor = a[column][column];
      for (let index = column; index < size; index += 1) a[column][index] /= divisor;
      b[column] /= divisor;
      for (let row = 0; row < size; row += 1) {
        if (row === column) continue;
        const factor = a[row][column];
        for (let index = column; index < size; index += 1) a[row][index] -= factor * a[column][index];
        b[row] -= factor * b[column];
      }
    }
    return b;
  }

  function simulateNetwork(rawModel, rawSettings = {}) {
    const model = normalizeNetworkModel(rawModel);
    const settings = {
      mode: rawSettings.mode === "steady" ? "steady" : "transient",
      durationMin: finiteNumber(rawSettings.durationMin, "Duration", 0.1, 1440),
      outputStepS: finiteNumber(rawSettings.outputStepS, "Output step", 0.1, 600),
      ambientC: finiteNumber(rawSettings.ambientC, "Ambient temperature", -273.15, 2000),
    };
    const blockIndex = new Map(model.blocks.map((block, index) => [block.id, index]));
    const conductanceSum = new Array(model.blocks.length).fill(0);
    model.connections.forEach((connection) => {
      const conductance = 1 / connection.resistanceCW;
      conductanceSum[blockIndex.get(connection.fromId)] += conductance;
      if (connection.toId !== "ambient") conductanceSum[blockIndex.get(connection.toId)] += conductance;
    });
    if (settings.mode === "steady") {
      const matrix = model.blocks.map(() => new Array(model.blocks.length).fill(0));
      const values = model.blocks.map((block) => block.heatW);
      model.connections.forEach((connection) => {
        const conductance = 1 / connection.resistanceCW;
        const fromIndex = blockIndex.get(connection.fromId);
        matrix[fromIndex][fromIndex] += conductance;
        if (connection.toId === "ambient") {
          values[fromIndex] += conductance * settings.ambientC;
        } else {
          const toIndex = blockIndex.get(connection.toId);
          matrix[toIndex][toIndex] += conductance;
          matrix[fromIndex][toIndex] -= conductance;
          matrix[toIndex][fromIndex] -= conductance;
        }
      });
      const steadyTemperatures = solveLinearSystem(matrix, values);
      const finalFlows = model.connections.map((connection) => {
        const fromIndex = blockIndex.get(connection.fromId);
        const toTemperature = connection.toId === "ambient" ? settings.ambientC : steadyTemperatures[blockIndex.get(connection.toId)];
        return { ...connection, heatFlowW: (steadyTemperatures[fromIndex] - toTemperature) / connection.resistanceCW };
      });
      const sourceIndex = Math.max(0, model.blocks.findIndex((block) => block.heatW > 0));
      const hottestIndex = steadyTemperatures.reduce((best, value, index) => value > steadyTemperatures[best] ? index : best, 0);
      const totalHeatW = model.blocks.reduce((sum, block) => sum + block.heatW, 0);
      const ambientHeatW = finalFlows.filter((flow) => flow.toId === "ambient").reduce((sum, flow) => sum + flow.heatFlowW, 0);
      const point = (timeS, temperatures) => ({
        timeS,
        timeMin: timeS / 60,
        temperatures: Object.fromEntries(model.blocks.map((block, index) => [block.id, temperatures[index]])),
      });
      return {
        model,
        settings,
        points: [point(0, model.blocks.map((block) => block.initialC)), point(settings.durationMin * 60, steadyTemperatures)],
        finalFlows,
        summary: {
          peakSourceC: steadyTemperatures[sourceIndex],
          finalSourceC: steadyTemperatures[sourceIndex],
          hottestBlockName: model.blocks[hottestIndex].name,
          hottestBlockC: steadyTemperatures[hottestIndex],
          finalTemperatures: Object.fromEntries(model.blocks.map((block, index) => [block.id, steadyTemperatures[index]])),
          totalCapacityKJK: model.blocks.reduce((sum, block) => sum + block.capacityJK, 0) / 1000,
          totalHeatW,
          inputEnergyKJ: 0,
          ambientEnergyKJ: 0,
          storedEnergyKJ: 0,
          energyBalanceKJ: 0,
          steadyEnergyBalanceW: totalHeatW - ambientHeatW,
          internalStepS: 0,
        },
      };
    }
    const stableDt = model.blocks.reduce((minimum, block, index) => {
      if (conductanceSum[index] <= 0) return minimum;
      return Math.min(minimum, block.capacityJK / conductanceSum[index] * 0.12);
    }, settings.outputStepS);
    const durationS = settings.durationMin * 60;
    const minimumDt = durationS / 250000;
    const dtS = Math.max(minimumDt, Math.min(settings.outputStepS, stableDt));
    const temperatures = model.blocks.map((block) => block.initialC);
    const initialTemperatures = [...temperatures];
    const peakTemperatures = [...temperatures];
    const points = [];
    let inputEnergyJ = 0;
    let ambientEnergyJ = 0;
    let nextOutputS = 0;
    let timeS = 0;

    function recordPoint(recordTimeS) {
      points.push({
        timeS: recordTimeS,
        timeMin: recordTimeS / 60,
        temperatures: Object.fromEntries(model.blocks.map((block, index) => [block.id, temperatures[index]])),
      });
    }

    recordPoint(0);
    nextOutputS = settings.outputStepS;
    while (timeS < durationS - 1e-9) {
      const stepS = Math.min(dtS, durationS - timeS);
      const energy = model.blocks.map((block) => block.heatW * stepS);
      model.blocks.forEach((block) => { inputEnergyJ += block.heatW * stepS; });
      model.connections.forEach((connection) => {
        const fromIndex = blockIndex.get(connection.fromId);
        const toIndex = connection.toId === "ambient" ? -1 : blockIndex.get(connection.toId);
        const toTemperature = toIndex < 0 ? settings.ambientC : temperatures[toIndex];
        const heatFlowW = (temperatures[fromIndex] - toTemperature) / connection.resistanceCW;
        const transferJ = heatFlowW * stepS;
        energy[fromIndex] -= transferJ;
        if (toIndex >= 0) energy[toIndex] += transferJ;
        else ambientEnergyJ += transferJ;
      });
      model.blocks.forEach((block, index) => {
        temperatures[index] += energy[index] / block.capacityJK;
        if (!Number.isFinite(temperatures[index]) || Math.abs(temperatures[index]) > 100000) {
          throw new Error("The model became unstable. Increase thermal capacity or resistance.");
        }
        peakTemperatures[index] = Math.max(peakTemperatures[index], temperatures[index]);
      });
      timeS += stepS;
      if (timeS + 1e-7 >= nextOutputS || timeS + 1e-7 >= durationS) {
        recordPoint(timeS);
        while (nextOutputS <= timeS + 1e-7) nextOutputS += settings.outputStepS;
      }
    }

    const finalFlows = model.connections.map((connection) => {
      const fromIndex = blockIndex.get(connection.fromId);
      const toTemperature = connection.toId === "ambient" ? settings.ambientC : temperatures[blockIndex.get(connection.toId)];
      return { ...connection, heatFlowW: (temperatures[fromIndex] - toTemperature) / connection.resistanceCW };
    });
    const storedEnergyJ = model.blocks.reduce(
      (sum, block, index) => sum + block.capacityJK * (temperatures[index] - initialTemperatures[index]),
      0,
    );
    const sourceIndex = Math.max(0, model.blocks.findIndex((block) => block.heatW > 0));
    const hottestIndex = peakTemperatures.reduce((best, value, index) => value > peakTemperatures[best] ? index : best, 0);
    return {
      model,
      settings,
      points,
      finalFlows,
      summary: {
        peakSourceC: peakTemperatures[sourceIndex],
        finalSourceC: temperatures[sourceIndex],
        hottestBlockName: model.blocks[hottestIndex].name,
        hottestBlockC: peakTemperatures[hottestIndex],
        finalTemperatures: Object.fromEntries(model.blocks.map((block, index) => [block.id, temperatures[index]])),
        totalCapacityKJK: model.blocks.reduce((sum, block) => sum + block.capacityJK, 0) / 1000,
        totalHeatW: model.blocks.reduce((sum, block) => sum + block.heatW, 0),
        inputEnergyKJ: inputEnergyJ / 1000,
        ambientEnergyKJ: ambientEnergyJ / 1000,
        storedEnergyKJ: storedEnergyJ / 1000,
        energyBalanceKJ: (inputEnergyJ - ambientEnergyJ - storedEnergyJ) / 1000,
        internalStepS: dtS,
      },
    };
  }

  function simulateHydraulics(raw = {}) {
    const flowLpm = finiteNumber(raw.flowLpm, "Flow rate", 0.001, 100000);
    const density = finiteNumber(raw.density, "Fluid density", 0.001, 100000);
    const viscosityMpas = finiteNumber(raw.viscosityMpas, "Fluid viscosity", 0.000001, 100000);
    const components = Array.isArray(raw.components) ? raw.components : [];
    const flowM3S = flowLpm / 60000;
    const viscosityPas = viscosityMpas / 1000;
    const solved = components.map((component, index) => {
      const diameterM = finiteNumber(component.diameterMm, `Component ${index + 1} diameter`, 0.01, 10000) / 1000;
      const lengthM = finiteNumber(component.lengthM, `Component ${index + 1} length`, 0, 100000);
      const minorK = finiteNumber(component.minorK, `Component ${index + 1} minor loss`, 0, 1000000);
      const areaM2 = Math.PI * diameterM * diameterM / 4;
      const velocityMS = flowM3S / areaM2;
      const reynolds = density * velocityMS * diameterM / viscosityPas;
      const friction = reynolds < 2300 ? 64 / Math.max(reynolds, 1) : 0.25 / Math.pow(Math.log10(5.74 / Math.pow(reynolds, 0.9)), 2);
      const pressureDropKPa = (friction * lengthM / diameterM + minorK) * density * velocityMS * velocityMS / 2 / 1000;
      return { ...component, pressureDropKPa, velocityMS, reynolds, friction };
    });
    const totalPressureDropKPa = solved.reduce((sum, component) => sum + component.pressureDropKPa, 0);
    return {
      components: solved,
      summary: {
        flowLpm,
        totalPressureDropKPa,
        pumpPowerW: totalPressureDropKPa * 1000 * flowM3S,
        maxVelocityMS: Math.max(...solved.map((component) => component.velocityMS), 0),
        maxReynolds: Math.max(...solved.map((component) => component.reynolds), 0),
      },
    };
  }

  function simulateCellHeat(raw = {}) {
    const currentA = finiteNumber(raw.currentA, "Cell current", 0, 100000);
    const resistanceMOhm = finiteNumber(raw.resistanceMOhm, "Internal resistance", 0, 1000000);
    const cellCount = finiteNumber(raw.cellCount, "Cell count", 1, 10000000);
    const durationMin = finiteNumber(raw.durationMin, "Duration", 0.1, 10080);
    const perCellW = currentA * currentA * resistanceMOhm / 1000;
    const points = Array.from({ length: 121 }, (_, index) => {
      const timeMin = durationMin * index / 120;
      const missionFactor = 0.78 + 0.22 * Math.sin(Math.PI * index / 120) ** 2;
      return { timeMin, heatW: perCellW * cellCount * missionFactor };
    });
    return {
      points,
      summary: {
        perCellW,
        peakHeatW: Math.max(...points.map((point) => point.heatW)),
        averageHeatW: points.reduce((sum, point) => sum + point.heatW, 0) / points.length,
        energyKJ: points.reduce((sum, point, index) => index ? sum + (point.heatW + points[index - 1].heatW) / 2 * durationMin * 60 / 120 : sum, 0) / 1000,
      },
    };
  }

  return { DEFAULT_INPUTS, normalizeInputs, simulate, normalizeNetworkModel, simulateNetwork, simulateHydraulics, simulateCellHeat };
});
