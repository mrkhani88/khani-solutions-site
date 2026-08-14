(function initializeThermalWorkspace() {
  "use strict";

  const MODEL_STORAGE_KEY = "khaniThermal.publicNetwork.v1";
  const CASE_STORAGE_KEY = "khaniThermal.publicCases.v1";
  const SERIES_COLORS = ["#2b67a0", "#a98234", "#33766d", "#a94a4a", "#655c93", "#3b858f"];

  const DEFAULT_MODEL = {
    materials: [
      { id: "electronics", name: "Electronics assembly", type: "solid", k: 1.6, density: 1600, cp: 900 },
      { id: "gap-pad", name: "Thermal interface pad", type: "solid", k: 3, density: 3200, cp: 1000 },
      { id: "aluminum", name: "Aluminum 6061-T6", type: "solid", k: 167, density: 2700, cp: 896 },
      { id: "coolant", name: "50/50 glycol-water", type: "liquid", k: 0.39, density: 1070, cp: 3400 },
    ],
    blocks: [
      { id: "device", name: "Electronics", materialId: "electronics", initialC: 25, heatW: 120, xMm: 100, yMm: 80, zMm: 20 },
      { id: "interface", name: "Interface pad", materialId: "gap-pad", initialC: 25, heatW: 0, xMm: 100, yMm: 80, zMm: 1 },
      { id: "plate", name: "Cold plate", materialId: "aluminum", initialC: 25, heatW: 0, xMm: 200, yMm: 160, zMm: 10 },
      { id: "fluid", name: "Coolant inventory", materialId: "coolant", initialC: 25, heatW: 0, xMm: 100, yMm: 100, zMm: 500 },
    ],
    connections: [
      { id: "device-interface", fromId: "device", toId: "interface", type: "conduction", resistanceCW: 0.08 },
      { id: "interface-plate", fromId: "interface", toId: "plate", type: "conduction", resistanceCW: 0.04 },
      { id: "plate-fluid", fromId: "plate", toId: "fluid", type: "convection", resistanceCW: 0.03 },
      { id: "fluid-ambient", fromId: "fluid", toId: "ambient", type: "heat rejection", resistanceCW: 0.35 },
    ],
  };

  const DEFAULT_HYDRAULIC_COMPONENTS = [
    { id: "pump-line", name: "Supply line", type: "Pipe", lengthM: 1.8, diameterMm: 16, minorK: 1.2 },
    { id: "cold-plate", name: "Cold plate", type: "Heat exchanger", lengthM: 0.8, diameterMm: 10, minorK: 6.5 },
    { id: "return-line", name: "Return line", type: "Pipe", lengthM: 2.1, diameterMm: 16, minorK: 1.7 },
    { id: "filter", name: "Filter and fittings", type: "Restriction", lengthM: 0.25, diameterMm: 12, minorK: 8 },
  ];

  const elements = {
    moduleTabs: [...document.querySelectorAll("[data-module-tab]")],
    modulePanels: [...document.querySelectorAll("[data-module-panel]")],
    materialsBody: document.querySelector("[data-materials-body]"),
    blocksBody: document.querySelector("[data-blocks-body]"),
    connectionsBody: document.querySelector("[data-connections-body]"),
    networkForm: document.querySelector("[data-network-form]"),
    runStatus: document.querySelector("[data-run-status]"),
    runTime: document.querySelector("[data-run-time]"),
    resultMetrics: document.querySelector("[data-result-metrics]"),
    temperatureChart: document.querySelector("[data-temperature-chart]"),
    chartLegend: document.querySelector("[data-chart-legend]"),
    assemblyView: document.querySelector("[data-assembly-view]"),
    flowChart: document.querySelector("[data-flow-chart]"),
    saveCaseForm: document.querySelector("[data-save-case-form]"),
    caseComparison: document.querySelector("[data-case-comparison]"),
    hydraulicComponents: document.querySelector("[data-hydraulic-components]"),
    hydraulicLoop: document.querySelector("[data-hydraulic-loop]"),
    hydraulicMetrics: document.querySelector("[data-hydraulic-metrics]"),
    cfdCases: document.querySelector("[data-cfd-cases]"),
    cfdViewer: document.querySelector("[data-cfd-viewer]"),
    cfdDetails: document.querySelector("[data-cfd-details]"),
    cellMetrics: document.querySelector("[data-cell-metrics]"),
    cellChart: document.querySelector("[data-cell-chart]"),
    libraryList: document.querySelector("[data-library-list]"),
    libraryCount: document.querySelector("[data-library-count]"),
  };

  let model = loadJson(MODEL_STORAGE_KEY, DEFAULT_MODEL);
  let cases = loadJson(CASE_STORAGE_KEY, []);
  let hydraulicComponents = clone(DEFAULT_HYDRAULIC_COMPONENTS);
  let latestResult = null;
  let latestSettings = null;

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function loadJson(key, fallback) {
    try {
      const value = JSON.parse(localStorage.getItem(key));
      return value && typeof value === "object" ? value : clone(fallback);
    } catch {
      return clone(fallback);
    }
  }

  function saveModel() {
    localStorage.setItem(MODEL_STORAGE_KEY, JSON.stringify(model));
  }

  function saveCases() {
    localStorage.setItem(CASE_STORAGE_KEY, JSON.stringify(cases));
  }

  function uid(prefix) {
    return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function formatNumber(value, digits = 1) {
    return Number(value).toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
  }

  function materialById(id) {
    return model.materials.find((material) => material.id === id);
  }

  function blockById(id) {
    return model.blocks.find((block) => block.id === id);
  }

  function blockCapacityKJK(block) {
    const material = materialById(block.materialId);
    if (!material) return 0;
    return Number(block.xMm) * Number(block.yMm) * Number(block.zMm) * 1e-9 * Number(material.density) * Number(material.cp) / 1000;
  }

  function selectOptions(items, selectedId, labelKey = "name") {
    return items.map((item) => `<option value="${escapeHtml(item.id)}"${item.id === selectedId ? " selected" : ""}>${escapeHtml(item[labelKey])}</option>`).join("");
  }

  function renderMaterials() {
    elements.materialsBody.innerHTML = model.materials.map((material) => `
      <tr>
        <td><input data-model-kind="material" data-id="${escapeHtml(material.id)}" data-field="name" aria-label="Material name" value="${escapeHtml(material.name)}" /></td>
        <td><select data-model-kind="material" data-id="${escapeHtml(material.id)}" data-field="type" aria-label="Material type">
          ${["solid", "liquid", "gas"].map((type) => `<option value="${type}"${material.type === type ? " selected" : ""}>${type}</option>`).join("")}
        </select></td>
        <td><input data-model-kind="material" data-id="${escapeHtml(material.id)}" data-field="k" type="number" min="0.000001" step="any" aria-label="${escapeHtml(material.name)} conductivity" value="${escapeHtml(material.k)}" /></td>
        <td><input data-model-kind="material" data-id="${escapeHtml(material.id)}" data-field="density" type="number" min="0.000001" step="any" aria-label="${escapeHtml(material.name)} density" value="${escapeHtml(material.density)}" /></td>
        <td><input data-model-kind="material" data-id="${escapeHtml(material.id)}" data-field="cp" type="number" min="0.000001" step="any" aria-label="${escapeHtml(material.name)} specific heat" value="${escapeHtml(material.cp)}" /></td>
        <td><button class="row-remove" type="button" data-remove-material="${escapeHtml(material.id)}" title="Remove material" aria-label="Remove ${escapeHtml(material.name)}"><i data-lucide="minus"></i></button></td>
      </tr>
    `).join("");
  }

  function renderBlocks() {
    elements.blocksBody.innerHTML = model.blocks.map((block) => `
      <tr>
        <td><input data-model-kind="block" data-id="${escapeHtml(block.id)}" data-field="name" aria-label="Block name" value="${escapeHtml(block.name)}" /></td>
        <td><select data-model-kind="block" data-id="${escapeHtml(block.id)}" data-field="materialId" aria-label="${escapeHtml(block.name)} material">${selectOptions(model.materials, block.materialId)}</select></td>
        <td><input data-model-kind="block" data-id="${escapeHtml(block.id)}" data-field="initialC" type="number" step="any" aria-label="${escapeHtml(block.name)} initial temperature" value="${escapeHtml(block.initialC)}" /></td>
        <td><input data-model-kind="block" data-id="${escapeHtml(block.id)}" data-field="heatW" type="number" step="any" aria-label="${escapeHtml(block.name)} heat" value="${escapeHtml(block.heatW)}" /></td>
        <td><input data-model-kind="block" data-id="${escapeHtml(block.id)}" data-field="xMm" type="number" min="0.001" step="any" aria-label="${escapeHtml(block.name)} X dimension" value="${escapeHtml(block.xMm)}" /></td>
        <td><input data-model-kind="block" data-id="${escapeHtml(block.id)}" data-field="yMm" type="number" min="0.001" step="any" aria-label="${escapeHtml(block.name)} Y dimension" value="${escapeHtml(block.yMm)}" /></td>
        <td><input data-model-kind="block" data-id="${escapeHtml(block.id)}" data-field="zMm" type="number" min="0.001" step="any" aria-label="${escapeHtml(block.name)} Z dimension" value="${escapeHtml(block.zMm)}" /></td>
        <td><span class="table-value">${formatNumber(blockCapacityKJK(block), 3)}</span></td>
        <td><button class="row-remove" type="button" data-remove-block="${escapeHtml(block.id)}" title="Remove block" aria-label="Remove ${escapeHtml(block.name)}"><i data-lucide="minus"></i></button></td>
      </tr>
    `).join("");
  }

  function renderConnections() {
    const destinations = [...model.blocks, { id: "ambient", name: "Ambient" }];
    elements.connectionsBody.innerHTML = model.connections.map((connection, index) => `
      <tr>
        <td><select data-model-kind="connection" data-id="${escapeHtml(connection.id)}" data-field="fromId" aria-label="Connection ${index + 1} source">${selectOptions(model.blocks, connection.fromId)}</select></td>
        <td><select data-model-kind="connection" data-id="${escapeHtml(connection.id)}" data-field="toId" aria-label="Connection ${index + 1} destination">${selectOptions(destinations, connection.toId)}</select></td>
        <td><select data-model-kind="connection" data-id="${escapeHtml(connection.id)}" data-field="type" aria-label="Connection ${index + 1} type">
          ${["conduction", "convection", "contact", "heat rejection"].map((type) => `<option value="${type}"${connection.type === type ? " selected" : ""}>${type}</option>`).join("")}
        </select></td>
        <td><input data-model-kind="connection" data-id="${escapeHtml(connection.id)}" data-field="resistanceCW" type="number" min="0.000001" step="any" aria-label="Connection ${index + 1} resistance" value="${escapeHtml(connection.resistanceCW)}" /></td>
        <td><button class="row-remove" type="button" data-remove-connection="${escapeHtml(connection.id)}" title="Remove connection" aria-label="Remove connection ${index + 1}"><i data-lucide="minus"></i></button></td>
      </tr>
    `).join("");
  }

  function renderModel() {
    renderMaterials();
    renderBlocks();
    renderConnections();
    renderAssembly(latestResult);
    renderFlowChart(latestResult);
    refreshIcons();
  }

  function updateModelControl(control) {
    const collection = control.dataset.modelKind === "material" ? model.materials : control.dataset.modelKind === "block" ? model.blocks : model.connections;
    const item = collection.find((candidate) => candidate.id === control.dataset.id);
    if (!item) return;
    const numericFields = new Set(["k", "density", "cp", "initialC", "heatW", "xMm", "yMm", "zMm", "resistanceCW"]);
    item[control.dataset.field] = numericFields.has(control.dataset.field) ? Number(control.value) : control.value;
    saveModel();
  }

  function networkSettings() {
    const data = new FormData(elements.networkForm);
    return {
      mode: String(data.get("mode")),
      durationMin: Number(data.get("durationMin")),
      outputStepS: Number(data.get("outputStepS")),
      ambientC: Number(data.get("ambientC")),
    };
  }

  function metricCard(label, value, unit) {
    return `<div class="metric-card"><small>${escapeHtml(label)}</small><strong>${escapeHtml(value)}</strong><em>${escapeHtml(unit)}</em></div>`;
  }

  function renderNetworkResult(result) {
    const finalTemperatures = Object.values(result.summary.finalTemperatures);
    elements.resultMetrics.innerHTML = [
      metricCard("Peak source", formatNumber(result.summary.peakSourceC, 1), "C"),
      metricCard("Hottest block", formatNumber(result.summary.hottestBlockC, 1), result.summary.hottestBlockName),
      metricCard("Total heat", formatNumber(result.summary.totalHeatW, 1), "W"),
      metricCard("Thermal capacity", formatNumber(result.summary.totalCapacityKJK, 2), "kJ/K"),
      metricCard("Final range", `${formatNumber(Math.min(...finalTemperatures), 1)}-${formatNumber(Math.max(...finalTemperatures), 1)}`, "C"),
    ].join("");
    elements.runTime.textContent = `${formatNumber(result.settings.durationMin, 1)} min | ${result.points.length} result times`;
    renderTemperatureChart(result);
    renderAssembly(result);
    renderFlowChart(result);
  }

  function renderTemperatureChart(result) {
    const width = 1100;
    const height = 390;
    const margin = { top: 26, right: 28, bottom: 52, left: 66 };
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    const allValues = result.points.flatMap((point) => model.blocks.map((block) => point.temperatures[block.id]));
    const minimum = Math.min(...allValues, result.settings.ambientC);
    const maximum = Math.max(...allValues, result.settings.ambientC);
    const range = Math.max(maximum - minimum, 1);
    const yMin = Math.floor((minimum - range * 0.1) / 5) * 5;
    const yMax = Math.ceil((maximum + range * 0.1) / 5) * 5;
    const xMax = result.settings.durationMin;
    const x = (value) => margin.left + value / xMax * plotWidth;
    const y = (value) => margin.top + (yMax - value) / Math.max(yMax - yMin, 1) * plotHeight;
    const xTicks = Array.from({ length: 6 }, (_, index) => xMax * index / 5);
    const yTicks = Array.from({ length: 6 }, (_, index) => yMin + (yMax - yMin) * index / 5);
    const paths = model.blocks.map((block, seriesIndex) => {
      const path = result.points.map((point, index) => `${index ? "L" : "M"}${x(point.timeMin).toFixed(2)},${y(point.temperatures[block.id]).toFixed(2)}`).join(" ");
      return `<path class="chart-series" stroke="${SERIES_COLORS[seriesIndex % SERIES_COLORS.length]}" d="${path}"></path>`;
    }).join("");
    elements.temperatureChart.innerHTML = `
      <svg viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="thermal-chart-title thermal-chart-desc">
        <title id="thermal-chart-title">Thermal network temperature history</title>
        <desc id="thermal-chart-desc">Calculated temperatures for ${model.blocks.length} thermal blocks over ${formatNumber(xMax, 1)} minutes.</desc>
        <g class="chart-grid">
          ${yTicks.map((tick) => `<line x1="${margin.left}" y1="${y(tick)}" x2="${width - margin.right}" y2="${y(tick)}"></line>`).join("")}
          ${xTicks.map((tick) => `<line x1="${x(tick)}" y1="${margin.top}" x2="${x(tick)}" y2="${height - margin.bottom}"></line>`).join("")}
        </g>
        ${yTicks.map((tick) => `<text class="chart-label" x="${margin.left - 12}" y="${y(tick) + 4}" text-anchor="end">${formatNumber(tick, 0)}</text>`).join("")}
        ${xTicks.map((tick) => `<text class="chart-label" x="${x(tick)}" y="${height - margin.bottom + 24}" text-anchor="middle">${formatNumber(tick, 1)}</text>`).join("")}
        <text class="chart-axis" x="${margin.left + plotWidth / 2}" y="${height - 10}" text-anchor="middle">Time (min)</text>
        <text class="chart-axis" x="18" y="${margin.top + plotHeight / 2}" text-anchor="middle" transform="rotate(-90 18 ${margin.top + plotHeight / 2})">Temperature (C)</text>
        ${paths}
      </svg>`;
    elements.chartLegend.innerHTML = model.blocks.map((block, index) => `<span class="legend-item" style="--series-color:${SERIES_COLORS[index % SERIES_COLORS.length]}">${escapeHtml(block.name)}</span>`).join("");
  }

  function temperatureColor(value, minimum, maximum) {
    const ratio = Math.max(0, Math.min(1, (value - minimum) / Math.max(maximum - minimum, 1)));
    if (ratio < 0.34) return { fill: "#e6eff7", border: "#2b67a0" };
    if (ratio < 0.67) return { fill: "#f3ecd9", border: "#a98234" };
    return { fill: "#f6e7e7", border: "#a94a4a" };
  }

  function renderAssembly(result) {
    const values = model.blocks.map((block) => result?.summary.finalTemperatures?.[block.id] ?? block.initialC);
    const minimum = Math.min(...values);
    const maximum = Math.max(...values);
    elements.assemblyView.innerHTML = `<div class="assembly-stack">${model.blocks.map((block, index) => {
      const color = temperatureColor(values[index], minimum, maximum);
      return `<div class="assembly-block" style="--block-color:${color.fill};--block-border:${color.border}"><strong>${escapeHtml(block.name)}</strong><span>${formatNumber(values[index], 1)} C</span><span>${formatNumber(blockCapacityKJK(block), 3)} kJ/K</span></div>`;
    }).join("")}</div>`;
  }

  function renderFlowChart(result) {
    const nodeIds = [...model.blocks.map((block) => block.id), "ambient"];
    const nodes = [...model.blocks.map((block) => ({ id: block.id, name: block.name })), { id: "ambient", name: "Ambient" }];
    const width = Math.max(700, nodes.length * 155);
    const nodeWidth = 112;
    const xFor = (id) => 26 + Math.max(0, nodeIds.indexOf(id)) * 155;
    const arrows = model.connections.map((connection, index) => {
      const fromX = xFor(connection.fromId) + nodeWidth;
      const toX = xFor(connection.toId);
      const y = 86 + (index % 2) * 68;
      const heatFlow = result?.finalFlows.find((item) => item.id === connection.id)?.heatFlowW;
      return `<path class="network-arrow" d="M${fromX},${y} C${fromX + 34},${y} ${toX - 34},${y} ${toX},${y}"></path>
        <text class="network-flow-label" x="${(fromX + toX) / 2}" y="${y - 10}">${Number.isFinite(heatFlow) ? `${formatNumber(heatFlow, 1)} W` : `R ${formatNumber(connection.resistanceCW, 3)} C/W`}</text>`;
    }).join("");
    elements.flowChart.innerHTML = `<svg class="network-svg" viewBox="0 0 ${width} 240" role="img" aria-label="Thermal network heat-flow chart"><defs><marker id="arrowhead" markerWidth="9" markerHeight="7" refX="8" refY="3.5" orient="auto"><polygon points="0 0, 9 3.5, 0 7" fill="#a98234"></polygon></marker></defs>${arrows}${nodes.map((node) => `<g class="network-node" transform="translate(${xFor(node.id)},38)"><rect width="${nodeWidth}" height="70" rx="4"></rect><text x="${nodeWidth / 2}" y="32">${escapeHtml(node.name)}</text><text x="${nodeWidth / 2}" y="50">${node.id === "ambient" ? formatNumber(latestSettings?.ambientC ?? 25, 1) : formatNumber(result?.summary.finalTemperatures?.[node.id] ?? blockById(node.id)?.initialC ?? 25, 1)} C</text></g>`).join("")}</svg>`;
  }

  function runNetwork(event) {
    event?.preventDefault();
    try {
      elements.runStatus.textContent = "Calculating";
      latestSettings = networkSettings();
      latestResult = window.KhaniThermalSolver.simulateNetwork(model, latestSettings);
      renderNetworkResult(latestResult);
      elements.runStatus.textContent = "Complete";
    } catch (error) {
      elements.runStatus.textContent = error instanceof Error ? error.message : "Simulation failed";
    }
  }

  function renderCases() {
    elements.libraryCount.textContent = `${cases.length} saved ${cases.length === 1 ? "case" : "cases"}`;
    if (!cases.length) {
      elements.caseComparison.innerHTML = `<div class="empty-state">No saved runs in this browser.</div>`;
      elements.libraryList.innerHTML = `<div class="empty-state">No saved analyses in this browser.</div>`;
      return;
    }
    const rows = cases.map((item) => `<tr><td>${escapeHtml(item.name)}</td><td>${escapeHtml(item.savedAt)}</td><td>${formatNumber(item.summary.peakSourceC, 1)} C</td><td>${formatNumber(item.summary.totalHeatW, 1)} W</td><td>${formatNumber(item.summary.totalCapacityKJK, 2)} kJ/K</td><td><button class="row-remove" type="button" data-case-load="${escapeHtml(item.id)}" title="Load case" aria-label="Load ${escapeHtml(item.name)}"><i data-lucide="folder-open"></i></button></td></tr>`).join("");
    elements.caseComparison.innerHTML = `<div class="table-scroll"><table class="engineering-table case-table"><thead><tr><th>Case</th><th>Saved</th><th>Peak Source</th><th>Total Heat</th><th>Capacity</th><th></th></tr></thead><tbody>${rows}</tbody></table></div>`;
    elements.libraryList.innerHTML = cases.map((item) => `<article class="library-item"><div><strong>${escapeHtml(item.name)}</strong><small>${escapeHtml(item.savedAt)} | ${item.model.blocks.length} blocks | ${item.model.connections.length} connections</small></div><span>${formatNumber(item.summary.peakSourceC, 1)} C peak</span><span>${formatNumber(item.summary.totalHeatW, 1)} W</span><button type="button" data-case-delete="${escapeHtml(item.id)}" title="Delete case" aria-label="Delete ${escapeHtml(item.name)}"><i data-lucide="trash-2"></i></button></article>`).join("");
    refreshIcons();
  }

  function saveCase(event) {
    event.preventDefault();
    if (!latestResult) {
      elements.runStatus.textContent = "Run the model before saving";
      return;
    }
    const data = new FormData(elements.saveCaseForm);
    const name = String(data.get("caseName") || "").trim();
    if (!name) return;
    cases.unshift({
      id: uid("case"),
      name,
      savedAt: new Date().toLocaleString("en-US", { dateStyle: "medium", timeStyle: "short" }),
      model: clone(model),
      settings: clone(latestSettings),
      summary: clone(latestResult.summary),
    });
    cases = cases.slice(0, 20);
    saveCases();
    elements.saveCaseForm.reset();
    renderCases();
  }

  function loadCase(id) {
    const item = cases.find((candidate) => candidate.id === id);
    if (!item) return;
    model = clone(item.model);
    Object.entries(item.settings || {}).forEach(([key, value]) => {
      const control = elements.networkForm.elements.namedItem(key);
      if (control) control.value = String(value);
    });
    saveModel();
    renderModel();
    setActiveModule("thermal");
    runNetwork();
  }

  function renderHydraulicComponents(result = null) {
    elements.hydraulicComponents.innerHTML = hydraulicComponents.map((component, index) => {
      const solved = result?.components[index];
      return `<tr><td><input data-hydraulic-component="${index}" data-field="name" aria-label="Hydraulic component name" value="${escapeHtml(component.name)}" /></td><td><input data-hydraulic-component="${index}" data-field="type" aria-label="${escapeHtml(component.name)} type" value="${escapeHtml(component.type)}" /></td><td><input data-hydraulic-component="${index}" data-field="lengthM" type="number" min="0" step="any" aria-label="${escapeHtml(component.name)} length" value="${escapeHtml(component.lengthM)}" /></td><td><input data-hydraulic-component="${index}" data-field="diameterMm" type="number" min="0.01" step="any" aria-label="${escapeHtml(component.name)} diameter" value="${escapeHtml(component.diameterMm)}" /></td><td><input data-hydraulic-component="${index}" data-field="minorK" type="number" min="0" step="any" aria-label="${escapeHtml(component.name)} minor loss" value="${escapeHtml(component.minorK)}" /></td><td><span class="table-value">${solved ? formatNumber(solved.pressureDropKPa, 2) : "--"}</span></td></tr>`;
    }).join("");
    elements.hydraulicLoop.innerHTML = hydraulicComponents.map((component, index) => `<div class="loop-component"><strong>${escapeHtml(component.name)}</strong><span>${result ? `${formatNumber(result.components[index].pressureDropKPa, 2)} kPa` : component.type}</span></div>`).join("");
  }

  function runHydraulics() {
    try {
      const inputs = Object.fromEntries([...document.querySelectorAll("[data-hydraulic-input]")].map((input) => [input.dataset.hydraulicInput, Number(input.value)]));
      const result = window.KhaniThermalSolver.simulateHydraulics({ ...inputs, components: hydraulicComponents });
      renderHydraulicComponents(result);
      elements.hydraulicMetrics.innerHTML = [
        metricCard("Pressure drop", formatNumber(result.summary.totalPressureDropKPa, 2), "kPa"),
        metricCard("Pump power", formatNumber(result.summary.pumpPowerW, 1), "W hydraulic"),
        metricCard("Max velocity", formatNumber(result.summary.maxVelocityMS, 2), "m/s"),
        metricCard("Max Reynolds", formatNumber(result.summary.maxReynolds, 0), "-"),
      ].join("");
    } catch (error) {
      elements.hydraulicMetrics.innerHTML = metricCard("Status", error instanceof Error ? error.message : "Analysis failed", "");
    }
  }

  function loadCfdDemo() {
    elements.cfdCases.innerHTML = `<tr><td>Heated cylinder</td><td>2 STL surfaces</td><td>128,400 cells</td><td>Velocity inlet + pressure outlet</td><td>buoyantSimpleFoam</td><td>Demo ready</td></tr>`;
    elements.cfdViewer.innerHTML = `<div class="cfd-domain" aria-label="Demonstration CFD mesh"></div>`;
    elements.cfdDetails.innerHTML = `<strong>Heated cylinder</strong><dl><dt>Domain</dt><dd>1.2 x 0.6 x 0.6 m</dd><dt>Inlet</dt><dd>2.0 m/s</dd><dt>Wall</dt><dd>350 K</dd><dt>Fluid</dt><dd>Air</dd><dt>Result</dt><dd>Demo geometry</dd></dl>`;
  }

  function renderSingleSeriesChart(target, points, xKey, yKey, labels) {
    const width = 1000;
    const height = 330;
    const margin = { top: 24, right: 24, bottom: 48, left: 64 };
    const xValues = points.map((point) => point[xKey]);
    const yValues = points.map((point) => point[yKey]);
    const xMin = Math.min(...xValues);
    const xMax = Math.max(...xValues);
    const yMin = Math.min(...yValues) * 0.9;
    const yMax = Math.max(...yValues) * 1.1 || 1;
    const x = (value) => margin.left + (value - xMin) / Math.max(xMax - xMin, 1) * (width - margin.left - margin.right);
    const y = (value) => margin.top + (yMax - value) / Math.max(yMax - yMin, 1) * (height - margin.top - margin.bottom);
    const path = points.map((point, index) => `${index ? "L" : "M"}${x(point[xKey]).toFixed(2)},${y(point[yKey]).toFixed(2)}`).join(" ");
    target.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(labels.title)}"><g class="chart-grid">${Array.from({ length: 6 }, (_, index) => { const yy = margin.top + index / 5 * (height - margin.top - margin.bottom); return `<line x1="${margin.left}" y1="${yy}" x2="${width - margin.right}" y2="${yy}"></line>`; }).join("")}</g><path class="chart-series" stroke="#a98234" d="${path}"></path><text class="chart-axis" x="${width / 2}" y="${height - 10}" text-anchor="middle">${escapeHtml(labels.x)}</text><text class="chart-axis" x="18" y="${height / 2}" text-anchor="middle" transform="rotate(-90 18 ${height / 2})">${escapeHtml(labels.y)}</text></svg>`;
  }

  function runCellHeat() {
    try {
      const inputs = Object.fromEntries([...document.querySelectorAll("[data-cell-input]")].map((input) => [input.dataset.cellInput, Number(input.value)]));
      const result = window.KhaniThermalSolver.simulateCellHeat(inputs);
      elements.cellMetrics.innerHTML = [
        metricCard("Per cell", formatNumber(result.summary.perCellW, 2), "W"),
        metricCard("Peak pack", formatNumber(result.summary.peakHeatW, 1), "W"),
        metricCard("Average pack", formatNumber(result.summary.averageHeatW, 1), "W"),
        metricCard("Generated energy", formatNumber(result.summary.energyKJ, 1), "kJ"),
      ].join("");
      renderSingleSeriesChart(elements.cellChart, result.points, "timeMin", "heatW", { title: "Generated battery heat profile", x: "Time (min)", y: "Heat (W)" });
    } catch (error) {
      elements.cellMetrics.innerHTML = metricCard("Status", error instanceof Error ? error.message : "Analysis failed", "");
    }
  }

  function setActiveModule(name, focus = false) {
    const selected = elements.moduleTabs.find((tab) => tab.dataset.moduleTab === name) || elements.moduleTabs[1];
    elements.moduleTabs.forEach((tab) => {
      const active = tab === selected;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", String(active));
      tab.tabIndex = active ? 0 : -1;
    });
    elements.modulePanels.forEach((panel) => {
      const active = panel.dataset.modulePanel === selected.dataset.moduleTab;
      panel.hidden = !active;
      panel.classList.toggle("is-active", active);
    });
    history.replaceState(null, "", `#${selected.dataset.moduleTab}`);
    if (focus) selected.focus();
  }

  function refreshIcons() {
    window.lucide?.createIcons();
  }

  elements.moduleTabs.forEach((tab, index) => {
    tab.addEventListener("click", () => setActiveModule(tab.dataset.moduleTab));
    tab.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      let next = index;
      if (event.key === "ArrowLeft") next = (index - 1 + elements.moduleTabs.length) % elements.moduleTabs.length;
      if (event.key === "ArrowRight") next = (index + 1) % elements.moduleTabs.length;
      if (event.key === "Home") next = 0;
      if (event.key === "End") next = elements.moduleTabs.length - 1;
      setActiveModule(elements.moduleTabs[next].dataset.moduleTab, true);
    });
  });

  document.addEventListener("input", (event) => {
    const control = event.target.closest("[data-model-kind]");
    if (control) updateModelControl(control);
    const hydraulicControl = event.target.closest("[data-hydraulic-component]");
    if (hydraulicControl) {
      const item = hydraulicComponents[Number(hydraulicControl.dataset.hydraulicComponent)];
      if (item) item[hydraulicControl.dataset.field] = ["lengthM", "diameterMm", "minorK"].includes(hydraulicControl.dataset.field) ? Number(hydraulicControl.value) : hydraulicControl.value;
    }
  });

  document.addEventListener("change", (event) => {
    if (event.target.closest("[data-model-kind]")) renderModel();
  });

  document.addEventListener("click", (event) => {
    const addMaterial = event.target.closest("[data-add-material]");
    const addBlock = event.target.closest("[data-add-block]");
    const addConnection = event.target.closest("[data-add-connection]");
    const removeMaterial = event.target.closest("[data-remove-material]");
    const removeBlock = event.target.closest("[data-remove-block]");
    const removeConnection = event.target.closest("[data-remove-connection]");
    const loadCaseButton = event.target.closest("[data-case-load]");
    const deleteCaseButton = event.target.closest("[data-case-delete]");
    if (addMaterial) model.materials.push({ id: uid("material"), name: "New material", type: "solid", k: 1, density: 1000, cp: 1000 });
    else if (addBlock) model.blocks.push({ id: uid("block"), name: "New block", materialId: model.materials[0]?.id || "", initialC: 25, heatW: 0, xMm: 50, yMm: 50, zMm: 10 });
    else if (addConnection) model.connections.push({ id: uid("connection"), fromId: model.blocks[0]?.id || "", toId: model.blocks[1]?.id || "ambient", type: "conduction", resistanceCW: 0.1 });
    else if (removeMaterial) {
      if (model.materials.length <= 1 || model.blocks.some((block) => block.materialId === removeMaterial.dataset.removeMaterial)) return;
      model.materials = model.materials.filter((item) => item.id !== removeMaterial.dataset.removeMaterial);
    } else if (removeBlock) {
      if (model.blocks.length <= 1) return;
      model.blocks = model.blocks.filter((item) => item.id !== removeBlock.dataset.removeBlock);
      model.connections = model.connections.filter((item) => item.fromId !== removeBlock.dataset.removeBlock && item.toId !== removeBlock.dataset.removeBlock);
    } else if (removeConnection) model.connections = model.connections.filter((item) => item.id !== removeConnection.dataset.removeConnection);
    else if (event.target.closest("[data-reset-model]")) {
      model = clone(DEFAULT_MODEL);
      latestResult = null;
    } else if (loadCaseButton) {
      loadCase(loadCaseButton.dataset.caseLoad);
      return;
    } else if (deleteCaseButton) {
      cases = cases.filter((item) => item.id !== deleteCaseButton.dataset.caseDelete);
      saveCases();
      renderCases();
      return;
    } else return;
    saveModel();
    renderModel();
    runNetwork();
  });

  elements.networkForm.addEventListener("submit", runNetwork);
  elements.saveCaseForm.addEventListener("submit", saveCase);
  document.querySelector("[data-run-hydraulics]").addEventListener("click", runHydraulics);
  document.querySelector("[data-load-cfd-demo]").addEventListener("click", loadCfdDemo);
  document.querySelector("[data-run-cellheat]").addEventListener("click", runCellHeat);

  renderModel();
  renderCases();
  renderHydraulicComponents();
  runHydraulics();
  runCellHeat();
  setActiveModule(window.location.hash.replace(/^#/, "") || "thermal");
  runNetwork();
  refreshIcons();
})();
