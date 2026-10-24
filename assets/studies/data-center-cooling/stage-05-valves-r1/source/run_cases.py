"""Run unique native case files without recompiling or overwriting previous stages."""
from pathlib import Path
import json,subprocess,os,hashlib,sys
B=Path(__file__).resolve().parents[1];D=json.loads((B/'model/design.json').read_text());R=B/'runs'/(sys.argv[1] if len(sys.argv)>1 else 'accepted-r1');R.mkdir(exist_ok=True)
assert hashlib.sha256((B/'model/DataCenterValveComparison.mo').read_bytes()).hexdigest()==D['model_sha256']
(R/'input_model.mo').write_bytes((B/'model/DataCenterValveComparison.mo').read_bytes())
logs=[];commands=[]
for c in D['cases']:
 output=R/(c['id']+'_res.csv');log=R/(c['id']+'.log')
 assert not output.exists(),'Use a fresh attempt directory instead of overwriting results'
 override=f"speedRatio={c['speed_ratio']:.16g},equipmentNominalPa[5]={c['rack05_nominal_Pa']:.16g},filterNominalPa={c['filter_nominal_Pa']:.16g}"
 cmd=[str(B/'runs/build-r1'/c['mode']),'-inputPath='+str(B/'runs/build-r1'),'-noHomotopyOnFirstTry','-override='+override,'-r='+str(output)]
 env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
 with log.open('w') as f:r=subprocess.run(cmd,cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT)
 logs.append(log.read_text());commands.append({'case':c['id'],'arguments':[a.replace(str(B),'${PROJECT_ROOT}') for a in cmd],'exit_code':r.returncode})
 assert r.returncode==0 and 'The simulation finished successfully.' in logs[-1],(c['id'],logs[-1][-3000:])
 print(c['id'],'completed',flush=True)
(R/'run.log').write_text('\n'.join(logs));(R/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
