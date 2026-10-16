"""Controlled Stage 04 comparison. Run: python source/run_pad_study.py
base_model.py is the unchanged Stage 03 solver. No commercial dependencies.
Both configurations use the same prescribed 3.75 W combined heat load.
"""
from pathlib import Path
import json,csv,shutil,zipfile,hashlib,time
import numpy as np
from scipy.sparse import coo_matrix,diags
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from shapely.geometry import box
import base_model as B

ROOT=Path(__file__).resolve().parents[1];P=B.P;PAD=P['rf_pad'];TA=B.TA
FOOTPRINT=box(*PAD['footprint_global_mm'])
for d in ['results','review','evidence']:(ROOT/d).mkdir(exist_ok=True)

class PaddedModel(B.Model):
    def __init__(self,spacing):
        super().__init__(spacing)
        # Remove the covered portion of the original RF board-to-back gap.
        # Retain its uncovered portion; never put a pad in parallel with air
        # over the same physical area.
        replacement=[];removed=0.
        for a,b,g,label in self.links:
            if label=='rf_back_gap':
                overlap=self.nodes[a]['poly'].intersection(self.nodes[b]['poly'])
                covered=overlap.intersection(FOOTPRINT).area
                old=g;g*=max(0,1-covered/overlap.area);removed+=old-g
            if g>1e-16:replacement.append((a,b,g,label))
        self.links=replacement
        cap=list(self.cap);loss=list(self.loss);grid={};indices=[]
        thickness=PAD['installed_thickness_mm'];z=PAD['bottom_z_mm'];k=PAD['k_W_mK']
        for j in range(int(np.ceil(147.6/spacing))):
            for i in range(int(np.ceil(71.6/spacing))):
                poly=FOOTPRINT.intersection(box(i*spacing,j*spacing,(i+1)*spacing,(j+1)*spacing)).buffer(0)
                if poly.area<1e-7:continue
                a=len(self.nodes);grid[i,j]=a;indices.append(a)
                self.nodes.append({'part':'RFPad','poly':poly,'x':poly.centroid.x,'y':poly.centroid.y,'z':z,'t':thickness,'i':i,'j':j})
                cap.append(poly.area*thickness*1e-9*PAD['rho_kg_m3']*PAD['cp_J_kgK']);loss.append(0.)
        self.groups['RFPad']=np.array(indices)
        self.layers['RFPad']={'grid':grid,'indices':np.array(indices),'shape':FOOTPRINT,'z':z,'t':thickness}
        for (i,j),a in grid.items():
            for ij,axis in [((i+1,j),'x'),((i,j+1),'y')]:
                if ij not in grid:continue
                b=grid[ij];na,nb=self.nodes[a],self.nodes[b]
                edge=na['poly'].boundary.intersection(nb['poly'].boundary).length
                self.link(a,b,k*thickness*1e-3*edge*1e-3/(abs(na[axis]-nb[axis])*1e-3),'inplane:RFPad')
        rpad=thickness*.0005/k;rc=PAD['contact_resistance_each_m2K_W']
        self.overlap('RFPCB','RFPad',.0003/P['properties']['RFPCB']['kz_W_mK']+rpad+rc,'RFPCB_to_pad',FOOTPRINT)
        self.overlap('RFPad','BackGlass',rpad+.0004/P['properties']['BackGlass']['kz_W_mK']+rc,'pad_to_back_cover',FOOTPRINT)
        nbase=self.n;self.cap=np.array(cap);self.loss=np.array(loss);self.n=len(cap)
        self.Q=np.vstack([self.Q,np.zeros((self.n-nbase,3))])
        row=[];col=[];val=[];self.contact_info={}
        for a,b,g,label in self.links:
            row.extend([a,a,b,b]);col.extend([a,b,a,b]);val.extend([g,-g,-g,g])
            info=self.contact_info.setdefault(label,{'links':0,'sum_conductance_W_K':0.});info['links']+=1;info['sum_conductance_W_K']+=g
        self.K=coo_matrix((val,(row,col)),shape=(self.n,self.n)).tocsc()+diags(self.loss,format='csc')
        assert np.max(abs(np.asarray(self.K.sum(axis=1)).ravel()-self.loss))<1e-10
        assert np.max(abs((self.K-self.K.T).data),initial=0)<1e-10
        self.removed_gap_conductance_W_K=removed
        assert abs(sum(self.nodes[a]['poly'].area for a in indices)-FOOTPRINT.area)<1e-8
        # Geometry proof: the pad sits entirely on clear RF PCB area.
        chips=B.unary_union([B.chip_shape(c) for c in B.CHIPS.values() if c['z']==4.8])
        assert FOOTPRINT.intersection(chips).area==0
        assert abs(FOOTPRINT.intersection(B.SHAPES['RFPCB'][0]).area-FOOTPRINT.area)<1e-8
        assert abs(z-4.8)<1e-12 and abs(z+thickness-7)<1e-12

