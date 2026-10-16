"""Stage 07: adhesive thickness study. Run with Python + requirements.txt.
Preserved base/pad/spreader modules reproduce the Stage 06 largest-spreader reference exactly.
"""
from pathlib import Path
import json,csv,shutil,zipfile,time
import numpy as np
from shapely.geometry import box
import run_spreader_study as S
B=S.B;P=S.P;ROOT=Path(__file__).resolve().parents[1]
SWEEP=json.loads((ROOT/'source/sweep.json').read_text());CASES=SWEEP['cases']
def make(case,spacing):
    t=CASES[case]['adhesive_thickness_mm'];S.SHEET=box(*SWEEP['footprint_mm']);S.G['footprint_global_mm']=SWEEP['footprint_mm'];S.A['thickness_mm']=t
    S.GTOP=7-t;S.GBOTTOM=S.GTOP-S.G['thickness_mm'];S.PAD_T=S.GBOTTOM-4.8
    m=S.SpreaderModel(spacing,S.G['kxy_W_mK']);m.adhesive_t=t;m.pad_t=S.PAD_T;return m
def diagnostic(spacing):
    m=make('reference',spacing);old=list(m.links);changed=[];delta=(.100-.025)*.001/(2*S.A['k_W_mK'])
    for a,b,g,label in old:
        if label in ['graphite_to_adhesive','adhesive_to_back_cover']:
            area=m.nodes[a]['poly'].intersection(m.nodes[b]['poly']).area*1e-6
            changed.append((a,b,area/(area/g+delta),label))
        else:changed.append((a,b,g,label))
    m.links=changed;m.reassemble()
    assert [x for x in old if x[3] not in ['graphite_to_adhesive','adhesive_to_back_cover']]==[x for x in m.links if x[3] not in ['graphite_to_adhesive','adhesive_to_back_cover']]
    return m
def metrics(m,r):
    idx=m.groups['BackGlass'];areas=np.array([m.nodes[i]['poly'].area for i in idx]);t=r['peak'][idx,2];peak=idx[np.argmax(t)]
    return {'area_above_40C_mm2':float(areas[t>40].sum()),'area_above_45C_mm2':float(areas[t>45].sum()),'mean_C':float(np.average(t,weights=areas)),'max_C':float(t.max()),'peak_center_mm':[m.nodes[peak]['x'],m.nodes[peak]['y']]}
