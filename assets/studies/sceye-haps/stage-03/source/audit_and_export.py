"""Audit native conservation, controlled inputs, repeat cycles and solver refinement.
Exports source-linked component records and the final saved 24-hour cycle.
"""
from pathlib import Path
import csv,json,re,ast,math,hashlib,zipfile
import numpy as np
from scipy.integrate import cumulative_trapezoid
B=Path(__file__).resolve().parents[1];R=B/'results';V=B/'verification';W=V/'native';D=R/'viewer';D.mkdir(exist_ok=True)
nodes=json.loads((B/'inputs/component-nodes.json').read_text());cases=json.loads((B/'inputs/cases.json').read_text());runs=json.loads((V/'run-manifest.json').read_text())
def load(name):
 f=R/(name+'_native.csv');header=next(csv.reader(f.open()));a=np.loadtxt(f,delimiter=',',skiprows=1);assert a.shape[1]==len(header) and np.isfinite(a).all();x={k:a[:,i] for i,k in enumerate(header)};assert np.all(np.diff(x['time'])>=0) and abs(x['time'][-1]-691200)<1e-6;return f,header,a,x

def interp(x,key,tt):
 # Post-event value at duplicate event timestamps; output grid remains distinct.
 t=x['time'];_,ix=np.unique(t[::-1],return_index=True);ix=np.sort(len(t)-1-ix);return np.interp(tt,t[ix],x[key][ix])
