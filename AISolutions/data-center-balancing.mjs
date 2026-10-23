// Display saved, audited native OpenModelica results. No browser-side solver.
const root = document.getElementById('dc-balancing-explorer');
if (root) {
  const base = '/assets/studies/data-center-cooling/stage-04-balancing-r1';
  const select = root.querySelector('#dc-balance-case');
  const status = root.querySelector('#dc-balance-status');
  const descriptions = {
    baseline: 'Baseline: unchanged Stage 03 settings. Near racks receive slightly more flow and every rack is above the target.',
    speed_only: 'Speed reduction only: the total meets the target, but rack flows remain uneven. The critical far rack is slightly below target.',
    throttle_only: 'Full-speed manual balance: every rack meets the target, while the valves dissipate the excess available head.',
    combined: 'Reduced speed + manual balance: the farthest circuit sets the head requirement; nearer branches absorb their small excess differential pressure.',
    resistance_check: 'Resistance sensitivity: hold the balanced speed and valve settings fixed, then increase only R05’s equipment resistance coefficient by 20%. This is a separate steady case.'
  };
  function render(data) {
    const c = data.cases.find(c => c.id === select.value);
    if (!c) return;
    const set = (id, value) => { root.querySelector('#'+id).textContent = value; };
    set('dc-balance-description', descriptions[c.id]);
    set('dc-balance-speed', c.speed_percent.toFixed(2)+'%');
    set('dc-balance-flow', c.total_flow_Lps.toFixed(3)+' L/s');
    set('dc-balance-power', c.electrical_power_kW.toFixed(3)+' kW');
    set('dc-balance-head', c.head_m.toFixed(3)+' m');
    set('dc-balance-power-label', 'Selected · '+c.electrical_power_kW.toFixed(3)+' kW');
    root.querySelector('#dc-balance-power-bar').style.width = (100-c.power_saving_percent).toFixed(3)+'%';
    set('dc-balance-saving', c.power_saving_percent.toFixed(2)+'% less electrical input than the baseline.');
    const chart = root.querySelector('#dc-balance-chart');
    chart.src = base+'/results/'+c.id+'-flows.svg';
    chart.alt = c.label+' rack flows compared with the Stage 03 baseline and 144.7 L/min target';
    set('dc-balance-valve-caption', c.label+' · actual operating drops, not valve dial positions');
    const rows = c.rack_flow_Lmin.map((flow,i) => {
      const tr = document.createElement('tr');
      const values = ['R-'+String(i+1).padStart(2,'0'),flow.toFixed(3),(flow-144.7).toFixed(3),c.valve_dp_kPa[i].toFixed(3),c.valve_Kv_m3h[i].toFixed(3)];
      values.forEach((v,j) => {const cell=document.createElement(j?'td':'th');if(!j)cell.scope='row';cell.textContent=v;tr.append(cell);});
      return tr;
    });
    root.querySelector('#dc-balance-racks').replaceChildren(...rows);
    status.textContent = c.label+' loaded: '+c.total_flow_Lps.toFixed(3)+' L/s, '+c.electrical_power_kW.toFixed(3)+' kW.';
  }
  select.disabled = true;
  fetch(base+'/results/comparison.json').then(response => {
    if (!response.ok) throw new Error('Data unavailable');
    return response.json();
  }).then(data => {
    if (!Array.isArray(data.cases) || data.cases.length !== 5) throw new Error('Invalid data');
    select.disabled = false;
    select.addEventListener('change', () => render(data));
    render(data);
  }).catch(() => {
    status.textContent = 'Interactive data could not load. The combined case, comparison table and downloadable report remain available.';
  });
}
