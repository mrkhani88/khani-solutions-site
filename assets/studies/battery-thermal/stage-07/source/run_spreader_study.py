"""Stage 05: pad-only reference versus bonded anisotropic graphite, plus control.
Run: python source/run_spreader_study.py. Free/open-source Python dependencies only.
base_model.py and pad_model.py preserve the earlier solvers byte for byte.
"""
from pathlib import Path
import json,csv,shutil,zipfile,time
import numpy as np
from scipy.sparse import coo_matrix,diags
from shapely.geometry import box
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import pad_model as M
B=M.B;P=B.P;ROOT=Path(__file__).resolve().parents[1];G=P['graphite'];A=P['spreader_adhesive'];TA=B.TA
SHEET=box(*G['footprint_global_mm']);GTOP=7-A['thickness_mm'];GBOTTOM=GTOP-G['thickness_mm'];PAD_T=GBOTTOM-4.8
for folder in ['results','review','evidence']:(ROOT/folder).mkdir(exist_ok=True)

class SpreaderModel(M.PaddedModel):
    def __init__(self,spacing,kxy):
        super().__init__(spacing)
        old_n=self.n;self.kxy=kxy
        assert SHEET.covers(M.FOOTPRINT) and PAD_T>0
        cap=list(self.cap);loss=list(self.loss)
        old_pad_t=P['rf_pad']['installed_thickness_mm']
        for i in self.groups['RFPad']:
            self.nodes[i]['t']=PAD_T;cap[i]*=PAD_T/old_pad_t
        self.layers['RFPad']['t']=PAD_T
        # Fit the added sheet/adhesive without moving the exterior cover.
        old_board_pad_R=.0003/.5+old_pad_t*.0005/P['rf_pad']['k_W_mK']+P['rf_pad']['contact_resistance_each_m2K_W']
        new_board_pad_R=.0003/.5+PAD_T*.0005/P['rf_pad']['k_W_mK']+P['rf_pad']['contact_resistance_each_m2K_W']
        modified=[]
        for a,b,g,label in self.links:
            if label=='inplane:RFPad':g*=PAD_T/old_pad_t
            elif label=='RFPCB_to_pad':g*=old_board_pad_R/new_board_pad_R
            modified.append((a,b,g,label))
        self.links=modified
        self.add_layer('GraphiteSpreader',GBOTTOM,G['thickness_mm'],kxy,G['rho_kg_m3'],G['cp_J_kgK'],cap,loss)
        self.add_layer('SpreaderAdhesive',GTOP,A['thickness_mm'],A['k_W_mK'],A['rho_kg_m3'],A['cp_J_kgK'],cap,loss)
        # Every old internal->back-cover gap is partitioned by the sheet footprint.
        # Retain uncovered paths; redirect covered paths onto graphite, at its
        # actual lower surface. Perimeter contacts of the back glass stay intact.
        main_chips=B.unary_union([B.chip_shape(c) for c in B.CHIPS.values() if c['z']==3.6])
        rf_chips=B.unary_union([B.chip_shape(c) for c in B.CHIPS.values() if c['z']==4.8])
        regions={'plate_back_gap':B.inner.difference(B.unary_union([B.SHAPES['Battery'][0],B.main])),
                 'cell_back_gap':B.SHAPES['Battery'][0],
                 'main_back_gap':B.main.difference(B.unary_union([main_chips,B.SHAPES['RFPCB'][0]])),
                 'rf_back_gap':B.SHAPES['RFPCB'][0].difference(B.unary_union([rf_chips,M.FOOTPRINT]))}
        kept=[];redirected_area={}
        for a,b,g,label in self.links:
            is_back=self.nodes[b]['part']=='BackGlass'
            redirect=is_back and (label.endswith('_back_gap') or label.startswith('package_back:') or label=='pad_to_back_cover')
            if not redirect:kept.append((a,b,g,label));continue
            na,nb=self.nodes[a],self.nodes[b];poly=na['poly'].intersection(nb['poly'])
            if label in regions:poly=poly.intersection(regions[label])
            assert poly.area>0
            covered=poly.intersection(SHEET)
            fraction=covered.area/poly.area
            if fraction<1:kept.append((a,b,g*(1-fraction),label))
            if covered.area<1e-8:continue
            if na['part']=='RFPad':
                resistance=PAD_T*.0005/P['rf_pad']['k_W_mK']+P['rf_pad']['contact_resistance_each_m2K_W']+G['thickness_mm']*.0005/G['kz_W_mK']
            else:
                prop=P['properties'].get(na['part'],P['properties']['package']);gap=(GBOTTOM-na['z']-na['t'])*.001
                assert gap>0,(na['part'],gap)
                resistance=na['t']*.0005/prop['kz_W_mK']+1/(P['contacts']['air_k_W_mK']/gap+P['contacts']['linearized_internal_radiation_W_m2K'])+G['thickness_mm']*.0005/G['kz_W_mK']
            target=self.layers['GraphiteSpreader']['grid'].get((nb['i'],nb['j']))
            assert target is not None
            new_label=na['part']+'_to_graphite'
            kept.append((a,target,covered.area*1e-6/resistance,new_label))
            redirected_area[na['part']]=redirected_area.get(na['part'],0.)+covered.area
        self.links=kept;self.redirected_area_mm2=redirected_area
        assert abs(sum(redirected_area.values())-SHEET.area)<1e-6,'Covered top-surface areas must partition the sheet footprint exactly once'
        rc=A['contact_resistance_each_m2K_W']
        self.overlap('GraphiteSpreader','SpreaderAdhesive',G['thickness_mm']*.0005/G['kz_W_mK']+A['thickness_mm']*.0005/A['k_W_mK']+rc,'graphite_to_adhesive',SHEET)
        self.overlap('SpreaderAdhesive','BackGlass',A['thickness_mm']*.0005/A['k_W_mK']+.0004/P['properties']['BackGlass']['kz_W_mK']+rc,'adhesive_to_back_cover',SHEET)
        self.cap=np.array(cap);self.loss=np.array(loss);self.n=len(cap);self.Q=np.vstack([self.Q,np.zeros((self.n-old_n,3))]);self.reassemble()
    def add_layer(self,name,z,t,kxy,rho,cp,cap,loss):
        grid={};indices=[];d=self.spacing
        for j in range(int(np.ceil(147.6/d))):
            for i in range(int(np.ceil(71.6/d))):
                poly=SHEET.intersection(box(i*d,j*d,(i+1)*d,(j+1)*d)).buffer(0)
                if poly.area<1e-7:continue
                a=len(self.nodes);grid[i,j]=a;indices.append(a)
                self.nodes.append({'part':name,'poly':poly,'x':poly.centroid.x,'y':poly.centroid.y,'z':z,'t':t,'i':i,'j':j});cap.append(poly.area*t*1e-9*rho*cp);loss.append(0.)
        self.groups[name]=np.array(indices);self.layers[name]={'grid':grid,'indices':np.array(indices),'shape':SHEET,'z':z,'t':t}
        for (i,j),a in grid.items():
            for ij,axis in [((i+1,j),'x'),((i,j+1),'y')]:
                if ij not in grid:continue
                b=grid[ij];na,nb=self.nodes[a],self.nodes[b];edge=na['poly'].boundary.intersection(nb['poly'].boundary).length
                self.links.append((a,b,kxy*t*.001*edge*.001/(abs(na[axis]-nb[axis])*.001),'inplane:'+name))
    def reassemble(self):
        row=[];col=[];val=[];self.contact_info={}
        for a,b,g,label in self.links:
            assert g>0
            row.extend([a,a,b,b]);col.extend([a,b,a,b]);val.extend([g,-g,-g,g])
            info=self.contact_info.setdefault(label,{'links':0,'sum_conductance_W_K':0.});info['links']+=1;info['sum_conductance_W_K']+=g
        self.K=coo_matrix((val,(row,col)),shape=(self.n,self.n)).tocsc()+diags(self.loss,format='csc')
        assert np.max(abs(np.asarray(self.K.sum(axis=1)).ravel()-self.loss))<1e-10
        assert np.max(abs((self.K-self.K.T).data),initial=0)<1e-10

