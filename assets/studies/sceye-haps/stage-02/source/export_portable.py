from pathlib import Path
import json,zipfile,hashlib,subprocess
B=Path(__file__).resolve().parents[1];out=B/'native';out.mkdir(exist_ok=True);records=json.loads((B/'verification/run-manifest.json').read_text());archives=[]
for r in records:
 name=r['id'];f=B/'results'/r['output'];assert hashlib.sha256(f.read_bytes()).hexdigest()==r['sha256'];log=B/'verification/native'/(name+'.log');case=json.dumps(r,indent=2).replace(str(B),'${PROJECT_ROOT}')+'\n';z=out/(name+'-full-native.zip')
 with zipfile.ZipFile(z,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as a:
  a.write(f,f.name);a.writestr(name+'.log',log.read_text().replace(str(B),'${PROJECT_ROOT}'));a.writestr('case-record.json',case)
 with zipfile.ZipFile(z) as a:assert a.testzip() is None
 archives.append({'path':'native/'+z.name,'bytes':z.stat().st_size,'sha256':hashlib.sha256(z.read_bytes()).hexdigest(),'raw_native_sha256':r['sha256'],'case':name});print(z.name,z.stat().st_size,flush=True)
(B/'verification/native-archives.json').write_text(json.dumps(archives,indent=2)+'\n')
prov={'model_source_sha256':hashlib.sha256((B/'source/HAPSDiurnal.mo').read_bytes()).hexdigest(),'openmodelica':subprocess.check_output(['omc','--version'],text=True).strip(),'Modelica_library':'4.1.0','cases':[r['id'] for r in records],'scope':'Native executed thermal-energy model; no physical validation','original_native_CSVs':'Unchanged inside per-case archives; public diagnostic paths normalized to ${PROJECT_ROOT}.','accepted_compile_log':'compile-r3.log','runtime_note':'Refinement uses explicit -stepSize and -tolerance runtime flags. A prior fine-output attempt used override syntax that retained the 60 s output grid; that attempt and its original log/CSV are retained on Intel but excluded from accepted archives.'}
(B/'verification/source-provenance.json').write_text(json.dumps(prov,indent=2)+'\n')
