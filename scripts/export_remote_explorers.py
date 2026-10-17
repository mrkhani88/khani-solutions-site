from pathlib import Path
import numpy as np,json,re,hashlib,shutil
from PIL import Image
O=Path('/tmp/khani-interactive-export');O.mkdir(exist_ok=True)
def dump(p,x):p.write_text(json.dumps(x,separators=(',',':'),allow_nan=False))
r=Path('/mnt/falcon-scratch/postprocessing/falcon9-ground-fill/lunar-round-trip-2d-20261016-r3'); c=r/'case';o=O/'lunar';o.mkdir(exist_ok=True)
df=np.atleast_1d(np.genfromtxt(c/'demo_ledger.csv',delimiter=',',names=True));df=np.sort(df,order='time_s');_,ix=np.unique(df['time_s'],return_index=True);df=df[np.sort(ix)]
mesh=np.load(r/'Planar_Mesh.npz');polys=[mesh['points'][mesh['connectivity'][a:b]].tolist() for a,b in zip(mesh['offsets'][:-1],mesh['offsets'][1:])]
assert len(polys)==2118
files=sorted((float(p.parent.name),p.parent) for p in c.glob('*/alpha.LOX'));selected=[]
for stage in range(1,36):
 rows=df[df['stage']==stage];lo,hi=rows['time_s'][[0,-1]]; candidates=[(t,p) for t,p in files if lo<=t<=hi]
 assert candidates,stage
 for j in np.unique(np.linspace(0,len(candidates)-1,7).round().astype(int)): selected.append((stage,*candidates[j]))
fields=[];snaps=[];hashes={}
def field(path,n,vec=False):
 b=path.read_bytes();hashes[str(path.relative_to(r))]=hashlib.sha256(b).hexdigest()
 m=re.search(rb'internalField\s+nonuniform\s+List<(?:scalar|vector)>\s+(\d+)\s*\n\(',b)
 if m:
  assert int(m[1])==n
  return np.frombuffer(b,dtype='<f8',count=n*(3 if vec else 1),offset=m.end()).reshape((n,3) if vec else n)
 m=re.search(rb'internalField\s+uniform\s+([^;]+);',b);assert m,path
 v=np.fromstring(m[1].decode().strip('()'),sep=' ')
 return np.tile(v,(n,1)) if vec else np.full(n,v[0])
for st,t,p in selected:
 a=field(p/'alpha.LOX',len(polys));u=field(p/'U',len(polys),True);fields.append([a,np.linalg.norm(u,axis=1)])
 row=df[np.argmin(abs(df['time_s']-t))]
 snaps.append({'time':t,'phase':str(st),'metrics':{k:float(row[k]) for k in df.dtype.names},'metrics_time':float(row['time_s'])})
np.asarray(fields,dtype='<f4').tofile(o/'fields.bin')
dump(o/'export.json',{'polygons':polys,'snapshots':snaps,'native_snapshot_count':len(files),'ledger':{k:df[k].tolist() for k in df.dtype.names},'source_hashes':hashes,'raw_alpha_range':[float(np.min(np.array(fields)[:,0])),float(np.max(np.array(fields)[:,0]))]})
shutil.copy2(c/'demo_ledger.csv',o/'ledger.csv');shutil.copy2(r/'Planar_Mesh.npz',o/'Planar_Mesh.npz');print('LUNAR',len(snaps),flush=True)
r=Path('/mnt/falcon-scratch/postprocessing/archer-midnight-cfd/20261014-transient-wake-r1');o=O/'wake';o.mkdir(exist_ok=True)
for p in (r/'results/frames').glob('frame_*.png'):
 im=Image.open(p).convert('RGB').crop((0,0,1400,1050));im.save(o/(p.stem+'.jpg'),quality=86)
for name in ['Force_History.csv','Circulation_History.json','Visualization_Validation.json','Study_Parameters.json','Run_Manifest.json']:
 p=(r/'results'/name) if (r/'results'/name).exists() else r/name;shutil.copy2(p,o/name)
print('WAKE',len(list(o.glob('*.jpg'))),flush=True)
