"""Independent network reconstruction, per-cell energy audit and VTK checks."""
from pathlib import Path
import json,csv,zipfile,hashlib,xml.etree.ElementTree as ET
import numpy as np
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import factorized
STAGE=Path(__file__).resolve().parents[1];R=STAGE/'results'
(STAGE/'evidence').mkdir(exist_ok=True)
viewer=json.loads((R/'viewer_data.json').read_text());proof={'cases':{},'physical_validation':False};audit={}
for case,c in viewer['cases'].items():
    nodes=json.loads((R/(case+'_mesh_nodes.json')).read_text());n=len(nodes);C=np.array([x['capacity_J_K'] for x in nodes]);H=np.array([x['ambient_conductance_W_K'] for x in nodes]);Q=np.array([float(x['combined_W_during_heating']) for x in csv.DictReader((R/(case+'_heat_source_nodes.csv')).open())]);assert abs(Q.sum()-3.75)<1e-10
    row=[];col=[];values=[];cell_links={}
    for x in csv.DictReader((R/(case+'_network_links.csv')).open()):
        a,b=int(x['from_node']),int(x['to_node']);g=float(x['conductance_W_K']);assert g>0;row.extend([a,a,b,b]);col.extend([a,b,a,b]);values.extend([g,-g,-g,g]);acell=nodes[a]['component']=='Battery';bcell=nodes[b]['component']=='Battery'
        if acell!=bcell:cell_links.setdefault(x['path'],[]).append((a,b,g*(1 if acell else -1)))
    K=coo_matrix((values,(row,col)),shape=(n,n)).tocsc()+diags(H);assert np.max(abs(np.asarray(K.sum(axis=1)).ravel()-H))<1e-10
    assert sum(H[i] for i,x in enumerate(nodes) if x['component'] not in ['Display','BackGlass','Frame'])==0
    field=np.fromfile(R/c['field_file'],dtype='<f4').reshape(c['shape']);assert np.isfinite(field).all() and field.min()>=25 and field.max()<75
    advance=factorized(diags(C,format='csc')+2*K);theta=np.zeros(n);worst=0.;lost=0.;energy_error=0.;cumulative={k:0. for k in cell_links};cellidx=np.array([i for i,x in enumerate(nodes) if x['component']=='Battery']);pack={k:np.array(v) for k,v in cell_links.items()}
    def cellflows(t):return {k:float(np.sum(v[:,2]*(t[v[:,0].astype(int)]-t[v[:,1].astype(int)]))) for k,v in pack.items()}
    for step in range(901):
        tt=step*2
        if tt%30==0:worst=max(worst,float(np.max(abs(theta+25-field[tt//30]))))
        energy_error=max(energy_error,abs(3.75*min(tt,600)-C@theta-lost))
        if tt==600:
            stored=float(C[cellidx]@theta[cellidx]);assert abs(1200-stored-sum(cumulative.values()))<1e-6
            audit[case]={'sign_convention':'Positive is heat leaving battery. Integrated with solver-consistent backward Euler end-step flows, 0..600 s.','cell_capacity_J_K':float(C[cellidx].sum()),'cell_input_J':1200.,'cell_stored_J':stored,'cell_net_out_J':sum(cumulative.values()),'path_net_out_J':dict(cumulative),'instantaneous_path_net_out_W':cellflows(theta)}
        if tt==1800:break
        theta=advance(C*theta+2*(Q if tt<600 else 0));lost+=2*H@theta
        if tt<600:
            for k,v in cellflows(theta).items():cumulative[k]+=2*v
    assert worst<5e-6 and energy_error<1e-5
    proof['cases'][case]={'nodes':n,'source_W':float(Q.sum()),'reconstruction_error_K':worst,'energy_error_J':energy_error}
with zipfile.ZipFile(R/'adhesive_comparison_vtk.zip') as z:
    assert z.testzip() is None
    for case,c in viewer['cases'].items():
        field=np.fromfile(R/c['field_file'],dtype='<f4').reshape(c['shape']);assert len(ET.fromstring(z.read(case+'/transient.pvd')).findall('.//DataSet'))==31
        for tt in [0,600,1800]:
            root=ET.fromstring(z.read(case+f'/t_{tt:04d}.vtu'));data={a.get('Name'):a.text for a in root.findall('.//CellData/DataArray')};ids=np.fromstring(data['ThermalNode_ID'],sep=' ',dtype=int);T=np.fromstring(data['Temperature_C'],sep=' ');assert len(set(ids))==c['mesh_nodes'] and max(abs(T-field[tt//30,ids]))<5e-6;xyz=np.fromstring(root.find('.//Points/DataArray').text,sep=' ');assert max(xyz)<.15
proof['vtk_times_and_node_mapping_verified']=True
assert hashlib.sha256((STAGE/'source/base_model.py').read_bytes()).hexdigest()=='00a57eefea46705485404243d70306f1e71efab8f808028d3e79d141049819f6'
assert hashlib.sha256((STAGE/'source/pad_model.py').read_bytes()).hexdigest()=='36c007be66e0934be02df061bb2afa46d49efd7103f941268576fadb001711b9'
assert hashlib.sha256((STAGE/'source/run_spreader_study.py').read_bytes()).hexdigest()=='decb3c0db84cebb214444d8d3ca5e773d35a7d38eb37cf9027daa3bdc43c8303'
proof['previous_solver_modules_byte_preserved']=True
assert (R/'reference_temperature_float32.bin').read_bytes()==(STAGE/'source/reference_stage06_temperature_float32.bin').read_bytes();proof['stage06_reference_byte_preserved']=True
(R/'battery_energy_audit.json').write_text(json.dumps(audit,indent=2));(STAGE/'evidence/export-verification.json').write_text(json.dumps(proof,indent=2));print(json.dumps(audit,indent=2));print(json.dumps(proof,indent=2))
