"""Stage 03: conservative layered finite volumes + lumped IC packages.
Run: python source/run_model.py [--quick]  (--quick skips refinement checks).
Geometry in mm; all conductance/capacity calculations in SI. No commercial solver.
All materials, contacts and sources are teaching assumptions; see inputs.json.
"""
from pathlib import Path
import json, csv, zipfile, sys, platform, time
import numpy as np
import scipy
from scipy.sparse import coo_matrix, diags
from scipy.sparse.linalg import factorized
import shapely
from shapely.geometry import box, Polygon, Point
from shapely.ops import unary_union, triangulate
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

ROOT=Path(__file__).resolve().parents[1]
P=json.loads((ROOT/'source/inputs.json').read_text())
D=json.loads((ROOT/'source/cad_parameters.json').read_text())
for folder in ['results','review','evidence']: (ROOT/folder).mkdir(exist_ok=True)
TA=P['ambient_C']; ON=P['heat_off_s']; END=P['end_s']; CONTACT=P['contacts']
assert P['initial_C']==TA
def rounded(x,y,w,h,r):
    return box(x+r,y+r,x+w-r,y+h-r).buffer(r,resolution=24)
inner=rounded(1.4,1.4,68.8,144.8,8.6)
outer=rounded(0,0,71.6,147.6,10)
main=Polygon(D['mainboard_outline'])
for x,y in D['board_holes']: main=main.difference(Point(x,y).buffer(.7,resolution=16))
SHAPES={
 'Battery':(box(6,27,42,105),1.75,4.45),
 'MainPCB':(main,2.8,.8), 'RFPCB':(box(46,39,65,59),4.2,.6),
 'Midplate':(inner,1,.6), 'Frame':(outer.difference(inner),0,7.8),
 'Display':(inner,0,1), 'BackGlass':(inner,7,.8)
}
CHIPS={c['id']:c for c in D['chips']}
def chip_shape(c): return box(c['x'],c['y'],c['x']+c['length'],c['y']+c['width'])

