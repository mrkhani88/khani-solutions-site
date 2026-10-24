"""3D steady anisotropic heat conduction, conforming 8-node brick FEM.
No proprietary geometry. SI units; 2x2x2 Gauss integration, consistent body loads.
Run on Intel: OPENBLAS_NUM_THREADS=1 python3 source/pcb_fem.py
"""
from pathlib import Path
import numpy as np,json,time,hashlib
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import cg,LinearOperator
B=Path(__file__).resolve().parents[1]
parts=[dict(id='CPU',x=[.01,.04],y=[.01,.035],fraction=40/85),dict(id='FPGA',x=[.055,.08],y=[.01,.03],fraction=20/85),dict(id='IO',x=[.01,.035],y=[.045,.07],fraction=15/85),dict(id='Power',x=[.06,.10],y=[.045,.07],fraction=10/85)]
# Bulk device conductivity is an assumed package surrogate, not a junction model.
def brick(h,k):
 signs=np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]])
 K=np.zeros((8,8)); f=np.zeros(8)
 for a in [-1/np.sqrt(3),1/np.sqrt(3)]:
  for b in [-1/np.sqrt(3),1/np.sqrt(3)]:
   for c in [-1/np.sqrt(3),1/np.sqrt(3)]:
    v=np.array([a,b,c]);N=np.prod(1+signs*v,axis=1)/8;grad=np.empty((8,3))
    for d in range(3):grad[:,d]=signs[:,d]/8*np.prod(1+signs[:,[e for e in range(3) if e!=d]]*v[[e for e in range(3) if e!=d]],axis=1)*2/h[d]
    det=np.prod(h)/8;K+=(grad*np.array(k))@grad.T*det;f+=N*det
 return K,f

