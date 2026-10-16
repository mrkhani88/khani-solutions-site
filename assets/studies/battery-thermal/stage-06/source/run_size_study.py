"""Stage 06: nested footprint study. Run with Python + requirements.txt.
Preserved base/pad/spreader modules reproduce the Stage 05 reference exactly.
"""
from pathlib import Path
import json,csv,shutil,zipfile,time
import numpy as np
from shapely.geometry import box
import run_spreader_study as S
B=S.B;P=S.P;ROOT=Path(__file__).resolve().parents[1]
SWEEP=json.loads((ROOT/'source/sweep.json').read_text());CASES=SWEEP['cases']
def make(case,spacing):
    footprint=CASES[case]['footprint_mm'];S.SHEET=box(*footprint);S.G['footprint_global_mm']=footprint
    return S.SpreaderModel(spacing,S.G['kxy_W_mK'])
def metrics(m,r):
    idx=m.groups['BackGlass'];areas=np.array([m.nodes[i]['poly'].area for i in idx]);t=r['peak'][idx,2];peak=idx[np.argmax(t)]
    return {'area_above_40C_mm2':float(areas[t>40].sum()),'area_above_45C_mm2':float(areas[t>45].sum()),'mean_C':float(np.average(t,weights=areas)),'max_C':float(t.max()),'peak_center_mm':[m.nodes[peak]['x'],m.nodes[peak]['y']]}
