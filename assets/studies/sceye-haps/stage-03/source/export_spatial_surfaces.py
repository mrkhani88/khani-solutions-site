"""Extract the actual exposed FEM boundary, canceling shared material interfaces."""
from pathlib import Path
import numpy as np,json
B=Path(__file__).resolve().parents[1]
facespec=[[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]
normals=[[0,0,-1],[0,0,1],[0,-1,0],[1,0,0],[0,1,0],[-1,0,0]]
def export():
 for stem in ['mesh2','mesh2_vias','mesh2_pad']:
  f=B/'spatial'/f'{stem}-surface.json';record=json.loads(f.read_text());a=np.load(B/'spatial'/f'{stem}.npz');xyz=a['xyz_m']*1000;T=a['rise_K_per_W'];boundary={}
  for c,tag in zip(a['hexahedra'],a['region']):
   for spec,normal in zip(facespec,normals):
    ids=c[spec];key=tuple(sorted(ids.tolist()))
    if key in boundary:del boundary[key]
    else:boundary[key]=(ids,int(tag),normal)
  region=['Pad','PCB','CPU','FPGA','IO','Power'];record['surfaces']=[dict(xyz_mm=xyz[ids].round(5).tolist(),rise=T[ids].round(8).tolist(),region=region[tag],normal=normal) for ids,tag,normal in boundary.values()];record['boundary_scope']='Actual exposed hexahedral faces, including bottom and side faces; shared material interfaces canceled.';f.write_text(json.dumps(record,separators=(',',':')));print(stem,len(record['surfaces']),flush=True)
if __name__=='__main__':export()
