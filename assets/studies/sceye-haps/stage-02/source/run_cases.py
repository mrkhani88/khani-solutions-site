"""Run the single native compiled OpenModelica model with controlled overrides."""
from pathlib import Path
import os,subprocess,json,hashlib,time,datetime,sys
B=Path(__file__).resolve().parents[1];W=B/'verification/native';O=B/'results';O.mkdir(exist_ok=True)
exe=W/'HAPSDiurnal.IntegratedMission';assert exe.exists()
cases=json.loads((B/'inputs/cases.json').read_text());cases += [{'id':'reference_fine','title':'Reference numerical refinement','override':{},'change':'Output interval and maximum solver step 30 s instead of 60 s; tolerance 1e-8 instead of 1e-7.'}]
records=json.loads((B/"verification/run-manifest.json").read_text()) if (B/"verification/run-manifest.json").exists() else []
for case in cases:
 name=case['id'];
 if len(sys.argv)>1 and name not in sys.argv[1:]:continue
 fine=name.endswith('_fine');step=30 if fine else 60;out=O/(name+'_native.csv');log=W/(name+'.log');overrides=dict(case['override']);tol=1e-8 if fine else 1e-7
 flags=[str(exe),'-stopTime=691200','-stepSize='+str(step),'-tolerance='+str(tol),'-r='+str(out),'-maxStepSize='+str(step),'-lv=LOG_STATS']
 if overrides:flags.append('-override='+','.join(k+'='+str(v) for k,v in overrides.items()))
 start=time.monotonic()
 with log.open('w') as f:r=subprocess.run(flags,cwd=W,stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'},timeout=180)
 success=r.returncode==0 and 'The simulation finished successfully.' in log.read_text() and out.exists()
 record={**case,'returncode':r.returncode,'execution_success':success,'output':out.name,'bytes':out.stat().st_size if out.exists() else None,'sha256':hashlib.sha256(out.read_bytes()).hexdigest() if out.exists() else None,'max_step_s':step,'output_interval_s':step,'tolerance':tol,'elapsed_s':time.monotonic()-start,'command':flags,'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()};records=[x for x in records if x['id']!=name]+[record]
 (B/'verification/run-manifest.json').write_text(json.dumps(records,indent=2)+'\n');print(name,success,record['bytes'],round(record['elapsed_s'],2),flush=True)
 if not success:raise RuntimeError(log.read_text()[-5000:])