def stats(m,r):return M.component_summary(m,r)
def exports(configurations):
    work=ROOT/'results/_export_scratch';work.mkdir(exist_ok=True);outputs={};base_shapes=dict(B.SHAPES)
    for case,(m,r) in configurations.items():
        root=work/case;(root/'results').mkdir(parents=True,exist_ok=True);B.ROOT=root
        for name,l in m.layers.items():B.SHAPES[name]=(l['shape'],l['z'],l['t'])
        B.save_fields(m,r);B.SHAPES.clear();B.SHAPES.update(base_shapes);outputs[case]=root/'results'
    B.ROOT=ROOT;out=ROOT/'results';after=outputs['after'];viewer=json.loads((after/'viewer_data.json').read_text());viewer['cases']={}
    viewer['metadata'].update(description=P['comparison'],new_components=['GraphiteSpreader','SpreaderAdhesive'],geometry_note='Before pad 2.2 mm; after/control pad 2.075 mm plus .1 mm graphite and .025 mm adhesive. Exterior fixed.')
    for name in ['thermal_surface_mesh.json','mesh_nodes.json']:shutil.copyfile(after/name,out/name)
    before_surfaces=json.loads((outputs['before']/'thermal_surface_mesh.json').read_text());before_pad=next(x for x in before_surfaces if x['id']=='RFPad')
    (out/'before_pad_mesh.json').write_text(json.dumps(before_pad,separators=(',',':')))
    labels={'before':'Pad only · Stage 04','after':'Pad + graphite spreader','control':'Control · low lateral conductivity'}
    n=configurations['after'][0].n
    for case,(m,r) in configurations.items():
        field=np.full((len(r['times']),n),np.nan,dtype='<f4');field[:,:m.n]=r['field'][:,:,2];fn=case+'_temperature_float32.bin';field.tofile(out/fn)
        viewer['cases'][case]={'label':labels[case],'power_W':3.75,'field_file':fn,'encoding':'little-endian float32 [time,node]; absent layers are NaN in pad-only case','shape':list(field.shape),'active_nodes':m.n}
        for filename in ['network_links.csv','heat_source_nodes.csv','mesh_nodes.json']:shutil.copyfile(outputs[case]/filename,out/(case+'_'+filename))
    for name in ['GraphiteSpreader','SpreaderAdhesive']:viewer['components'][name]['active_cases']=['after','control']
    viewer['components']['RFPad']['weights_by_case']={case:m.cap[m.groups['RFPad']].tolist() for case,(m,r) in configurations.items()}
    (out/'viewer_data.json').write_text(json.dumps(viewer,separators=(',',':')))
    for filename in ['component_history.csv','heat_flows.csv','energy_history.csv']:
        with (out/filename).open('w',newline='') as f:
            wr=csv.writer(f);header=None
            for case,folder in outputs.items():
                with (folder/filename).open() as src:
                    rows=csv.reader(src);h=next(rows)
                    if header is None:wr.writerow(h);header=h
                    for row in rows:
                        if row[0]=='combined':row[0]=case;wr.writerow(row)
    with zipfile.ZipFile(out/'spreader_comparison_vtk.zip','w',zipfile.ZIP_DEFLATED) as target:
        target.writestr('README.txt','Open before/transient.pvd, after/transient.pvd or control/transient.pvd. Coordinates meters; layer mid-surfaces, not 3D volume elements. Temperature_C CellData; ThermalNode_ID repeats on visualization triangles. Component order: Battery,MainPCB,RFPCB,Midplate,Frame,Display,BackGlass,U01,U02,U03,U04,U05,U06,U07,RFPad. After/control append GraphiteSpreader,SpreaderAdhesive. Pad thickness changes with installed stack. No exterior skin or junction gradient resolved.\n')
        for case,folder in outputs.items():
            with zipfile.ZipFile(folder/'coupled_vtk.zip') as src:
                for name in src.namelist():
                    if name.startswith('combined/'):target.writestr(case+'/'+name.split('/',1)[1],src.read(name))
    shutil.rmtree(work)

