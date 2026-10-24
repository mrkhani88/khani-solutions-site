// Saved, audited native Modelica cases; selections do not run a browser solver.
const root = document.getElementById('dc-valve-explorer');
if (root) {
  const base = '.';
  const scenario = root.querySelector('#dc-valve-scenario');
  const policy = root.querySelector('#dc-valve-policy');
  const status = root.querySelector('#dc-valve-status');
  const set = (id, value) => {root.querySelector('#'+id).textContent=value;};
  const fmt = (v,n=3) => Number(v).toFixed(n);
  const scenarios = {
    reference:'Reference equipment map: 100 kPa per rack. Reference filter map: 20 kPa.',
    rack5:'Only R05’s equipment-map coefficient rises from 100 to 105 kPa; filter remains 20 kPa.',
    rack20:'Only R05’s equipment-map coefficient rises from 100 to 120 kPa; filter remains 20 kPa.',
    filter25:'All racks retain their reference equipment maps; the filter coefficient rises from 20 to 25 kPa.',
    filter100:'All racks retain their reference equipment maps; the filter coefficient rises from 20 to 40 kPa.',
    both:'R05’s equipment-map coefficient rises from 100 to 120 kPa and the filter coefficient rises from 20 to 40 kPa.'
  };
  function row(values) {
    const tr=document.createElement('tr');
    values.forEach((v,i)=>{const cell=document.createElement(i?'td':'th');if(!i)cell.scope='row';cell.textContent=v;tr.append(cell);});
    return tr;
  }
  function render(data) {
    const get=mode=>data.cases.find(c=>c.id===`${scenario.value}_${policy.value}_${mode}`);
    const m=get('manual'),p=get('picv');if(!m||!p)return;
    const policyText=policy.value==='fixed'?'Each technology retains its own commissioned pump speed.':'Final steady speeds are recalculated, with a 100% cap. Manual presets stay fixed; PICV reset seeks a 5 kPa reserve above its minimum.';
    set('dc-valve-context',scenarios[scenario.value]+' Values refer to nominal flow; actual device losses vary with flow squared. '+policyText);
    set('dc-valve-case-caption',m.scenario_label+' / '+(policy.value==='fixed'?'commissioned speeds held':'steady speed reset, ≤100%')+' · both duty pumps');
    const chart=root.querySelector('#dc-valve-chart');chart.src=`${base}/results/${scenario.value}-${policy.value}-flows.svg`;root.querySelector('#dc-valve-chart-link').href=chart.src;chart.alt=m.scenario_label+' rack flows: manual versus generic PICV, '+policyText;
    root.querySelector('#dc-valve-metrics').replaceChildren(...[m,p].map(c=>row([c.mode==='manual'?'Manual':'Generic PICV',fmt(c.speed_percent,2)+'%',fmt(c.minimum_rack_flow_Lmin)+'–'+fmt(c.maximum_rack_flow_Lmin),fmt(c.rack05_flow_Lmin),fmt(c.total_flow_Lps),fmt(c.electrical_power_kW),String(c.racks_below_target)+' / 10'])));
    for(const c of [m,p]) {
      set(`dc-valve-${c.mode}-power`,(c.mode==='manual'?'Manual':'Generic PICV')+' · '+fmt(c.electrical_power_kW)+' kW');
      root.querySelector(`#dc-valve-${c.mode}-bar`).style.width=fmt(c.electrical_power_kW/12*100)+'%';
    }
    const dp=Math.min(...p.valve_dp_kPa),margin=dp-35;
    let note=`PICV regulation: ${p.regulating_count}/10 racks. Minimum valve Δp ${fmt(dp,2)} kPa (${fmt(Math.abs(margin),2)} kPa ${margin<0?'below':'above'} the 35 kPa threshold). `;
    if(policy.value==='reset')note+=`Calculated speeds before the cap: manual ${fmt(m.requested_speed_percent,2)}%, PICV ${fmt(p.requested_speed_percent,2)}% (PICV includes the 5 kPa reserve). `;
    note+=`Actual filter Δp: manual ${fmt(m.filter_actual_dp_kPa,2)} kPa; PICV ${fmt(p.filter_actual_dp_kPa,2)} kPa.`;
    set('dc-valve-pressure-note',note);
    root.querySelector('#dc-valve-racks').replaceChildren(...m.rack_flow_Lmin.map((q,i)=>row(['R-'+String(i+1).padStart(2,'0'),fmt(q),fmt(p.rack_flow_Lmin[i]),fmt(p.valve_dp_kPa[i]),p.regulating[i]?'Regulating':'Below minimum Δp'])));
    status.textContent=`Loaded ${m.scenario_label}; manual ${fmt(m.electrical_power_kW)} kW, PICV ${fmt(p.electrical_power_kW)} kW. ${m.racks_below_target} manual and ${p.racks_below_target} PICV racks below target.`;
  }
  scenario.disabled=true;policy.disabled=true;
  fetch(base+'/results/comparison.json').then(r=>{if(!r.ok)throw new Error();return r.json();}).then(data=>{
    if(data.cases?.length!==24)throw new Error();
    scenario.disabled=false;policy.disabled=false;
    scenario.addEventListener('change',()=>render(data));policy.addEventListener('change',()=>render(data));render(data);
  }).catch(()=>{status.textContent='Interactive data could not load. The default case, complete table and downloadable report remain available.';});
}
