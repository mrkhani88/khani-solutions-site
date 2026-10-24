from pathlib import Path
import os,subprocess,json,hashlib,time,datetime,sys
B=Path(__file__).resolve().parents[1];W=B/'verification/native';R=B/'results';exe=W/'HAPSDiurnal.IntegratedMission'
cases=json.loads((B/'inputs/cases.json').read_text());cases += [dict(id='managed_fine',title='Managed startup numerical refinement',override=next(c['override'] for c in cases if c['id']=='managed'))]
records=json.loads((B/'verification/run-manifest.json').read_text()) if (B/'verification/run-manifest.json').exists() else []
for c in cases:
 id=c['id']
 if len(sys.argv)>1 and id not in sys.argv[1:]:continue
 fine=id.endswith('_fine');step=5 if fine else 10;maxstep=.5 if fine else 2;tol=1e-8 if fine else 1e-7
 out=R/(id+'_native.csv');log=W/(id+'.log')
 flags=[str(exe),'-stopTime=691200','-stepSize='+str(step),'-tolerance='+str(tol),'-r='+str(out),'-maxStepSize='+str(maxstep),'-lv=LOG_STATS','-override='+','.join(k+'='+str(v) for k,v in c['override'].items())]
 start=time.monotonic()
 with log.open('w') as f:r=subprocess.run(flags,cwd=W,stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'},timeout=600)
 success=r.returncode==0 and 'The simulation finished successfully.' in log.read_text() and out.exists()
 record={**c,'execution_success':success,'returncode':r.returncode,'max_step_s':maxstep,'output_interval_s':step,'tolerance':tol,'bytes':out.stat().st_size if out.exists() else 0,'sha256':hashlib.sha256(out.read_bytes()).hexdigest() if out.exists() else None,'elapsed_s':time.monotonic()-start,'command':flags,'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()};records=[x for x in records if x['id']!=id]+[record];(B/'verification/run-manifest.json').write_text(json.dumps(records,indent=2));print(id,success,record['bytes'],round(record['elapsed_s'],2),flush=True)
 if not success:raise RuntimeError(log.read_text()[-5000:])
