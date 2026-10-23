"""Audit native OpenModelica outputs and independently solve the same assumptions.

Independent calculation uses exact Colebrook friction instead of the MSL pipe
implementation. This is numerical verification, not experimental validation.
"""
from pathlib import Path
import csv,json,math,hashlib,re,sys
import numpy as np
from scipy.optimize import root,brentq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path(__file__).resolve().parents[1]
RUN=B/'runs'/ (sys.argv[1] if len(sys.argv)>1 else 'r5')
OUT=B/'results';OUT.mkdir(exist_ok=True)
A=json.loads((B/'model/assumptions.json').read_text())
rho=A['rho_kg_m3'];mu=A['mu_Pa_s'];g=9.80665
qnom=1e6/(A['cp_J_kgK']*10)/rho;qrnom=qnom/10
def load(name):
 p=RUN/(name+'_res.csv');rows=list(csv.DictReader(p.open()))
 assert rows and abs(float(rows[-1]['time'])-1)<1e-12,p
 assert all(math.isfinite(float(v)) for row in rows for v in row.values()),p
 return {k:float(v) for k,v in rows[-1].items()},len(rows)
data={};rowcounts={}
for name in ['baseline','flat','raised']:data[name],rowcounts[name]=load(name)
x=data['baseline']
v=lambda k:x[k]
flows=np.array([v(f'rackFlowLmin[{i}]') for i in range(1,11)])
press_s=np.array([v(f'supplyPressureAbsKPa[{i}]') for i in range(1,11)])
press_r=np.array([v(f'returnPressureAbsKPa[{i}]') for i in range(1,11)])
mass=max([abs(v('systemMassResidual')),abs(v('referenceMakeupKgS'))]+[abs(v(f'branchMassResidual[{i}]')) for i in range(1,11)])
loop=max(abs(v(f'loopResidualPa[{i}]')) for i in range(1,11))
energy=abs(v('pumpEnergyResidualW'))
assert mass<1e-7 and loop<1e-4 and energy<1e-4,(mass,loop,energy)
assert np.all(flows>0)
assert abs(v('totalFlowLps')-flows.sum()/60)<1e-8

def friction(reynolds,d):
 if reynolds<1e-8:return 0.0
 if reynolds<2300:return 64/reynolds
 rr=A['roughness_m']/d
 return brentq(lambda f:1/math.sqrt(f)+2*math.log10(rr/3.7+2.51/(reynolds*math.sqrt(f))),.005,.12,xtol=1e-13)
def dp_pipe(q,l,d,k=0):
 area=math.pi*d*d/4;vel=q/area;rey=rho*abs(vel)*d/mu
 return (friction(rey,d)*l/d+k)*rho*vel*abs(vel)/2
routes_path=B/'inputs/pipe-route-schedule.csv'
if not routes_path.exists():routes_path=B.parent/'stage-02-design-r1/cad/pipe-route-schedule.csv'
if not routes_path.exists():routes_path=B.parent/'Stage-02-Design-R1/cad/pipe-route-schedule.csv'
routes={r['tag']:r for r in csv.DictReader(routes_path.open())}
length=lambda tag:float(routes[tag]['centerline_m'])
common125=sum(length(t) for t in ['CDU_suction','CDU_discharge','HX_to_suction','CDU_supply_riser','CDU_return_to_HX'])
leg65=length('P-101A_in')+length('P-101A_out')
branch_length=length('L-201S')+length('L-201R')
def pump_dp(q):
 z=q/qnom;return rho*g*(37-.5*z-9*z*z)
def residual(q):
 total=q.sum();suffix=np.cumsum(q[::-1])[::-1]
 common=dp_pipe(total,common125,.125,4)+dp_pipe(total/2,leg65,.065,2)+65000*(total/qnom)**2
 header=np.array([dp_pipe(qi,li,.125,.2) for qi,li in zip(suffix,A['active_header_segments_m'])])
 branch=np.array([dp_pipe(qi,branch_length,.04,8)+115000*(qi/qrnom)**2 for qi in q])
 return pump_dp(total)-common-2*np.cumsum(header)-branch
ind=root(residual,np.full(10,qrnom),tol=1e-11)
assert ind.success and np.max(np.abs(residual(ind.x)))<1e-4 and np.all(ind.x>0)
indflow=ind.x*60000;flow_delta=(indflow-flows)/flows
assert max(abs(flow_delta))<.005,max(abs(flow_delta))
indhead=pump_dp(ind.x.sum())/(rho*g)
assert abs(indhead-v('pumpHeadM'))/v('pumpHeadM')<.005

