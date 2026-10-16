"""Reproduce Stage 02: 1 W vs 2 W lumped temperatures and a separate 2D heat map.
Dependencies: NumPy, SciPy, Matplotlib. No commercial solver or GPU required.
All inputs are teaching assumptions. The full phone is context CAD, not a solved
assembly. No temperatures are assigned to its unsolved components.
"""
from pathlib import Path
import json,csv,zipfile,platform
import numpy as np
import scipy
from scipy.integrate import solve_ivp
from scipy.sparse import lil_matrix,eye
from scipy.sparse.linalg import factorized
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
for d in ['results','review','evidence','results/vtk']: (ROOT/d).mkdir(parents=True,exist_ok=True)
P=json.loads((ROOT/'source/inputs.json').read_text());S=P['spatial_extension']
w,h,t=[P['geometry_mm'][k]*1e-3 for k in ['width','height','thickness']]
rho=P['density_kg_m3'];cp=P['specific_heat_J_kgK'];he=P['effective_surface_loss_W_m2K']
ta=P['ambient_temperature_C'];assert P['initial_temperature_C']==ta
on=P['heating_duration_s'];end=P['total_duration_s'];q1=P['baseline_heat_W'];q2=P['comparison_heat_W']
C=rho*cp*w*h*t;A=2*(w*h+w*t+h*t);G=he*A;tau=C/G
times=np.arange(0,end+1,1,dtype=float)
def lumped(q):
    def rhs(power):return lambda tt,y:[(power-G*(y[0]-ta))/C,G*(y[0]-ta)]
    a=solve_ivp(rhs(q),(0,on),[ta,0],t_eval=times[times<=on],rtol=1e-10,atol=1e-11)
    b=solve_ivp(rhs(0),(on,end),a.y[:,-1],t_eval=times[times>=on],rtol=1e-10,atol=1e-11)
    assert a.success and b.success
    T=np.r_[a.y[0],b.y[0,1:]];lost=np.r_[a.y[1],b.y[1,1:]]
    inp=q*np.minimum(times,on);stored=C*(T-ta);res=inp-stored-lost
    ana=ta+np.where(times<=on,q/G*(1-np.exp(-times/tau)),q/G*(1-np.exp(-on/tau))*np.exp(-(times-on)/tau))
    assert np.max(np.abs(T-ana))<1e-6 and np.max(np.abs(res))<1e-5
    return dict(T=T,lost=lost,input=inp,stored=stored,analytical_error_K=float(np.max(np.abs(T-ana))),energy_error_J=float(np.max(np.abs(res))))
one,two=lumped(q1),lumped(q2)
linearity=float(np.max(np.abs((two['T']-ta)-2*(one['T']-ta))))
assert linearity<1e-6
with (ROOT/'results/lumped_comparison.csv').open('w',newline='') as f:
    wr=csv.writer(f);wr.writerow(['time_s','stage1_1W_average_C','stage2_2W_average_C','difference_K','stage1_input_J','stage2_input_J','stage1_stored_J','stage2_stored_J','stage1_ambient_loss_J','stage2_ambient_loss_J'])
    wr.writerows(zip(times,one['T'],two['T'],two['T']-one['T'],one['input'],two['input'],one['stored'],two['stored'],one['lost'],two['lost']))