def component_summary(m,r):
    return {name:{'at_600s_min_C':B.stats(m,r['peak'][:,2],name)[0],'at_600s_mean_C':B.stats(m,r['peak'][:,2],name)[1],'at_600s_max_C':B.stats(m,r['peak'][:,2],name)[2],'max_over_saved_times_C':float(r['field'][:,m.groups[name],2].max()),'at_1800s_mean_C':B.stats(m,r['final'][:,2],name)[1]} for name in m.groups}

def plot(m0,r0,m1,r1):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'savefig.facecolor':'white','axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(1,3,figsize=(13,4.4),layout='constrained')
    for ax,name in zip(axs,['RFPCB','U07','BackGlass']):
        for m,r,label,style in [(m0,r0,'Before · air gap','--'),(m1,r1,'After · thermal pad','-')]:
            vals=r['field'][:,m.groups[name],2].max(axis=1);ax.plot(np.array(r['times'])/60,vals,ls=style,lw=2,label=label)
        ax.set(title=name+' maximum',xlabel='Time (min)',ylabel='Temperature (°C)',xlim=(0,30));ax.axvline(10,c='gray',ls=':');ax.grid(alpha=.2);ax.legend(frameon=False,fontsize=8)
    fig.suptitle('Stage 04 · Same 3.75 W heat input; change only the RF pad design');fig.savefig(ROOT/'review/before_after_histories.png',dpi=170);plt.close(fig)
    fig,axs=plt.subplots(2,3,figsize=(11,8),layout='constrained')
    for row,(m,r,label) in enumerate([(m0,r0,'Before'),(m1,r1,'After')]):
        for ax,name in zip(axs[row],['RFPCB','MainPCB','BackGlass']):
            polys=[];vals=[]
            for a in m.groups[name]:
                for tri in B.triangles(m.nodes[a]['poly']):polys.append(tri);vals.append(r['peak'][a,2])
            pc=PolyCollection(polys,array=np.array(vals),cmap='inferno',clim=(25,75),edgecolors='none',antialiased=False);ax.add_collection(pc);ax.autoscale_view();ax.set_aspect('equal');ax.set(title=label+' · '+name,xlabel='x (mm)',ylabel='y (mm)')
            if name in ['RFPCB','BackGlass']:
                from matplotlib.patches import Rectangle
                x0,y0,x1,y1=PAD['footprint_global_mm'];ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,edgecolor='#45d1d1',lw=1.5,ls='--'))
    fig.colorbar(pc,ax=axs,label='Layer temperature at 600 s (°C)',shrink=.75);fig.suptitle('Before / after on the same 25–75 °C scale · cyan outline = pad footprint')
    fig.savefig(ROOT/'review/before_after_maps.png',dpi=170);plt.close(fig)