class Model:
    def __init__(self,spacing):
        self.spacing=spacing;self.nodes=[];self.layers={};self.links=[]
        self.cap=[];self.loss=[];self.groups={};self.contact_info={}
        for name,(shape,z,t) in SHAPES.items():
            prop=P['properties'][name];grid={};idx=[]
            for j in range(int(np.ceil(147.6/spacing))):
                for i in range(int(np.ceil(71.6/spacing))):
                    poly=shape.intersection(box(i*spacing,j*spacing,(i+1)*spacing,(j+1)*spacing)).buffer(0)
                    if poly.area<1e-7: continue
                    n=len(self.nodes);grid[i,j]=n;idx.append(n)
                    self.nodes.append({'part':name,'poly':poly,'x':poly.centroid.x,'y':poly.centroid.y,'z':z,'t':t,'i':i,'j':j})
                    self.cap.append(poly.area*t*1e-9*prop['rho_kg_m3']*prop['cp_J_kgK']);self.loss.append(0.)
            self.layers[name]={'grid':grid,'indices':np.array(idx),'shape':shape,'z':z,'t':t}
            self.groups[name]=np.array(idx)
            for (i,j),a in grid.items():
                for ij,axis in [((i+1,j),'x'),((i,j+1),'y')]:
                    if ij not in grid:continue
                    b=grid[ij];na,nb=self.nodes[a],self.nodes[b]
                    edge=na['poly'].boundary.intersection(nb['poly'].boundary).length
                    if edge<1e-7:continue
                    distance=abs(na[axis]-nb[axis])*1e-3
                    self.link(a,b,prop['kxy_W_mK']*t*1e-3*edge*1e-3/distance,'inplane:'+name)
        for name,c in CHIPS.items():
            n=len(self.nodes);self.groups[name]=np.array([n]);poly=chip_shape(c)
            self.nodes.append({'part':name,'poly':poly,'x':poly.centroid.x,'y':poly.centroid.y,'z':c['z'],'t':c['height'],'i':-1,'j':-1})
            prop=P['properties']['package'];self.cap.append(poly.area*c['height']*1e-9*prop['rho_kg_m3']*prop['cp_J_kgK']);self.loss.append(0.)
        rc=CONTACT['area_resistance_m2K_W']
        def half(name):return SHAPES[name][2]*.0005/P['properties'][name]['kz_W_mK']
        # Every link is inserted once with identical opposite contributions.
        self.overlap('Battery','Midplate',half('Battery')+half('Midplate')+CONTACT['adhesive_thickness_mm']*.001/CONTACT['adhesive_k_W_mK']+rc,'cell_adhesive')
        self.overlap('Display','Midplate',half('Display')+half('Midplate')+rc,'display_laminate')
        pedestal=box(48,92,62,106)
        mounts=unary_union([Point(x,y).buffer(1.35,resolution=16).difference(Point(x,y).buffer(.7,resolution=16)) for x,y in D['board_holes']])
        self.overlap('MainPCB','Midplate',half('MainPCB')+half('Midplate')+CONTACT['underboard_TIM_thickness_mm']*.001/CONTACT['underboard_TIM_k_W_mK']+CONTACT['pedestal_height_mm']*.001/CONTACT['pedestal_k_W_mK']+rc,'pcb_pedestal_TIM',pedestal)
        self.overlap('MainPCB','Midplate',half('MainPCB')+half('Midplate')+CONTACT['support_height_mm']*.001/CONTACT['support_k_W_mK']+rc,'pcb_supports',mounts)
        gapR=1/(CONTACT['air_k_W_mK']/.0012+CONTACT['linearized_internal_radiation_W_m2K'])
        self.overlap('MainPCB','Midplate',half('MainPCB')+half('Midplate')+gapR,'pcb_plate_gap',main.difference(unary_union([pedestal,mounts])))
        posts=unary_union([Point(x,y).buffer(CONTACT['rf_post_radius_mm'],resolution=16) for x,y in [(46.6,40),(64.2,40),(46.6,57.5),(64.2,57.5)]])
        self.overlap('RFPCB','MainPCB',half('RFPCB')+half('MainPCB')+.0006/CONTACT['support_k_W_mK']+rc,'rf_posts',posts)
        gapR=1/(CONTACT['air_k_W_mK']/.0006+CONTACT['linearized_internal_radiation_W_m2K'])
        self.overlap('RFPCB','MainPCB',half('RFPCB')+half('MainPCB')+gapR,'rf_board_gap',SHAPES['RFPCB'][0].difference(posts))
        # Chip footprints interrupt the board-to-back gap; RF interrupts the main board.
        occupied=unary_union([SHAPES['Battery'][0],main])
        self.gap('Midplate',5.4,inner.difference(occupied),'plate_back_gap')
        self.gap('Battery',.8,SHAPES['Battery'][0],'cell_back_gap')
        main_chips=unary_union([chip_shape(c) for c in CHIPS.values() if c['z']==3.6])
        rf_chips=unary_union([chip_shape(c) for c in CHIPS.values() if c['z']==4.8])
        self.gap('MainPCB',3.4,main.difference(unary_union([main_chips,SHAPES['RFPCB'][0]])),'main_back_gap')
        self.gap('RFPCB',2.2,SHAPES['RFPCB'][0].difference(rf_chips),'rf_back_gap')
        for name,c in CHIPS.items():
            board='MainPCB' if c['z']==3.6 else 'RFPCB'
            self.package_contact(name,board,c['height']*.0005/P['properties']['package']['kz_W_mK']+half(board)+rc,'package_board:'+name)
            gap=(7-c['z']-c['height'])*.001
            r=1/(CONTACT['air_k_W_mK']/gap+CONTACT['linearized_internal_radiation_W_m2K'])
            self.package_contact(name,'BackGlass',c['height']*.0005/P['properties']['package']['kz_W_mK']+half('BackGlass')+r,'package_back:'+name)
        # Panels meet the frame around their perimeter; edge contact uses panel thickness.
        for name in ['Midplate','Display','BackGlass']: self.edge_contact(name,'Frame',rc)
        h=P['external_effective_h_W_m2K']
        for name in ['Display','BackGlass']:
            for a in self.groups[name]:self.loss[a]+=h*self.nodes[a]['poly'].area*1e-6
        # Outer vertical side and exposed top/bottom rim. No ambient sink on buried layers.
        for a in self.groups['Frame']:
            poly=self.nodes[a]['poly'];edge=poly.boundary.intersection(outer.boundary).length
            self.loss[a]+=h*(edge*.0078*.001+2*poly.area*1e-6)
        self.cap=np.array(self.cap);self.loss=np.array(self.loss);self.n=len(self.cap)
        row=[];col=[];val=[]
        for a,b,g,label in self.links:
            row.extend([a,a,b,b]);col.extend([a,b,a,b]);val.extend([g,-g,-g,g])
        self.K=coo_matrix((val,(row,col)),shape=(self.n,self.n)).tocsc()+diags(self.loss,format='csc')
        sym=self.K-self.K.T
        assert sym.nnz==0 or np.max(abs(sym.data))<1e-12
        assert np.max(abs(np.asarray(self.K.sum(axis=1)).ravel()-self.loss))<1e-10
        assert np.min(self.cap)>0
        # Three prescribed source vectors, on until precisely 600 s.
        battery=np.zeros(self.n);idx=self.groups['Battery'];areas=np.array([self.nodes[a]['poly'].area for a in idx])
        patch=box(*P['cell_patch_global_mm']);patch_area=np.array([self.nodes[a]['poly'].intersection(patch).area for a in idx])
        fraction=P['cell_localized_fraction']
        battery[idx]=P['cell_heat_W']*((1-fraction)*areas/areas.sum()+fraction*patch_area/patch_area.sum())
        electronics=np.zeros(self.n)
        for name,c in CHIPS.items(): electronics[self.groups[name][0]]=c['illustrative_power_W']*P['electronics_heat_scale_from_CAD']
        self.Q=np.column_stack([battery*c['battery_scale']+electronics*c['electronics_scale'] for c in P['cases'].values()])
        assert np.allclose(self.Q.sum(axis=0),[2,1.75,3.75])
        self.internal_ambient_W_K=float(self.loss[np.r_[self.groups['Battery'],self.groups['MainPCB'],self.groups['RFPCB'],*[self.groups[n] for n in CHIPS]]].sum())
        assert self.internal_ambient_W_K==0
    def link(self,a,b,g,label):
        if g<=0:return
        self.links.append((a,b,float(g),label))
        self.contact_info.setdefault(label,{'links':0,'sum_conductance_W_K':0.})
        self.contact_info[label]['links']+=1;self.contact_info[label]['sum_conductance_W_K']+=float(g)
    def overlap(self,left,right,resistance,label,region=None):
        agrid=self.layers[left]['grid'];bgrid=self.layers[right]['grid']
        for ij,a in agrid.items():
            if ij not in bgrid:continue
            b=bgrid[ij];poly=self.nodes[a]['poly'].intersection(self.nodes[b]['poly'])
            if region is not None:poly=poly.intersection(region)
            self.link(a,b,poly.area*1e-6/resistance,label)
    def package_contact(self,name,layer,resistance,label):
        a=self.groups[name][0];poly=self.nodes[a]['poly']
        for b in self.groups[layer]:
            area=poly.intersection(self.nodes[b]['poly']).area
            self.link(a,b,area*1e-6/resistance,label)
    def gap(self,left,gap_mm,region,label):
        r=1/(CONTACT['air_k_W_mK']/(gap_mm*.001)+CONTACT['linearized_internal_radiation_W_m2K'])
        r+=SHAPES[left][2]*.0005/P['properties'][left]['kz_W_mK']+.0004/P['properties']['BackGlass']['kz_W_mK']
        self.overlap(left,'BackGlass',r,label,region)
    def edge_contact(self,left,right,rc):
        for (i,j),a in self.layers[left]['grid'].items():
            na=self.nodes[a]
            for di in [-1,0,1]:
                for dj in [-1,0,1]:
                    b=self.layers[right]['grid'].get((i+di,j+dj))
                    if b is None:continue
                    nb=self.nodes[b];edge=na['poly'].boundary.intersection(nb['poly'].boundary)
                    if edge.length<1e-7:continue
                    d=np.hypot(na['x']-nb['x'],na['y']-nb['y'])*.001
                    r=d/2/P['properties'][left]['kxy_W_mK']+d/2/P['properties'][right]['kxy_W_mK']+rc
                    self.link(a,b,edge.length*na['t']*1e-6/r,'edge:'+left)
    def run(self,dt,store=True):
        solve=factorized(diags(self.cap,format='csc')+dt*self.K)
        state=np.zeros((self.n,3));lost=np.zeros(3);error=0.;frames=[];times=[];flows=[];energy=[];peak=None;max_seen=np.zeros(3)
        for step in range(round(END/dt)+1):
            tt=step*dt
            error=max(error,float(np.max(abs(np.minimum(tt,ON)*self.Q.sum(axis=0)-self.cap@state-lost))))
            max_seen=np.maximum(max_seen,state.max(axis=0))
            if abs(tt-ON)<1e-7:peak=state.copy()
            if store and abs(tt/P['viewer_interval_s']-round(tt/P['viewer_interval_s']))<1e-7:
                frames.append(state.copy()+TA);times.append(tt);energy.append([*self.cap@state,*lost])
                flow={}
                for a,b,g,label in self.links:
                    if label.startswith('inplane:'):continue
                    flow[label]=flow.get(label,np.zeros(3))+g*(state[a]-state[b])
                flows.append(flow)
            if step==round(END/dt):break
            source=self.Q if tt<ON-1e-9 else 0
            state=solve(self.cap[:,None]*state+dt*source)
            lost+=dt*self.loss@state
        assert error<1e-5,(error,self.n)
        assert state.min()>-1e-8 and peak.min()>-1e-8
        return dict(field=np.array(frames),times=times,peak=peak+TA,final=state+TA,energy_error_J=error,flows=flows,energy=energy,max_seen_C=max_seen+TA)

