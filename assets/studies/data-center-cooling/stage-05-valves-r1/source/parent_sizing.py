"""Reproducible independent Colebrook sizing, then native Modelica case generation.
Run on Intel with Python/NumPy/SciPy. Does not modify the accepted Stage 03.
"""
from pathlib import Path
import numpy as np
from scipy.optimize import root,brentq
import json,math,hashlib
B=Path(__file__).resolve().parents[1]
A=json.loads((B/'inputs/baseline-assumptions.json').read_text())
rho=A['rho_kg_m3']; mu=A['mu_Pa_s']; g=9.80665
qn=1e6/(A['cp_J_kgK']*10)/rho; qrn=qn/10
qt=144.7/60000; Q=qt*10
lengths=np.array(A['active_header_segments_m'])
def f(Re,D):
 if Re<1e-9:return 0
 if Re<2300:return 64/Re
 return brentq(lambda z:1/math.sqrt(z)+2*math.log10(A['roughness_m']/D/3.7+2.51/Re/math.sqrt(z)),.005,.12,xtol=1e-13)
def pipe(q,L,D,K=0):
 v=q/(math.pi*D*D/4);Re=rho*abs(v)*D/mu
 return (f(Re,D)*L/D+K)*rho*v*abs(v)/2

def losses(q,valves,rackmap=None):
 rackmap=np.full(10,1e5) if rackmap is None else np.array(rackmap)
 Q=sum(q);suffix=np.cumsum(q[::-1])[::-1]
 common=pipe(Q,12.11093,.125,4)+pipe(Q/2,1.11708,.065,2)+65000*(Q/qn)**2
 heads=2*np.cumsum([pipe(x,L,.125,.2) for x,L in zip(suffix,lengths)])
 branches=np.array([pipe(x,4.746992,.04,8) for x in q])+(rackmap+valves)*(q/qrn)**2
 return common+heads+branches

def pump(Q,s):
 r=Q/qn
 return rho*g*(37*s*s-.5*s*r-9*r*r)
def solve(s,valves,rackmap=None):
 sol=root(lambda q:pump(sum(q),s)-losses(q,np.array(valves),rackmap),np.full(10,qt),tol=1e-11)
 assert sol.success and max(abs(sol.fun))<1e-4 and min(sol.x)>0
 return sol.x
def generate():
 basev=np.full(10,15000.)
 speedonly=brentq(lambda s:sum(solve(s,basev))-Q,.8,1)
 # At equal target flow, retain ACTUAL 15 kPa at critical rack R10.
 q=np.full(10,qt); novalve=losses(q,np.zeros(10)); required=max(novalve)+15000
 combinedspeed=brentq(lambda s:pump(Q,s)-required,.8,1)
 combinedv=(required-novalve)/(qt/qrn)**2
 fullv=(pump(Q,1)-novalve)/(qt/qrn)**2
 cases=[('baseline','Baseline · 100% speed',1.,basev,None),('speed_only','Speed reduction only',speedonly,basev,None),('throttle_only','Manual balance · 100% speed',1.,fullv,None),('combined','Reduced speed + manual balance',combinedspeed,combinedv,None),('resistance_check','Same settings · R05 resistance +20%',combinedspeed,combinedv,[1e5]*4+[1.2e5]+[1e5]*5)]
 data=[]
 for key,label,s,v,rm in cases:
  flow=solve(s,v,rm); dp=pump(sum(flow),s);power=dp*sum(flow)/.675
  data.append(dict(id=key,label=label,speed_ratio=float(s),valve_nominal_Pa=v.tolist(),rack_nominal_Pa=rm or [1e5]*10,independent_flow_Lmin=(flow*60000).tolist(),independent_dp_Pa=float(dp),independent_power_W=float(power)))
 model=(B/'inputs/parent-model.mo').read_text().replace('DataCenterHydraulics','DataCenterBalancing')
 model=model.replace('parameter SI.Length supplyLength=1.698496;','parameter SI.PressureDifference valveNominalPa=15000;\n    parameter SI.PressureDifference equipmentNominalPa=100000;\n    parameter SI.Length supplyLength=1.698496;')
 model=model.replace('dp_nominal=100000,m_flow_nominal=mRackNom','dp_nominal=equipmentNominalPa,m_flow_nominal=mRackNom').replace('dp_nominal=15000,m_flow_nominal=mRackNom','dp_nominal=valveNominalPa,m_flow_nominal=mRackNom')
 model=model.replace('parameter Real speedRatio=1;','parameter Real speedRatio=1;\n    parameter SI.PressureDifference valveNominalPa[10]=fill(15000,10);\n    parameter SI.PressureDifference equipmentNominalPa[10]=fill(100000,10);')
 for i in range(1,11):
  model=model.replace(f'RackBranch rack{i}(supplyLength=',f'RackBranch rack{i}(valveNominalPa=valveNominalPa[{i}],equipmentNominalPa=equipmentNominalPa[{i}],supplyLength=')
 classes=[]
 for d in data:
  vals=','.join(format(z,'.15g') for z in d['valve_nominal_Pa']);rms=','.join(format(z,'.15g') for z in d['rack_nominal_Pa'])
  name='Case_'+d['id']
  classes.append(f'  model {name}\n    extends Baseline(speedRatio={d["speed_ratio"]:.15g},valveNominalPa={{{vals}}},equipmentNominalPa={{{rms}}});\n  end {name};')
 model=model.replace('end DataCenterBalancing;','\n'.join(classes)+'\nend DataCenterBalancing;')
 (B/'model/DataCenterBalancing.mo').write_text(model)
 manifest={'target_rack_Lmin':144.7,'target_total_Lps':Q*1000,'parent_model_sha256':hashlib.sha256((B/'inputs/parent-model.mo').read_bytes()).hexdigest(),'model_sha256':hashlib.sha256(model.encode()).hexdigest(),'critical_rack':'R-10','critical_valve_actual_floor_Pa':15000,'optimization_scope':'Minimum speed for equal target flow with unchanged topology, two duty pumps and actual 15 kPa critical-valve floor; not global hardware optimization','cases':data}
 (B/'model/design.json').write_text(json.dumps(manifest,indent=2)+'\n')
 mos=['setCommandLineOptions("--numProcs=2");','loadModel(Modelica,{"4.1.0"});','loadFile("../../model/DataCenterBalancing.mo");','getErrorString();','checkModel(DataCenterBalancing.Case_combined);','getErrorString();']
 for d in data:
  mos += [f'simulate(DataCenterBalancing.Case_{d["id"]},startTime=0,stopTime=1,numberOfIntervals=1,tolerance=1e-8,outputFormat="csv",fileNamePrefix="{d["id"]}",cflags="-O1",simflags="-noHomotopyOnFirstTry");','getErrorString();']
 (B/'source/run.mos').write_text('\n'.join(mos)+'\n')
 print(json.dumps([{k:d[k] for k in ['id','speed_ratio','independent_power_W','independent_flow_Lmin']} for d in data],indent=2))

if __name__=="__main__":generate()