def spatial(nx,ny,dt,fraction,edge_loss=True,store=True):
    dx=w/nx;dy=h/ny;n=nx*ny;cap=rho*cp*dx*dy*t
    K=lil_matrix((n,n));loss=np.full(n,2*he*dx*dy)
    gx=S['kx_W_mK']*t*dy/dx;gy=S['ky_W_mK']*t*dx/dy
    for j in range(ny):
        for i in range(nx):
            a=j*nx+i
            for b,g in [(a+1,gx)] if i<nx-1 else []:
                K[a,a]+=g;K[b,b]+=g;K[a,b]-=g;K[b,a]-=g
            for b,g in [(a+nx,gy)] if j<ny-1 else []:
                K[a,a]+=g;K[b,b]+=g;K[a,b]-=g;K[b,a]-=g
            if edge_loss:
                loss[a]+=(int(i==0)+int(i==nx-1))*he*t*dy/(1+he*dx/(2*S['kx_W_mK']))
                loss[a]+=(int(j==0)+int(j==ny-1))*he*t*dx/(1+he*dy/(2*S['ky_W_mK']))
    K=K.tocsc();K.setdiag(K.diagonal()+loss)
    xx,yy=np.meshgrid((np.arange(nx)+.5)*dx,(np.arange(ny)+.5)*dy)
    patch=S['patch_local_mm'];mask=(xx>=patch['x_min']*.001)&(xx<patch['x_max']*.001)&(yy>=patch['y_min']*.001)&(yy<patch['y_max']*.001)
    assert mask.sum()>0
    source=np.full(n,q2*(1-fraction)/n);source[mask.ravel()]+=q2*fraction/mask.sum()
    assert abs(source.sum()-q2)<1e-10
    L=eye(n,format='csc')*cap+dt/2*K;R=eye(n,format='csc')*cap-dt/2*K;solve=factorized(L)
    theta=np.zeros(n);lost=0.0;maxres=0.0;snaps=[];ts=[];peak_state=None
    for step in range(round(end/dt)+1):
        tt=step*dt
        if abs(tt-on)<1e-7:peak_state=theta.copy()
        if store and abs(tt/S['viewer_interval_s']-round(tt/S['viewer_interval_s']))<1e-7:
            snaps.append((ta+theta).astype(float));ts.append(tt)
        maxres=max(maxres,abs(q2*min(tt,on)-cap*theta.sum()-lost))
        if step==round(end/dt):break
        power=source if tt<on-1e-9 else np.zeros(n)
        nxt=solve(R@theta+dt*power)
        lost+=dt/2*float(loss@(theta+nxt));theta=nxt
    assert theta.min()>-1e-7 and peak_state.min()>-1e-7
    assert maxres<1e-5
    field=np.array(snaps).reshape((-1,ny,nx)) if store else None
    return {'field':field,'time':ts,'peak':ta+peak_state,'final':ta+theta,'energy_error_J':maxres,'source_W':source,'loss':loss,'cap':cap,'nx':nx,'ny':ny,'dx':dx,'dy':dy}
uniform=spatial(S['nx'],S['ny'],S['dt_s'],0)
local=spatial(S['nx'],S['ny'],S['dt_s'],S['localized_fraction'])
# Verify a uniform-temperature limiting case against its analytical slab model.
limit=spatial(12,26,.5,0,edge_loss=False,store=False)
tau_limit=C/(2*he*w*h);expected=ta+q2/(2*he*w*h)*(1-np.exp(-on/tau_limit))
limit_error=float(np.max(np.abs(limit['peak']-expected)));assert limit_error<1e-4
fine=spatial(48,104,.5,S['localized_fraction'],store=False)
timecheck=spatial(S['nx'],S['ny'],1.0,S['localized_fraction'],store=False)
mesh_delta=float(abs(local['peak'].max()-fine['peak'].max()));dt_delta=float(abs(local['peak'].max()-timecheck['peak'].max()))
assert mesh_delta<.05 and dt_delta<.002,(mesh_delta,dt_delta)
frames=np.array(local['time']);sample=frames.astype(int)
viewer={'metadata':{'units':'degC','times_s':frames.tolist(),'nx':S['nx'],'ny':S['ny'],'width_mm':w*1000,'height_mm':h*1000,'thickness_mm':t*1000,'assembly_cell_origin_mm':[6,27,1.75],'ambient_C':ta,'heating_duration_s':on,'mesh_cells':S['nx']*S['ny'],'patch_mm':S['patch_local_mm'],'shared_color_range_C':[25,65],'description':'2D FVM field, uniform through thickness; unsolved CAD components must remain gray'},'cases':{}}
viewer['cases']['one']={'label':'Stage 01 · 1 W · uniform temperature','kind':'lumped','temperature_C':np.round(one['T'][sample],5).tolist()}
viewer['cases']['two']={'label':'Stage 02 · 2 W · uniform temperature','kind':'lumped','temperature_C':np.round(two['T'][sample],5).tolist()}
for key,r,label in [('uniform',uniform,'Spatial control · 2 W · uniform heat source'),('local',local,'Spatial extension · 2 W · localized heat source')]:
    viewer['cases'][key]={'label':label,'kind':'spatial','field_C':np.round(r['field'],5).reshape((len(frames),-1)).tolist(),'mean_C':np.round(r['field'].mean(axis=(1,2)),5).tolist(),'min_C':np.round(r['field'].min(axis=(1,2)),5).tolist(),'max_C':np.round(r['field'].max(axis=(1,2)),5).tolist()}