def export(m0,r0,m1,r1):
    work=ROOT/'results/_export_scratch';work.mkdir(exist_ok=True)
    stages=[]
    for name,m,r in [('before',m0,r0),('after',m1,r1)]:
        folder=work/name;(folder/'results').mkdir(parents=True,exist_ok=True)
        B.ROOT=folder
        if name=='after':B.SHAPES['RFPad']=(FOOTPRINT,PAD['bottom_z_mm'],PAD['installed_thickness_mm'])
        B.save_fields(m,r);stages.append(folder/'results')
        if name=='after':del B.SHAPES['RFPad']
    B.ROOT=ROOT;out=ROOT/'results';before,after=stages
    for filename in ['thermal_surface_mesh.json','mesh_nodes.json']:
        shutil.copyfile(after/filename,out/filename)
    viewer=json.loads((after/'viewer_data.json').read_text());viewer['metadata'].update(description=P['comparison'],pad_absent_case='before',pad_component='RFPad')
    viewer['components']['RFPad']['active_cases']=['after'];viewer['cases']={}
    for label,m,r in [('before',m0,r0),('after',m1,r1)]:
        field=np.full((len(r['times']),m1.n),np.nan,dtype='<f4');field[:,:m.n]=r['field'][:,:,2]
        filename=label+'_temperature_float32.bin';field.tofile(out/filename)
        viewer['cases'][label]={'label':'Before · air gap' if label=='before' else 'After · RF thermal pad','power_W':3.75,'field_file':filename,'encoding':'little-endian float32 [time,node]; absent pad nodes are NaN before installation','shape':list(field.shape),'active_nodes':m.n}
    (out/'viewer_data.json').write_text(json.dumps(viewer,separators=(',',':')))
    for filename in ['component_history.csv','heat_flows.csv','energy_history.csv']:
        with (out/filename).open('w',newline='') as f:
            w=csv.writer(f);header=None
            for label,folder in zip(['before','after'],stages):
                with (folder/filename).open() as src:
                    rows=csv.reader(src);h=next(rows)
                    if header is None:w.writerow(h);header=h
                    for row in rows:
                        if row[0]=='combined':row[0]=label;w.writerow(row)
    for label,folder in zip(['before','after'],stages):
        for filename in ['network_links.csv','heat_source_nodes.csv','mesh_nodes.json']:shutil.copyfile(folder/filename,out/(label+'_'+filename))
    with zipfile.ZipFile(out/'before_after_vtk.zip','w',zipfile.ZIP_DEFLATED) as target:
        target.writestr('README.txt','Layer mid-surface triangles in meters. Open before/transient.pvd and after/transient.pvd. Temperature_C is a layer/package value, not resolved skin/junction temperature. ThermalNode_ID can repeat over several triangles. Before has 9683 nodes, after includes the new RFPad nodes. Other physics matches Stage 03.\n')
        for label,folder in zip(['before','after'],stages):
            with zipfile.ZipFile(folder/'coupled_vtk.zip') as src:
                for name in src.namelist():
                    if name.startswith('combined/'):target.writestr(label+'/'+name.split('/',1)[1],src.read(name))
    shutil.rmtree(work)