def figures(configurations):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'savefig.facecolor':'white','axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(1,3,figsize=(13,4.5),layout='constrained')
    for ax,name in zip(axs,['BackGlass','RFPCB','Battery']):
        for case,(m,r) in configurations.items():
            vals=r['field'][:,m.groups[name],2].max(axis=1);ax.plot(np.array(r['times'])/60,vals,ls={'before':'--','after':'-','control':':'}[case],lw=2,label={'before':'Pad only','after':'Graphite 800/5','control':'Lateral-k control 5/5'}[case])
        ax.set(title=name+' layer maximum',xlabel='Time (min)',ylabel='Temperature (°C)',xlim=(0,30));ax.axvline(10,ls=':',c='gray');ax.grid(alpha=.2);ax.legend(frameon=False,fontsize=8)
    fig.suptitle('Stage 05 · Same 3.75 W heat input and exterior cooling');fig.savefig(ROOT/'review/spreader_histories.png',dpi=170);plt.close(fig)
    fig,axs=plt.subplots(1,3,figsize=(11,6),layout='constrained')
    for ax,(case,(m,r)) in zip(axs,configurations.items()):
        polys=[];vals=[]
        for a in m.groups['BackGlass']:
            for tri in B.triangles(m.nodes[a]['poly']):polys.append(tri);vals.append(r['peak'][a,2])
        pc=PolyCollection(polys,array=np.array(vals),cmap='inferno',clim=(25,75),edgecolors='none',antialiased=False);ax.add_collection(pc);ax.autoscale_view();ax.set_aspect('equal');ax.set(title={'before':'Pad only','after':'Graphite spreader','control':'Low lateral-k control'}[case],xlabel='x (mm)',ylabel='y (mm)')
        from matplotlib.patches import Rectangle
        x0,y0,x1,y1=G['footprint_global_mm'];ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,ec='#48c8d5',ls='--',lw=1.3))
    fig.colorbar(pc,ax=axs,label='Back-cover layer temperature at 600 s (°C)',shrink=.75);fig.suptitle('Cover maps · shared 25–75 °C range · cyan = spreader footprint');fig.savefig(ROOT/'review/cover_comparison.png',dpi=170);plt.close(fig)

