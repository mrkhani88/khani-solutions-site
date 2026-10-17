from pathlib import Path
import numpy as np,json,hashlib,shutil
import pyvista as pv
from scipy.spatial import cKDTree
r=Path('/Users/reza/Library/Mobile Documents/com~apple~CloudDocs/Khani Workspace/Results/Codex Visualizations/2026-10-10/01a12775-9ec5-77b2-a3ab-d4637172c6be/battery-module-elmer')
o=Path('/tmp/khani-interactive-input/battery');o.mkdir(exist_ok=True)
print('READING_BATTERY',flush=True)
# Stream the cloud file rather than mapping it. Native source stays untouched.
local=o/'render_fields.npz'
with (r/'render_fields.npz').open('rb') as src,local.open('wb') as dst:shutil.copyfileobj(src,dst,1024*1024)
f=np.load(local);print([(k,f[k].shape) for k in f.files],flush=True)
pts,tets,body=f['points'],f['tets'],f['body'];temp=f['temperature'];times=f['time']
g=pv.UnstructuredGrid(np.column_stack([np.full(len(tets),4),tets]).ravel(),np.full(len(tets),pv.CellType.TETRA,np.uint8),pts);g.cell_data['body']=body
tree=cKDTree(pts);views=[]
for key,title,normal,origin,axes in [('section','Module center section · X/Z',(0,1,0),(0,0,0),(0,2)),('upper','Upper plate mid-channel · X/Y',(0,0,1),(0,0,.091),(0,1)),('lower','Lower plate mid-channel · X/Y',(0,0,1),(0,0,-.091),(0,1))]:
 s=g.slice(normal=normal,origin=origin).triangulate();xyz=s.points;faces=s.faces.reshape(-1,4)[:,1:];dist,idx=tree.query(xyz);ids=np.repeat(idx[:,None],4,axis=1);w=np.zeros((len(xyz),4));w[:,0]=1;ix=np.flatnonzero(dist>1e-9)
 if len(ix):
  ci=g.find_containing_cell(xyz[ix]);bad=ci<0;ci[bad]=g.find_closest_cell(xyz[ix][bad]);ids[ix]=tets[ci];v=pts[ids[ix]];a=np.transpose(v[:,1:]-v[:,0,None,:],(0,2,1));bc=np.linalg.solve(a,(xyz[ix]-v[:,0])[...,None])[...,0];w[ix,1:]=bc;w[ix,0]=1-bc.sum(1)
 assert np.max(np.abs(np.einsum('ij,ijk->ik',w,pts[ids])-xyz))<1e-8
 values=np.array([((t[ids]*w).sum(1)[faces].mean(1)-273.15) for t in temp],dtype='<f4');values.tofile(o/(key+'.bin'))
 polygons=(xyz[:,axes][faces]*1000).round(6).tolist();views.append({'id':key,'label':title,'polygons':polygons,'components':s.cell_data['body'].astype(int).tolist(),'field_file':key+'.bin','axis_labels':['X / mm',('Z' if key=='section' else 'Y')+' / mm'],'cells':len(faces)})
 print(key,len(faces),values.min(),values.max(),flush=True)
meta={'times':times.tolist(),'views':views,'render_fields_sha256':hashlib.sha256(local.read_bytes()).hexdigest(),'native_nodes':len(pts),'native_tets':len(tets),'snapshot_count':len(times)}
(o/'export.json').write_text(json.dumps(meta,separators=(',',':')))
for name in ['thermal_history.csv','results_summary.json','simulation_assumptions.json','mesh_validation.json','flow_validation.json','flux_reconstruction.json','MODEL_NOTES.txt','RESULTS.txt','battery_module_elmer.FCStd']:
 shutil.copy2(r/name,o/name)
shutil.copy2(r/'cad/battery_module_all.step',o/'battery_module_all.step')
print('BATTERY_DONE',flush=True)