def main():
    start=time.perf_counter();print('Reproducing frozen Stage 03 baseline…',flush=True)
    m0=B.Model(P['grid_mm']);r0=m0.run(P['dt_s'])
    reference=np.fromfile(ROOT/'source/reference_stage03_combined_float32.bin',dtype='<f4').reshape((-1,m0.n))
    assert np.array_equal(reference,r0['field'][:,:,2].astype('<f4')),'Baseline changed'
    print('Solving RF pad configuration…',flush=True);m1=PaddedModel(P['grid_mm']);r1=m1.run(P['dt_s'])
    # All old sources, capacities, exterior sinks and unmodified contact links are fixed.
    assert np.array_equal(m0.cap,m1.cap[:m0.n]) and np.array_equal(m0.loss,m1.loss[:m0.n])
    assert np.array_equal(m0.Q,m1.Q[:m0.n]) and np.all(m1.Q[m0.n:]==0)
    unchanged0=[x for x in m0.links if x[3]!='rf_back_gap']
    unchanged1=[x for x in m1.links if x[0]<m0.n and x[1]<m0.n and x[3]!='rf_back_gap']
    assert unchanged0==unchanged1
    superposition=float(np.max(abs((r1['field'][:,:,2]-TA)-(r1['field'][:,:,0]-TA)-(r1['field'][:,:,1]-TA))))
    assert superposition<1e-7
    print('Checking pad model at 1 s and 1 mm…',flush=True);rt=m1.run(P['dt_s']/2,False)
    mf=PaddedModel(P['grid_mm']/2);rf=mf.run(P['dt_s'],False)
    refinements={name:{'mesh_max_difference_K':abs(B.stats(m1,r1['peak'][:,2],name)[2]-B.stats(mf,rf['peak'][:,2],name)[2]),'time_max_difference_K':abs(B.stats(m1,r1['peak'][:,2],name)[2]-B.stats(m1,rt['peak'][:,2],name)[2])} for name in m1.groups}
    assert max(v['mesh_max_difference_K'] for v in refinements.values())<1
    assert max(v['time_max_difference_K'] for v in refinements.values())<.1
    before=component_summary(m0,r0);after=component_summary(m1,r1)
    delta={name:{'mean_change_K':after[name]['at_600s_mean_C']-before[name]['at_600s_mean_C'],'max_change_K':after[name]['at_600s_max_C']-before[name]['at_600s_max_C']} for name in before}
    frozen=json.loads((ROOT/'source/reference_stage03_summary.json').read_text())
    effect_refinement={}
    for name in before:
        fine_change=B.stats(mf,rf['peak'][:,2],name)[2]-frozen['refinement'][name]['fine_max_C']
        coarse_change=delta[name]['max_change_K']
        effect_refinement[name]={'coarse_change_in_max_K':coarse_change,'fine_change_in_max_K':fine_change,'change_in_predicted_effect_K':abs(fine_change-coarse_change)}
    def patch_mean(m,r):
        idx=m.groups['BackGlass'];weights=np.array([m.nodes[a]['poly'].intersection(FOOTPRINT).area for a in idx]);return float(np.average(r['peak'][idx,2],weights=weights))
    area=FOOTPRINT.area*1e-6;rpad=PAD['installed_thickness_mm']*.001/PAD['k_W_mK']
    summary={'study':'Stage 04 RF pad before / after','basis':P['basis'],'comparison':P['comparison'],'pad':PAD,'pad_area_mm2':FOOTPRINT.area,'pad_capacity_J_K':float(m1.cap[m1.groups['RFPad']].sum()),'pad_mass_g':area*PAD['installed_thickness_mm']*.001*PAD['rho_kg_m3']*1000,'pad_bulk_resistance_K_W':rpad/area,'two_contacts_resistance_K_W':2*PAD['contact_resistance_each_m2K_W']/area,'midplane_to_midplane_path_resistance_K_W':(rpad+2*PAD['contact_resistance_each_m2K_W']+.0003/.5+.0004/1)/area,'removed_air_gap_conductance_W_K':m1.removed_gap_conductance_W_K,'before_nodes':m0.n,'after_nodes':m1.n,'pad_nodes':len(m1.groups['RFPad']),'fine_nodes':mf.n,'before':before,'after':after,'change_at_600s':delta,'back_cover_pad_footprint_mean_C':{'before':patch_mean(m0,r0),'after':patch_mean(m1,r1)},'heat_flow_at_600s_W':{'before_RF_to_back_gap_total':float(r0['flows'][20]['rf_back_gap'][2]),'after_RF_to_back_remaining_gap':float(r1['flows'][20]['rf_back_gap'][2]),'after_RF_to_pad':float(r1['flows'][20]['RFPCB_to_pad'][2]),'after_pad_to_back':float(r1['flows'][20]['pad_to_back_cover'][2])},'energy_at_600s_J':{'before':{'input':2250,'stored':r0['energy'][20][2],'ambient_loss':r0['energy'][20][5]},'after':{'input':2250,'stored':r1['energy'][20][2],'ambient_loss':r1['energy'][20][5]}},'verification':{'baseline_float32_byte_identical_to_stage03':True,'old_capacities_sources_and_external_sinks_identical':True,'unmodified_links_identical':True,'before_energy_residual_J':r0['energy_error_J'],'after_energy_residual_J':r1['energy_error_J'],'after_source_superposition_error_K':superposition,'refinement':refinements},'physical_validation':False,'pad_representation':'One through-thickness temperature per planar pad control volume, finite mass, in-plane conduction and two resistive contacts; no compression mechanics','runtime_s':time.perf_counter()-start}
    summary['verification']['effect_mesh_refinement']=effect_refinement
    plot(m0,r0,m1,r1);export(m0,r0,m1,r1)
    (ROOT/'results/summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__':main()
