from pathlib import Path
import json,zipfile,hashlib,datetime,subprocess,re
B=Path(__file__).resolve().parents[1];V=B/'verification';W=V/'native';S=B/'source/HAPSDiurnal.mo';old=B/'source/Stage04-reference.mo.txt'
assert re.findall(r'connect\([^;]+?\)',S.read_text())==re.findall(r'connect\([^;]+?\)',old.read_text())
(B/'native').mkdir(exist_ok=True)
a=json.loads((V/'numerical-audit.json').read_text());assert a['all_passed'];runs=json.loads((V/'run-manifest.json').read_text());records=[]
for run in runs:
 id=run['id'];raw=B/'results'/f'{id}_native.csv';assert hashlib.sha256(raw.read_bytes()).hexdigest()==run['sha256'];assert run['execution_success'];z=B/'native'/f'{id}-full-native.zip'
 if z.exists():raise RuntimeError('Archive already exists: preserve it rather than overwriting accepted evidence')
 with zipfile.ZipFile(z,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as f:
  f.write(raw,'results/'+raw.name);f.write(S,'source/HAPSDiurnal.mo')
  log=(W/f'{id}.log').read_text().replace(str(B),'${PROJECT_ROOT}');f.writestr('verification/native/'+id+'.log',log)
  f.writestr('verification/run-record.json',json.dumps(run,indent=2).replace(str(B),'${PROJECT_ROOT}'))
 with zipfile.ZipFile(z) as f:assert f.testzip() is None;assert hashlib.sha256(f.read('results/'+raw.name)).hexdigest()==run['sha256']
 record=dict(id=id,path='native/'+z.name,bytes=z.stat().st_size,sha256=hashlib.sha256(z.read_bytes()).hexdigest(),native_CSV_sha256=run['sha256']);records.append(record);print(id,record['bytes'],flush=True)
(V/'native-archives.json').write_text(json.dumps(records,indent=2))
provenance=dict(stage=B.name,UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),engineering_host='Intel',source_sha256=hashlib.sha256(S.read_bytes()).hexdigest(),compiled_executable_sha256=hashlib.sha256((W/'HAPSDiurnal.IntegratedMission').read_bytes()).hexdigest(),compiled_log_sha256=hashlib.sha256((W/'compile.log').read_bytes()).hexdigest(),case_file_sha256=hashlib.sha256((B/'inputs/cases.json').read_bytes()).hexdigest(),native_connections_unchanged=True,baseline_source_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),software={'OpenModelica':subprocess.check_output(['omc','--version'],text=True).strip(),'Modelica':'4.1.0'},scope='Numerical verification of an assumed integrated thermal network; no hardware correlation or operating qualification')
(V/'provenance.json').write_text(json.dumps(provenance,indent=2));print('ALL ARCHIVES VERIFIED',sum(x['bytes'] for x in records),flush=True)