def stats(m,field,name):
    idx=m.groups[name];x=field[idx];weights=m.cap[idx]
    return [float(x.min()),float(np.average(x,weights=weights)),float(x.max())]

def triangles(poly):
    result=[]
    for tri in triangulate(poly):
        if poly.covers(tri):result.append(list(tri.exterior.coords)[:3])
    assert abs(sum(Polygon(t).area for t in result)-poly.area)<max(1e-5,poly.area*1e-6)
    return result

def save_fields(m,r):
    # Thermal surface mesh: flat FV cell colors, no invented within-cell gradient.
    surface=[];points=[];conn=[];node_ids=[];part_ids=[]
    names=list(m.groups)
    for name in names:
        verts=[];tris=[];lookup=[];grid_vertices=[]
        for a in m.groups[name]:
            n=m.nodes[a];poly=n['poly'];z=n['z'];t=n['t']
            for tri in triangles(poly):
                pts=[[x,y,z+t/2] for x,y in tri];start=len(points);points.extend(pts);conn.append([start,start+1,start+2]);node_ids.append(int(a));part_ids.append(names.index(name))
                for zz in [z,z+t]:
                    start=len(verts);verts.extend([[x,y,zz] for x,y in tri]);tris.append([start,start+1,start+2]);lookup.extend([int(a)]*3)
            geoms=list(poly.geoms) if poly.geom_type=='MultiPolygon' else [poly]
            for geom in geoms:
                for ring in [geom.exterior,*geom.interiors]:
                    coords=list(ring.coords)
                    for (x,y),(xx,yy) in zip(coords,coords[1:]):
                        grid_vertices.extend([[x,y,z+t+.02],[xx,yy,z+t+.02]])
                        from shapely.geometry import LineString
                        edge=LineString([(x,y),(xx,yy)])
                        if name in SHAPES and edge.intersection(SHAPES[name][0].boundary.buffer(1e-7)).length<edge.length*.99:continue
                        start=len(verts);verts.extend([[x,y,z],[xx,yy,z],[xx,yy,z+t],[x,y,z+t]]);lookup.extend([int(a)]*4);tris.extend([[start,start+1,start+2],[start,start+2,start+3]])
        if name in SHAPES:surface.append({'id':name,'vertices':np.round(verts,6).tolist(),'triangles':tris,'node_indices':lookup,'grid_vertices':np.round(grid_vertices,6).tolist(),'kind':'spatial layer'})
    (ROOT/'results/thermal_surface_mesh.json').write_text(json.dumps(surface,separators=(',',':')))
    viewer={'metadata':{'times_s':r['times'],'ambient_C':TA,'heat_off_s':ON,'mesh_nodes':m.n,'spatial_cells':sum(len(m.groups[n]) for n in SHAPES),'lumped_packages':len(CHIPS),'grid_mm':m.spacing,'shared_color_range_C':[25,75],'component_order':names,'description':P['scope']},'components':{},'cases':{}}
    for name in names:
        viewer['components'][name]={'indices':m.groups[name].tolist(),'weights_J_K':m.cap[m.groups[name]].tolist(),'kind':'One lumped package temperature' if name in CHIPS else 'Spatial finite-volume layer; uniform through thickness'}
    for k,(name,c) in enumerate(P['cases'].items()):
        filename=name+'_temperature_float32.bin'
        r['field'][:,:,k].astype('<f4').tofile(ROOT/'results'/filename)
        viewer['cases'][name]={'label':c['label'],'power_W':float(m.Q[:,k].sum()),'field_file':filename,'encoding':'little-endian float32, row-major [time,node]','shape':[len(r['times']),m.n]}
    (ROOT/'results/viewer_data.json').write_text(json.dumps(viewer,separators=(',',':')))
    (ROOT/'results/mesh_nodes.json').write_text(json.dumps([{'id':i,'component':n['part'],'centroid_mm':[n['x'],n['y'],n['z']+n['t']/2],'area_mm2':n['poly'].area,'thickness_mm':n['t'],'capacity_J_K':m.cap[i],'ambient_conductance_W_K':m.loss[i]} for i,n in enumerate(m.nodes)],separators=(',',':')))
    with (ROOT/'results/network_links.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['from_node','to_node','conductance_W_K','path']);w.writerows(m.links)
    with (ROOT/'results/heat_source_nodes.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['node','component',*[name+'_W_during_heating' for name in P['cases']]])
        w.writerows([[i,n['part'],*m.Q[i]] for i,n in enumerate(m.nodes)])
    with (ROOT/'results/component_history.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['case','time_s','component','min_C','mean_C','max_C'])
        for k,name in enumerate(P['cases']):
            for frame,tt in zip(r['field'],r['times']):
                for part in names:w.writerow([name,tt,part,*stats(m,frame[:,k],part)])
    with (ROOT/'results/heat_flows.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['case','time_s','path','positive_from_component','positive_to_component','heat_flow_W'])
        direction={label:(m.nodes[a]['part'],m.nodes[b]['part']) for a,b,g,label in m.links}
        for k,name in enumerate(P['cases']):
            for flow,tt in zip(r['flows'],r['times']):
                for path,value in flow.items():w.writerow([name,tt,path,*direction[path],float(value[k])])
    with (ROOT/'results/energy_history.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['case','time_s','heat_input_J','stored_J','ambient_loss_J','residual_J'])
        for k,name in enumerate(P['cases']):
            for e,tt in zip(r['energy'],r['times']):
                inp=float(m.Q[:,k].sum())*min(tt,ON);w.writerow([name,tt,inp,e[k],e[k+3],inp-e[k]-e[k+3]])
    # VTK triangles in assembly coordinates (meters), one dataset per case/time.
    def array(vals):return ' '.join(str(x) for x in vals)
    head=f'''<?xml version="1.0"?><VTKFile type="UnstructuredGrid" version="0.1" byte_order="LittleEndian"><UnstructuredGrid><Piece NumberOfPoints="{len(points)}" NumberOfCells="{len(conn)}"><Points><DataArray type="Float64" NumberOfComponents="3" format="ascii">{array(np.array(points).ravel()*.001)}</DataArray></Points><Cells><DataArray type="Int32" Name="connectivity" format="ascii">{array(np.array(conn).ravel())}</DataArray><DataArray type="Int32" Name="offsets" format="ascii">{array(np.arange(1,len(conn)+1)*3)}</DataArray><DataArray type="UInt8" Name="types" format="ascii">{array([5]*len(conn))}</DataArray></Cells><CellData Scalars="Temperature_C"><DataArray type="Int32" Name="Component_ID" format="ascii">{array(part_ids)}</DataArray><DataArray type="Int32" Name="ThermalNode_ID" format="ascii">{array(node_ids)}</DataArray>'''
    with zipfile.ZipFile(ROOT/'results/coupled_vtk.zip','w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('README.txt','Layer mid-surfaces in assembly coordinates, units meters. CellData temperatures are FV node values. Multiple triangles can share a ThermalNode_ID; do not sum source power per triangle. Component_ID order: '+', '.join(names)+'. Chip packages are lumped; through-thickness gradients are not resolved. Open each transient.pvd in ParaView.\n')
        for k,name in enumerate(P['cases']):
            datasets=[]
            for frame,tt in zip(r['field'],r['times']):
                if tt%P['vtk_interval_s']!=0:continue
                filename=f't_{int(tt):04d}.vtu';vals=frame[np.array(node_ids),k]
                xml=head+f'<DataArray type="Float64" Name="Temperature_C" format="ascii">{array(np.round(vals,6))}</DataArray></CellData></Piece></UnstructuredGrid></VTKFile>'
                z.writestr(name+'/'+filename,xml);datasets.append(f'<DataSet timestep="{tt:g}" group="" part="0" file="{filename}"/>')
            z.writestr(name+'/transient.pvd','<?xml version="1.0"?><VTKFile type="Collection" version="0.1" byte_order="LittleEndian"><Collection>'+''.join(datasets)+'</Collection></VTKFile>')

def figures(m,r):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})
    f,axs=plt.subplots(1,5,figsize=(14,5),layout='constrained')
    for ax,name in zip(axs,['Battery','MainPCB','RFPCB','Midplate','BackGlass']):
        polys=[];vals=[]
        for a in m.groups[name]:
            for tri in triangles(m.nodes[a]['poly']):polys.append(tri);vals.append(r['peak'][a,2])
        pc=PolyCollection(polys,array=np.array(vals),cmap='inferno',clim=(25,75),edgecolors='none',antialiased=False);ax.add_collection(pc);ax.autoscale_view();ax.set_aspect('equal');ax.set(title=name,xlabel='x (mm)');ax.set_ylabel('y (mm)')
    f.colorbar(pc,ax=axs,label='Temperature at heat-off (°C)',shrink=.8);f.suptitle('Stage 03 · Coupled product · 2 W battery + 1.75 W electronics · shared 25–75 °C scale')
    f.savefig(ROOT/'review/component_maps.png',dpi=170);plt.close(f)
    f,axs=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
    for k,(name,c) in enumerate(P['cases'].items()):
        idx=m.groups['Battery'];avg=np.average(r['field'][:,idx,k],axis=1,weights=m.cap[idx]);axs[0].plot(np.array(r['times'])/60,avg,label=c['label'],lw=2)
    for name in ['Battery','MainPCB','RFPCB','U01','U06','Midplate','BackGlass']:
        idx=m.groups[name];vals=r['field'][:,idx,2].max(axis=1);axs[1].plot(np.array(r['times'])/60,vals,label=name,lw=1.7)
    axs[0].set(title='Unpowered battery warms from electronics',ylabel='Cell mean temperature (°C)');axs[1].set(title='Combined case: component maximum',ylabel='Maximum temperature (°C)')
    for ax in axs:ax.set(xlabel='Time (min)',xlim=(0,30));ax.axvline(10,ls=':',c='gray');ax.grid(alpha=.2);ax.legend(fontsize=8,frameon=False)
    f.savefig(ROOT/'review/coupled_histories.png',dpi=170);plt.close(f)

def main_run():
    start=time.perf_counter();print('Building 2 mm layered model…',flush=True)
    m=Model(P['grid_mm']);print(f'Solving {m.n} nodes, {len(m.links)} links, three source cases…',flush=True)
    r=m.run(P['dt_s']);superposition=float(np.max(abs((r['field'][:,:,2]-TA)-(r['field'][:,:,0]-TA)-(r['field'][:,:,1]-TA))))
    assert superposition<1e-7
    # Independent two-node exact matrix-exponential solution tests link signs,
    # storage and implicit-Euler time integration in a simple limiting network.
    ca,cb,g,h=3.,5.,2.,.4;K=np.array([[g+h,-g],[-g,g+h]]);cap=np.array([ca,cb]);dt=.001
    from scipy.linalg import expm
    exact=np.linalg.solve(K,np.array([1.,0.]));expected=exact-expm(-np.diag(1/cap)@K*2)@exact
    state=np.zeros(2);advance=np.linalg.inv(np.diag(cap)+dt*K)
    for _ in range(2000):state=advance@(cap*state+dt*np.array([1.,0.]))
    benchmark_error=float(np.max(abs(state-expected)));assert benchmark_error<1e-4
    refinement={}
    if '--quick' not in sys.argv:
        print('Checking 1 s time step…',flush=True);rt=m.run(P['dt_s']/2,False)
        print('Checking 1 mm spatial grid…',flush=True);mf=Model(P['grid_mm']/2);rf=mf.run(P['dt_s'],False)
        for name in m.groups:
            coarse=stats(m,r['peak'][:,2],name);fine=stats(mf,rf['peak'][:,2],name);timefine=stats(m,rt['peak'][:,2],name)
            refinement[name]={'coarse_max_C':coarse[2],'fine_max_C':fine[2],'mesh_max_difference_K':abs(coarse[2]-fine[2]),'mesh_mean_difference_K':abs(coarse[1]-fine[1]),'time_step_max_difference_K':abs(coarse[2]-timefine[2])}
        assert max(v['time_step_max_difference_K'] for v in refinement.values())<.15
        assert max(v['mesh_max_difference_K'] for v in refinement.values())<2.0
        refinement['fine_nodes']=mf.n
    summary={'model':'Layered spatial FVM + lumped packages, backward Euler; not a 3D CFD/FEA solve','assumptions':P['scope'],'thermal_nodes':m.n,'spatial_cells':sum(len(m.groups[n]) for n in SHAPES),'package_nodes':len(CHIPS),'pairwise_links':len(m.links),'dt_s':P['dt_s'],'grid_mm':m.spacing,'capacity_J_K':float(m.cap.sum()),'external_conductance_W_K':float(m.loss.sum()),'direct_internal_to_ambient_W_K':m.internal_ambient_W_K,'energy_max_residual_J':r['energy_error_J'],'superposition_error_K':superposition,'two_node_exact_solution_error_K':benchmark_error,'refinement':refinement,'components':{},'contact_paths':m.contact_info,'physical_validation':False,'software':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'shapely':shapely.__version__}}
    for k,(case,c) in enumerate(P['cases'].items()):
        summary['components'][case]={name:{'at_600s_min_C':stats(m,r['peak'][:,k],name)[0],'at_600s_mean_C':stats(m,r['peak'][:,k],name)[1],'at_600s_max_C':stats(m,r['peak'][:,k],name)[2],'max_over_saved_times_C':float(r['field'][:,m.groups[name],k].max()),'final_mean_C':stats(m,r['final'][:,k],name)[1]} for name in m.groups}
    save_fields(m,r);figures(m,r);summary['runtime_s']=time.perf_counter()-start
    (ROOT/'results/summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k not in ['contact_paths','components','refinement']},indent=2),flush=True)
    print(json.dumps(summary['components']['combined'],indent=2),flush=True)

if __name__=='__main__':main_run()
