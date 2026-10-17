from pathlib import Path
import numpy as np,json,re,hashlib,shutil
r=Path('/Users/reza/Documents/ChatGPT/Job/output/midnight-ground-tr-r5');o=Path('/tmp/khani-interactive-input/plume');o.mkdir(exist_ok=True)
# Reuse the existing native cell parser; it only reads source mesh and fields.
import sys;sys.path.insert(0,str(r));from foam_post import polygons,centres,field
print('MESH',len(polygons),flush=True)
cache=r/'results/white-turbo-r5/solved_field_display_cache.npz';local=o/'native-cache.npz'
with cache.open('rb') as src,local.open('wb') as dst:shutil.copyfileobj(src,dst,1024*1024)
f=np.load(local);T=f['T_C'];U=f['U_xy'];times=f['times'];assert T.shape==(61,len(polygons));speed=np.linalg.norm(U,axis=2)
values=np.stack([T,speed],axis=1).astype('<f4');assert np.isfinite(values).all();values.tofile(o/'fields.bin')
(o/'export.json').write_text(json.dumps({'polygons':[p.tolist() for p in polygons],'times':times.tolist(),'centres':centres.tolist(),'cache_sha256':hashlib.sha256(local.read_bytes()).hexdigest(),'bounds':[[float(T.min()),float(T.max())],[float(speed.min()),float(speed.max())]]},separators=(',',':')))
for name in ['run_summary.json','cell_metrics.json']:shutil.copy2(r/'results'/name,o/name)
for name in ['geometry.json','geometry_validation.json','prepare_cfd.py','README.md','center_section_with_vent.step','midnight_center_section.FCStd']:shutil.copy2(r/name,o/name)
print('PLUME_DONE',flush=True)
