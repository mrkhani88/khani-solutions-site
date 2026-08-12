const moduleTabs = [...document.querySelectorAll("[data-module-tab]")];
const modulePanels = [...document.querySelectorAll("[data-module-panel]")];
const menu = document.querySelector("[data-menu]");
const menuButton = document.querySelector("[data-menu-button]");
const simulatorForm = document.querySelector("[data-simulator-form]");
const simulatorStatus = document.querySelector("[data-simulator-status]");
const simulatorReset = document.querySelector("[data-simulator-reset]");
const simulatorChart = document.querySelector("[data-simulator-chart]");
const simulatorResultFields = [...document.querySelectorAll("[data-result]")];

function setActiveModule(moduleName, options = {}) {
  const selectedTab = moduleTabs.find((tab) => tab.dataset.moduleTab === moduleName) || moduleTabs[0];
  if (!selectedTab) return;

  moduleTabs.forEach((tab) => {
    const isSelected = tab === selectedTab;
    tab.setAttribute("aria-selected", String(isSelected));
    tab.tabIndex = isSelected ? 0 : -1;
  });

  modulePanels.forEach((panel) => {
    const isSelected = panel.dataset.modulePanel === selectedTab.dataset.moduleTab;
    panel.hidden = !isSelected;
    panel.classList.toggle("is-active", isSelected);
  });

  if (options.updateHash !== false) {
    history.replaceState(null, "", `#${selectedTab.dataset.moduleTab}`);
  }

  if (options.focus) selectedTab.focus();
}

moduleTabs.forEach((tab, index) => {
  tab.addEventListener("click", () => setActiveModule(tab.dataset.moduleTab));
  tab.addEventListener("keydown", (event) => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    let nextIndex = index;
    if (event.key === 'ArrowLeft') nextIndex = (index - 1 + moduleTabs.length) % moduleTabs.length;
    if (event.key === 'ArrowRight') nextIndex = (index + 1) % moduleTabs.length;
    if (event.key === 'Home') nextIndex = 0;
    if (event.key === 'End') nextIndex = moduleTabs.length - 1;
    setActiveModule(moduleTabs[nextIndex].dataset.moduleTab, { focus: true });
  });
});

function closeMenu() {
  menu?.classList.remove("is-open");
  menuButton?.setAttribute("aria-expanded", "false");
}

menuButton?.addEventListener("click", () => {
  const isOpen = menu?.classList.toggle("is-open") ?? false;
  menuButton.setAttribute("aria-expanded", String(isOpen));
});

document.addEventListener("click", (event) => {
  if (!menu?.classList.contains("is-open")) return;
  if (event.target instanceof Element && event.target.closest("[data-header]")) return;
  closeMenu();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeMenu();
});

menu?.addEventListener("click", (event) => {
  if (event.target instanceof Element && event.target.closest("a")) closeMenu();
});

function simulatorInputs() {
  const data = new FormData(simulatorForm);
  return Object.fromEntries([...data.entries()].map(([key, value]) => [key, Number(value)]));
}

function setSimulatorInputs(values) {
  Object.entries(values).forEach(([key, value]) => {
    const input = simulatorForm?.elements.namedItem(key);
    if (input instanceof HTMLInputElement) input.value = String(value);
  });
}

