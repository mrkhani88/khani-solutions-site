"""Audit native mission conservation, baseline reproducibility and P/PI behavior."""
from pathlib import Path
import json,csv,hashlib
import numpy as np
from scipy.integrate import cumulative_trapezoid
B=Path(__file__).resolve().parents[1];V=B/'verification';R=B/'results';D=R/'viewer';D.mkdir(exist_ok=True)
cases=json.loads((B/'inputs/cases.json').read_text());nodes=json.loads((B/'inputs/component-nodes.json').read_text());tt=np.arange(604800,691201,60);tprev=tt-86400

def load(name,base=B):
 p=base/'results'/f'{name}_native.csv';h=next(csv.reader(p.open()));a=np.loadtxt(p,delimiter=',',skiprows=1);assert np.isfinite(a).all();return p,h,a,{k:a[:,i] for i,k in enumerate(h)}
def ip(x,k,t):
 _,j=np.unique(x['time'][::-1],return_index=True);j=np.sort(len(x['time'])-1-j);return np.interp(t,x['time'][j],x[k][j])
def integ(y,t):return float(np.trapezoid(y,t))
summ=[];aud=[];traces={};cache={}
for c in cases+[dict(id='pi_fine',title='PI numerical refinement',override=next(c['override'] for c in cases if c['id']=='pi'))]:
 id=c['id'];p,h,a,x=load(id);t=x['time'];m=t>=604800;assert t[-1]==691200 and np.all(np.diff(t)>=0)
 storage=sum(n['C_J_K']*(x[n['key']+'.T']-n['T0_K']) for n in nodes);prefix=[k[:-6] for k in x if k.endswith('.Qconv')];ext=sum(x[k+'.Qconv']+x[k+'.Qdirect']+x[k+'.Qreflected']+x[k+'.Qir'] for k in prefix);gen=x['avionics.Pelec']+x['power.Qdc']+x['power.Qmppt']+x['battery.Qloss']+x['payload.Pelec']-x['payload.Prf']+x['propulsion.Pelec']-x['propulsion.Pshaft']+x['heaterPower'];quad=cumulative_trapezoid(ext+gen-x['power.Ppanel'],t,initial=0);sysquad=cumulative_trapezoid(ext-x['propulsion.Pshaft']-x['payload.Prf'],t,initial=0)
 cyc=max(float(max(abs(ip(x,n['key']+'.T',tt)-ip(x,n['key']+'.T',tprev)))) for n in nodes);soccyc=float(max(abs(ip(x,'battery.SOC',tt)-ip(x,'battery.SOC',tprev))))
 o=c['override'];cap=100*o['motorHeaterScale'];kp=o.get('motorKp',30);ki=o.get('motorKi',0);mode=o.get('motorMode',0);I=x['propulsion.heater.I'];error=x['propulsion.heater.error'];u=x['propulsion.heater.u'];P=x['propulsion.Pheat'];sensor=x['propulsion.heater.sensorT'];T=x['propulsion.housing.T'];
 checks=dict(case=id,finite=True,finish_s=float(t[-1]),rows=len(t),columns=len(h),source_native_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),storage_error_J=float(max(abs(storage-x['thermalStorage']))),external_error_W=float(max(abs(ext-x['Qexternal']))),generation_error_W=float(max(abs(gen-x['Qgenerated']))),native_system_residual_J=float(max(abs(x['systemResidualJ']))),native_thermal_residual_J=float(max(abs(x['thermalResidualJ']))),independent_energy_fraction=float(max(max(abs(quad-storage)),max(abs(sysquad-storage-x['chemicalStorage'])))/x['loadEnergy'][-1]),cycle_temperature_K=cyc,cycle_SOC=soccyc,all_mission_SOC=[float(min(x['battery.SOC'])),float(max(x['battery.SOC']))],control_equation_error_W=float(max(abs(u-kp*error-(I if mode else 0)))),limit_equation_error_W=float(max(abs(P-np.clip(u,0,cap)))),sensor_equation_error_K=float(max(abs(error-(268.15-sensor)))),sensor_lag_difference_K=float(max(abs(sensor-T))))
 assert checks['storage_error_J']<.01 and checks['external_error_W']<1e-6 and checks['generation_error_W']<1e-6
 assert checks['native_system_residual_J']<.1 and checks['native_thermal_residual_J']<.1 and checks['independent_energy_fraction']<.001
 assert cyc<.02 and soccyc<1e-4 and min(x['battery.SOC'])>0 and max(x['battery.SOC'])<1
 assert checks['control_equation_error_W']<1e-5 and checks['limit_equation_error_W']<1e-5 and checks['sensor_equation_error_K']<1e-8
 if o.get('motorSensorLag',0)==0:assert checks['sensor_lag_difference_K']<1e-8
 else:assert checks['sensor_lag_difference_K']>.001
 if mode:assert max(abs(I))>10
 else:assert max(abs(I))<1e-10
 expectedRate=ki*error+(P-u)/60 if mode else np.zeros_like(error)
 checks['anti_windup_equation_error_W_s']=float(max(abs(x['propulsion.heater.Irate']-expectedRate)))
 assert checks['anti_windup_equation_error_W_s']<1e-6
 checks['integral_state_range_W']=[float(min(I)),float(max(I))]
 checks['controller_I_cycle_max_W']=float(max(abs(ip(x,'propulsion.heater.I',tt)-ip(x,'propulsion.heater.I',tprev))))
 checks['sensor_cycle_max_K']=float(max(abs(ip(x,'propulsion.heater.sensorT',tt)-ip(x,'propulsion.heater.sensorT',tprev))))
 checks['all_mission_peak_motor_heater_W']=float(max(P))
 checks['all_mission_at_cap_h']=integ((P>=.999*cap).astype(float),t)/3600
 assert checks['controller_I_cycle_max_W']<1 and checks['sensor_cycle_max_K']<.02
 def delta(k):return float(x[k][-1]-ip(x,k,[604800])[0])
 stat={n['key']:dict(min_C=float(min(x[n['key']+'.T'][m])-273.15),max_C=float(max(x[n['key']+'.T'][m])-273.15)) for n in nodes}
 housing=T[m]-273.15;ph=P[m];tm=t[m];active=ph>1;err=housing+5;dur=integ(active.astype(float),tm)
 control=dict(target_C=-5,capacity_W=cap,Kp_W_K=kp,Ki_W_K_s=ki,Ti_s=kp/ki if ki else None,minimum_housing_C=float(min(housing)),maximum_housing_C=float(max(housing)),peak_heater_W=float(max(ph)),headroom_W=cap-float(max(ph)),headroom_fraction=1-float(max(ph))/cap,at_capacity_h=integ((ph>=.999*cap).astype(float),tm)/3600,motor_energy_Wh=delta('propulsion.heater.E')/3600,degree_hours_below_target=integ(np.maximum(0,-err),tm)/3600,hours_below_target_minus_0_5=integ((housing< -5.5).astype(float),tm)/3600,active_h=dur/3600,active_RMSE_K=float(np.sqrt(integ(err**2*active,tm)/dur)) if dur else 0,active_max_abs_error_K=float(max(abs(err[active]))) if active.any() else 0,active_within_half_degree_fraction=integ(((abs(err)<=.5)&active).astype(float),tm)/dur if dur else 1,study_tracking_pass=bool(min(housing)>=-5.5 and max(ph)<.95*cap and (max(abs(err[active]))<=.5 if active.any() else True)),scope='Heating-only chosen minimum target. Warm daytime temperature is not regulated down to target.±0.5K and5%headroom are study acceptance criteria, not component qualification limits.')
 summary={**c,'motor_control':control,'node_temperatures':stat,'heater_energy_Wh':delta('heaterEnergy')/3600,'load_energy_kWh':delta('loadEnergy')/3.6e6,'SOC_min':float(min(x['battery.SOC'][m])),'SOC_max':float(max(x['battery.SOC'][m])),'cycle_difference_K':cyc};aud.append(checks);cache[id]={k:ip(x,k,tt) for k in [n['key']+'.T' for n in nodes]+['heaterPower','heaterEnergy','battery.SOC']}
 if id=='pi_fine':fineSummary=summary;continue
 summ.append(summary)
 with (R/f'{id}_day08.csv').open('w',newline='') as f:w=csv.writer(f);w.writerow(h);w.writerows(a[m])
 series={n['key']:[round(float(v-273.15),7) for v in ip(x,n['key']+'.T',tt)] for n in nodes}
 for k in ['propulsion.Pheat','heaterPower','battery.Pheat','avionics.Pheat','payload.Pheat','battery.SOC','power.Pload','environment.bus.Tair','environment.bus.wind','propulsion.heater.error','propulsion.heater.u','propulsion.heater.I','propulsion.heater.sensorT']:
  series[k]=[round(float(v-273.15 if k in ['environment.bus.Tair','propulsion.heater.sensorT'] else v),8) for v in ip(x,k,tt)]
 for native,key,unit in [('heaterEnergy','heaterEnergy_kWh',3.6e6),('loadEnergy','loadEnergy_kWh',3.6e6),('propulsion.heater.E','motorEnergy_Wh',3600)]:
  vals=ip(x,native,tt);series[key]=[round(float(v-vals[0])/unit,8) for v in vals]
 viewer=dict(case=id,source_native_sha256=checks['source_native_sha256'],source_time_range_s=[604800,691200],local_solar_hour=(np.arange(1441)/60).tolist(),series=series,scope='Saved native results, uniform60s final-day grid, post-event interpolation; no browser solver')
 (D/f'{id}.json').write_text(json.dumps(viewer,separators=(',',':')));print(id,'housing min',round(control['minimum_housing_C'],4),'heaterpeak',round(control['peak_heater_W'],2),'energy',round(summary['heater_energy_Wh']/1000,5),'activeError',round(control['active_max_abs_error_K'],4),'cyc',round(cyc,6),flush=True)
