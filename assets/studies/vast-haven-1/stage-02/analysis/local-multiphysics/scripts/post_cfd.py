from pathlib import Path
import json,re,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'cfd-flatpanel'
def listdata(s,ncomp=1):
    m=re.search(r'\n\s*(\d+)\s*\n\s*\(\s*\n',s)
    if not m: raise ValueError('No Foam data list')
    end=s.index('\n)',m.end()); a=np.fromstring(s[m.end():end].replace('(',' ').replace(')',' '),sep=' ')
    return a.reshape(int(m.group(1)),ncomp).squeeze()
def internal(p,ncomp=1): return listdata(p.read_text().split('boundaryField')[0],ncomp)
def patch(s,key): return re.search(r'\b'+re.escape(key)+r'\s*\{(.*?)\}',s,re.S).group(1)
def phipatch(path,key,n):
    s=patch(path.read_text().split('boundaryField')[1],key)
    if 'nonuniform' in s: return listdata(s)
    return np.full(n,float(re.search(r'value\s+uniform\s+([^;]+)',s).group(1)))
def loglast(p,regexp):
    matches=re.findall(regexp,p.read_text()); return float(matches[-1]) if matches else None
def case(name):
    p=OUT/name; times=sorted([a for a in p.iterdir() if a.is_dir() and re.fullmatch(r'\d+',a.name) and a.name!='0'],key=lambda a:int(a.name)); t=times[-1]
    C=internal(t/'C',3); U=internal(t/'U',3); T=internal(t/'T'); P=internal(t/'p_rgh');owner=listdata((p/'constant/polyMesh/owner').read_text()).astype(int);boundary=(p/'constant/polyMesh/boundary').read_text();a=json.loads((p/'assumptions.json').read_text())
    def bp(n):
      s=patch(boundary,n);return int(re.search(r'nFaces\s+(\d+)',s).group(1)),int(re.search(r'startFace\s+(\d+)',s).group(1))
    n,start=bp('outlet'); op=phipatch(t/'phi','outlet',n);Tc=T[owner[start:start+n]];tout=float(op@Tc/op.sum());n,si=bp('inlet');ip=phipatch(t/'phi','inlet',n)
    dp=float(P[owner[si:si+n]].mean())*a['rho_kg_m3'];heat=float(op.sum()*a['rho_kg_m3']*a['cp_J_kgK']*(tout-a['inlet_K']))
    log=(p/'log.solve').read_text(); residuals={}
    for field in ['Ux','Uy','Uz','T','p_rgh']:
      matches=re.findall(r'Solving for '+field+r', Initial residual = ([\deE.+-]+), Final residual = ([\deE.+-]+)',log);residuals[field]=dict(initial=float(matches[-1][0]),final=float(matches[-1][1]))
    data=dict(case=name,cells=len(T),iteration=int(t.name),inlet_speed_m_s=a['inlet_speed_m_s'],volume_flow_m3_s=float(op.sum()),volume_flow_m3_h=float(op.sum()*3600),mass_balance_fraction=float(abs(op.sum()+ip.sum())/abs(ip.sum())),outlet_mass_weighted_C=tout-273.15,air_cell_peak_C=float(T.max()-273.15),heater_area_average_C=loglast(p/'log.solve',r'areaAverage\(heater\) of T = ([\deE.+-]+)')-273.15,pressure_drop_Pa=dp,air_power_W=float(dp*op.sum()),outlet_sensible_heat_W=heat,imposed_heat_W=a['heat_W'],outlet_heat_closure_fraction=float(abs(heat-a['heat_W'])/a['heat_W']),residuals=residuals,mesh_check_passed='Mesh OK.' in (p/'log.checkMesh').read_text(),iteration_status=('SIMPLE residual-control convergence' if 'SIMPLE solution converged' in log else 'Stopped at fixed iteration cap; convergence requires residual and heat-balance review'))
    with (p/'cell-results.csv').open('w') as f:
      w=csv.writer(f);w.writerow(['x_m','y_m','z_m','Ux_m_s','Uy_m_s','Uz_m_s','T_C','p_Pa']);w.writerows(np.column_stack([C,U,T-273.15,P*a['rho_kg_m3']]))
    return data,(C,U,T,P)
