"""Retain complete native solver evidence in per-run ZIPs on Intel, not bulkMac."""
from pathlib import Path
import json,zipfile,hashlib,subprocess,datetime
B=Path(__file__).resolve().parents[2];V=B/'verification/engineering';R=B/'results/engineering';S=B/'source/engineering';W=V/'native';A=V/'archives';A.mkdir(exist_ok=True)
records=[]
man=json.loads((V/'run-manifest.json').read_text())+json.loads((V/'equilibrium-manifest.json').read_text())
man+=[dict(id='stage05_reference',native_sha256=hashlib.sha256((R/'stage05_reference_native.csv').read_bytes()).hexdigest(),execution_success=True)]
for rec in man:
 id=rec['id'];raw=R/(id+'_native.csv');assert rec['execution_success'] and hashlib.sha256(raw.read_bytes()).hexdigest()==rec['native_sha256'];out=A/(id+'-native.zip')
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  z.write(raw,'results/engineering/'+raw.name)
  for p in S.iterdir():
   if p.is_file() and p.suffix in ['.py','.mo','.mos','.FCMacro','.md']:z.write(p,'source/engineering/'+p.name)
  for p in [W/(id+'.log'),W/'compile.log',W/'equilibrium-compile.log',V/'source-provenance.json',V/'audit.json',V/'conduction-audit.json',V/'dynamic-reduction-audit.json',V/'stage05-reproduction.json']:
   if p.exists():z.write(p,str(p.relative_to(B)))
  z.writestr('run-record.json',json.dumps(rec,indent=2))
 records.append(dict(id=id,path=str(out.relative_to(B)),remote_path=str(out),bytes=out.stat().st_size,sha256=hashlib.sha256(out.read_bytes()).hexdigest(),native_csv_sha256=rec['native_sha256'],scope='Complete rawCSV and exactsource/logs; artifact is numericalevidence, notphysicalvalidation'));print(id,out.stat().st_size,flush=True)
(V/'native-archives.json').write_text(json.dumps(records,indent=2));(B/'verification/native-archives.json').write_text(json.dumps(records,indent=2))
(V/'final-provenance.json').write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),host='falcon-intel',OpenModelica=subprocess.check_output(['omc','--version'],text=True).strip(),source_sha256=hashlib.sha256((S/'HAPSInterview.mo').read_bytes()).hexdigest(),compiled_executable_sha256=hashlib.sha256((W/'HAPSInterview.IntegratedMission').read_bytes()).hexdigest(),raw_case_count=len(records),archives_total_bytes=sum(x['bytes'] for x in records),science_boundary='Independent assumedmodel; noOEMdata,physicaltests,qualificationorflightreadiness'),indent=2))