def solve(level,kz=.69,padk=3,verify=False):
 start=time.monotonic();m=2**level;xs=np.linspace(0,.12,24*m+1);ys=np.linspace(0,.08,16*m+1);zs=np.r_[np.linspace(0,.0005,m+1),np.linspace(.0005,.0025,2*m+1)[1:],np.linspace(.0025,.0045,m+1)[1:]]
 nx,ny,nz=len(xs),len(ys),len(zs);ids=np.arange(nx*ny*nz).reshape(nz,ny,nx);allc=[];tags=[];vol=[];ke=[];fe=[];keys=[]
 cache={};region=[]
 for z in range(nz-1):
  for y in range(ny-1):
   for x in range(nx-1):
    xc=(xs[x]+xs[x+1])/2;yc=(ys[y]+ys[y+1])/2;zc=(zs[z]+zs[z+1])/2
    p=next((i for i,r in enumerate(parts) if r['x'][0]<xc<r['x'][1] and r['y'][0]<yc<r['y'][1]),-1)
    if zc>.0025 and p<0:continue
    tag=0 if zc<.0005 else 1 if zc<.0025 else p+2
    k=(padk,)*3 if tag==0 else (20,20,kz) if tag==1 else (3,)*3
    h=(xs[1]-xs[0],ys[1]-ys[0],zs[z+1]-zs[z]);key=(tag,round(h[2],12))
    if key not in cache:cache[key]=brick(h,k)
    K,f=cache[key];nodes=ids[z:z+2,y:y+2,x:x+2].flatten()[[0,1,3,2,4,5,7,6]]
    allc.append(nodes);tags.append(tag);vol.append(np.prod(h));ke.append(K);fe.append(f);region.append(p)
 conn=np.array(allc);tags=np.array(tags);vol=np.array(vol);fe=np.array(fe);n=nx*ny*nz
 used=np.unique(conn);remap=np.full(n,-1);remap[used]=np.arange(len(used));conn=remap[conn];n=len(used)
 xyz=np.stack(np.meshgrid(xs,ys,zs,indexing='xy'),-1) if False else np.array([(xs[i%nx],ys[(i//nx)%ny],zs[i//(nx*ny)]) for i in used])
 rows=np.repeat(conn,8,axis=1).ravel();cols=np.tile(conn,(1,8)).ravel();K=coo_matrix((np.array(ke).ravel(),(rows,cols)),shape=(n,n)).tocsr();f=np.zeros(n)
 for tag,p in enumerate(parts,2):
  sel=tags==tag;density=p['fraction']/sum(vol[sel]);np.add.at(f,conn[sel].ravel(),(fe[sel]*density).ravel())
 assert abs(sum(f)-1)<1e-10
 fixed=np.where(xyz[:,2]==0)[0];free=np.where(xyz[:,2]>0)[0];A=K[free][:,free];rhs=f[free];count=[0]
 def cb(x):count[0]+=1
 sol,info=cg(A,rhs,rtol=1e-10,atol=1e-13,maxiter=20000,M=LinearOperator(A.shape,matvec=lambda v:v/A.diagonal()),callback=cb);assert info==0,info
 T=np.zeros(n);T[free]=sol;res=K@T-f;reaction=-sum(res[fixed]);err=np.max(abs(res[free]));peak=float(T.max());comp=[]
 for tag,p in enumerate(parts,2):
  ci=np.where(tags==tag)[0];nodes=np.unique(conn[ci]);avg=float(sum(np.mean(T[conn[ci]],axis=1)*vol[ci])/sum(vol[ci]));comp.append(dict(id=p['id'],rise_peak_K_per_W=float(max(T[nodes])),rise_mean_K_per_W=avg,fraction=p['fraction']))
 out=dict(level=level,nodes=n,elements=len(conn),peak_rise_K_per_W=peak,components=comp,reaction_W=float(reaction),source_W=float(sum(f)),relative_energy_error=abs(float(reaction)-sum(f)),free_residual_max_W=float(err),iterations=count[0],elapsed_s=time.monotonic()-start,conductivity_pcb_W_mK=[20,20,kz],pad_k_W_mK=padk,scope='3D steady linear conduction; frozen mission tray boundary; all other faces adiabatic; no junction, convection or radiation model')
 # Top surface strips and board top surface, plus a y=20mm cut, with shared FEM nodal temperatures.
 surfaces=[];skin=[]
 for c,tag in zip(conn,tags):
  ztop=float(xyz[c[4],2]);p=parts[tag-2] if tag>=2 else None
  if tag==1 and abs(ztop-.0025)<1e-10 or tag>=2 and abs(ztop-.0045)<1e-10:
   face=c[[4,5,6,7]];surfaces.append(dict(xyz_mm=(xyz[face]*1000).round(5).tolist(),rise=T[face].round(8).tolist(),region='PCB' if tag==1 else p['id']))
 (B/'spatial').mkdir(exist_ok=True)
 stem='mesh'+str(level)+('_vias' if kz!=.69 else '_pad' if padk!=3 else '')
 np.savez_compressed(B/'spatial'/f'{stem}.npz',xyz_m=xyz,hexahedra=conn,region=tags,rise_K_per_W=T)
 if level==2:
  # Legacy VTK readable in ParaView, FreeCAD FEM or meshio. Full volume field.
  with (B/'spatial'/f'{stem}.vtk').open('w') as g:
   g.write('# vtk DataFile Version 3.0\nRepresentative HAPS compute PCB steady thermal FEM\nASCII\nDATASET UNSTRUCTURED_GRID\nPOINTS %d double\n'%n);np.savetxt(g,xyz,fmt='%.9g');g.write('CELLS %d %d\n'%(len(conn),len(conn)*9));np.savetxt(g,np.column_stack([np.full(len(conn),8),conn]),fmt='%d');g.write('CELL_TYPES %d\n'%len(conn));np.savetxt(g,np.full(len(conn),12),fmt='%d');g.write('POINT_DATA %d\nSCALARS rise_K_per_W double 1\nLOOKUP_TABLE default\n'%n);np.savetxt(g,T,fmt='%.9g')
  (B/'spatial'/f'{stem}-surface.json').write_text(json.dumps(dict(surfaces=surfaces,**out),separators=(',',':')))
 print(stem,json.dumps(out),flush=True);return out

def tests():
 # 1D manufactured solution in a genuinely assembled 3D brick stack.
 L=.003;A=.01*.02;k=2;Q=10;N=8;K=np.zeros(((N+1)*4,)*2);f=np.zeros((N+1)*4)
 for j in range(N):
  ke,fe=brick((.01,.02,L/N),(k,k,k));nodes=np.r_[np.arange(j*4,j*4+4),np.arange((j+1)*4,(j+1)*4+4)];K[np.ix_(nodes,nodes)]+=ke;f[nodes]+=fe*Q/(A*L)
 T=np.zeros(len(f));T[4:]=np.linalg.solve(K[4:,4:],f[4:]);z=np.repeat(np.linspace(0,L,N+1),4);exact=Q/(A*L*k)*(L*z-z*z/2);err=max(abs(T-exact));r=K@T-f
 assert err<1e-9 and abs(-sum(r[:4])-Q)<1e-8
 return dict(test='Uniform volumetric slab heating, insulated top/sides, fixed bottom; exact quadratic nodal solution',max_error_K=float(err),source_W=Q,reaction_W=float(-sum(r[:4])),passed=True)
if __name__=='__main__':
 checks=tests();runs=[solve(i) for i in range(3)];runs += [solve(2,kz=5),solve(2,padk=.5)]
 change=abs(runs[2]['peak_rise_K_per_W']-runs[1]['peak_rise_K_per_W'])/runs[2]['peak_rise_K_per_W'];assert change<.03,change
 report=dict(manufactured_solution=checks,mesh_refinement_relative_peak_change=change,mesh_refinement_pass=change<.03,runs=runs,parts=parts)
 (B/'verification/pcb-fem-audit.json').write_text(json.dumps(report,indent=2))

if __name__=="__main__":
 from export_spatial_surfaces import export
 export()