function formatResult(value, digits = 1) {
  return Number(value).toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function chartPath(points, xScale, yScale, valueKey) {
  return points
    .map((point, index) => `${index ? "L" : "M"}${xScale(point.timeMin).toFixed(2)},${yScale(point[valueKey]).toFixed(2)}`)
    .join(" ");
}

function renderThermalChart(result) {
  if (!simulatorChart) return;
  const width = 820;
  const height = 330;
  const margin = { top: 28, right: 26, bottom: 48, left: 62 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const values = result.points.flatMap((point) => [point.sourceC, point.coolantC]);
  const rawMin = Math.min(...values, result.inputs.ambientC);
  const rawMax = Math.max(...values, result.inputs.ambientC);
  const range = Math.max(rawMax - rawMin, 1);
  const yMin = Math.floor((rawMin - range * 0.08) / 5) * 5;
  const yMax = Math.ceil((rawMax + range * 0.08) / 5) * 5;
  const xMax = result.inputs.durationMin;
  const xScale = (value) => margin.left + value / xMax * plotWidth;
  const yScale = (value) => margin.top + (yMax - value) / Math.max(yMax - yMin, 1) * plotHeight;
  const yTicks = Array.from({ length: 5 }, (_, index) => yMin + (yMax - yMin) * index / 4);
  const xTicks = Array.from({ length: 5 }, (_, index) => xMax * index / 4);
  const sourcePath = chartPath(result.points, xScale, yScale, "sourceC");
  const coolantPath = chartPath(result.points, xScale, yScale, "coolantC");

  simulatorChart.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="thermal-chart-title thermal-chart-description">
      <title id="thermal-chart-title">Transient temperature result</title>
      <desc id="thermal-chart-description">Source and coolant temperatures over ${formatResult(xMax, 1)} minutes.</desc>
      <g class="chart-grid">
        ${yTicks.map((tick) => `<line x1="${margin.left}" y1="${yScale(tick)}" x2="${width - margin.right}" y2="${yScale(tick)}"></line>`).join("")}
        ${xTicks.map((tick) => `<line x1="${xScale(tick)}" y1="${margin.top}" x2="${xScale(tick)}" y2="${height - margin.bottom}"></line>`).join("")}
      </g>
      <g class="chart-axis-labels">
        ${yTicks.map((tick) => `<text x="${margin.left - 12}" y="${yScale(tick) + 4}" text-anchor="end">${formatResult(tick, 0)}</text>`).join("")}
        ${xTicks.map((tick) => `<text x="${xScale(tick)}" y="${height - margin.bottom + 24}" text-anchor="middle">${formatResult(tick, 1)}</text>`).join("")}
        <text class="axis-title" x="${margin.left + plotWidth / 2}" y="${height - 8}" text-anchor="middle">Time (min)</text>
        <text class="axis-title" x="15" y="${margin.top + plotHeight / 2}" text-anchor="middle" transform="rotate(-90 15 ${margin.top + plotHeight / 2})">Temperature (&deg;C)</text>
      </g>
      <path class="chart-line chart-line-source" d="${sourcePath}"></path>
      <path class="chart-line chart-line-coolant" d="${coolantPath}"></path>
      <circle class="chart-point chart-point-source" cx="${xScale(xMax)}" cy="${yScale(result.summary.finalSourceC)}" r="5"></circle>
      <circle class="chart-point chart-point-coolant" cx="${xScale(xMax)}" cy="${yScale(result.summary.finalCoolantC)}" r="5"></circle>
    </svg>
  `;
}

function renderThermalResult(result) {
  const digits = {
    peakSourceC: 1,
    finalCoolantC: 1,
    coolantRiseC: 2,
    loopCapacityKJK: 2,
  };
  simulatorResultFields.forEach((field) => {
    const key = field.dataset.result;
    field.textContent = formatResult(result.summary[key], digits[key] ?? 1);
  });
  renderThermalChart(result);
}

function runThermalSimulation(event) {
  event?.preventDefault();
  try {
    simulatorStatus.textContent = "Calculating";
    const result = window.KhaniThermalSolver.simulate(simulatorInputs());
    renderThermalResult(result);
    simulatorStatus.textContent = "Complete";
  } catch (error) {
    simulatorStatus.textContent = error instanceof Error ? error.message : "Simulation could not run";
  }
}

simulatorForm?.addEventListener("submit", runThermalSimulation);
simulatorReset?.addEventListener("click", () => {
  setSimulatorInputs(window.KhaniThermalSolver.DEFAULT_INPUTS);
  runThermalSimulation();
});

setActiveModule(window.location.hash.replace(/^#/, ""), { updateHash: false });
window.lucide?.createIcons();
window.addEventListener("load", () => window.lucide?.createIcons());
window.addEventListener("pageshow", () => runThermalSimulation());
