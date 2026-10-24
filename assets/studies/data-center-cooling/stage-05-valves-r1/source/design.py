"""Independent steady network including an explicitly pressure-limited PICV.
Generic characteristic, not a fitted or qualified commercial valve model.
"""
from pathlib import Path
import json,hashlib,math
import numpy as np
from scipy.optimize import root,brentq
from parent_sizing import rho,g,qn,qrn,qt,pipe,lengths
B=Path(__file__).resolve().parents[1]
DP_MIN=35000.;DP_MARGIN=5000.;DP_MAX=414000.
old=json.loads((B/'inputs/stage04-design.json').read_text())['cases'][3]
valves=np.array(old['valve_nominal_Pa']);sm=old['speed_ratio']
scenarios=[('reference','Reference filter / unchanged racks',1e5,20000),('rack5','R05 equipment resistance +5%',1.05e5,20000),('rack20','R05 equipment resistance +20%',1.2e5,20000),('filter25','Filter coefficient +25%',1e5,25000),('filter100','Filter coefficient doubled',1e5,40000),('both','R05 +20% and filter doubled',1.2e5,40000)]
def no_valve(q,rack05,filterdp):
 Q=sum(q);suffix=np.cumsum(q[::-1])[::-1]
 common=pipe(Q,12.11093,.125,4)+pipe(Q/2,1.11708,.065,2)+(45000+filterdp)*(Q/qn)**2
 header=2*np.cumsum([pipe(x,L,.125,.2) for x,L in zip(suffix,lengths)])
 rackmap=np.full(10,1e5);rackmap[4]=rack05
 return common+header+np.array([pipe(x,4.746992,.04,8) for x in q])+rackmap*(q/qrn)**2

def pump(Q,s):
 r=Q/qn;return rho*g*(37*s*s-.5*s*r-9*r*r)
def speed_for_dp(dp):return brentq(lambda s:pump(qt*10,s)-dp,.5,1.5)
def solve(mode,s,rack05,filterdp):
 def fun(q):
  available=pump(sum(q),s)-no_valve(q,rack05,filterdp)
  if mode=='manual':return (available-valves*(q/qrn)**2)/1e5
  # Regulation above minimum differential; open-orifice limit below it.
  return q/qt-np.minimum(1.,np.sqrt(np.maximum(available,0)/DP_MIN))
 guess=np.full(10,qt*.98)
 sol=root(fun,guess,tol=1e-10)
 assert sol.success and max(abs(fun(sol.x)))<1e-7 and min(sol.x)>0,(mode,s,sol.message,fun(sol.x))
 return sol.x

def generate():
 sp=speed_for_dp(max(no_valve(np.full(10,qt),1e5,20000))+DP_MIN+DP_MARGIN)
 cases=[]
 for sid,label,rack05,fdp in scenarios:
  for policy in ['fixed','reset']:
   for mode in ['manual','picv']:
    if policy=='fixed':requested=sm if mode=='manual' else sp
    elif mode=='picv':requested=speed_for_dp(max(no_valve(np.full(10,qt),rack05,fdp))+DP_MIN+DP_MARGIN)
    else:
     requested=brentq(lambda s:min(solve(mode,s,rack05,fdp))-qt,.8,1.3)
    speed=min(1.,requested);q=solve(mode,speed,rack05,fdp);dp=pump(sum(q),speed);vdp=dp-no_valve(q,rack05,fdp)
    cases.append({'id':f'{sid}_{policy}_{mode}','scenario':sid,'scenario_label':label,'policy':policy,'mode':mode,'speed_ratio':float(speed),'requested_speed_ratio':float(requested),'speed_limited':bool(requested>1+1e-8),'rack05_nominal_Pa':rack05,'filter_nominal_Pa':fdp,'independent_flow_Lmin':(q*60000).tolist(),'independent_valve_dp_Pa':vdp.tolist(),'independent_power_W':float(dp*sum(q)/.675),'independent_pump_dp_Pa':float(dp)})
 data={'target_rack_Lmin':144.7,'picv_min_dp_Pa':DP_MIN,'picv_commissioning_margin_Pa':DP_MARGIN,'picv_upper_envelope_Pa':DP_MAX,'manual_reference_speed':sm,'picv_reference_speed':sp,'speed_limit':1.,'policy_note':'Fixed: retain each technology\'s own commissioned speed. Reset: independently calculate new steady speed; cap at 100%. No time-domain pump controller is simulated. Manual valve settings remain fixed in every case.','parent_model_sha256':hashlib.sha256((B/'inputs/parent-model.mo').read_bytes()).hexdigest(),'cases':cases}
 (B/'model/design.json').write_text(json.dumps(data,indent=2)+'\n')
 print(json.dumps([{k:c[k] for k in ['id','speed_ratio','requested_speed_ratio','speed_limited','independent_flow_Lmin','independent_power_W']} for c in cases],indent=2))
if __name__=='__main__':generate()