elevation={}
for name in ['flat','raised']:
 d=data[name];qdiff=max(abs(d[f'rackFlowLmin[{i}]']-flows[i-1]) for i in range(1,11))
 hdiff=d['pumpHeadM']-v('pumpHeadM')
 expected=0 if name=='flat' else -rho*g*(3-2.7)/1000
 # Flat removes the entire common height above the 0.55 m pressure reference.
 if name=='flat':expected=rho*g*(2.7-.55)/1000
 sd=np.array([d[f'supplyPressureAbsKPa[{i}]']-press_s[i-1] for i in range(1,11)])
 rd=np.array([d[f'returnPressureAbsKPa[{i}]']-press_r[i-1] for i in range(1,11)])
 assert qdiff<1e-5 and abs(hdiff)<1e-7,(name,qdiff,hdiff)
 assert max(np.max(abs(sd-expected)),np.max(abs(rd-expected)))<1e-5,(name,sd,expected)
 elevation[name]={'max_rack_flow_difference_Lmin':qdiff,'pump_head_difference_m':hdiff,'expected_header_pressure_shift_kPa':expected,'actual_supply_shift_kPa':sd.tolist(),'actual_return_shift_kPa':rd.tolist(),'interpretation':'Gravity check at fixed lengths, not a new routed CAD scenario'}

