"""Verify all native cases; generate public comparison data and scientific figures."""
from pathlib import Path
import csv,json,hashlib,math,re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from design import B,rho,g,solve
D=json.loads((B/'model/design.json').read_text()); R=B/'runs/r5';O=B/'results'
log=(R/'run.log').read_text()
compiler_log=(B/'runs/r1/run.log').read_text()
assert log.count('The simulation finished successfully.')==5,log[-4000:]
assert not re.search(r'INCONSISTENT due to specified unit information|LOG_ASSERT\s*\| error|LOG_INIT\s*\| error|Error:',log)
assert hashlib.sha256((R/'input_model.mo').read_bytes()).hexdigest()==D['model_sha256']
base=json.loads((B/'inputs/accepted-baseline-summary.json').read_text())
cases=[];allrows=[]
for design in D['cases']:
 k=design['id']; path=R/(k+'_res.csv');rows=list(csv.DictReader(path.open()));x={n:float(v) for n,v in rows[-1].items()}
 assert abs(x['time']-1)<1e-12 and all(math.isfinite(float(v)) for r in rows for v in r.values())
 flows=np.array([x[f'rackFlowLmin[{i}]'] for i in range(1,11)])
 mass=max([abs(x['systemMassResidual']),abs(x['referenceMakeupKgS'])]+[abs(x[f'branchMassResidual[{i}]']) for i in range(1,11)])
 pressure=max(abs(x[f'loopResidualPa[{i}]']) for i in range(1,11));energy=abs(x['pumpEnergyResidualW'])
 assert mass<1e-7 and pressure<1e-4 and energy<1e-4,(k,mass,pressure,energy)
 assert abs(sum(flows)/60-x['totalFlowLps'])<1e-8
 assert abs(x['pumpElectricalW']-x['pumpDPkPa']*x['totalFlowLps']/.675)<1e-5
 independent=np.array(design['independent_flow_Lmin']);diff=max(abs(independent/flows-1))*100
 assert diff<.001,(k,diff)
 if k=='baseline':
  assert max(abs(flows-base['rack_flow_Lmin']))<1e-6
  assert abs(x['pumpElectricalW']-base['electrical_power_W'])<1e-4
 if k in ['combined','throttle_only']:assert max(abs(flows-144.7))<.001,(k,flows)
 if k=='speed_only':assert abs(x['totalFlowLps']-144.7/6)<.001
 valves=np.array([x[f'rack{i}.balancingValve.dp']/1000 for i in range(1,11)])
 kv=(flows*.06)/np.sqrt(valves/100/(rho/1000))
 item={'id':k,'label':design['label'],'speed_percent':design['speed_ratio']*100,'total_flow_Lps':x['totalFlowLps'],'head_m':x['pumpHeadM'],'dp_kPa':x['pumpDPkPa'],'hydraulic_power_kW':x['pumpHydraulicW']/1000,'electrical_power_kW':x['pumpElectricalW']/1000,'rack_flow_Lmin':flows.tolist(),'flow_spread_percent':float(np.ptp(flows)/np.mean(flows)*100),'max_target_error_Lmin':float(max(abs(flows-144.7))),'valve_dp_kPa':valves.tolist(),'valve_Kv_m3h':kv.tolist(),'valve_loss_kW':float(sum(valves*flows/60)/1000),'audits':{'mass_residual_kg_s':mass,'loop_residual_Pa':pressure,'pump_work_energy_residual_W':energy,'independent_max_flow_difference_percent':float(diff),'csv_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'csv_rows':len(rows)}}
 item['power_saving_percent']=100*(1-item['electrical_power_kW']/(base['electrical_power_W']/1000))
 cases.append(item)
 for i in range(10):allrows.append([k,f'R-{i+1:02d}',flows[i],144.7,valves[i],kv[i],independent[i],design['valve_nominal_Pa'][i],design['rack_nominal_Pa'][i]])
assert abs(cases[3]['valve_dp_kPa'][-1]-15)<.001
summary={'stage':'Stage 04 - Pump speed and static rack balancing','result_kind':'Steady algebraic OpenModelica cases, 0-1 s export is not a transient','qualification':'Numerically verified assumed network; no hardware selection or physical validation','software':'OpenModelica 1.27.1 / MSL 4.1.0','accepted_attempt':'r5','initialization':'Direct nonlinear initialization (-noHomotopyOnFirstTry); compiled r1 binaries from the identical SHA256-verified model. Initial homotopy failures and solver trials are retained in prior-attempt logs.','target_rack_Lmin':144.7,'target_total_Lps':144.7/6,'target_rounding_note':'144.7 is the requested rounded target; 100 kW / (rho cp 10 K) gives 144.70370686 L/min. Difference 0.0026%.','critical_valve_floor_kPa':15,'optimization_scope':D['optimization_scope'],'efficiency_assumptions':{'hydraulic':.75,'motor':.90,'additional_VFD_losses':'not modeled'},'source_model_sha256':D['model_sha256'],'parent_model_sha256':D['parent_model_sha256'],'warnings_retained':sorted(set(re.findall(r'Warning: ([^\n]+)',compiler_log))),'cases':cases}
(O/'comparison.json').write_text(json.dumps(summary,indent=2)+'\n')
with (O/'rack-comparison.csv').open('w',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['case','rack','flow_Lmin','target_Lmin','valve_dp_kPa','equivalent_Kv_m3h','independent_Colebrook_Lmin','valve_reference_dp_Pa','equipment_reference_dp_Pa']);w.writerows(allrows)
with (O/'case-comparison.csv').open('w',newline='') as f:
 keys=['id','speed_percent','total_flow_Lps','head_m','dp_kPa','electrical_power_kW','power_saving_percent','flow_spread_percent','valve_loss_kW']
 w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore',lineterminator='\n');w.writeheader();w.writerows(cases)
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','text.color':'#17394d','axes.labelcolor':'#17394d','grid.alpha':.22,'svg.fonttype':'none'})
colors=['#718797','#b26b1c','#9a4595','#087f74','#b84035'];nums=np.arange(1,11)
fig,axs=plt.subplots(2,2,figsize=(15,10),constrained_layout=True)
for c,col in zip(cases[:4],colors):axs[0,0].plot(nums,c['rack_flow_Lmin'],'o-',label=c['label'],color=col,ms=4)
axs[0,0].axhline(144.7,color='#17394d',ls='--',lw=1,label='Target 144.7')
axs[0,0].set(title='Total flow control alone leaves an uneven rack split',xlabel='Rack (near CDU → far end)',ylabel='Flow [L/min]',xticks=nums);axs[0,0].legend(fontsize=8)
labels=['Baseline','Speed only','Throttle only','Speed + balance']
axs[0,1].bar(labels,[c['electrical_power_kW'] for c in cases[:4]],color=colors[:4])
for i,c in enumerate(cases[:4]):axs[0,1].text(i,c['electrical_power_kW']+.10,f"{c['electrical_power_kW']:.3f}",ha='center')
axs[0,1].set(title='Both duty pumps: estimated electric input',ylabel='Power [kW]',ylim=(0,11))
for c,col in zip([cases[2],cases[3]],[colors[2],colors[3]]):axs[1,0].plot(nums,c['valve_dp_kPa'],'o-',label=c['label'],color=col)
axs[1,0].set(title='Lower speed avoids unnecessary valve dissipation',xlabel='Rack',ylabel='Actual valve pressure drop [kPa]',xticks=nums);axs[1,0].legend(fontsize=8)
for c,col in zip([cases[3],cases[4]],[colors[3],colors[4]]):axs[1,1].plot(nums,c['rack_flow_Lmin'],'o-',label=c['label'],color=col)
axs[1,1].axhline(144.7,color='#17394d',ls='--',lw=1);axs[1,1].set(title='Static balance is specific to the commissioned resistance',xlabel='Rack',ylabel='Flow [L/min]',xticks=nums);axs[1,1].legend(fontsize=8)
for ax in axs.flat:ax.grid(axis='y');ax.set_axisbelow(True)
fig.suptitle('Data-center hydraulics | Pump speed and rack balancing\nSame routed network · two duty pumps · assumed curves · fixed efficiencies',fontsize=17)
fig.savefig(O/'balancing-comparison.png',dpi=160);fig.savefig(O/'balancing-comparison.svg');plt.close(fig)
for c,col in zip(cases,colors):
 fig,ax=plt.subplots(figsize=(10,4.7),constrained_layout=True)
 ax.plot(nums,cases[0]['rack_flow_Lmin'],'o--',color=colors[0],label='Stage 03 baseline',ms=4)
 ax.plot(nums,c['rack_flow_Lmin'],'o-',color=col,label=c['label'],lw=2,ms=5)
 ax.axhline(144.7,color='#17394d',ls=':',label='Target 144.7 L/min')
 ax.set(xlabel='Rack (near CDU → far end)',ylabel='Flow [L/min]',xticks=nums,ylim=(132,158),title=c['label']);ax.grid(axis='y');ax.legend(fontsize=9,loc='lower left')
 fig.savefig(O/(c['id']+'-flows.svg'));plt.close(fig)
for path in O.glob('*.svg'):path.write_text('\n'.join(l.rstrip() for l in path.read_text().splitlines())+'\n')
print(json.dumps([{k:c[k] for k in ['id','speed_percent','total_flow_Lps','head_m','electrical_power_kW','power_saving_percent','max_target_error_Lmin']} for c in cases],indent=2))
print('PASS: five native cases, baseline reproduction, each balanced rack within 0.001 L/min, conservation, finite values and independent Colebrook checks.')
