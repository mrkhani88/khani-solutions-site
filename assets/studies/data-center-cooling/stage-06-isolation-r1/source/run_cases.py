from pathlib import Path
import json,subprocess,os,hashlib,sys
B=Path(__file__).resolve().parents[1];D=json.loads((B/'model/design.json').read_text());R=B/'runs'/(sys.argv[1] if len(sys.argv)>1 else 'accepted-r1');R.mkdir(exist_ok=True)
BUILD=B/'runs'/(sys.argv[2] if len(sys.argv)>2 else 'build-r3')
assert hashlib.sha256((B/'model/DataCenterIsolation.mo').read_bytes()).hexdigest()==D['model_sha256']
(R/'input_model.mo').write_bytes((B/'model/DataCenterIsolation.mo').read_bytes())
records=[];logs=[]
for c in D['cases']:
 out=R/(c['id']+'_res.csv');log=R/(c['id']+'.log');assert not out.exists(),'Use a fresh attempt directory'
 binary={'reference':'reference','supply_only':'supply_closed','return_only':'return_closed','dual':'dual_closed','reset':'dual_closed'}.get(c['state'],'open')
 override=f"speedRatio={c['speed_ratio']:.16g}"
 if c['diameter_mm']>0:override+=f",holeDiameterMM={c['diameter_mm']:.16g}"
 if binary=='open':override+=f",supplyOpening={c['supply_opening']:.16g},returnOpening={c['return_opening']:.16g}"
 cmd=[str(BUILD/binary),'-inputPath='+str(BUILD),'-noHomotopyOnFirstTry','-override='+override,'-r='+str(out)]
 with log.open('w') as f:r=subprocess.run(cmd,cwd=R,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'),stdout=f,stderr=subprocess.STDOUT)
 txt=log.read_text();logs.append(txt);records.append({'case':c['id'],'arguments':[a.replace(str(B),'${PROJECT_ROOT}') for a in cmd],'exit_code':r.returncode})
 assert r.returncode==0 and 'The simulation finished successfully.' in txt,(c['id'],txt[-3000:])
 print(c['id'],'completed',flush=True)
(R/'run.log').write_text('\n'.join(logs));(R/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
