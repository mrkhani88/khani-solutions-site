from pathlib import Path
import json,hashlib,datetime
B=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
runs=json.loads((B/'verification/run-manifest.json').read_text())
r=dict(recorded_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_model_sha256=sha(B/'source/HAPSDiurnal.mo'),controller_cases_sha256=sha(B/'inputs/cases.json'),compiled_executable_sha256=sha(B/'verification/native/HAPSDiurnal.IntegratedMission'),accepted_compile_log_sha256=sha(B/'verification/native/compile.log'),runs=[dict(case=r['id'],native_CSV_sha256=r['sha256'],success=r['execution_success']) for r in runs],scope='Native executable and source retained on Intel; runtime overrides are audited from controller outputs. Not physical validation. Development attempts retained separately and excluded from accepted outputs.')
(B/'verification/provenance.json').write_text(json.dumps(r,indent=2));print(r['source_model_sha256'])
