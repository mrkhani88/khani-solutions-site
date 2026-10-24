from pathlib import Path
import json,subprocess,numpy as np,csv
B=Path(__file__).resolve().parents[1];W=B/'verification/native';records={}
for name,stop in [('Actuator',60),('Sensor',300)]:
 exe=W/('HAPSDelayProbes.'+name);out=W/(name.lower()+'_probe.csv');log=W/(name.lower()+'_probe.log')
 with log.open('w') as f:r=subprocess.run([str(exe),'-r='+str(out),'-maxStepSize=0.01','-stepSize=0.1','-tolerance=1e-9'],cwd=W,stdout=f,stderr=subprocess.STDOUT)
 assert r.returncode==0 and 'The simulation finished successfully.' in log.read_text()
 h=next(csv.reader(out.open()));a=np.loadtxt(out,delimiter=',',skiprows=1);x={k:a[:,i] for i,k in enumerate(h)};t=x['time']
 if name=='Actuator':
  expected=np.where(t<=2,0,300*(1-np.exp(-np.maximum(0,t-2)/5)));error=float(max(abs(x['heater.P']-expected)));assert error<.001
 else:
  expected=268.15-35*np.exp(-t/30);error=float(max(abs(x['heater.sensorT']-expected)));assert error<1e-5
 records[name]={'analytical_max_error':error,'unit':'W' if name=='Actuator' else 'K','passed':True,'output':out.name}
(B/'verification/analytical-delay-probes.json').write_text(json.dumps({'all_passed':True,'checks':records,'scope':'Analytical first-order/dead-time checks, not physical response characterization'},indent=2));print(records)