def maps(results):
    plt.rcParams.update({'font.size':12,'axes.spines.top':False,'axes.spines.right':False})
    rows=[results[k] for k in ['baseline','double_flow']];x=np.linspace(0,1.6,200);z=np.linspace(0,.8,100);xx,zz=np.meshgrid(x,z);mask=(xx>.6)&(xx<1)&(zz<.04)
    for field,title,units,filename in [('speed','Forced ventilation: central equipment-bay plane','Velocity [m/s]','velocity-comparison'),('T','Air temperature around the equipment envelope','Air temperature [°C]','temperature-comparison'),('p','Static pressure in the local bay','Gauge pressure [Pa]','pressure-comparison')]:
      fig,axs=plt.subplots(1,2,figsize=(13,5),layout='constrained');vals=[];grids=[]
      for d,(C,U,T,P) in rows:
        sl=abs(C[:,1]-.4)<.04;v=np.linalg.norm(U,axis=1) if field=='speed' else T-273.15 if field=='T' else P*1.2
        gv=griddata(C[sl][:,[0,2]],v[sl],(xx,zz),method='linear');gv[mask]=np.nan;grids.append(gv);vals.extend(v[sl])
      lo=0 if field=='speed' else min(vals);hi=max(vals)
      for ax,(d,(C,U,T,P)),gv in zip(axs,rows,grids):
        im=ax.pcolormesh(xx,zz,gv,cmap='viridis' if field=='speed' else 'inferno' if field=='T' else 'coolwarm',vmin=lo,vmax=hi,shading='auto')
        ax.add_patch(plt.Rectangle((.6,0),.4,.04,color='#3e495a',zorder=4));ax.text(.8,.07,'Equipment envelope',ha='center',va='center',color='white',fontsize=11,zorder=5)
        ax.set_aspect('equal');ax.set_xlabel('Bay X [m]');ax.set_ylabel('Bay Z [m]');ax.set_title('%.0f L/s inlet; %.0f W heat'%(d['volume_flow_m3_s']*1000,d['imposed_heat_W']))
        if field=='speed':
          sl=abs(C[:,1]-.4)<.04;ux=griddata(C[sl][:,[0,2]],U[sl,0],(xx,zz),method='linear');uz=griddata(C[sl][:,[0,2]],U[sl,2],(xx,zz),method='linear');ux[mask]=np.nan;uz[mask]=np.nan;ax.streamplot(x,z,ux,uz,color='white',density=.8,linewidth=.5,arrowsize=.7)
      fig.colorbar(im,ax=axs,label=units,shrink=.7);fig.suptitle(title+'\ng = 0; simplified pressurized cabin bay',fontsize=17);fig.savefig(OUT/(filename+'.png'),dpi=160);fig.savefig(OUT/(filename+'.svg'));plt.close(fig)
def main():
    r={n:case(n) for n in ['baseline','double_flow','mesh_fine','mesh_finer']};maps(r)
    s={n:a[0] for n,a in r.items()};s['mesh_sensitivity']=dict(base_cells=s['baseline']['cells'],fine_cells=s['mesh_fine']['cells'],heater_mean_delta_C=s['mesh_fine']['heater_area_average_C']-s['baseline']['heater_area_average_C'],peak_air_delta_C=s['mesh_fine']['air_cell_peak_C']-s['baseline']['air_cell_peak_C'],outlet_delta_C=s['mesh_fine']['outlet_mass_weighted_C']-s['baseline']['outlet_mass_weighted_C'],pressure_delta_fraction=(s['mesh_fine']['pressure_drop_Pa']/s['baseline']['pressure_drop_Pa']-1))
    s['mesh_sensitivity']['finer_cells']=s['mesh_finer']['cells'];s['mesh_sensitivity']['heater_finer_minus_fine_C']=s['mesh_finer']['heater_area_average_C']-s['mesh_fine']['heater_area_average_C'];s['mesh_sensitivity']['pressure_finer_minus_fine_fraction']=s['mesh_finer']['pressure_drop_Pa']/s['mesh_fine']['pressure_drop_Pa']-1
    (OUT/'summary.json').write_text(json.dumps(s,indent=2));print(json.dumps(s,indent=2))
if __name__=='__main__':main()
