from pathlib import Path
import json,zipfile,hashlib
B=Path(__file__).resolve().parents[1];out=B/'native';out.mkdir(exist_ok=True);records=json.loads((B/'verification/run-manifest.json').read_text());archives=[]
for r in records:
 if r['id'] not in ['reference','heater3','switch','combined','combined_fine']:continue
 name=r['id'];f=B/'results'/r['output'];assert hashlib.sha256(f.read_bytes()).hexdigest()==r['sha256'];z=out/(name+'-full-native.zip')
 with zipfile.ZipFile(z,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as a:
  a.write(f,f.name);a.writestr(name+'.log',(B/'verification/native'/(name+'.log')).read_text().replace(str(B),'${PROJECT_ROOT}'));a.writestr('case-record.json',json.dumps(r,indent=2).replace(str(B),'${PROJECT_ROOT}'))
 with zipfile.ZipFile(z) as a:assert a.testzip() is None
 archives.append(dict(path='native/'+z.name,bytes=z.stat().st_size,sha256=hashlib.sha256(z.read_bytes()).hexdigest(),raw_native_sha256=r['sha256'],case=name));print(name,z.stat().st_size,flush=True)
(B/'verification/native-archives.json').write_text(json.dumps(archives,indent=2))
