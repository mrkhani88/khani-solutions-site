"""Reproducible 3D linear-tetrahedron conduction and small-strain thermoelasticity.
All dimensions, loads, contacts, supports are analyst-selected demonstration inputs.
No manufacturer-specific material/contact/load data or qualification is claimed.
"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
from pathlib import Path
import json,csv,time
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'fea'; OUT.mkdir(exist_ok=True)
E=69e9; nu=.33; alpha=23e-6; k=167.; Tcool=20.; Tref=20.; power=80.
lam=E*nu/((1+nu)*(1-2*nu)); mu=E/(2*(1+nu))
D=np.zeros((6,6)); D[:3,:3]=lam; np.fill_diagonal(D[:3,:3],lam+2*mu); D[3:,3:]=np.eye(3)*mu
def mesh(nx,ny,nz):
    xs=np.linspace(0,.30,nx+1); ys=np.linspace(0,.20,ny+1); zs=np.linspace(0,.006,nz+1)
    xyz=np.array([(x,y,z) for z in zs for y in ys for x in xs]); idx=lambda i,j,l:l*(ny+1)*(nx+1)+j*(nx+1)+i
    pattern=[[0,1,2,6],[0,2,3,6],[0,3,7,6],[0,7,4,6],[0,4,5,6],[0,5,1,6]]
    t=[]
    for l in range(nz):
     for j in range(ny):
      for i in range(nx):
       v=[idx(i,j,l),idx(i+1,j,l),idx(i+1,j+1,l),idx(i,j+1,l),idx(i,j,l+1),idx(i+1,j,l+1),idx(i+1,j+1,l+1),idx(i,j+1,l+1)]
       t.extend([[v[a] for a in q] for q in pattern])
    t=np.array(t); boundary={}
    for tet in t:
      for f in [[0,1,2],[0,1,3],[0,2,3],[1,2,3]]:
        q=tuple(sorted(tet[f])); boundary[q]=boundary.get(q,0)+1
    faces=np.array([f for f,c in boundary.items() if c==1])
    return xyz,t,faces
def prep(xyz,tets):
    a=np.concatenate((np.ones((len(tets),4,1)),xyz[tets]),axis=2)
    inv=np.linalg.inv(a); grads=np.transpose(inv[:,1:,:],(0,2,1)); volumes=np.abs(np.linalg.det(a))/6
    return grads,volumes
def solve_thermal(xyz,tets,faces,h):
    grads,V=prep(xyz,tets); n=len(xyz); rows=[];cols=[]; vals=[]; f=np.zeros(n)
    def add(nodes,a):
      rows.extend(np.repeat(nodes,len(nodes))); cols.extend(np.tile(nodes,len(nodes))); vals.extend(a.ravel())
    for nodes,g,v in zip(tets,grads,V): add(nodes,k*v*g@g.T)
    top=[]; sink=[]
    for face in faces:
      p=xyz[face]; c=p.mean(axis=0); area=np.linalg.norm(np.cross(p[1]-p[0],p[2]-p[0]))/2
      if np.allclose(p[:,2],.006) and .075<c[0]<.225 and .05<c[1]<.15: top.append((face,area))
      if np.allclose(p[:,2],0) and (c[0]<.05 or c[0]>.25): sink.append((face,area))
    heated_area=sum(a for _,a in top); sink_area=sum(a for _,a in sink)
    for face,a in top: f[face]+=power*a/heated_area/3
    for face,a in sink:
      add(face,h*a/12*(np.ones((3,3))+np.eye(3)))
      f[face]+=h*Tcool*a/3
    K=coo_matrix((vals,(rows,cols)),shape=(n,n)).tocsr(); T=spsolve(K,f)
    Q=sum(h*a*(T[face].mean()-Tcool) for face,a in sink)
    residual=np.linalg.norm(K@T-f)/np.linalg.norm(f)
    return T,dict(heater_W=power,rejected_W=float(Q),energy_error_fraction=abs(Q-power)/power,residual_relative=float(residual),heated_area_m2=heated_area,sink_area_m2=sink_area,h_W_m2K=h,peak_C=float(T.max()),min_C=float(T.min()),mean_C=float(T.mean()))
def structural(xyz,tets,T,supports):
    grads,V=prep(xyz,tets); rows=[];cols=[];vals=[]; f=np.zeros(len(xyz)*3); Bs=[]
    for nodes,g,v in zip(tets,grads,V):
      B=np.zeros((6,12))
      for i,(gx,gy,gz) in enumerate(g):
        B[:,i*3:i*3+3]=[[gx,0,0],[0,gy,0],[0,0,gz],[gy,gx,0],[0,gz,gy],[gz,0,gx]]
      dof=(nodes[:,None]*3+np.arange(3)).ravel(); a=v*B.T@D@B
      rows.extend(np.repeat(dof,12));cols.extend(np.tile(dof,12));vals.extend(a.ravel())
      eth=alpha*(T[nodes].mean()-Tref)*np.array([1,1,1,0,0,0]); f[dof]+=v*B.T@D@eth; Bs.append(B)
    K=coo_matrix((vals,(rows,cols)),shape=(len(f),len(f))).tocsr()
    if supports=='both_ends_clamped':
      fixed=(np.where(np.isclose(xyz[:,0],0)|np.isclose(xyz[:,0],.3))[0][:,None]*3+np.arange(3)).ravel()
    else:
      fixed=list(np.where(np.isclose(xyz[:,0],0))[0]*3)
      a=np.argmin(np.linalg.norm(xyz,axis=1)); b=np.argmin(np.linalg.norm(xyz-np.array([0,.2,0]),axis=1));fixed.extend([a*3+1,a*3+2,b*3+2]);fixed=np.array(fixed)
    free=np.setdiff1d(np.arange(len(f)),fixed); u=np.zeros(len(f)); u[free]=spsolve(K[free][:,free],f[free])
    stress=[]
    for nodes,B in zip(tets,Bs):
      dof=(nodes[:,None]*3+np.arange(3)).ravel(); eth=alpha*(T[nodes].mean()-Tref)*np.array([1,1,1,0,0,0]); stress.append(D@(B@u[dof]-eth))
    s=np.array(stress); vm=np.sqrt(.5*((s[:,0]-s[:,1])**2+(s[:,1]-s[:,2])**2+(s[:,2]-s[:,0])**2)+3*(s[:,3:]**2).sum(axis=1))
    ur=u.reshape(-1,3)
    return ur,vm,dict(supports=supports,max_von_mises_MPa=float(vm.max()/1e6),percentile95_von_mises_MPa=float(np.quantile(vm,.95)/1e6),max_displacement_mm=float(np.linalg.norm(ur,axis=1).max()*1000),residual_free_relative=float(np.linalg.norm((K@u-f)[free])/np.linalg.norm(f[free])),fixed_dof_count=len(fixed))
def vtk(name,xyz,tets,T,u,vm):
    p=OUT/(name+'.vtk')
    with p.open('w') as f:
      f.write('# vtk DataFile Version 3.0\nRepresentative plate thermal stress\nASCII\nDATASET UNSTRUCTURED_GRID\nPOINTS %d double\n'%len(xyz)); np.savetxt(f,xyz)
      f.write('CELLS %d %d\n'%(len(tets),len(tets)*5));np.savetxt(f,np.column_stack([np.full(len(tets),4),tets]),fmt='%d');f.write('CELL_TYPES %d\n'%len(tets));np.savetxt(f,np.full(len(tets),10),fmt='%d')
      f.write('POINT_DATA %d\nSCALARS temperature_C double\nLOOKUP_TABLE default\n'%len(xyz));np.savetxt(f,T)
      f.write('VECTORS displacement_m double\n');np.savetxt(f,u)
      f.write('CELL_DATA %d\nSCALARS von_mises_Pa double\nLOOKUP_TABLE default\n'%len(tets));np.savetxt(f,vm)
def plots(xyz,tets,Tlist,vmlist,labels):
    plt.rcParams.update({'font.size':12,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'#f5f8fc'})
    top=np.isclose(xyz[:,2],.006); vmin=min(t.min() for t in Tlist);vmax=max(t.max() for t in Tlist)
    fig,axs=plt.subplots(1,2,figsize=(12.8,5),layout='constrained')
    for ax,T,label in zip(axs,Tlist,labels):
      im=ax.tricontourf(xyz[top,0]*1000,xyz[top,1]*1000,T[top],levels=np.linspace(vmin,vmax,24),cmap='inferno',vmin=vmin,vmax=vmax)
      ax.set_aspect('equal');ax.set_xlabel('Panel X [mm]');ax.set_ylabel('Panel Y [mm]');ax.set_title(label+'\nPeak %.1f °C'%T.max());ax.axvline(50,color='cyan',ls='--',lw=1);ax.axvline(250,color='cyan',ls='--',lw=1)
    fig.colorbar(im,ax=axs,label='Temperature [°C]',shrink=.8);fig.suptitle('80 W equipment panel: contact conductance trade',fontsize=18)
    fig.savefig(OUT/'thermal-comparison.png',dpi=160);fig.savefig(OUT/'thermal-comparison.svg');plt.close(fig)
    cen=xyz[tets].mean(axis=1);fig,axs=plt.subplots(1,2,figsize=(12.8,5),layout='constrained'); vmax=max(v.max() for v in vmlist)/1e6
    for ax,vm,label in zip(axs,vmlist,['Both ends clamped','Kinematic / sliding support']):
      # Mean through-thickness equivalent stress projected to panel; avoid implying surface extraction.
      bins={}
      for (x,y,z),v in zip(cen,vm): bins.setdefault((round(float(x),9),round(float(y),9)),[]).append(v/1e6)
      a=np.array([(x*1000,y*1000,np.mean(v)) for (x,y),v in bins.items()]);im=ax.tricontourf(a[:,0],a[:,1],a[:,2],levels=np.linspace(0,max(vmax,.001),24),cmap='magma',vmin=0,vmax=vmax)
      ax.set_aspect('equal');ax.set_xlabel('Panel X [mm]');ax.set_ylabel('Panel Y [mm]');ax.set_title(label+'\nMax element stress %.1f MPa'%(vm.max()/1e6))
    fig.colorbar(im,ax=axs,label='Through-thickness averaged von Mises [MPa]',shrink=.8);fig.suptitle('Same baseline temperature field, different restraints',fontsize=18)
    fig.savefig(OUT/'stress-comparison.png',dpi=160);fig.savefig(OUT/'stress-comparison.svg');plt.close(fig)
def main():
    start=time.time(); xyz,tets,faces=mesh(24,16,2)
    T0,a0=solve_thermal(xyz,tets,faces,500); T1,a1=solve_thermal(xyz,tets,faces,2000)
    u0,v0,s0=structural(xyz,tets,T0,'both_ends_clamped');u1,v1,s1=structural(xyz,tets,T0,'kinematic_sliding')
    vtk('baseline_clamped',xyz,tets,T0,u0,v0);vtk('baseline_sliding',xyz,tets,T0,u1,v1)
    u2,v2,s2=structural(xyz,tets,T1,'kinematic_sliding');vtk('improved_contact_sliding',xyz,tets,T1,u2,v2)
    xf,tf,ff=mesh(36,24,3); Tf,af=solve_thermal(xf,tf,ff,500)
    uf,vf,sf=structural(xf,tf,Tf,'both_ends_clamped');us,vs,ss=structural(xf,tf,Tf,'kinematic_sliding')
    # Uniform thermal expansion patch test, same weak kinematic support. Exact free expansion from x=0,y=0,z=0.
    tu,tv,ts=structural(xyz,tets,np.full(len(xyz),40.),'kinematic_sliding')
    exact=alpha*20*xyz;patcherr=float(np.linalg.norm(tu-exact)/np.linalg.norm(exact))
    plots(xyz,tets,[T0,T1],[v0,v1],['h = 500 W/(m² K)','h = 2,000 W/(m² K)'])
    summary=dict(solver='Custom 3D linear tetrahedral FEM, Python NumPy/SciPy',thermal_baseline=a0,thermal_improved_contact=a1,structure_clamped=s0,structure_sliding=s1,structure_improved_contact_sliding=s2,mesh=dict(coarse_nodes=len(xyz),coarse_tetrahedra=len(tets),fine_nodes=len(xf),fine_tetrahedra=len(tf),fine_peak_C=float(Tf.max()),peak_delta_C=float(Tf.max()-T0.max()),thermal_fine_energy_error=af['energy_error_fraction'],fine_clamped_max_MPa=sf['max_von_mises_MPa'],fine_clamped_p95_MPa=sf['percentile95_von_mises_MPa'],fine_sliding_max_MPa=ss['max_von_mises_MPa'],fine_sliding_p95_MPa=ss['percentile95_von_mises_MPa']),verification=dict(uniform_expansion_relative_error=patcherr,uniform_expansion_max_stress_Pa=float(tv.max())),runtime_s=time.time()-start,limits=['Assumed flat 300 x 200 x 6 mm aluminium equipment mounting panel, not a flight drawing','Linear elastic small-strain static thermal expansion only. No pressure, launch vibration, fatigue, fasteners, plasticity, buckling or flight allowables.','Maximum clamp-adjacent stresses depend on ideal restraints and mesh. Prefer stress distributions and 95th percentile when discussing design.','Two thermal meshes give an initial sensitivity check, not full convergence proof.','No physical test correlation or manufacturer requirements.'])
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2));(OUT/'assumptions.json').write_text(json.dumps(dict(plate_m=[.3,.2,.006],material='Representative Al6061-like constant isotropic properties',conductivity_W_mK=k,youngs_Pa=E,poisson=nu,expansion_per_K=alpha,total_heat_W=power,heater_patch_m=[.15,.1],coolant_C=Tcool,reference_stressfree_C=Tref,sink_strips='bottom x<0.05m or x>0.25m; effective TIM+coolant contact h=500 or2000W/m2K',references=['https://www.nist.gov/mml/acmd/aluminum-6061-t6-uns-aa96061','https://ntrs.nasa.gov/api/citations/20130010779/downloads/20130010779.pdf']),indent=2))
    with (OUT/'nodal-results.csv').open('w') as f:
      w=csv.writer(f);w.writerow(['x_m','y_m','z_m','T_baseline_C','T_improved_C','u_slide_x_m','u_slide_y_m','u_slide_z_m']);w.writerows(np.column_stack([xyz,T0,T1,u1]))
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
