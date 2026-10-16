"""Plot pointwise battery temperature changes from the saved fields at600s.
Run after run_size_study.py. No interpolation between FV unknowns.
"""
from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
R=Path(__file__).resolve().parents[1];v=json.loads((R/'results/viewer_data.json').read_text());ref=v['cases']['reference'];ref_nodes=json.loads((R/'results/reference_mesh_nodes.json').read_text());ref_field=np.fromfile(R/'results'/ref['field_file'],dtype='<f4').reshape(ref['shape']);ref_ids=ref['components']['Battery']['indices']
fig,axs=plt.subplots(1,2,figsize=(7,7),layout='constrained')
for ax,case in zip(axs,['small','large']):
    c=v['cases'][case];field=np.fromfile(R/'results'/c['field_file'],dtype='<f4').reshape(c['shape']);nodes=json.loads((R/'results'/(case+'_mesh_nodes.json')).read_text());ids=c['components']['Battery']['indices'];assert ids==ref_ids
    assert all(nodes[i]['centroid_mm']==ref_nodes[i]['centroid_mm'] and nodes[i]['capacity_J_K']==ref_nodes[i]['capacity_J_K'] for i in ids)
    surface=next(x for x in json.loads((R/'results'/c['surface_file']).read_text()) if x['id']=='Battery');delta={i:float(field[20,i])-float(ref_field[20,i]) for i in ids};polys=[];values=[]
    for tri in surface['triangles']:
        pts=np.array([surface['vertices'][i] for i in tri]);cross=(pts[1,0]-pts[0,0])*(pts[2,1]-pts[0,1])-(pts[1,1]-pts[0,1])*(pts[2,0]-pts[0,0])
        if abs(cross)<1e-10 or abs(pts[0,2]-6.2)>1e-5:continue
        polys.append(pts[:,:2]);values.append(delta[surface['node_indices'][tri[0]]])
    pc=PolyCollection(polys,array=np.array(values),cmap='coolwarm',clim=(-.5,.5),edgecolors='none',antialiased=False);ax.add_collection(pc);ax.set(xlim=(4,44),ylim=(25,107),xlabel='x (mm)',ylabel='y (mm)',title=c['label']+'\nminus 30 × 50 mm reference');ax.set_aspect('equal')
fig.colorbar(pc,ax=axs,label='Pointwise cell temperature change at 600 s (K)',shrink=.8);fig.suptitle('Blue = cooler · Red = warmer · same coordinates and difference scale');fig.savefig(R/'review/battery_difference.png',dpi=170);plt.close(fig)
