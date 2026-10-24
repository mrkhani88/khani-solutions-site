"""Intel-only numerical work: conservative 3D orthogonal finite-volume conduction.

PCB anisotropy, five isothermal package-case terminals, distributed bottom pad.
Steady terminal Schur complement is exact for the discretized linear model.
Dynamic capacities are a partitioned engineering reduction, checked separately.
Not a junction model, actual ECAD, convection solution, or hardware validation.
"""
from pathlib import Path
import numpy as np,json,time
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import splu
B=Path(__file__).resolve().parents[2]
R=B/'results/engineering';V=B/'verification/engineering';R.mkdir(exist_ok=True,parents=True)
PARTS=[dict(id='tx',label='RF transmitter aggregate',xy=[.018,.078,.018,.072],C=900),dict(id='beamformer',label='Beamforming electronics',xy=[.096,.150,.018,.072],C=550),dict(id='baseband',label='Baseband / network processor',xy=[.168,.222,.018,.072],C=700),dict(id='server',label='Edge server',xy=[.024,.108,.102,.162],C=1300),dict(id='power',label='Payload DC supply',xy=[.144,.222,.108,.162],C=650)]
def solve(nx=40,ny=30,nz=4,kz=.69,pad_t=.0005,pad_k=3,system=False):
    start=time.monotonic();dx=.24/nx;dy=.18/ny;dz=.002/nz;N=nx*ny*nz;nt=N+5
    xyz=np.array([((i+.5)*dx,(j+.5)*dy,(k+.5)*dz) for k in range(nz) for j in range(ny) for i in range(nx)])
    rows=[];cols=[];data=[];diag=np.zeros(nt)
    def link(a,b,g):
        diag[a]+=g;diag[b]+=g;rows.extend((a,b));cols.extend((b,a));data.extend((-g,-g))
    gbase=np.zeros(N);terminal_sets=[]
    for n,(x,y,z) in enumerate(xyz):
        i=n%nx;j=n//nx%ny;k=n//(nx*ny)
        if i+1<nx:link(n,n+1,20*dy*dz/dx)
        if j+1<ny:link(n,n+nx,20*dx*dz/dy)
        if k+1<nz:link(n,n+nx*ny,kz*dx*dy/dz)
        if k==0:gbase[n]=dx*dy/(dz/(2*kz)+pad_t/pad_k);diag[n]+=gbase[n]
    for p,part in enumerate(PARTS):
        a,b,c,d=part['xy'];sel=np.where((xyz[:,0]>=a)&(xyz[:,0]<b)&(xyz[:,1]>=c)&(xyz[:,1]<d)&(xyz[:,2]>.002-dz))[0];terminal_sets.append(sel)
        assert len(sel)>0
        for n in sel:link(n,N+p,dx*dy/(dz/(2*kz)+.0002/3))
    rows.extend(range(nt));cols.extend(range(nt));data.extend(diag)
    K=coo_matrix((data,(rows,cols)),shape=(nt,nt)).tocsc();F=np.zeros((nt,5));F[N:]=np.eye(5)
    theta=splu(K).solve(F);RR=theta[N:];GG=np.linalg.inv(RR);off=GG.copy();np.fill_diagonal(off,0);Gij=-off;Gbase=GG.sum(axis=1)
    assert np.max(abs(RR-RR.T))<1e-9
    assert Gij.min()>-1e-8 and Gbase.min()>0
    residual=float(np.max(abs(K@theta-F)));reactions=gbase@theta[:N]
    centers=np.array([[(p['xy'][0]+p['xy'][1])/2,(p['xy'][2]+p['xy'][3])/2] for p in PARTS]);partition=((xyz[:,:2,None]-centers.T[None,:,:])**2).sum(axis=1).argmin(axis=1)
    C=np.array([p['C'] for p in PARTS],float)+np.bincount(partition,minlength=5)*dx*dy*dz*1850*1000
    case=dict(nx=nx,ny=ny,nz=nz,cells=N,terminal_nodes=5,k_board_W_mK=[20,20,kz],pad_thickness_m=pad_t,pad_k_W_mK=pad_k,R_K_W=RR.tolist(),G_base_W_K=Gbase.tolist(),G_between_W_K=Gij.tolist(),C_J_K=C.tolist(),board_mass_kg=.24*.18*.002*1850,terminal_C_J_K=[p['C'] for p in PARTS],energy_reaction_W_per_unit_source=reactions.tolist(),max_algebraic_residual_W=residual,elapsed_s=time.monotonic()-start)
    if system:return case,K,np.r_[np.full(N,dx*dy*dz*1850*1000),[p['C'] for p in PARTS]]
    return case,xyz,theta,terminal_sets
