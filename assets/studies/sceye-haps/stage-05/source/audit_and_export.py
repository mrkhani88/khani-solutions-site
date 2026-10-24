from pathlib import Path
import csv,json,hashlib
import numpy as np
from scipy.integrate import cumulative_trapezoid
B=Path(__file__).resolve().parents[1];R=B/'results';V=B/'verification';cases=json.loads((B/'inputs/cases.json').read_text());nodes=json.loads((B/'inputs/component-nodes.json').read_text());audit=[];summary=[];cache={}
def load(p):
 h=next(csv.reader(p.open()));a=np.loadtxt(p,delimiter=',',skiprows=1);return h,a,{k:a[:,i] for i,k in enumerate(h)}
def interp(x,k,tt):
 _,ix=np.unique(x['time'][::-1],return_index=True);ix=np.sort(len(x['time'])-1-ix);return np.interp(tt,x['time'][ix],x[k][ix])
def integ(y,t):return float(np.trapezoid(y,t))
def duration(t,b):return integ(np.asarray(b,float),t)/3600
for c in cases+[dict(id='managed_fine',override=next(c['override'] for c in cases if c['id']=='managed'))]:
 id=c['id'];p=R/(id+'_native.csv');h,a,x=load(p);t=x['time'];o=c['override'];T=x['propulsion.housing.T'];P=x['propulsion.Pheat'];cmd=x['propulsion.heater.command'];u=x['propulsion.heater.u'];I=x['propulsion.heater.I'];error=x['propulsion.heater.error'];sensor=x['propulsion.heater.sensorT'];cap=300;ceiling=o.get('motorCommandCeiling',300)
 assert np.isfinite(a).all() and t[0]==0 and t[-1]==691200 and np.all(np.diff(t)>=0)
 storage=sum(n['C_J_K']*(x[n['key']+'.T']-x[n['key']+'.T'][0]) for n in nodes)
 prefixes=[k[:-6] for k in x if k.endswith('.Qconv')];ext=sum(x[k+'.Qconv']+x[k+'.Qdirect']+x[k+'.Qreflected']+x[k+'.Qir'] for k in prefixes)
 gen=x['avionics.Pelec']+x['power.Qdc']+x['power.Qmppt']+x['battery.Qloss']+x['payload.Pelec']-x['payload.Prf']+x['propulsion.Pelec']-x['propulsion.Pshaft']+x['heaterPower']
 thermal=cumulative_trapezoid(ext+gen-x['power.Ppanel'],t,initial=0);system=cumulative_trapezoid(ext-x['propulsion.Pshaft']-x['payload.Prf'],t,initial=0)
 q=dict(case=id,finite=True,rows=len(t),columns=len(h),source_native_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),finish_s=float(t[-1]),storage_error_J=float(max(abs(storage-x['thermalStorage']))),external_error_W=float(max(abs(ext-x['Qexternal']))),generation_error_W=float(max(abs(gen-x['Qgenerated']))),native_thermal_residual_J=float(max(abs(x['thermalResidualJ']))),native_system_residual_J=float(max(abs(x['systemResidualJ']))),independent_energy_fraction=float(max(max(abs(thermal-storage)),max(abs(system-storage-x['chemicalStorage'])))/x['loadEnergy'][-1]),PI_equation_error_W=float(max(abs(u-o.get('motorKp',300)*error-I))),command_limit_error_W=float(max(abs(cmd-np.clip(u,0,ceiling)))),sensor_equation_error_K=float(max(abs(error-(268.15-sensor)))),antiwindup_equation_error_W_s=float(max(abs(x['propulsion.heater.Irate']-(o.get('motorKi',2)*error+(cmd-u)/60)))),sensor_initial_C=float(sensor[0]-273.15),heater_initial_W=float(P[0]),allmission_SOC=[float(min(x['battery.SOC'])),float(max(x['battery.SOC']))])
 q['initial_temperatures_C']={n['key']:float(x[n['key']+'.T'][0]-273.15) for n in nodes}
 for n in nodes:
  expected=o.get(n['key']+'.T0',o.get('motorInitialT',293.15) if n['subsystem']=='propulsion' else n['T0_K'])-273.15
  assert abs(q['initial_temperatures_C'][n['key']]-expected)<1e-8,(id,n,expected)
 assert q['storage_error_J']<.02 and q['external_error_W']<1e-6 and q['generation_error_W']<1e-6
 assert q['native_thermal_residual_J']<.1 and q['native_system_residual_J']<.1 and q['independent_energy_fraction']<.001
 assert q['PI_equation_error_W']<1e-5 and q['command_limit_error_W']<1e-5 and q['sensor_equation_error_K']<1e-8 and q['antiwindup_equation_error_W_s']<1e-5
 q['delivered_power_range_W']=[float(min(P)),float(max(P))];q['power_bound_numerical_tolerance_W']=0.001
 assert min(P)>-0.001 and max(P)<ceiling+0.001 and min(x['battery.SOC'])>0 and max(x['battery.SOC'])<1
 if o.get('motorCommandDelay',0)>0:assert max(P[t<o['motorCommandDelay']])<1e-6
 target=o.get('motorInitialT',293.15)-273.15;assert abs(q['sensor_initial_C']-target)<1e-8
 tt=np.arange(604800,691201,60);q['cycle_temperature_K']=max(float(max(abs(interp(x,n['key']+'.T',tt)-interp(x,n['key']+'.T',tt-86400)))) for n in nodes);q['cycle_SOC']=float(max(abs(interp(x,'battery.SOC',tt)-interp(x,'battery.SOC',tt-86400))))
 assert q['cycle_temperature_K']<.02 and q['cycle_SOC']<.0001
 windows={};viewer={}
 for name,start,end,step in [('startup',0,86400,10),('settled',604800,691200,60)]:
  m=(t>=start)&(t<=end);tm=t[m];temp=T[m]-273.15;power=P[m];command=cmd[m];err=temp+5
  def delta(k):return float(interp(x,k,[end])[0]-interp(x,k,[start])[0])
  # Acquisition means first true housing entry into +/-0.5K, followed by 600s continuously in band.
  grid=np.arange(start,end+1,1.0);tg=interp(x,'propulsion.housing.T',grid)-273.15;inside=np.abs(tg+5)<=.5
  dwell=600;miss=np.convolve((~inside).astype(int),np.ones(dwell+1,dtype=int),'valid');good=np.flatnonzero(miss==0);acq=float(grid[good[0]]-start)/60 if len(good) else None
  # Warm-start reference already above target, so report acquisition only for genuinely cold starts.
  if temp[0]>-4.5:acq=None
  active=power>1;night=active&(tm<start+6*3600);post=night.copy()
  if acq is not None:post &= tm>=start+acq*60
  else:post &= False
  windows[name]=dict(initial_housing_C=float(temp[0]),min_housing_C=float(min(temp)),max_housing_C=float(max(temp)),acquire_10min_band_minutes=acq,peak_heater_W=float(max(power)),hardware_headroom_W=cap-float(max(power)),hours_near_hardware_cap=duration(tm,power>=.99*cap),hours_at_command_ceiling=duration(tm,command>=.999*ceiling),motor_energy_kWh=delta('propulsion.heater.E')/3.6e6,all_heater_energy_kWh=delta('heaterEnergy')/3.6e6,DC_energy_kWh=delta('loadEnergy')/3.6e6,early_post_acquisition_error_K=float(max(abs(err[post]))) if post.any() else None,heater_on_max_abs_error_K=float(max(abs(err[active]))) if active.any() else 0,SOC_min=float(min(x['battery.SOC'][m])),temperatures={n['key']:dict(min_C=float(min(x[n['key']+'.T'][m])-273.15),max_C=float(max(x[n['key']+'.T'][m])-273.15)) for n in nodes})
  grid=np.arange(start,end+1,step);series={n['key']:[round(float(v-273.15),7) for v in interp(x,n['key']+'.T',grid)] for n in nodes}
  for k in ['propulsion.Pheat','propulsion.heater.command','propulsion.heater.delayedCommand','propulsion.heater.error','propulsion.heater.I','propulsion.heater.u','propulsion.heater.sensorT','heaterPower','battery.SOC','environment.bus.Tair']:
   series[k]=[round(float(v-273.15 if k in ['propulsion.heater.sensorT','environment.bus.Tair'] else v),8) for v in interp(x,k,grid)]
  for native,key in [('heaterEnergy','allEnergy_kWh'),('loadEnergy','DCenergy_kWh'),('propulsion.heater.E','motorEnergy_kWh')]:
   vv=interp(x,native,grid);series[key]=[round(float(v-vv[0])/3.6e6,9) for v in vv]
  viewer[name]=dict(hours=((grid-start)/3600).tolist(),step_s=step,series=series)
  if id!='managed_fine':
   keys=list(series)
   with (R/f'{id}_{name}.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['elapsed_s']+keys);w.writerows(zip((grid-start).tolist(),*[series[k] for k in keys]))
 cache[id]={'startup':viewer['startup'],'settled':viewer['settled'],'metrics':windows}
 if id!='managed_fine':
  summary.append({**c,'windows':windows,'hardware_cap_W':300,'command_ceiling_W':ceiling});(R/'viewer'/f'{id}.json').write_text(json.dumps(dict(case=id,source_native_sha256=q['source_native_sha256'],scope='Native solved integrated mission; first24h and settled day08 shown separately. Time-linked browser is not a solver.',windows=viewer),separators=(',',':')))
 audit.append(q);print(id,json.dumps({k:{a:round(v,5) if isinstance(v,float) else v for a,v in s.items() if a in ['acquire_10min_band_minutes','peak_heater_W','hours_near_hardware_cap','motor_energy_kWh','all_heater_energy_kWh','heater_on_max_abs_error_K']} for k,s in windows.items()}),flush=True)
# Coarser and finer managed startup sampled on the exact same output grid.
diffs={}
for win in ['startup','settled']:
 xx=cache['managed'][win];yy=cache['managed_fine'][win]
 diffs[win]={k:float(np.max(np.abs(np.array(v)-np.array(yy['series'][k])))) for k,v in xx['series'].items()}
assert max(v for d in diffs.values() for k,v in d.items() if k in [n['key'] for n in nodes])<.02
assert max(d['allEnergy_kWh'] for d in diffs.values())<.001
(V/'refinement.json').write_text(json.dumps(dict(passed=True,differences=diffs,scope='Maximum integration step2s/tolerance1e-7 versus0.5s/1e-8; same export grid'),indent=2))
# Baseline is unchanged Stage04 PI, verified against its native 8-day data.
_,_,prior=load(B/'inputs/stage04-pi-day08.csv');tt=np.arange(604800,691201,60);baseline={n['key']:float(max(abs(np.array(cache['reference']['settled']['series'][n['key']])-(interp(prior,n['key']+'.T',tt)-273.15)))) for n in nodes}
assert max(baseline.values())<.001
(V/'stage04-reproduction.json').write_text(json.dumps(dict(passed=True,max_difference_K=max(baseline.values()),differences=baseline),indent=2))
(V/'numerical-audit.json').write_text(json.dumps(dict(all_passed=True,cases=audit,scope='Numerical verification only; all hardware/time constants and cold limits assumed, no physical correlation'),indent=2));(R/'summary.json').write_text(json.dumps(summary,indent=2));print('ALL CHECKS PASSED',flush=True)