(ROOT/'results/viewer_data.json').write_text(json.dumps(viewer,separators=(',',':')))
with (ROOT/'results/spatial_statistics.csv').open('w',newline='') as f:
    wr=csv.writer(f);wr.writerow(['time_s','uniform_source_mean_C','uniform_source_min_C','uniform_source_max_C','localized_source_mean_C','localized_source_min_C','localized_source_max_C'])
    for k,tt in enumerate(frames):wr.writerow([tt,*[float(fn(r['field'][k])) for r in [uniform,local] for fn in [np.mean,np.min,np.max]]])
def vtu(r,field):
    nx,ny=r['nx'],r['ny'];points=' '.join(f'{i*r["dx"]:.9g} {j*r["dy"]:.9g} 0' for j in range(ny+1) for i in range(nx+1))
    conn=' '.join(f'{j*(nx+1)+i} {j*(nx+1)+i+1} {(j+1)*(nx+1)+i+1} {(j+1)*(nx+1)+i}' for j in range(ny) for i in range(nx));n=nx*ny
    return f'''<?xml version="1.0"?><VTKFile type="UnstructuredGrid" version="0.1" byte_order="LittleEndian"><UnstructuredGrid><Piece NumberOfPoints="{(nx+1)*(ny+1)}" NumberOfCells="{n}"><Points><DataArray type="Float64" NumberOfComponents="3" format="ascii">{points}</DataArray></Points><Cells><DataArray type="Int32" Name="connectivity" format="ascii">{conn}</DataArray><DataArray type="Int32" Name="offsets" format="ascii">{' '.join(str(4*(i+1)) for i in range(n))}</DataArray><DataArray type="UInt8" Name="types" format="ascii">{' '.join(['9']*n)}</DataArray></Cells><CellData Scalars="Temperature_C"><DataArray type="Float64" Name="Temperature_C" format="ascii">{' '.join(f'{x:.7f}' for x in field.ravel())}</DataArray><DataArray type="Float64" Name="HeatSource_W_per_cell_during_heating" format="ascii">{' '.join(f'{x:.9g}' for x in r['source_W'])}</DataArray></CellData></Piece></UnstructuredGrid></VTKFile>'''
for name,r in [('uniform',uniform),('localized',local)]:
    folder=ROOT/'results/vtk'/name;folder.mkdir(exist_ok=True);datasets=[]
    for k,tt in enumerate(frames):
        if abs(tt/S['vtk_interval_s']-round(tt/S['vtk_interval_s']))>1e-7:continue
        fn=f't_{int(tt):04d}.vtu';(folder/fn).write_text(vtu(r,r['field'][k]));datasets.append(f'<DataSet timestep="{tt:g}" group="" part="0" file="{fn}"/>')
    (folder/'transient.pvd').write_text('<?xml version="1.0"?><VTKFile type="Collection" version="0.1" byte_order="LittleEndian"><Collection>'+''.join(datasets)+'</Collection></VTKFile>')
with zipfile.ZipFile(ROOT/'results/spatial_vtk.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted((ROOT/'results/vtk').rglob('*')):
        if p.is_file():z.write(p,str(p.relative_to(ROOT/'results/vtk')))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'text.color':'#243d50','axes.labelcolor':'#243d50','savefig.facecolor':'white'})
