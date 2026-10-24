from pathlib import Path
import json,numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
B=Path(__file__).resolve().parents[1];plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.right':False,'axes.spines.top':False,'figure.facecolor':'white'})
S=json.loads((B/'results/summary.json').read_text());V={i:json.loads((B/'results/viewer'/f'{i}.json').read_text()) for i in ['reference','heater3','switch','combined']};C=['#245c7b','#bc532f','#32876f','#7756a7'];names=['Reference','Larger heaters','Radiator switch','Switch + motor heater']
fig,axs=plt.subplots(2,2,figsize=(14,9),sharex=True,constrained_layout=True)
for ax,key,label in zip(axs.flat,['avionics.cpu','battery.core','payload.rf','propulsion.winding'],['Processor aggregate','Battery core','RF aggregate','Motor winding']):
 for (id,v),color,n in zip(V.items(),C,names):ax.plot(v['local_solar_hour'],v['series'][key],color=color,label=n,lw=1.8)
 ax.set(title=label,ylabel='Temperature [°C]',xlim=(0,24),xticks=[0,6,12,18,24]);ax.axvspan(0,6,color='#d7dfeb',alpha=.45);ax.axvspan(18,24,color='#d7dfeb',alpha=.45);ax.grid(alpha=.2);ax.set_xlabel('Local solar time [h]')
axs[0,0].legend(fontsize=9);fig.suptitle('Night thermal control: four controlled designs / final repeated day\nAssumed hardware and mission; numerical results, no physical correlation',fontsize=15);fig.savefig(B/'review/night-control-comparison.png',dpi=150);plt.close(fig)
sel=S[:4];fig,axs=plt.subplots(1,2,figsize=(13,5),constrained_layout=True)
for k,c,label in zip(['avionics','battery','payload','propulsion'],C,['Avionics','Battery','Payload','Motor']):
 values=np.array([s['heaters'][k]['energy_Wh']/1000 for s in sel]);bottom=sum(np.array([s['heaters'][p]['energy_Wh']/1000 for s in sel]) for p in ['avionics','battery','payload','propulsion'][:['avionics','battery','payload','propulsion'].index(k)]) if k!='avionics' else np.zeros(4);axs[0].bar(np.arange(4),values,bottom=bottom,color=c,label=label)
axs[0].set(ylabel='Heater energy [kWh/day]',title='Where heater energy is spent',xticks=np.arange(4),xticklabels=['Reference','Larger\nheaters','Radiator\nswitch','Switch +\nmotor heater']);axs[0].legend(fontsize=9)
axs[1].bar(np.arange(4),[s['load_energy_kWh'] for s in sel],color=C);axs[1].set(ylabel='DC bus demand [kWh/day]',title='System demand includes heater load and conversion loss',xticks=np.arange(4),xticklabels=['Reference','Larger\nheaters','Radiator\nswitch','Switch +\nmotor heater'],ylim=(0,75));fig.suptitle('Energy comparison / identical loads and environment');fig.savefig(B/'review/energy-comparison.png',dpi=150);plt.close(fig)
mission=V['combined'];i=720;tray=mission['series']['avionics.tray'][i];P=mission['series']['cpuPower_W'][i]
fig,axs=plt.subplots(1,3,figsize=(15,5.5),constrained_layout=True)
for ax,stem,title in zip(axs,['mesh2','mesh2_vias','mesh2_pad'],['Nominal board k_z=0.69','Improved effective k_z=5','Degraded pad k=0.5']):
 a=json.loads((B/'spatial'/f'{stem}-surface.json').read_text());faces=[np.array(f['xyz_mm'])[:,:2] for f in a['surfaces'] if f.get('normal',[0,0,1])[2]>0];temp=[tray+P*np.mean(f['rise']) for f in a['surfaces'] if f.get('normal',[0,0,1])[2]>0];pc=PolyCollection(faces,array=np.array(temp),cmap='cividis',clim=(-20,200),edgecolors='none');ax.add_collection(pc);ax.set(xlim=(0,120),ylim=(0,80),aspect='equal',xlabel='x [mm]',ylabel='y [mm]',title=title+'\nPeak %.1f °C'%(tray+P*a['peak_rise_K_per_W']));
 for r in json.loads((B/'verification/pcb-fem-audit.json').read_text())['parts']:ax.text(1000*sum(r['x'])/2,1000*sum(r['y'])/2,r['id'],ha='center',va='center',fontsize=9,color='white',bbox=dict(facecolor='#152b42',alpha=.8,pad=2))
fig.colorbar(pc,ax=axs,shrink=.65,label='Steady bulk temperature [°C]');fig.suptitle('Representative PCB / same noon tray %.1f °C and %.1f W total in every design\nFull 3D conduction solution, shown as a top projection; device junctions are not resolved'%(tray,P),fontsize=13);fig.savefig(B/'review/pcb-thermal-comparison.png',dpi=150);plt.close(fig)
# Through-thickness cut exposes the 3D gradient; dimensions are actual, plotting aspect is stretched.
a=np.load(B/'spatial/mesh2.npz');xyz=a['xyz_m']*1000;mask=np.isclose(xyz[:,1],20);xx=xyz[mask,0];zz=xyz[mask,2];tt=tray+P*a['rise_K_per_W'][mask];import matplotlib.tri as tri
tr=tri.Triangulation(xx,zz);cx=xx[tr.triangles].mean(1);cz=zz[tr.triangles].mean(1);tr.set_mask((cz>2.5)&~(((cx>10)&(cx<40))|((cx>55)&(cx<80))))
fig,ax=plt.subplots(figsize=(12,4),constrained_layout=True);im=ax.tricontourf(tr,tt,levels=np.linspace(-20,200,45),cmap='cividis',extend='both');ax.set(xlabel='x [mm]',ylabel='z [mm]',title='3D FEM section at y=20 mm / vertical axis enlarged for readability');fig.colorbar(im,ax=ax,label='Steady bulk temperature [°C]');fig.savefig(B/'review/pcb-through-thickness.png',dpi=150);plt.close(fig)
(B/'spatial/coupling.json').write_text(json.dumps(dict(coupling='One-way steady frozen-boundary snapshots. Solve linear temperature rise per watt once per physical design; T=Ttray(t)+Pcpu(t)*rise(x). This is not a solved transient PCB field or an improved validated avionics design.',mission='combined',hour=12,tray_C=tray,power_W=P,lumped_cpu_C=mission['series']['avionics.cpu'][i],cases=[dict(stem=stem,title=title) for stem,title in [('mesh2','Nominal board'),('mesh2_vias','Improved effective through-plane path'),('mesh2_pad','Degraded pad')]]),indent=2))
print('Rendered five scientific figures and coupling record')