def slab_test():
    # Same cell-centered stencil on a slab with imposed top flux and bottom Dirichlet.
    n=20;L=.002;k=.69;A=.004;Q=10;dz=L/n;K=np.zeros((n,n));f=np.zeros(n);f[-1]=Q
    for i in range(n-1):g=k*A/dz;K[i,i]+=g;K[i+1,i+1]+=g;K[i,i+1]-=g;K[i+1,i]-=g
    K[0,0]+=2*k*A/dz;T=np.linalg.solve(K,f);exact=Q*(np.arange(n)+.5)*dz/(k*A)
    return dict(description='Cell-centred 3D conduction stencil reduced to analytical flux-heated slab',max_error_K=float(max(abs(T-exact))),reaction_W=float(2*k*A/dz*T[0]),source_W=Q,passed=bool(max(abs(T-exact))<1e-9))
if __name__=='__main__':
    records={};saved={}
    for label,nx,ny,nz,kz,pt,pk in [('baseline_coarse',20,15,2,.69,.0005,3),('improved_coarse',20,15,2,10,.00025,6),('baseline',40,30,4,.69,.0005,3),('baseline_fine',80,60,8,.69,.0005,3),('improved',40,30,4,10,.00025,6),('improved_fine',80,60,8,10,.00025,6)]:
        out,xyz,theta,sets=solve(nx,ny,nz,kz,pt,pk);records[label]=out
        if label in ['baseline_fine','improved_fine']:
            np.savez_compressed(R/(label+'-conduction.npz'),xyz_m=xyz,response_K_per_W=theta,**{f'terminal_{i}':s for i,s in enumerate(sets)})
        print(label,out['cells'],np.diag(out['R_K_W']),flush=True)
    changes={key:float(np.max(abs(np.array(records[key]['R_K_W'])-np.array(records[key+'_fine']['R_K_W'])))/np.max(records[key+'_fine']['R_K_W'])) for key in ['baseline','improved']}
    audit=dict(method='3D conservative cell-centred finite-volume conduction; isothermal case terminals; orthotropic homogeneous PCB; distributed pad to fixed-temperature plate; other external faces adiabatic',limitations=['No ECAD traces or selected packages; no junction-to-case result','Steady conductance reduction exact for discretized model; dynamic lumped capacities are approximate','No CFD, radiation, contact pressure or temperature-dependent materials in spatial submodel'],parts=PARTS,runs=records,refinement_relative_max_R_change=changes,slab_test=slab_test(),refinement_criterion_relative_R=.03,baseline_refinement_pass=changes['baseline']<.03,selected_refinement_pass=changes['improved']<.03,baseline_interpretation='Ordinary-board high-temperature failure screen, not a mesh-qualified hardware prediction',passed=bool(changes['improved']<.03 and slab_test()['passed'] and max(max(abs(np.array(r['energy_reaction_W_per_unit_source'])-1)) for r in records.values())<1e-9))
    (R/'conduction-reduction.json').write_text(json.dumps(audit,indent=2));(V/'conduction-audit.json').write_text(json.dumps(audit,indent=2));assert audit['passed']
