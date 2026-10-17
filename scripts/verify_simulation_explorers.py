"""Audit deliverable integrity, dimensions, numerical bounds and regressions."""
from pathlib import Path
import json,hashlib,subprocess
import numpy as np
R=Path(__file__).resolve().parents[1];O=R/'assets/studies/explorers';report={}
for key in ['plume','battery','lunar','wake']:
 d=O/key;j=json.loads((d/'viewer.json').read_text());m=json.loads((d/'manifest.json').read_text())
 for n,x in m['files'].items():
  p=d/n;assert p.stat().st_size==x['bytes'];assert hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256']
 times=np.array([s['time'] for s in j['snapshots']]);assert np.all(np.diff(times)>=0);h=j['history'];assert np.all(np.diff(h['time'])>0)
 for s in h['series']:assert len(s['values'])==len(h['time']);assert np.isfinite(s['values']).all()
 row={'snapshots':len(times),'time_range_s':[float(times[0]),float(times[-1])],'manifest_files':len(m['files'])}
 if j['mode']=='cells':
  v=j['views'][0];n=len(v['polygons']);q=j.get('quantity_count',len(j['variables']));a=np.fromfile(d/v['file'],dtype='<f4').reshape(len(times),q,n);assert np.isfinite(a).all();row.update(cells=n,ranges=[[float(a[:,i].min()),float(a[:,i].max())] for i in range(q)])
  assert all(len(p)>=3 for p in v['polygons'])
  if key=='plume':
   metrics=json.loads((d/'cell_metrics.json').read_text());assert len(metrics)==len(times)
   for i,x in enumerate(metrics):assert abs(float(a[i,0].max())-x['max_cell_temperature_C'])<1e-4;assert abs(float(a[i,1].max())-x['max_cell_speed_m_s'])<1e-4
  if key=='battery':
   summary=json.loads((d/'results_summary.json').read_text());assert abs(h['series'][0]['values'][-1]-summary['final']['battery_max_C'])<1e-10;assert a[-1].max()<=summary['final']['battery_max_C']+1e-4;assert len(v['components'])==n;assert set(v['components'])==set(range(1,8))
  if key=='lunar':
   assert len(set(s['phase'] for s in j['snapshots']))==35;assert a[:,0].min()>-1e-5 and a[:,0].max()<1.00001;assert all(abs(s['metrics_time']-s['time'])==min(abs(np.array(h['time'])-s['time'])) for s in j['snapshots']);row['native_source_states']=3022
 else:
  assert len(list(d.glob('frame_*.jpg')))==len(times)==75
  gamma=json.loads((d/'Circulation_History.json').read_text());assert all(s['time']==g['time_s'] and s['circulation']==g['Gamma_m2_s'] for s,g in zip(j['snapshots'],gamma))
 report[key]=row
# Existing PCB HTML, JS, CSS and angle interaction modules must be unchanged.
protected=['AISolutions/midnight-sweep.js','AISolutions/midnight-sweep.css','scripts/battery_thermal.py']+[str(p.relative_to(R)) for p in (R/'AISolutions').glob('battery-thermal*')]
assert subprocess.run(['git','diff','--exit-code','HEAD','--',*protected],cwd=R,capture_output=True).returncode==0
report['preserved_existing_interactive_files']=protected
print(json.dumps(report,indent=2));(O/'verification.json').write_text(json.dumps(report,indent=2))