fig,(ax,bx)=plt.subplots(2,1,figsize=(11,7),sharex=True,gridspec_kw={'height_ratios':[2,1]},constrained_layout=True)
for r,color,label,ls in [(one,'#246287','Stage 01: 1 W','-'),(two,'#c47b25','Stage 02: 2 W','--')]:ax.plot(times/60,r['T'],c=color,ls=ls,lw=2.3,label=label)
ax.axhline(ta,c='#667785',ls=':',lw=1.3,label='Ambient 25 °C');ax.axvline(on/60,c='#a9b2b9',ls=':',lw=1)
ax.set(ylabel='Average cell temperature (°C)',title='Stage 02   Double the heat input; keep everything else fixed',ylim=(24,53));ax.legend(frameon=False);ax.grid(axis='y',alpha=.18)
ax.annotate(f'{two["T"].max():.2f} °C',xy=(10,two['T'].max()),xytext=(13,49.5),arrowprops={'arrowstyle':'-','color':'#526b7a'})
ax.annotate(f'{one["T"].max():.2f} °C',xy=(10,one['T'].max()),xytext=(13,37),arrowprops={'arrowstyle':'-','color':'#526b7a'})
for q,color,label,ls in [(q1,'#246287','1 W input','-'),(q2,'#c47b25','2 W input','--')]:bx.step([0,10,10,30],[q,q,0,0],where='post',color=color,lw=2,ls=ls,label=label)
bx.set(xlabel='Time (min)',ylabel='Heat input (W)',xlim=(0,30),ylim=(-.05,2.3));bx.set_xticks([0,5,10,15,20,25,30]);bx.legend(frameon=False);bx.grid(axis='y',alpha=.18)
fig.savefig(ROOT/'review/heat_input_comparison.png',dpi=180);fig.savefig(ROOT/'review/heat_input_comparison.svg');plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(9,6),constrained_layout=True)
for ax,r,title in zip(axs,[uniform,local],['2 W spread uniformly','2 W: 80% in an assumed patch']):
    im=ax.imshow(r['peak'].reshape((S['ny'],S['nx'])),origin='lower',extent=(0,36,0,78),cmap='inferno',vmin=25,vmax=65,interpolation='nearest');ax.set(title=title,xlabel='Cell width (mm)',ylabel='Cell height (mm)')
fig.colorbar(im,ax=axs,label='Temperature at 600 s (°C)',shrink=.8);fig.suptitle('Separate 2D finite-volume extension · same 2 W total',fontsize=14);fig.savefig(ROOT/'review/spatial_heat_maps.png',dpi=180);plt.close(fig)
summary={'stage1_peak_C':float(one['T'].max()),'stage2_peak_C':float(two['T'].max()),'stage1_final_C':float(one['T'][-1]),'stage2_final_C':float(two['T'][-1]),'peak_difference_K':float(two['T'].max()-one['T'].max()),'stage1_rise_K':float(one['T'].max()-ta),'stage2_rise_K':float(two['T'].max()-ta),'time_constant_s':tau,'linearity_max_error_K':linearity,'lumped_energy_error_J':max(one['energy_error_J'],two['energy_error_J']),'spatial_uniform_peak_C':float(uniform['peak'].max()),'spatial_localized_peak_C':float(local['peak'].max()),'spatial_localized_min_at_600_C':float(local['peak'].min()),'spatial_localized_average_at_600_C':float(local['peak'].mean()),'spatial_cells':S['nx']*S['ny'],'spatial_points':(S['nx']+1)*(S['ny']+1),'mesh_peak_difference_K_1248_vs_4992_cells':mesh_delta,'time_step_peak_difference_K_0_5_vs_1_s':dt_delta,'spatial_energy_error_J':max(local['energy_error_J'],uniform['energy_error_J']),'uniform_limiting_case_analytical_error_K':limit_error,'viewer_frames':len(frames),'vtk_frames_per_spatial_case':len(datasets),'physical_validation':False,'assembly_components_thermally_solved':['Effective pouch cell only'],'software':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__}}
(ROOT/'results/summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