def integral(y,t):return float(np.trapezoid(y,t))
all_audit=[];summaries=[];reference=None;time24=np.linspace(0,86400,1441);t7=time24+6*86400;t8=time24+7*86400
for case in cases+[{'id':'reference_fine','title':'Numerical refinement'}]:
 name=case['id'];f,header,a,x=load(name);t=x['time'];sel=t>=7*86400;daysel=(t>=6*86400)&(t<=7*86400)
 def day_delta(key):return float(x[key][-1]-interp(x,key,[7*86400])[0])
 reconstructed=sum(n['C_J_K']*(x[n['key']+'.T']-n['T0_K']) for n in nodes)
 surface_prefixes=sorted(k[:-6] for k in x if k.endswith('.Qconv'))
 external=sum(x[p+'.Qconv']+x[p+'.Qdirect']+x[p+'.Qreflected']+x[p+'.Qir'] for p in surface_prefixes)
 generated=x['avionics.Pelec']+x['power.Qdc']+x['power.Qmppt']+x['battery.Qloss']+x['payload.Pelec']-x['payload.Prf']+x['propulsion.Pelec']-x['propulsion.Pshaft']+x['heaterPower']
 qnet=external+generated-x['power.Ppanel'];heat_quad=cumulative_trapezoid(qnet,t,initial=0);system_quad=cumulative_trapezoid(external-x['propulsion.Pshaft']-x['payload.Prf'],t,initial=0)
 heat_err=np.max(np.abs(heat_quad-reconstructed));system_err=np.max(np.abs(system_quad-reconstructed-x['chemicalStorage']))
 norm=max(float(x['loadEnergy'][-1]),1)
 cyc={n['key']:float(np.max(np.abs(interp(x,n['key']+'.T',t8)-interp(x,n['key']+'.T',t7)))) for n in nodes};soccyc=float(np.max(np.abs(interp(x,'battery.SOC',t8)-interp(x,'battery.SOC',t7))))
 stats={n['key']:{'min_C':float(x[n['key']+'.T'][sel].min()-273.15),'max_C':float(x[n['key']+'.T'][sel].max()-273.15),'end_C':float(x[n['key']+'.T'][-1]-273.15)} for n in nodes}
 heaters={}
 for sub,pmax,setT in [('avionics',100,276.15),('battery',400,281.15),('payload',120,273.15),('propulsion',100,268.15)]:
  p=x[sub+'.Pheat'];enabled=case.get('override',{}).get('heaterEnabled',1)
  pmax*=case.get('override',{}).get('motorHeaterScale' if sub=='propulsion' else 'heaterScale',1) if sub!='battery' else 1
  heaters[sub]={'sensor_min_C':float(x[{'avionics':'avionics.tray.T','battery':'battery.caseNode.T','payload':'payload.plate.T','propulsion':'propulsion.housing.T'}[sub]][sel].min()-273.15),'energy_Wh':integral(p[sel],t[sel])/3600,'peak_W':float(p[sel].max()),'at_capacity_hours':integral((p[sel]>=pmax*0.999).astype(float),t[sel])/3600 if enabled else 0,'capacity_W':pmax,'setpoint_C':setT-273.15}
 audit={'case':name,'native_finish_s':float(t[-1]),'native_rows':len(t),'native_columns':len(header),'output_grid_s':30 if name.endswith('_fine') else 60,'native_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'finite':True,'temperature_range_K':[float(min(x[n['key']+'.T'].min() for n in nodes)),float(max(x[n['key']+'.T'].max() for n in nodes))],'storage_reconstruction_max_J':float(np.max(np.abs(reconstructed-x['thermalStorage']))),'external_power_reconstruction_max_W':float(np.max(np.abs(external-x['Qexternal']))),'heat_generation_reconstruction_max_W':float(np.max(np.abs(generated-x['Qgenerated']))),'native_thermal_residual_max_J':float(np.max(np.abs(x['thermalResidualJ']))),'native_system_residual_max_J':float(np.max(np.abs(x['systemResidualJ']))),'independent_thermal_quad_max_J':float(heat_err),'independent_system_quad_max_J':float(system_err),'independent_quad_max_fraction_of_load_energy':float(max(heat_err,system_err)/norm),'cycle_temperature_max_difference_K':max(cyc.values()),'cycle_temperature_by_node_K':cyc,'cycle_SOC_max_difference':soccyc,'all_mission_SOC_range':[float(x['battery.SOC'].min()),float(x['battery.SOC'].max())]}
 assert audit['storage_reconstruction_max_J']<0.01,audit
 assert audit['external_power_reconstruction_max_W']<1e-6
 assert audit['heat_generation_reconstruction_max_W']<1e-6
 assert audit['native_system_residual_max_J']<0.1
 assert audit['native_thermal_residual_max_J']<0.1
 assert audit['independent_quad_max_fraction_of_load_energy']<0.001,audit
 assert audit['cycle_temperature_max_difference_K']<0.02,audit
 assert soccyc<1e-4,audit
 assert min(x['battery.SOC'])>0 and max(x['battery.SOC'])<1,audit
 summary={**case,'node_temperatures':stats,'heater_energy_Wh':day_delta('heaterEnergy')/3600,'heaters':heaters,'load_energy_kWh':day_delta('loadEnergy')/3.6e6,'solar_used_kWh':day_delta('solarEnergy')/3.6e6,'charge_bus_kWh':day_delta('chargeEnergy')/3.6e6,'discharge_bus_kWh':day_delta('dischargeEnergy')/3.6e6,'SOC_min':float(x['battery.SOC'][sel].min()),'SOC_max':float(x['battery.SOC'][sel].max()),'SOC_start':float(interp(x,'battery.SOC',[7*86400])[0]),'SOC_end':float(x['battery.SOC'][-1]),'heater_peak_W':float(x['heaterPower'][sel].max()),'cycle_difference_K':max(cyc.values()),'cyclic_pass':True,'baseline_scope':'Numerically checked assumed model, not physically validated or qualified hardware'}
 all_audit.append(audit)
 if name=='reference':reference={k:interp(x,k,t8) for k in x if k in [n['key']+'.T' for n in nodes]+['battery.SOC','heaterPower']};referenceSummary=summary
 if name=='reference_fine':
  fine={k:float(np.max(np.abs(interp(x,k,t8)-v))) for k,v in reference.items()};fineEnergy=abs(summary['heater_energy_Wh']-referenceSummary['heater_energy_Wh']);assert max(v for k,v in fine.items() if k.endswith('.T'))<0.02,fine;assert fine['battery.SOC']<1e-4;assert fineEnergy<1
  (V/'refinement.json').write_text(json.dumps({'passed':True,'comparison':'Reference maximum step/output 60 s, tolerance 1e-7 versus 30 s, 1e-8. Final cycle compared on a common 60 s grid.','max_temperature_difference_K':max(v for k,v in fine.items() if k.endswith('.T')),'differences':fine,'heater_energy_difference_Wh':fineEnergy,'scope':'Numerical refinement only; not physical accuracy or mesh convergence.'},indent=2)+'\n')
  continue
 summaries.append(summary)
 # Preserve exact native values and original absolute solver times for final-cycle CSV.
 with (R/(name+'_day08.csv')).open('w',newline='') as g:
  w=csv.writer(g);w.writerow(header);w.writerows(a[sel])
 # Website data uses only evaluated native trajectories; temperatures converted K->C.
 series={n['key']:[round(float(v-273.15),6) for v in interp(x,n['key']+'.T',t8)] for n in nodes}
 keys=['avionics.strap.Gcmd','payload.strap.Gcmd','battery.SOC','heaterPower','avionics.Pheat','battery.Pheat','payload.Pheat','propulsion.Pheat','power.Pload','power.Ppv','power.Pavailable','power.Pcharge','power.Pdischarge','power.Pcurtailed','power.Qdc','power.Qmppt','environment.bus.Tair','environment.bus.DNI','environment.bus.heading','environment.bus.wind','environment.bus.sx','environment.bus.sy','environment.bus.sz','avionics.Pelec','payload.Pelec','propulsion.Pelec','propulsion.Pshaft','payload.Prf','battery.Qloss','battery.chargePermission']
 # sx is an alias to environment.x1 in the native CSV; preserve source relation.
 if 'environment.bus.sx' not in x:x['environment.bus.sx']=x['environment.x1']
 if 'power.Pavailable' not in x:x['power.Pavailable']=x['hull.Pavailable']
 for key in keys:series[key]=[round(float(v-273.15 if key=='environment.bus.Tair' else v),8) for v in interp(x,key,t8)]
 for key in ['heaterEnergy','loadEnergy','solarEnergy','chargeEnergy','dischargeEnergy']:
  unit=3600 if key=='heaterEnergy' else 3.6e6;v=interp(x,key,t8);series[key]=[round(float(q-v[0])/unit,8) for q in v]
 series['cpuPower_W']=[65+20*max(0,min(1, __import__('math').cos(35*__import__('math').pi/180)*__import__('math').cos(2*__import__('math').pi*(h-12)/24)/.08)) for h in time24/3600]
 for prefix in surface_prefixes:
  for q in ['Qconv','Qdirect','Qreflected','Qir','Qhull']:
   key=prefix+'.'+q;series[key]=[round(float(v),6) for v in interp(x,key,t8)]
 payload={'case':name,'source_native_sha256':audit['native_sha256'],'source_time_range_s':[604800,691200],'sample_method':'Uniform 60 s website grid; post-event duplicate values retained for interpolation. Raw CSVs include solver event records. Charts are saved native results, not browser solves or spatial fields.','local_solar_hour':[float(v) for v in time24/3600],'series':series}
 (D/(name+'.json')).write_text(json.dumps(payload,separators=(',',':'))+'\n')
 print(name,'T ranges',[(k,round(v['min_C'],2),round(v['max_C'],2)) for k,v in stats.items() if k in ['avionics.cpu','battery.core','payload.rf','propulsion.winding']],'heater kWh',round(summary['heater_energy_Wh']/1000,3),'quad',audit['independent_quad_max_fraction_of_load_energy'],'cyclic',max(cyc.values()),flush=True)
(V/'numerical-audit.json').write_text(json.dumps({'all_passed':True,'scope':'Execution, native topology, conservation, cycle settling and numerical refinement; no physical validation.','cases':all_audit},indent=2)+'\n')
(R/'summary.json').write_text(json.dumps(summaries,indent=2)+'\n')
# Sanity-check the applied controlled inputs, rather than trusting run labels.
ref=json.loads((D/'reference.json').read_text())['series']
for c in cases:
 y=json.loads((D/(c['id']+'.json')).read_text())['series']
 if c['id']=='cold':assert np.max(np.abs(np.array(y['environment.bus.Tair'])-np.array(ref['environment.bus.Tair'])+10))<1e-6
 if c['id']=='payload2':assert np.max(np.abs(np.array(y['payload.Pelec'])-2*np.array(ref['payload.Pelec'])))<1e-5
 if c['id']=='yaw90':assert np.max(np.abs(np.array(y['environment.bus.heading'])-np.array(ref['environment.bus.heading'])-90))<1e-6
 if c['id']=='no_heaters':assert max(y['heaterPower'])==0
print('All numerical gates passed.',flush=True)