def exports(configs):
    out=ROOT/'results';scratch=out/'_scratch';scratch.mkdir(exist_ok=True);old_shapes=dict(B.SHAPES);oldroot=B.ROOT;viewer={'metadata':None,'components':None,'cases':{}};folders={}
    for case,(m,r) in configs.items():
        work=scratch/case;(work/'results').mkdir(parents=True,exist_ok=True);B.ROOT=work
        for name,l in m.layers.items():B.SHAPES[name]=(l['shape'],l['z'],l['t'])
        B.save_fields(m,r);B.SHAPES.clear();B.SHAPES.update(old_shapes);folder=work/'results';folders[case]=folder
        v=json.loads((folder/'viewer_data.json').read_text());entry=v['cases']['combined'];entry.update(label=CASES[case]['label'],components=v['components'],mesh_nodes=m.n,surface_file=case+'_thermal_surface_mesh.json',assembly_file=case+'_assembly_mesh.json',field_file=case+'_temperature_float32.bin')
        viewer['cases'][case]=entry
        if case=='reference':viewer['metadata']=v['metadata'];viewer['components']=v['components']
        shutil.copyfile(folder/'combined_temperature_float32.bin',out/entry['field_file'])
        for fn in ['thermal_surface_mesh.json','mesh_nodes.json','network_links.csv','heat_source_nodes.csv']:shutil.copyfile(folder/fn,out/(case+'_'+fn))
    B.ROOT=oldroot
    viewer['metadata'].update(description=SWEEP['basis'],reference_case='reference',geometry_note='Case-specific sheet/adhesive geometry, node counts, capacities and temperature indexing; pad 2.075 mm in every size.')
    (out/'viewer_data.json').write_text(json.dumps(viewer,separators=(',',':')))
    for fn in ['component_history.csv','heat_flows.csv','energy_history.csv']:
        with (out/fn).open('w',newline='') as f:
            w=csv.writer(f);first=True
            for case,folder in folders.items():
                with (folder/fn).open() as src:
                    rows=csv.reader(src);h=next(rows)
                    if first:w.writerow(h);first=False
                    for row in rows:
                        if row[0]=='combined':row[0]=case;w.writerow(row)
    with zipfile.ZipFile(out/'size_comparison_vtk.zip','w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('README.txt','Open small/transient.pvd, reference/transient.pvd, large/transient.pvd. Layer mid-surfaces in meters. CellData Temperature_C, ThermalNode_ID, Component_ID. Repeated visualization triangles share thermal nodes: do not sum their capacities or source powers. All cases have independent meshes; no through-thickness field or exterior skin prediction.\n')
        for case,folder in folders.items():
            with zipfile.ZipFile(folder/'coupled_vtk.zip') as src:
                for n in src.namelist():
                    if n.startswith('combined/'):z.writestr(case+'/'+n.split('/',1)[1],src.read(n))
    shutil.rmtree(scratch)
def figures(configs):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.patches import Rectangle
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'savefig.facecolor':'white','axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(2,3,figsize=(11,9),layout='constrained')
    for col,(case,(m,r)) in enumerate(configs.items()):
        for row,name in enumerate(['BackGlass','Battery']):
            ax=axs[row,col];polys=[];values=[]
            for i in m.groups[name]:
                for tri in B.triangles(m.nodes[i]['poly']):polys.append(tri);values.append(r['peak'][i,2])
            pc=PolyCollection(polys,array=np.array(values),cmap='inferno',clim=(25,75),edgecolors='none',antialiased=False);ax.add_collection(pc)
            x,y,xx,yy=CASES[case]['footprint_mm'];ax.add_patch(Rectangle((x,y),xx-x,yy-y,fill=False,ec='#20bbc9',ls='--',lw=1.5));ax.set(xlim=(0,71.6),ylim=(0,147.6),title=CASES[case]['label']+'\n'+name+' max '+format(max(values),'.2f')+' °C',xlabel='x (mm)',ylabel='y (mm)');ax.set_aspect('equal')
    fig.colorbar(pc,ax=axs,label='Layer temperature at 600 s (°C)',shrink=.8);fig.suptitle('Stage 06 · cyan = sheet footprint · same position scale and 25–75 °C color range');fig.savefig(ROOT/'review/size_maps.png',dpi=160);plt.close(fig)
    fig,axs=plt.subplots(1,3,figsize=(13,4.3),layout='constrained')
    for ax,(name,metric) in zip(axs,[('BackGlass','max'),('Battery','mean'),('Battery','max')]):
        for case,(m,r) in configs.items():
            vals=[B.stats(m,f[:,2],name)[1 if metric=='mean' else 2] for f in r['field']];ax.plot(np.array(r['times'])/60,vals,lw=2,label=CASES[case]['label'])
        ax.set(title=name+' '+metric,xlabel='Time (min)',ylabel='Temperature (°C)',xlim=(0,30));ax.axvline(10,c='gray',ls=':');ax.grid(alpha=.2);ax.legend(frameon=False,fontsize=8)
    fig.suptitle('Same heat pulse: 3.75 W for 10 min, then sources off');fig.savefig(ROOT/'review/size_histories.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(6,7),layout='constrained')
    for name in ['Battery','RFPCB','BackGlass']:
        poly=B.SHAPES[name][0];gs=list(poly.geoms) if poly.geom_type=='MultiPolygon' else [poly]
        for g in gs:ax.fill(*g.exterior.xy,alpha=.12,label=name)
    for (case,c),color in zip(CASES.items(),['#b34440','#167e93','#7b3eb5']):
        x,y,xx,yy=c['footprint_mm'];ax.add_patch(Rectangle((x,y),xx-x,yy-y,fill=False,ec=color,lw=2,label=c['label']))
    ax.add_patch(Rectangle((27,84),12,18,fill=False,ec='orange',hatch='///',label='Prescribed cell heat patch'));ax.plot(68,30,'ko');ax.annotate('Fixed corner (68, 30)',(68,30),(-110,-25),textcoords='offset points');ax.set(xlim=(-3,75),ylim=(-3,151),xlabel='x (mm)',ylabel='y (mm)',title='Nested sheets grow toward the battery');ax.set_aspect('equal');ax.legend(fontsize=8,loc='upper left');fig.savefig(ROOT/'review/size_layout.png',dpi=170);plt.close(fig)
def main():
    start=time.perf_counter();configs={};summary={'study':'Stage 06 graphite size / coverage comparison','sweep':SWEEP,'components':{},'cases':{},'verification':{},'physical_validation':False}
    for case in CASES:
        print('Solve '+case,flush=True);m=make(case,P['grid_mm']);r=m.run(P['dt_s']);configs[case]=(m,r)
        if case=='reference':assert np.array_equal(r['field'][:,:,2].astype('<f4'),np.fromfile(ROOT/'source/reference_stage05_temperature_float32.bin',dtype='<f4').reshape((-1,m.n)))
        fine=make(case,P['grid_mm']/2);rf=fine.run(P['dt_s'],False);rt=m.run(P['dt_s']/2,False)
        comp=S.stats(m,r);summary['components'][case]=comp;sheet=box(*CASES[case]['footprint_mm'])
        summary['cases'][case]={'label':CASES[case]['label'],'footprint_mm':CASES[case]['footprint_mm'],'area_mm2':sheet.area,'cell_overlap_mm2':sheet.intersection(B.SHAPES['Battery'][0]).area,'graphite_mass_g':sheet.area*.1*1e-6*1800,'adhesive_mass_g':sheet.area*.025*1e-6*1200,'nodes':m.n,'fine_nodes':fine.n,'cover':metrics(m,r),'flows_at_600s_W':{k:float(v[2]) for k,v in r['flows'][20].items() if 'graphite' in k or 'adhesive_to_back' in k},'energy_at_600s_J':{'input':2250.,'stored':r['energy'][20][2],'ambient_loss':r['energy'][20][5]},'capacity_J_K':float(m.cap.sum())}
        check={'energy_residual_J':r['energy_error_J'],'source_superposition_error_K':float(np.max(abs(r['field'][:,:,2]-r['field'][:,:,0]-r['field'][:,:,1]+25))),'refinement':{n:{'coarse_min_mean_max_C':B.stats(m,r['peak'][:,2],n),'fine_min_mean_max_C':B.stats(fine,rf['peak'][:,2],n),'time_min_mean_max_C':B.stats(m,rt['peak'][:,2],n)} for n in m.groups}}
        check['largest_mesh_max_difference_K']=max(abs(v['coarse_min_mean_max_C'][2]-v['fine_min_mean_max_C'][2]) for v in check['refinement'].values());check['largest_time_max_difference_K']=max(abs(v['coarse_min_mean_max_C'][2]-v['time_min_mean_max_C'][2]) for v in check['refinement'].values());assert check['largest_mesh_max_difference_K']<1 and check['largest_time_max_difference_K']<.1;assert check['source_superposition_error_K']<1e-7
        summary['verification'][case]=check;del fine,rf,rt
    base=configs['reference'][0]
    for case,(m,r) in configs.items():
        assert np.array_equal(m.Q[:9710],base.Q[:9710]) and np.array_equal(m.loss[:9710],base.loss[:9710]) and np.array_equal(m.cap[:9710],base.cap[:9710]);assert np.all(m.Q[9710:]==0) and np.all(m.loss[9710:]==0)
    summary['verification']['stage05_reference_byte_identical']=True;summary['verification']['base_capacities_sources_sinks_unchanged']=True;summary['verification']['effect_refinement']={}
    for case in ['small','large']:
        summary['verification']['effect_refinement'][case]={}
        for name,metric in [('BackGlass',2),('Battery',1),('Battery',2)]:
            a=summary['verification'][case]['refinement'][name];b=summary['verification']['reference']['refinement'][name];coarse=a['coarse_min_mean_max_C'][metric]-b['coarse_min_mean_max_C'][metric];fine=a['fine_min_mean_max_C'][metric]-b['fine_min_mean_max_C'][metric]
            summary['verification']['effect_refinement'][case][name+('_mean' if metric==1 else '_max')]={'coarse_change_K':coarse,'fine_change_K':fine,'change_in_effect_K':abs(fine-coarse)}
    figures(configs);exports(configs);summary['runtime_s']=time.perf_counter()-start;(ROOT/'results/summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary['cases'],indent=2),flush=True)
if __name__=='__main__':main()