def exports(configs):
    out=ROOT/'results';scratch=out/'_scratch';scratch.mkdir(exist_ok=True);old_shapes=dict(B.SHAPES);oldroot=B.ROOT;viewer={'metadata':None,'components':None,'cases':{}};folders={}
    for case,(m,r) in configs.items():
        work=scratch/case;(work/'results').mkdir(parents=True,exist_ok=True);B.ROOT=work
        for name,l in m.layers.items():B.SHAPES[name]=(l['shape'],l['z'],l['t'])
        B.save_fields(m,r);B.SHAPES.clear();B.SHAPES.update(old_shapes);folder=work/'results';folders[case]=folder
        v=json.loads((folder/'viewer_data.json').read_text());entry=v['cases']['combined'];entry.update(pad_thickness_mm=m.pad_t,adhesive_thickness_mm=m.adhesive_t,label=CASES[case]['label'],components=v['components'],mesh_nodes=m.n,surface_file=case+'_thermal_surface_mesh.json',assembly_file=case+'_assembly_mesh.json',field_file=case+'_temperature_float32.bin')
        viewer['cases'][case]=entry
        if case=='reference':viewer['metadata']=v['metadata'];viewer['components']=v['components']
        shutil.copyfile(folder/'combined_temperature_float32.bin',out/entry['field_file'])
        for fn in ['thermal_surface_mesh.json','mesh_nodes.json','network_links.csv','heat_source_nodes.csv']:shutil.copyfile(folder/fn,out/(case+'_'+fn))
    B.ROOT=oldroot
    viewer['metadata'].update(description=SWEEP['basis'],reference_case='reference',geometry_note='Fixed50x70mm footprint; adhesive25/50/100µm; pad2.075/2.050/2.000mm; film/graphite elevations vary by case; outer cover fixed.')
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
    with zipfile.ZipFile(out/'adhesive_comparison_vtk.zip','w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('README.txt','Open reference/transient.pvd, medium/transient.pvd, thick/transient.pvd. Layer mid-surfaces in meters. CellData Temperature_C, ThermalNode_ID, Component_ID. Repeated visualization triangles share thermal nodes: do not sum their capacities or source powers. All cases have independent meshes; no through-thickness field or exterior skin prediction.\n')
        for case,folder in folders.items():
            with zipfile.ZipFile(folder/'coupled_vtk.zip') as src:
                for n in src.namelist():
                    if n.startswith('combined/'):z.writestr(case+'/'+n.split('/',1)[1],src.read(n))
    shutil.rmtree(scratch)
def figures(configs):
    from plot_adhesive import figures
    figures(configs,B,ROOT,CASES)
def main():
    start=time.perf_counter();configs={};summary={'study':'Stage 07 adhesive thickness comparison','sweep':SWEEP,'components':{},'cases':{},'verification':{},'physical_validation':False}
    for case in CASES:
        print('Solve '+case,flush=True);m=make(case,P['grid_mm']);r=m.run(P['dt_s']);configs[case]=(m,r)
        if case=='reference':assert np.array_equal(r['field'][:,:,2].astype('<f4'),np.fromfile(ROOT/'source/reference_stage06_temperature_float32.bin',dtype='<f4').reshape((-1,m.n)))
        fine=make(case,P['grid_mm']/2);rf=fine.run(P['dt_s'],False);rt=m.run(P['dt_s']/2,False)
        comp=S.stats(m,r);summary['components'][case]=comp;sheet=box(*CASES[case]['footprint_mm'])
        summary['cases'][case]={'label':CASES[case]['label'],'footprint_mm':CASES[case]['footprint_mm'],'area_mm2':sheet.area,'cell_overlap_mm2':sheet.intersection(B.SHAPES['Battery'][0]).area,'graphite_mass_g':sheet.area*.1*1e-6*1800,'adhesive_mass_g':sheet.area*m.adhesive_t*1e-6*1200,'adhesive_thickness_mm':m.adhesive_t,'pad_thickness_mm':m.pad_t,'graphite_bottom_z_mm':7-m.adhesive_t-.1,'adhesive_bulk_Rpp_m2K_W':m.adhesive_t*.001/.2,'bond_Rpp_m2K_W':m.adhesive_t*.001/.2+.0002,'nodes':m.n,'fine_nodes':fine.n,'cover':metrics(m,r),'flows_at_600s_W':{k:float(v[2]) for k,v in r['flows'][20].items() if 'graphite' in k or 'adhesive_to_back' in k},'energy_at_600s_J':{'input':2250.,'stored':r['energy'][20][2],'ambient_loss':r['energy'][20][5]},'capacity_J_K':float(m.cap.sum())}
        check={'energy_residual_J':r['energy_error_J'],'source_superposition_error_K':float(np.max(abs(r['field'][:,:,2]-r['field'][:,:,0]-r['field'][:,:,1]+25))),'refinement':{n:{'coarse_min_mean_max_C':B.stats(m,r['peak'][:,2],n),'fine_min_mean_max_C':B.stats(fine,rf['peak'][:,2],n),'time_min_mean_max_C':B.stats(m,rt['peak'][:,2],n)} for n in m.groups}}
        check['largest_mesh_max_difference_K']=max(abs(v['coarse_min_mean_max_C'][2]-v['fine_min_mean_max_C'][2]) for v in check['refinement'].values());check['largest_time_max_difference_K']=max(abs(v['coarse_min_mean_max_C'][2]-v['time_min_mean_max_C'][2]) for v in check['refinement'].values());assert check['largest_mesh_max_difference_K']<1 and check['largest_time_max_difference_K']<.1;assert check['source_superposition_error_K']<1e-7
        summary['verification'][case]=check;del fine,rf,rt
    base=configs['reference'][0]
    for case,(m,r) in configs.items():
        assert np.array_equal(m.Q[:9710],base.Q[:9710]) and np.array_equal(m.loss[:9710],base.loss[:9710]) and np.array_equal(m.cap[:9683],base.cap[:9683]);assert np.all(m.Q[9710:]==0) and np.all(m.loss[9710:]==0)
    summary['verification']['stage06_reference_byte_identical']=True;summary['verification']['original_base_capacities_sources_sinks_unchanged']=True;summary['verification']['effect_refinement']={}
    for case in ['medium','thick']:
        summary['verification']['effect_refinement'][case]={}
        for name,metric in [('BackGlass',2),('Battery',1),('Battery',2)]:
            a=summary['verification'][case]['refinement'][name];b=summary['verification']['reference']['refinement'][name];coarse=a['coarse_min_mean_max_C'][metric]-b['coarse_min_mean_max_C'][metric];fine=a['fine_min_mean_max_C'][metric]-b['fine_min_mean_max_C'][metric]
            summary['verification']['effect_refinement'][case][name+('_mean' if metric==1 else '_max')]={'coarse_change_K':coarse,'fine_change_K':fine,'change_in_effect_K':abs(fine-coarse)}
    print('Resistance-only diagnostic on reference stack…',flush=True)
    md=diagnostic(P['grid_mm']);rd=md.run(P['dt_s']);mref,rref=configs['reference']
    assert np.array_equal(md.cap,mref.cap) and np.array_equal(md.Q,mref.Q) and np.array_equal(md.loss,mref.loss)
    fd=diagnostic(P['grid_mm']/2);fr=fd.run(P['dt_s'],False);tr=md.run(P['dt_s']/2,False)
    summary['diagnostic']={'description':SWEEP['diagnostic'],'components':S.stats(md,rd),'cover':metrics(md,rd),'energy_error_J':rd['energy_error_J'],'identical_reference_geometry_capacity_sources_sinks':True,'only_two_vertical_adhesive_half_resistances_changed':True,'refinement':{n:{'coarse_min_mean_max_C':B.stats(md,rd['peak'][:,2],n),'fine_min_mean_max_C':B.stats(fd,fr['peak'][:,2],n),'time_min_mean_max_C':B.stats(md,tr['peak'][:,2],n)} for n in md.groups}}
    assert max(abs(v['coarse_min_mean_max_C'][2]-v['fine_min_mean_max_C'][2]) for v in summary['diagnostic']['refinement'].values())<1
    assert max(abs(v['coarse_min_mean_max_C'][2]-v['time_min_mean_max_C'][2]) for v in summary['diagnostic']['refinement'].values())<.1
    # Keep the diagnostic inspectable without presenting it as another physical CAD assembly.
    with (ROOT/'results/resistance_diagnostic_history.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['time_s','component','min_C','mean_C','max_C'])
        for tt,field in zip(rd['times'],rd['field']):
            for name in md.groups:w.writerow([tt,name,*B.stats(md,field[:,2],name)])
    figures(configs);exports(configs);summary['runtime_s']=time.perf_counter()-start;(ROOT/'results/summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary['cases'],indent=2),flush=True)
if __name__=='__main__':main()
