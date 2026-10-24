"""Independent pressure-maintained leak/isolation network.
Fault R05 is reversible; supply/return header flows differ by the leak flow.
Not a finite-inventory depressurization or water-hammer model.
"""
from pathlib import Path
import json,hashlib,math
import numpy as np
from scipy.optimize import root,brentq
from parent_sizing import rho,g,qn,qrn,qt,pipe,lengths
B=Path(__file__).resolve().parents[1]
OLD=json.loads((B/'inputs/stage04-design.json').read_text())['cases'][3]
VALVES=np.array(OLD['valve_nominal_Pa']);SPEED=OLD['speed_ratio']
PREF=300000.;PATM=101325.;CD=.62;D=.04
isoDP=.5*rho*(qrn/(math.pi*D*D/4))**2/2

def pump(Q,s):
 r=Q/qn;return rho*g*(37*s*s-.5*s*r-9*r*r)
def branch(q,i):return pipe(q,4.746992,.04,8)+(100000+VALVES[i])*(q/qrn)*abs(q/qrn)
def isolation_flow(dp,opening):
 x=dp/isoDP
 return opening*qrn*x/(x*x+1e-16)**.25

def solve(dmm,os,orr,s=SPEED):
 area=math.pi*(dmm/1000)**2/4
 def equations(z,details=False):
  q=z[:10]*qt;t=q.copy();t[4]=z[10]*qt;pl=z[11]*1e5
  Q=sum(q);Qr=sum(t)
  # Split common routes on the correct side of the leak mass deficit.
  supply=pipe(Q,2.05,.125)+pipe(Q/2,1.11708,.065,2)+pipe(Q,4.382611,.125,2)+20000*(Q/qn)**2
  ret=pipe(Qr,5.678319,.125,2)+45000*(Qr/qn)**2
  ps=PREF+pump(Q,s)-supply-rho*g*2.15-np.cumsum([pipe(x,L,.125,.2) for x,L in zip(np.cumsum(q[::-1])[::-1],lengths)])
  pr=PREF+ret-rho*g*2.15+np.cumsum([pipe(x,L,.125,.2) for x,L in zip(np.cumsum(t[::-1])[::-1],lengths)])
  res=[(ps[i]-pr[i]-branch(q[i],i))/1e5 for i in range(10) if i!=4]
  ds=ps[4]-pl-pipe(q[4],1.698496,.04,3.5)+rho*g*1.15
  dr=pl-pr[4]-pipe(t[4],3.048496,.04,3.5)-(100000+VALVES[4])*(t[4]/qrn)*abs(t[4]/qrn)-rho*g*1.15
  leak=CD*area*math.sqrt(max(2*(pl-PATM)/rho,0))
  res += [(q[4]-isolation_flow(ds,os))/qt,(t[4]-isolation_flow(dr,orr))/qt,(q[4]-t[4]-leak)/qt]
  if details:return q,t,leak,ps,pr,pl,ds,dr
  return res
 guess=np.r_[np.ones(10),1.,5.]
 if os==0:guess[4]=0;guess[10]=-.03
 if orr==0:guess[10]=0;guess[4]=.04
 if os==0 and orr==0:guess[4]=0;guess[10]=0;guess[11]=PATM/1e5
 sol=root(equations,guess,tol=1e-10)
 # Near zero leak flow, a smooth native orifice and scalar pressure root differ
 # only by numerical roundoff. Reuse the previous seed if necessary.
 if not sol.success or max(abs(np.array(equations(sol.x))))>1e-6:
  sol=root(equations,sol.x,method='lm',options={'ftol':1e-12,'xtol':1e-12,'gtol':1e-12,'maxiter':2000})
 assert max(abs(np.array(equations(sol.x))))<1e-6,(dmm,os,orr,sol.message,equations(sol.x))
 q,t,leak,ps,pr,pl,ds,dr=equations(sol.x,True)
 return {'supply_flow_Lmin':(q*60000).tolist(),'return_flow_Lmin':(t*60000).tolist(),'leak_Lmin':float(leak*60000),'leak_node_abs_kPa':float(pl/1000),'supply_pressure_kPa':(ps/1000).tolist(),'return_pressure_kPa':(pr/1000).tolist(),'pump_flow_Lps':float(sum(q)*1000),'return_total_Lps':float(sum(t)*1000),'power_kW':float(pump(sum(q),s)*sum(q)/.675/1000),'pump_dp_kPa':float(pump(sum(q),s)/1000)}

