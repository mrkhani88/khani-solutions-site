"""Audit native solves, verify inherited cases, publish comparison rows and plots."""
from pathlib import Path
import csv,json,math,re,hashlib,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from design import B,DP_MIN,DP_MAX,qt,rho
D=json.loads((B/'model/design.json').read_text());R=B/'runs'/(sys.argv[1] if len(sys.argv)>1 else 'accepted-r1');O=B/'results';O.mkdir(exist_ok=True)
log=(R/'run.log').read_text();compiler=(B/'runs/build-r1'/(sys.argv[2] if len(sys.argv)>2 else 'build.log')).read_text()
assert log.count('The simulation finished successfully.')==24
assert not re.search(r'LOG_ASSERT\s*\| error|LOG_INIT\s*\| error|INCONSISTENT due to specified unit|Error:',log+compiler)
assert hashlib.sha256((R/'input_model.mo').read_bytes()).hexdigest()==D['model_sha256']
parent=json.loads((B/'inputs/stage04-comparison.json').read_text());accepted={c['id']:c for c in parent['cases']}
items=[];rackrows=[]
for c in D['cases']:
 p=R/(c['id']+'_res.csv');rows=list(csv.DictReader(p.open()));x={k:float(v) for k,v in rows[-1].items()}
 assert abs(x['time']-1)<1e-12 and all(math.isfinite(float(v)) for row in rows for v in row.values())
 assert abs(x['commandedSpeedPercent']-c['speed_ratio']*100)<1e-9
 assert abs(x['rack5.rackMap.dp']-c['rack05_nominal_Pa']*(x['rackFlowLmin[5]']/(1e6/4179/10/rho/10*60000))**2)<.1
 assert abs(x['filterMap.dp']-c['filter_nominal_Pa']*(x['totalFlowLps']/(1e6/4179/10/rho*1000))**2)<.1
 q=np.array([x[f'rackFlowLmin[{i}]'] for i in range(1,11)]);vdp=np.array([x[f'rack{i}.balancingValve.dp'] for i in range(1,11)])
 mass=max([abs(x['systemMassResidual']),abs(x['referenceMakeupKgS'])]+[abs(x[f'branchMassResidual[{i}]']) for i in range(1,11)])
 pressure=max(abs(x[f'loopResidualPa[{i}]']) for i in range(1,11));energy=abs(x['pumpEnergyResidualW'])
 assert mass<1e-7 and pressure<1e-4 and energy<1e-4,(c['id'],mass,pressure,energy)
 assert abs(sum(q)/60-x['totalFlowLps'])<1e-8
 assert abs(x['pumpElectricalW']-x['pumpDPkPa']*x['totalFlowLps']/.675)<1e-4
 independent=np.array(c['independent_flow_Lmin']);delta=max(abs(q/independent-1))*100
 assert delta<.002,(c['id'],delta,q,independent)
 if c['id'] in ['reference_fixed_manual','rack20_fixed_manual']:
  prior=accepted['combined' if c['scenario']=='reference' else 'resistance_check']
  assert max(abs(q-np.array(prior['rack_flow_Lmin'])))<1e-6
  assert abs(x['pumpElectricalW']/1000-prior['electrical_power_kW'])<1e-7
 assert np.all(q>0) and np.all(vdp>0) and c['speed_ratio']<=1
 if c['mode']=='picv':
  assert max(vdp)<DP_MAX,'Case exceeds the generic upper operating envelope'
  regulated=(vdp>=DP_MIN-.1)
  assert max(abs(q-144.7*np.minimum(1.,np.sqrt(vdp/DP_MIN))))<1e-4
  assert max(q)<=144.70001
 else:regulated=np.zeros(10,dtype=bool)
 item={k:c[k] for k in ['id','scenario','scenario_label','policy','mode','speed_limited','rack05_nominal_Pa','filter_nominal_Pa']}
 item.update(speed_percent=x['commandedSpeedPercent'],requested_speed_percent=c['requested_speed_ratio']*100,total_flow_Lps=x['totalFlowLps'],head_m=x['pumpHeadM'],pump_dp_kPa=x['pumpDPkPa'],electrical_power_kW=x['pumpElectricalW']/1000,hydraulic_power_kW=x['pumpHydraulicW']/1000,rack_flow_Lmin=q.tolist(),rack05_flow_Lmin=float(q[4]),minimum_rack_flow_Lmin=float(min(q)),maximum_rack_flow_Lmin=float(max(q)),flow_spread_percent=float(np.ptp(q)/q.mean()*100),rack_meets_target=(abs(q-144.7)<.001).tolist(),racks_below_target=int(sum(q<144.7-.001)),valve_dp_kPa=(vdp/1000).tolist(),regulating=regulated.tolist(),regulating_count=int(sum(regulated)) if c['mode']=='picv' else None,minimum_picv_dp_margin_kPa=float((min(vdp)-DP_MIN)/1000) if c['mode']=='picv' else None,filter_actual_dp_kPa=x['filterMap.dp']/1000,nominal_duty_power_difference_from_stage04_kW=x['pumpElectricalW']/1000-accepted['combined']['electrical_power_kW'],audits={'max_mass_residual_kg_s':mass,'max_loop_pressure_residual_Pa':pressure,'pump_work_energy_residual_W':energy,'independent_max_flow_difference_percent':float(delta),'native_csv_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'csv_rows':len(rows)})
 items.append(item)
 for i in range(10):rackrows.append([c['id'],c['scenario'],c['policy'],c['mode'],f'R-{i+1:02d}',q[i],144.7,vdp[i]/1000,bool(regulated[i]) if c['mode']=='picv' else 'not applicable',independent[i]])
summary={'stage':'Stage 05 - Manual balancing versus pressure-independent valves','software':'OpenModelica 1.27.1 / MSL 4.1.0','result_kind':'24 steady network solutions; 0-1 s export is not a physical transient or control response','qualification':'Generic ideal PICV envelope and assumed pump/device maps; numerical verification only, not vendor prediction or physical validation','target_Lmin':144.7,'picv_minimum_dp_kPa':35,'picv_design_margin_kPa':5,'picv_upper_envelope_kPa':414,'picv_law':'q/q_target=min(1,sqrt(max(dp,0)/35000 Pa)); adiabatic, zero reverse flow','picv_limitations':['Ideal flow-limiting plateau has no manufacturing/control error','No actuator, diaphragm, sensor or controller dynamics','35 kPa minimum and 5 kPa reserve are study choices, not a fitted catalog selection','414 kPa upper-envelope guard; no case exceeds it','Real catalog +/-5% setpoint accuracy can exceed the small-change flow differences here'],'pump_policy':D['policy_note'],'speed_limit_percent':100,'hydraulic_efficiency':.75,'motor_efficiency':.9,'extra_VFD_losses':'not modeled','filter_reference_note':'20 kPa was already an assumed dirty-filter allowance in Stage 03; this study increases that coefficient to 25 or 40 kPa at the same nominal total flow. Not measured clean/dirty curves.','source_model_sha256':D['model_sha256'],'parent_model_sha256':D['parent_model_sha256'],'accepted_attempt':R.name,'warnings_retained':sorted(set(re.findall(r'Warning: ([^\n]+)',compiler))),'cases':items}
(O/'comparison.json').write_text(json.dumps(summary,indent=2)+'\n')
with (O/'rack-comparison.csv').open('w',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['case','scenario','pump_policy','valve_type','rack','flow_Lmin','target_Lmin','valve_dp_kPa','PICV_regulating','independent_flow_Lmin']);w.writerows(rackrows)
keys=['id','scenario','policy','mode','speed_percent','requested_speed_percent','speed_limited','total_flow_Lps','head_m','electrical_power_kW','minimum_rack_flow_Lmin','maximum_rack_flow_Lmin','rack05_flow_Lmin','racks_below_target','regulating_count','filter_actual_dp_kPa']
with (O/'case-comparison.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore',lineterminator='\n');w.writeheader();w.writerows(items)
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','text.color':'#17394d','axes.labelcolor':'#17394d','grid.alpha':.22,'svg.fonttype':'none'})
colors={'manual':'#b26b1c','picv':'#126d9b'};num=np.arange(1,11)
scenario_list=list(dict.fromkeys(c['scenario'] for c in items))
lookup={c['id']:c for c in items}
for scenario in scenario_list:
 for policy in ['fixed','reset']:
  pair=[lookup[f'{scenario}_{policy}_{mode}'] for mode in ['manual','picv']]
  fig,ax=plt.subplots(figsize=(10,4.6),constrained_layout=True)
  for c in pair:ax.plot(num,c['rack_flow_Lmin'],'o-' if c['mode']=='manual' else 's--',color=colors[c['mode']],label='Manual' if c['mode']=='manual' else 'Generic PICV',ms=5)
  ax.axhline(144.7,color='#17394d',ls=':',label='Target 144.7 L/min')
  ax.set(xlabel='Rack (near CDU → far end)',ylabel='Flow [L/min]',xticks=num,ylim=(128,158),title=pair[0]['scenario_label']+' | '+('Commissioned speeds held' if policy=='fixed' else 'Steady speed reset, capped at 100%'))
  ax.grid(axis='y');ax.legend(loc='lower left',fontsize=9);fig.savefig(O/f'{scenario}-{policy}-flows.svg');plt.close(fig)
fig,axs=plt.subplots(2,2,figsize=(15,10),constrained_layout=True)
for policy,ax in zip(['fixed','reset'],axs[0]):
 for mode in ['manual','picv']:
  vals=[lookup[f'{sid}_{policy}_{mode}']['minimum_rack_flow_Lmin'] for sid in scenario_list]
  ax.plot(np.arange(len(vals))+(-.055 if mode=='manual' else .055),vals,'o' if mode=='manual' else 's',label='Manual' if mode=='manual' else 'Generic PICV',color=colors[mode])
 ax.axhline(144.7,color='#17394d',ls=':',label='Target')
 ax.set(title='Minimum rack flow | '+('fixed commissioned speeds' if policy=='fixed' else 'speed reset, ≤100%'),ylabel='Minimum rack flow [L/min]',ylim=(128,146),xticks=range(6),xticklabels=['Reference','R05 +5%','R05 +20%','Filter +25%','Filter ×2','Both severe']);ax.legend(fontsize=9);ax.grid(axis='y')
for policy,ax in zip(['fixed','reset'],axs[1]):
 xs=np.arange(6)
 for mode,off in [('manual',-.18),('picv',.18)]:
  vals=[lookup[f'{sid}_{policy}_{mode}']['electrical_power_kW'] for sid in scenario_list]
  ax.bar(xs+off,vals,width=.36,color=colors[mode],label='Manual' if mode=='manual' else 'Generic PICV')
 ax.set(title='Pump-bank electrical input | '+('fixed speeds' if policy=='fixed' else 'speed reset, ≤100%'),ylabel='Estimated electric input [kW]',xticks=xs,xticklabels=['Reference','R05 +5%','R05 +20%','Filter +25%','Filter ×2','Both severe'],ylim=(0,11));ax.legend(fontsize=9);ax.grid(axis='y');ax.set_axisbelow(True)
fig.suptitle('Data-center hydraulics | Manual balance versus pressure-limited PICVs\nSame piping and pump curve · 144.7 L/min target · ideal static regulation · assumed efficiencies',fontsize=16)
fig.savefig(O/'valve-comparison.png',dpi=160);fig.savefig(O/'valve-comparison.svg');plt.close(fig)
# Local characteristic illustration, shown with its explicit pressure envelope.
dps=np.linspace(0,80,200);fig,ax=plt.subplots(figsize=(9,4.5),constrained_layout=True)
ax.plot(dps,144.7*np.minimum(1,np.sqrt(dps/35)),color=colors['picv'],label='Generic ideal PICV')
ax.plot(dps,144.7*np.sqrt(dps/15),color=colors['manual'],label='Manual example, 15 kPa at target')
ax.axvline(35,color='#17394d',ls=':',label='PICV regulation starts at 35 kPa');ax.axhline(144.7,color='#17394d',ls='--',lw=1)
ax.set(xlabel='Valve differential pressure [kPa]',ylabel='Flow [L/min]',ylim=(0,240),title='Illustrative local valve laws | not measured manufacturer curves');ax.legend(fontsize=9);ax.grid();fig.savefig(O/'valve-characteristic.svg');plt.close(fig)
for path in O.glob('*.svg'):path.write_text('\n'.join(l.rstrip() for l in path.read_text().splitlines())+'\n')
print('PASS: 24 native steady cases; all runtime overrides verified; baseline and +20% case reproduced; finite values, conservation, PICV envelope and independent Colebrook agreement.')
for sid in scenario_list:
 for pol in ['fixed','reset']:
  print(sid,pol,[(mode,round(lookup[f'{sid}_{pol}_{mode}']['minimum_rack_flow_Lmin'],3),round(lookup[f'{sid}_{pol}_{mode}']['electrical_power_kW'],3)) for mode in ['manual','picv']])