critical=int(np.argmin(flows))+1
common_names=['suctionCommon','suctionLegs','dischargeLegs','dischargeCommon','returnCommon']
budget={'CDU / pump-leg piping':sum(v(n+'.dp') for n in common_names)/1000,'Filter map':v('filterMap.dp')/1000,'HX map':v('hxMap.dp')/1000,'Supply header to R-%02d'%critical:sum(v(f's{i}.dp') for i in range(1,critical+1))/1000,'Return header from R-%02d'%critical:sum(v(f'r{i}.dp') for i in range(1,critical+1))/1000,'Rack equipment map':v(f'rack{critical}.rackMap.dp')/1000,'Balancing valve map':v(f'rack{critical}.balancingValve.dp')/1000,'Rack piping / fittings':(v(f'rack{critical}.supplyPipe.dp')+v(f'rack{critical}.internalElevation.dp')+v(f'rack{critical}.returnPipe.dp'))/1000}
assert min(budget.values())>=0
assert abs(sum(budget.values())-v('pumpDPkPa'))<1e-7
log=(RUN/'run.log').read_text()
assert log.count('The simulation finished successfully.')==3,log[-1500:]
assert 'INCONSISTENT due to specified unit information' not in log
assert 'Variable violating min constraint' not in log
assert not re.search(r'(LOG_ASSERT\s*\| error|LOG_INIT\s*\| error|Error:)',log)
warnings=sorted(set(re.findall(r'Warning: ([^\n]+)',log)))
summary={'qualification':'Initial steady hydraulic numerical result; assumed device curves and fitting losses; no experimental validation or selected hardware','software':'OpenModelica 1.27.1 / MSL 4.1.0','model_equations':int(re.search(r'has (\d+) equation',log).group(1)),'run_attempt':RUN.name,'result_kind':'Algebraic steady solution repeated over 0-1 s; not startup dynamics','rack_heat_load_status':'1 MW used to define target flow; rack heating and physical HX thermal performance not solved','rho_kg_m3':rho,'flow_target_total_Lps':qnom*1000,'flow_target_rack_Lmin':qrnom*60000,'total_flow_Lps':v('totalFlowLps'),'flow_per_duty_pump_m3h':v('flowPerDutyPumpM3h'),'pump_head_m':v('pumpHeadM'),'pump_dp_kPa':v('pumpDPkPa'),'hydraulic_power_W':v('pumpHydraulicW'),'shaft_power_W':v('pumpShaftW'),'electrical_power_W':v('pumpElectricalW'),'pump_suction_absolute_kPa':v('pumpSuctionAbsKPa'),'rack_flow_Lmin':flows.tolist(),'flow_spread_percent_of_mean':float((flows.max()-flows.min())/flows.mean()*100),'minimum_flow_rack':'R-%02d'%critical,'supply_pressure_absolute_kPa':press_s.tolist(),'return_pressure_absolute_kPa':press_r.tolist(),'pressure_budget_kPa':budget,'numerical_audits':{'max_mass_residual_kg_s':mass,'max_loop_pressure_residual_Pa':loop,'pump_work_numerical_bath_energy_residual_W':energy,'all_csv_values_finite':True,'all_cases_reached_final_time':True,'csv_rows':rowcounts,'elevation':elevation},'independent_colebrook_check':{'rack_flow_Lmin':indflow.tolist(),'max_flow_difference_percent':float(max(abs(flow_delta))*100),'pump_head_m':float(indhead),'max_nonlinear_residual_Pa':float(np.max(np.abs(residual(ind.x)))),'scope':'Same assumed network independently solved using exact Colebrook friction; not experimental validation'},'warnings_retained':warnings,'source_model_sha256':hashlib.sha256((RUN/'input_model.mo').read_bytes()).hexdigest()}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
with (OUT/'rack-results.csv').open('w',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['rack','flow_Lmin','target_Lmin','supply_absolute_kPa','return_absolute_kPa','branch_dp_kPa','independent_Colebrook_flow_Lmin'])
 for i in range(10):w.writerow([f'R-{i+1:02d}',flows[i],qrnom*60000,press_s[i],press_r[i],v(f'rackDPkPa[{i+1}]'),indflow[i]])
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','axes.labelcolor':'#17394d','text.color':'#17394d','axes.edgecolor':'#a4bac6','grid.alpha':.2})
fig,ax=plt.subplots(2,2,figsize=(15,10),constrained_layout=True)
nums=np.arange(1,11)
ax[0,0].plot(nums,flows,'o-',color='#167bac',label='OpenModelica')
ax[0,0].plot(nums,indflow,'o',color='#cc7c1b',ms=4,label='Independent Colebrook')
ax[0,0].axhline(qrnom*60000,color='#a23939',ls='--',label='Nominal heat / delta-T target')
ax[0,0].set(xticks=nums,xlabel='Rack number (near CDU -> far end)',ylabel='Flow [L/min]',title='Distribution: near racks receive slightly more flow',ylim=(135,160));ax[0,0].legend(fontsize=8)
ax[0,1].plot(nums,press_s,'o-',color='#167bac',label='Supply')
ax[0,1].plot(nums,press_r,'o-',color='#cb552d',label='Return')
ax[0,1].set(xticks=nums,xlabel='Rack number',ylabel='Absolute pressure [kPa]',title='Header pressures at 2.70 m elevation');ax[0,1].legend()
qq=np.linspace(0,qnom*2,160);hh=np.array([pump_dp(q)/(rho*g) for q in qq])
ax[1,0].plot(qq*1000,hh,color='#17394d',label='Assumed two-pump equivalent curve')
ax[1,0].plot(v('totalFlowLps'),v('pumpHeadM'),'o',color='#cb552d',ms=8,label='Solved network operating point')
ax[1,0].set(xlabel='Total bank flow [L/s]',ylabel='Head [m]',title='Pump curve is illustrative, not a vendor selection',ylim=(0,40));ax[1,0].legend(fontsize=8)
ax[1,1].barh(list(budget),list(budget.values()),color=['#8a9fab','#7094ac','#56798d','#167bac','#cb552d','#456b7d','#b88b46','#759c8e'])
ax[1,1].invert_yaxis();ax[1,1].set(xlabel='Pressure loss [kPa]',title='Pressure budget through the lowest-flow rack')
for a in ax.flat:a.grid(axis='y' if a!=ax[1,1] else 'x');a.set_axisbelow(True)
fig.suptitle('Data-center hydraulics | First steady OpenModelica network\n10 parallel racks - CAD routes - fixed water properties - assumed equipment curves',fontsize=17)
fig.savefig(OUT/'hydraulic-baseline.png',dpi=160)
fig.savefig(OUT/'hydraulic-baseline.svg')
(OUT/'hydraulic-baseline.svg').write_text('\n'.join(l.rstrip() for l in (OUT/'hydraulic-baseline.svg').read_text().splitlines())+'\n')
print(json.dumps({k:summary[k] for k in ['total_flow_Lps','pump_head_m','pump_dp_kPa','electrical_power_W','rack_flow_Lmin','flow_spread_percent_of_mean','warnings_retained']},indent=2))
print('All numerical acceptance checks passed. Independent maximum rack-flow difference:',summary['independent_colebrook_check']['max_flow_difference_percent'],'%')