def generate():
 states=[('unisolated','Leak, both valves open',1,1),('supply_only','Supply closed; return open',0,1),('return_only','Return closed; supply open',1,0),('dual','Both isolation valves closed',0,0),('seat_leak','Closed command; 1% residual conductance',.01,.01)]
 cases=[{'id':'reference','diameter_mm':0,'state':'reference','label':'No leak; commissioned baseline','supply_opening':1.,'return_opening':1.,'speed_ratio':SPEED}]
 for d in [1,3,6]:
  for key,label,os,orr in states:
   cases.append({'id':f'd{d}_{key}','diameter_mm':d,'state':key,'label':label,'supply_opening':os,'return_opening':orr,'speed_ratio':SPEED})
  reset=brentq(lambda s:min(v for i,v in enumerate(solve(d,0,0,s)['supply_flow_Lmin']) if i!=4)-144.7,.7,1.)
  cases.append({'id':f'd{d}_reset','diameter_mm':d,'state':'reset','label':'Both closed; reset pump for nine racks','supply_opening':0.,'return_opening':0.,'speed_ratio':reset})
 for opening in [.5,.1]:cases.append({'id':f'd3_partial_{int(opening*100)}','diameter_mm':3,'state':'partial','label':f'Closure snapshot: {int(opening*100)}% conductance','supply_opening':opening,'return_opening':opening,'speed_ratio':SPEED})
 for c in cases:c['independent']=solve(c['diameter_mm'],c['supply_opening'],c['return_opening'],c['speed_ratio'])
 # Maintained-pressure, zero-surge upper pressure envelope, not transient pressure.
 p_bound=PREF+rho*g*37-rho*g*1.0
 timing=[]
 for d in [1,3,6]:
  qbound=CD*math.pi*(d/1000)**2/4*math.sqrt(2*(p_bound-PATM)/rho)*60000
  for delay in [.5,2,5]:
   for closure in [1,3]:
    duration=delay+.2+closure
    timing.append({'diameter_mm':d,'detection_delay_s':delay,'logic_delay_s':.2,'closure_s':closure,'time_to_two_closed_s':duration,'maintained_pressure_leak_bound_Lmin':qbound,'preclosure_spill_bound_L':qbound*duration/60,'assumed_drainable_inventory_L':10,'with_full_inventory_bound_L':qbound*duration/60+10})
 data={'cases':cases,'target_Lmin':144.7,'reference_abs_Pa':PREF,'atmosphere_abs_Pa':PATM,'leak_Cd':CD,'fault_rack':'R05','fault_node_elevation_m':1.55,'reference_elevation_m':.55,'isolation_open_K_each':.5,'isolation_nominal_dp_Pa':isoDP,'pressure_boundary_scope':'Pressure maintained by an unlimited ideal reference source. Reference makeup equals leak loss; no finite fill/expansion depletion prediction.','leak_sizing_scope':'Equivalent round hole, constant Cd; not a hose rupture, crack growth or spray model.','timing_scope':'Conservative steady-pressure screen. Hold shutoff-envelope leak rate until both valves finish closing; no transient fluid or sensor/actuator model. Surge can exceed the envelope.','steady_leak_pressure_bound_abs_kPa':p_bound/1000,'assumed_drainable_inventory_L':10,'timing_cases':timing,'parent_model_sha256':hashlib.sha256((B/'inputs/parent-model.mo').read_bytes()).hexdigest()}
 (B/'model/design.json').write_text(json.dumps(data,indent=2)+'\n')
 for c in cases:print(c['id'],'leak',round(c['independent']['leak_Lmin'],4),'R05 S/R',round(c['independent']['supply_flow_Lmin'][4],3),round(c['independent']['return_flow_Lmin'][4],3),'power',round(c['independent']['power_kW'],4),'speed',round(c['speed_ratio']*100,3))
if __name__=='__main__':generate()
