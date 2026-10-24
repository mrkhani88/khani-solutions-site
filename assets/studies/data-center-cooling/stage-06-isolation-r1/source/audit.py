"""Audit native algebraic solves against the separate SciPy network; create plots."""
from pathlib import Path
import csv,json,math,re,hashlib,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path(__file__).resolve().parents[1];D=json.loads((B/'model/design.json').read_text());R=B/'runs'/(sys.argv[1] if len(sys.argv)>1 else 'accepted-reduced-r3');O=B/'results';O.mkdir(exist_ok=True)
log=(R/'run.log').read_text()
assert log.count('The simulation finished successfully.')==21
assert not re.search(r'LOG_ASSERT\s*\| error|Error:',log)
assert hashlib.sha256((R/'input_model.mo').read_bytes()).hexdigest()==D['model_sha256']
items=[]
for c in D['cases']:
 p=R/(c['id']+'_res.csv');rows=list(csv.DictReader(p.open()));x={k:float(v) for k,v in rows[-1].items()}
 assert x['time']==1 and all(math.isfinite(float(v)) for row in rows for v in row.values())
 q=np.array([x[f'rackFlowLmin[{i}]'] for i in range(1,11)]);ref=c['independent'];h=np.delete(q,4)
 err=max(abs(q-np.array(ref['supply_flow_Lmin'])));leak=x['leakFlowLmin'];r=x['rack05ReturnLmin'];power=x['pumpElectricalW']/1000
 assert err<.00005,(c['id'],'flow',err)
 assert abs(leak-ref['leak_Lmin'])<.00005
 assert abs(x['leakNodeAbsKPa']-ref['leak_node_abs_kPa'])<.0001,(c['id'],x['leakNodeAbsKPa'],ref['leak_node_abs_kPa'])
 assert abs(power-ref['power_kW'])<.000005
 residual=max(abs(x[k]) for k in ['massResidualKgS','faultMassResidualKgS'])
 iso=max(abs(x[k]) for k in ['leakEquationResidualLmin','supplyIsolationResidualLmin','returnIsolationResidualLmin'])
 pres=max(abs(x[f'pressureResidualPa[{i}]']) for i in range(1,11))
 assert residual<1e-8 and iso<1e-5 and pres<.001
 assert abs(x['makeupFlowLmin']-leak)<1e-6
 assert leak>=-1e-6 and x['leakNodeAbsKPa']>=101.325-1e-6 and min(h)>0
 assert abs(power-x['pumpDPkPa']*x['totalFlowLps']/.675/1000)<1e-9
 assert abs(x['commandedSpeedPercent']-100*c['speed_ratio'])<1e-8
 if c['state']=='supply_only':assert r<0 and abs(q[4])<1e-6
 if c['state'] in ['dual','reset']:assert max(abs(q[4]),abs(r),abs(leak))<1e-6
 if c['state']=='reset':assert min(h)>=144.7-.001
 if c['id']=='reference':assert max(abs(q-144.7))<.001 and abs(power-8.189584)<.00001
 item={k:c[k] for k in ['id','state','label','diameter_mm','supply_opening','return_opening']}
 item.update(speed_percent=x['commandedSpeedPercent'],rack_flow_Lmin=q.tolist(),rack05_supply_Lmin=float(q[4]),rack05_return_Lmin=r,leak_Lmin=leak,makeup_Lmin=x['makeupFlowLmin'],healthy_min_Lmin=float(min(h)),healthy_max_Lmin=float(max(h)),healthy_below_target=int(sum(h<144.699)),electrical_power_kW=power,total_flow_Lps=x['totalFlowLps'],return_total_Lps=x['returnTotalFlowLps'],pump_dp_kPa=x['pumpDPkPa'],leak_node_abs_kPa=x['leakNodeAbsKPa'],audits={'max_independent_flow_error_Lmin':float(err),'mass_residual_kg_s':residual,'constitutive_residual_Lmin':iso,'pressure_residual_Pa':pres,'native_csv_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'csv_rows':len(rows)})
 items.append(item)
data={'stage':'Stage 06 - Rack leak isolation','software':'OpenModelica 1.27.1 / MSL 4.1.0; independent SciPy/Colebrook check','accepted_attempt':R.name,'result_kind':'21 isothermal algebraic steady solutions; exported 0-1 s is not elapsed leak response','native_scope':D['native_scope'],'qualification':'Numerically verified assumed network; no physical leak/actuator/sensor validation or pressure surge qualification','pressure_boundary_scope':D['pressure_boundary_scope'],'leak_sizing_scope':D['leak_sizing_scope'],'timing_scope':D['timing_scope'],'steady_leak_pressure_bound_abs_kPa':D['steady_leak_pressure_bound_abs_kPa'],'source_model_sha256':D['model_sha256'],'target_Lmin':144.7,'known_branch_pipe_inventory_L':math.pi*.04**2/4*4.746992*1000,'assumed_drainable_inventory_L':10,'leak_Cd':.62,'timing_cases':D['timing_cases'],'cases':items}
(O/'comparison.json').write_text(json.dumps(data,indent=2)+'\n')
keys=[k for k in items[0] if k not in ['rack_flow_Lmin','audits']]
with (O/'case-comparison.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore',lineterminator='\n');w.writeheader();w.writerows(items)
with (O/'rack-comparison.csv').open('w',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['case','rack','supply_flow_Lmin','return_flow_Lmin','status'])
 for c in items:
  for i,q in enumerate(c['rack_flow_Lmin']):w.writerow([c['id'],f'R{i+1:02}',q,c['rack05_return_Lmin'] if i==4 else q,'faulted; not useful cooling' if i==4 and c['id']!='reference' else 'healthy'])
with (O/'timing-screen.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=D['timing_cases'][0],lineterminator='\n');w.writeheader();w.writerows(D['timing_cases'])
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'text.color':'#17394d','grid.alpha':.2,'svg.fonttype':'none'})
lookup={c['id']:c for c in items};states=['unisolated','supply_only','return_only','dual','seat_leak','reset'];labels=['Both open','Supply closed','Return closed','Both closed','1% Kv fault','Both + reset']
fig,axs=plt.subplots(1,2,figsize=(13,4.8),constrained_layout=True)
for d,col in [(1,'#126d9b'),(3,'#c2721c'),(6,'#a33a4b')]:axs[0].plot(range(6),[lookup[f'd{d}_{s}']['leak_Lmin'] for s in states],'o-',color=col,label=f'{d} mm hole')
axs[0].set(ylabel='Sustained leak [L/min]',title='Two boundaries are needed to stop header feed',xticks=range(6),xticklabels=labels,ylim=(0,33));axs[0].tick_params(axis='x',rotation=25);axs[0].legend();axs[0].grid(axis='y')
cs=[lookup['reference'],lookup['d3_unisolated'],lookup['d3_dual'],lookup['d3_reset']]
axs[1].bar(range(4),[c['electrical_power_kW'] for c in cs],color=['#71869a','#c2721c','#126d9b','#27785c'])
axs[1].set(ylabel='Estimated pump-bank electrical input [kW]',title='Reset after R05 is removed from service',xticks=range(4),xticklabels=['10-rack reference','3 mm leak','9 racks; fixed speed','9 racks; reset'],ylim=(0,10));axs[1].tick_params(axis='x',rotation=20);axs[1].grid(axis='y');axs[1].set_axisbelow(True)
fig.suptitle('Stage 06 | Assumed pressure-maintained network · steady states, not closure dynamics',fontsize=13)
fig.savefig(O/'isolation-comparison.svg');fig.savefig(O/'isolation-comparison.png',dpi=150);plt.close(fig)
for c in items:
 fig,ax=plt.subplots(figsize=(9,3.8),constrained_layout=True)
 ax.bar(range(1,11),c['rack_flow_Lmin'],color=['#bd6543' if i==4 else '#126d9b' for i in range(10)])
 ax.axhline(144.7,color='#17394d',ls=':',label='Healthy-rack target 144.7 L/min')
 ax.set(title=c['label']+(f' | {c["diameter_mm"]} mm hole' if c['diameter_mm'] else ''),xlabel='Rack (R05 is the faulted zone)',ylabel='Supply flow [L/min]',xticks=range(1,11),ylim=(0,190));ax.grid(axis='y');ax.set_axisbelow(True);ax.legend(fontsize=9)
 fig.savefig(O/(c['id']+'-flows.svg'));plt.close(fig)
for p in O.glob('*.svg'):p.write_text('\n'.join(l.rstrip() for l in p.read_text().splitlines())+'\n')
(B/'verification/audit.json').write_text(json.dumps({'passed':True,'native_cases':21,'model_sha256':D['model_sha256'],'checks':'Finite values, final time, independent flow/pressure/power, branch and system mass, signed backfeed, closed zero feed, baseline and healthy-rack reset.'},indent=2)+'\n')
print('PASS: 21 native pressure-flow cases, independent agreement and conservation.')
print(json.dumps({c['id']:{k:c[k] for k in ['leak_Lmin','healthy_min_Lmin','healthy_max_Lmin','electrical_power_kW']} for c in items if c['id'] in ['d3_unisolated','d3_supply_only','d3_dual','d3_reset']},indent=2))
