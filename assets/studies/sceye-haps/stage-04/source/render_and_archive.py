from pathlib import Path
import json,numpy as np,hashlib,zipfile,sys,subprocess
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path(__file__).resolve().parents[1];R=B/'results';V=B/'verification';plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white'})
S=json.loads((R/'summary.json').read_text());cs={c['id']:c for c in S};tr={i:json.loads((R/'viewer'/f'{i}.json').read_text()) for i in ['reference','p300','pi']};colors=['#245c7b','#bd5636','#27846c'];names=['Stage03 P30','P300','PI300 / Ki2']
fig,axs=plt.subplots(2,2,figsize=(14,9),constrained_layout=True)
for (id,d),color,n in zip(tr.items(),colors,names):
 t=d['local_solar_hour'];s=d['series'];axs[0,0].plot(t,s['propulsion.housing'],color=color,label=n);axs[0,1].plot(t,s['propulsion.housing'],color=color,label=n);axs[1,0].plot(t,s['propulsion.Pheat'],color=color,label=n);axs[1,1].plot(t,s['heaterEnergy_kWh'],color=color,label=n)
for ax in axs.flat:
 ax.set(xlim=(0,24),xticks=[0,6,12,18,24],xlabel='Local solar time [h]');ax.axvspan(0,6,color='#e3eaf1');ax.axvspan(18,24,color='#e3eaf1');ax.grid(alpha=.2)
for ax in axs[0]:ax.axhline(-5,color='#333',ls='--',lw=1,label='Chosen target −5°C');ax.axhspan(-5.5,-4.5,color='#acd9c5',alpha=.4)
axs[0,0].set(title='Full mission / housing temperature',ylabel='Housing temperature [°C]');axs[0,1].set(title='Cold-target zoom / warm daytime outside range',ylabel='Housing temperature [°C]',ylim=(-12,-3));axs[1,0].axhline(300,color='#333',ls='--',label='Same300W cap');axs[1,0].set(title='Delivered motor heater power',ylabel='Power [W]',ylim=(0,320));axs[1,1].set(title='All heaters / cumulative energy',ylabel='Energy [kWh]');axs[0,0].legend(fontsize=9);axs[1,0].legend(fontsize=9);fig.suptitle('Stage04: fix the control offset with the same thermal hardware\nSaved native OpenModelica final-day results / independent assumed HAPS',fontsize=15);fig.savefig(B/'review/motor-control-comparison.png',dpi=150);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(13,5),constrained_layout=True)
for id,linestyle,color,n in [('cold_p','--','#245c7b','Stage03 / cold'),('cold_pi','-','#27846c','PI / cold'),('pi','-','#775ba5','PI / nominal'),('lag_pi',':','#c5652c','PI /30s sensor lag')]:
 d=json.loads((R/'viewer'/f'{id}.json').read_text());axs[0].plot(d['local_solar_hour'],d['series']['propulsion.housing'],ls=linestyle,color=color,label=n);axs[1].plot(d['local_solar_hour'],d['series']['propulsion.Pheat'],ls=linestyle,color=color,label=n)
for ax in axs:
 ax.set(xlim=(0,24),xlabel='Local solar time [h]',xticks=[0,6,12,18,24]);ax.grid(alpha=.2);ax.axvspan(0,6,color='#e3eaf1');ax.axvspan(18,24,color='#e3eaf1')
axs[0].set(ylim=(-13,-3),ylabel='Housing temperature [°C]',title='Cold-target zoom / fixed300W heater');axs[0].axhline(-5,color='#333',ls='--');axs[0].axhspan(-5.5,-4.5,color='#acd9c5',alpha=.4);axs[0].legend(fontsize=9);axs[1].set(ylabel='Motor heater [W]',ylim=(0,320),title='Colder air and sensor-lag checks');axs[1].axhline(300,color='#333',ls='--');fig.suptitle('Controlled sensitivities, not a complete environmental or fault qualification');fig.savefig(B/'review/motor-control-sensitivities.png',dpi=150);plt.close(fig)
# Preserve a compact set of unchanged full native run archives; all other final-day CSVs are included in the main deliverable.
(B/'native').mkdir(exist_ok=True);runs=json.loads((V/'run-manifest.json').read_text());archives=[]
for r in runs:
 if r['id'] not in ['reference','p300','pi','pi_fine']:continue
 id=r['id'];p=R/r['output'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'];z=B/'native'/f'{id}-full-native.zip'
 with zipfile.ZipFile(z,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as a:
  a.write(p,p.name);a.writestr('case-record.json',json.dumps(r,indent=2).replace(str(B),'${PROJECT_ROOT}'));a.writestr(id+'.log',(V/'native'/f'{id}.log').read_text().replace(str(B),'${PROJECT_ROOT}'))
 with zipfile.ZipFile(z) as a:assert a.testzip() is None
 archives.append(dict(path='native/'+z.name,bytes=z.stat().st_size,sha256=hashlib.sha256(z.read_bytes()).hexdigest(),case=id));print(id,z.stat().st_size,flush=True)
(V/'native-archives.json').write_text(json.dumps(archives,indent=2))
graph=[]
old=B.parent/'stage-03-night-control-spatial-r1'
for cls in ['Avionics','Battery','Payload','Propulsion','HullSolar','Structure','PowerManager','IntegratedMission']:
 g=json.loads((V/f'native-{cls}.json').read_text());o=json.loads((old/'verification'/f'native-{cls}.json').read_text());assert g.get('connections',[])==o.get('connections',[]);graph.append(dict(model=g['name'],connections=len(g.get('connections',[])),unchanged_from_stage03=True))
(V/'native-connection-audit.json').write_text(json.dumps(dict(passed=True,models=graph,change='Only Propulsion.heater class becomes MotorHeater; same physical heat ports and24 thermal capacities.'),indent=2))
(V/'software.json').write_text(json.dumps(dict(OpenModelica=subprocess.check_output(['omc','--version'],text=True).strip(),Python=sys.version,NumPy=np.__version__,execution='Intel Linux; OMP/OpenBLAS threads1, omc numProcs2, Modelica4.1.0'),indent=2))
print('Figures, full native archives and topology audit complete')
