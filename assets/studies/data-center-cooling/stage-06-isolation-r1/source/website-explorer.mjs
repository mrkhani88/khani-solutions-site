const base = '/assets/studies/data-center-cooling/stage-06-isolation-r1';
const root=document.querySelector('#dc-isolation-explorer');
if(root){
 const el=id=>document.getElementById('dc-iso-'+id), fmt=(v,n=2)=>(Math.abs(v)<1e-8?0:v).toFixed(n);
 const hole=el('hole'), state=el('state');
 try{
  const response=await fetch(base+'/results/comparison.json');if(!response.ok)throw new Error('Saved case data unavailable');
  const data=await response.json(), cases=new Map(data.cases.map(c=>[c.id,c]));
  function timing(){
   const vals=['detect','logic','close','inventory','accuracy'].map(id=>Number(el(id).value));
   if(vals.some((v,i)=>!Number.isFinite(v)||el(['detect','logic','close','inventory','accuracy'][i]).value===''||!el(['detect','logic','close','inventory','accuracy'][i]).validity.valid)){
    el('exposure').textContent='Enter valid values within the displayed input limits.';el('meters').textContent='';return;
   }
   const [detect,logic,close,inventory,accuracy]=vals,d=Number(hole.value),q=.62*Math.PI*(d/1000)**2/4*Math.sqrt(2*(data.steady_leak_pressure_bound_abs_kPa*1000-101325)/992.2)*60000;
   const seconds=detect+logic+close,spill=q*seconds/60;
   el('exposure').textContent=`${d} mm opening · ${fmt(q)} L/min steady feed bound × ${fmt(seconds,1)} s = ${fmt(spill)} L before sealing; + ${fmt(inventory)} L assumed full-drain inventory = ${fmt(spill+inventory)} L combined exposure ceiling under these assumptions.`;
   const c=cases.get(`d${d}_unisolated`),bound=accuracy/100*(c.total_flow_Lps+c.return_total_Lps)*60;
   el('meters').textContent=`Flow-meter screen (unisolated ${d} mm case): the modeled leak is ${fmt(c.leak_Lmin)} L/min. Two meters each ±${fmt(accuracy)}% of reading allow a worst-case difference error of ±${fmt(bound)} L/min. ${c.leak_Lmin<=bound?'This instantaneous global flow difference cannot distinguish the leak from the assumed accuracy bounds.':'The modeled leak exceeds this assumed accuracy bound; a detection threshold still needs noise, calibration, delay and transient testing.'} This adds error bounds; it is not a statistical confidence interval.`;
  }
  function render(){
   if(state.value.startsWith('partial_'))hole.value='3';
   const id=state.value==='reference'?'reference':`d${hole.value}_${state.value}`,c=cases.get(id);if(!c)throw new Error('Case not found');
   el('context').textContent=`${c.label}${c.diameter_mm?` · ${c.diameter_mm} mm equivalent opening`:''}. Saved native steady solution; the response/closure time is not simulated.`;
   root.dataset.case=id;
   const descriptions={reference:'Commissioned no-leak reference: ten racks at 144.7 L/min. Both isolation elements replace part of the inherited fitting K, so the open-path resistance is preserved.',unisolated:'Both headers remain connected. R05 supply feed splits between the leak and the continuing return flow. Its supply reading does not establish useful cooling.',supply_only:'The supply path is shut, but return-header pressure drives reverse flow through the damaged rack. One-sided isolation has not stopped the leak.',return_only:'The return path is shut, but the supply header still feeds the leak. One-sided isolation has not stopped the leak.',dual:'Two ideal tight valves stop sustained header feed. Trapped rack coolant can still drain; see the separate inventory screen below.',seat_leak:'Both valves retain 1% of fully open hydraulic conductance. This assumed fault still passes fluid at the available pressure. A close command is not proof of a tight seal.',reset:'Both valves are tight shut, R05 is offline, and pump speed is recalculated for the lowest-flow healthy rack to reach target. Other manual settings remain fixed.',partial_50:'Independent steady snapshot at 50% of fully open Kv on both valves, not 50% travel or a measured instant during closure.',partial_10:'Independent steady snapshot at 10% of fully open Kv on both valves. The rack cooling flow falls substantially before the leak feed has stopped.'};
   el('interpretation').textContent=descriptions[state.value];
   el('service').textContent=c.id==='reference'?'Reference service: ten rack design duties.':`R05 must be removed from cooling service. Healthy racks: 9; ${c.healthy_below_target} below the 144.7 L/min target (0.001 L/min numerical tolerance). Nine rack duties correspond to a 900 kW design basis; actual heat and thermal ride-through are not solved.`;
   const kpis=[['Sustained leak',fmt(c.leak_Lmin)+' L/min'],['Reference makeup',fmt(c.makeup_Lmin)+' L/min'],['R05 supply / return',fmt(c.rack05_supply_Lmin)+' / '+fmt(c.rack05_return_Lmin)+' L/min'],['Healthy range',fmt(c.healthy_min_Lmin)+'–'+fmt(c.healthy_max_Lmin)+' L/min'],['Pump speed',fmt(c.speed_percent)+'%'],['Pump-bank electric',fmt(c.electrical_power_kW,3)+' kW']];
   el('kpis').replaceChildren(...kpis.map(([label,value])=>{const box=document.createElement('div'),name=document.createElement('span'),v=document.createElement('strong');name.textContent=label;v.textContent=value;box.append(name,v);return box;}));
   const url=base+'/results/'+id+'-flows.svg';el('chart').src=url;el('chart').alt=c.label+'; rack supply flows; R05 fault supply is not useful cooling';el('chart-link').href=url;
   for(const side of ['supply','return']){const o=c[side+'_opening'];el(side+'-valve').setAttribute('fill',o===0?'#ab4d37':o===1?'#27785c':'#c2721c');el(side+'-label').textContent=side[0].toUpperCase()+side.slice(1)+(o===0?' tight shut':o===1?' open':` ${fmt(o*100,0)}% Kv`);}
   el('supply-flow').textContent='Supply: '+fmt(c.rack05_supply_Lmin)+' L/min';el('return-flow').textContent='Return: '+fmt(c.rack05_return_Lmin)+' L/min';el('leak-label').textContent='Leak: '+fmt(c.leak_Lmin)+' L/min → atmosphere';
   for(const [side,q] of [['supply',c.rack05_supply_Lmin],['return',c.rack05_return_Lmin]]){el(side+'-arrow').setAttribute('d',side==='supply'?(q>=0?'M270 130H310':'M310 130H270'):(q>=0?'M640 130H690':'M690 130H640'));el(side+'-arrow').style.opacity=Math.abs(q)<1e-8?'0':'1';}
   el('leak-path').style.opacity=Math.abs(c.leak_Lmin)<1e-8?'.2':'1';el('leak-path').setAttribute('marker-end',Math.abs(c.leak_Lmin)<1e-8?'':'url(#dc-iso-arrow)');
   el('diagram-desc').textContent=`${c.label}. Supply ${fmt(c.rack05_supply_Lmin)} L/min. Return ${fmt(c.rack05_return_Lmin)} L/min; negative return means backfeed. Leak ${fmt(c.leak_Lmin)} L/min.`;
   timing();
  }
  hole.addEventListener('change',()=>{if(state.value.startsWith('partial_'))state.value='unisolated';render();});state.addEventListener('change',render);
  for(const id of ['detect','logic','close','inventory','accuracy'])el(id).addEventListener('input',timing);
  render();
 }catch(error){el('context').textContent='Interactive data could not load. Use the full saved-case table and downloads below.';console.error(error);}
}