def main():
    start=time.perf_counter();print('Reproducing Stage 04 pad-only reference…',flush=True);m0=M.PaddedModel(P['grid_mm']);r0=m0.run(P['dt_s'])
    frozen=np.fromfile(ROOT/'source/reference_stage04_pad_temperature_float32.bin',dtype='<f4').reshape((-1,m0.n));assert np.array_equal(frozen,r0['field'][:,:,2].astype('<f4'))
    print('Solving bonded graphite and matched lateral-conductivity control…',flush=True)
    m1=SpreaderModel(P['grid_mm'],G['kxy_W_mK']);r1=m1.run(P['dt_s']);mc=SpreaderModel(P['grid_mm'],G['diagnostic_kxy_W_mK']);rc=mc.run(P['dt_s'])
    assert np.array_equal(m0.Q,m1.Q[:m0.n]) and np.array_equal(m0.loss,m1.loss[:m0.n]) and np.all(m1.loss[m0.n:]==0)
    unchanged=[i for i in range(m0.n) if m0.nodes[i]['part']!='RFPad'];assert np.array_equal(m0.cap[unchanged],m1.cap[unchanged])
    assert np.array_equal(m1.cap,mc.cap) and np.array_equal(m1.Q,mc.Q) and np.array_equal(m1.loss,mc.loss)
    assert [v for v in m1.links if v[3]!='inplane:GraphiteSpreader']==[v for v in mc.links if v[3]!='inplane:GraphiteSpreader']
    print('Grid/time verification for spreader and lateral-k control…',flush=True);refinement={};fine_data={}
    for case,m,r,k in [('after',m1,r1,G['kxy_W_mK']),('control',mc,rc,G['diagnostic_kxy_W_mK'])]:
        rt=m.run(P['dt_s']/2,False);mf=SpreaderModel(P['grid_mm']/2,k);rf=mf.run(P['dt_s'],False);fine_data[case]=(mf,rf)
        refinement[case]={name:{'coarse_max_C':B.stats(m,r['peak'][:,2],name)[2],'fine_max_C':B.stats(mf,rf['peak'][:,2],name)[2],'mesh_max_difference_K':abs(B.stats(m,r['peak'][:,2],name)[2]-B.stats(mf,rf['peak'][:,2],name)[2]),'time_max_difference_K':abs(B.stats(m,r['peak'][:,2],name)[2]-B.stats(m,rt['peak'][:,2],name)[2])} for name in m.groups}
        assert max(x['mesh_max_difference_K'] for x in refinement[case].values())<1
        assert max(x['time_max_difference_K'] for x in refinement[case].values())<.1
    configurations={'before':(m0,r0),'after':(m1,r1),'control':(mc,rc)}
    summary={'study':'Stage 05 graphite spreader','basis':P['basis'],'comparison':P['comparison'],'graphite':G,'adhesive':A,'installed_pad_thickness_mm':PAD_T,'graphite_bottom_z_mm':GBOTTOM,'graphite_top_z_mm':GTOP,'area_mm2':SHEET.area,'before_nodes':m0.n,'after_nodes':m1.n,'fine_nodes':fine_data['after'][0].n,'components':{},'cover_metrics':{},'heat_flow_at_600s_W':{},'energy_at_600s_J':{},'verification':{'baseline_byte_identical_to_stage04':True,'sources_and_external_sinks_unchanged':True,'old_capacities_unchanged_except_trimmed_pad':True,'control_changes_only_graphite_inplane_conductivity':True,'refinement':refinement},'physical_validation':False}
    for case,(m,r) in configurations.items():
        summary['components'][case]=stats(m,r);idx=m.groups['BackGlass'];areas=np.array([m.nodes[i]['poly'].area for i in idx]);temp=r['peak'][idx,2]
        summary['cover_metrics'][case]={'area_above_45C_mm2':float(areas[temp>45].sum()),'area_above_40C_mm2':float(areas[temp>40].sum()),'max_minus_min_K':float(temp.max()-temp.min()),'standard_deviation_K':float(np.sqrt(np.average((temp-np.average(temp,weights=areas))**2,weights=areas))),'sheet_footprint_mean_C':float(np.average(temp,weights=[m.nodes[i]['poly'].intersection(SHEET).area for i in idx]))}
        summary['heat_flow_at_600s_W'][case]={k:float(v[2]) for k,v in r['flows'][20].items() if 'graphite' in k or 'adhesive_to_back' in k or 'pad_to_back' in k}
        summary['energy_at_600s_J'][case]={'input':2250.,'stored':r['energy'][20][2],'ambient_loss':r['energy'][20][5]}
        summary['verification'][case+'_energy_residual_J']=r['energy_error_J'];summary['verification'][case+'_superposition_error_K']=float(np.max(abs((r['field'][:,:,2]-25)-(r['field'][:,:,0]-25)-(r['field'][:,:,1]-25))))
        assert summary['verification'][case+'_superposition_error_K']<1e-7
    summary['verification']['effect_refinement']={}
    # Reconstruct the fine pad reference for paired changes, rather than subtracting
    # unsigned refinement differences from earlier stages.
    mbf=M.PaddedModel(P['grid_mm']/2);rbf=mbf.run(P['dt_s'],False)
    for name in m0.groups:
        coarse=summary['components']['after'][name]['at_600s_max_C']-summary['components']['before'][name]['at_600s_max_C'];fine=refinement['after'][name]['fine_max_C']-B.stats(mbf,rbf['peak'][:,2],name)[2]
        summary['verification']['effect_refinement'][name]={'coarse_change_K':coarse,'fine_change_K':fine,'change_in_effect_K':abs(fine-coarse)}
    summary['mass_and_capacity']={'trimmed_pad_mass_g':M.FOOTPRINT.area*PAD_T*1e-6*P['rf_pad']['rho_kg_m3'],'graphite_mass_g':SHEET.area*G['thickness_mm']*1e-6*G['rho_kg_m3'],'adhesive_mass_g':SHEET.area*A['thickness_mm']*1e-6*A['rho_kg_m3'],'added_net_capacity_J_K':float(m1.cap.sum()-m0.cap.sum())}
    figures(configurations);exports(configurations);summary['runtime_s']=time.perf_counter()-start
    (ROOT/'results/summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k not in ['components','verification']},indent=2));print(json.dumps({c:{n:round(v[n]['at_600s_max_C'],4) for n in ['BackGlass','RFPCB','U07','Battery']} for c,v in summary['components'].items()},indent=2),flush=True)

if __name__=='__main__':main()