ref=cache['pi'];fi=cache['pi_fine'];diff={k:float(max(abs(ref[k]-fi[k]))) for k in ref};E=abs(next(s for s in summ if s['id']=='pi')['heater_energy_Wh']-fineSummary['heater_energy_Wh']);assert max(v for k,v in diff.items() if k.endswith('.T'))<.02 and E<1
(V/'refinement.json').write_text(json.dumps(dict(passed=True,max_temperature_difference_K=max(v for k,v in diff.items() if k.endswith('.T')),heater_energy_difference_Wh=E,differences=diff),indent=2))
old=B.parent/'stage-03-night-control-spatial-r1';_,_,_,prior=load('combined',old);oldDiff={k:float(max(abs(cache['reference'][k]-ip(prior,k,tt)))) for k in cache['reference']};assert max(v for k,v in oldDiff.items() if k.endswith('.T'))<.001
(V/'stage03-reproduction.json').write_text(json.dumps(dict(passed=True,max_temperature_difference_K=max(v for k,v in oldDiff.items() if k.endswith('.T')),differences=oldDiff),indent=2))
assert next(s for s in summ if s['id']=='pi')['motor_control']['study_tracking_pass']
(V/'numerical-audit.json').write_text(json.dumps(dict(all_passed=True,cases=aud,scope='Numerical verification and applied control equations; not physical test validation'),indent=2));(R/'summary.json').write_text(json.dumps(summ,indent=2));print('ALL CHECKS PASSED',flush=True)
