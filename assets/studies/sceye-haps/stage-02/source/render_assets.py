from pathlib import Path
import json,math,html,re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path(__file__).resolve().parents[1];R=B/'review';R.mkdir(exist_ok=True)
H=json.loads((B/'inputs/model-hierarchy.json').read_text());N=json.loads((B/'inputs/component-nodes.json').read_text());S=json.loads((B/'results/summary.json').read_text());D=json.loads((B/'results/viewer/reference.json').read_text());x=np.array(D['local_solar_hour']);y=D['series']
P={'avionics':'#23749b','battery':'#737b32','payload':'#a65388','propulsion':'#bd7028','neutral':'#546575'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.labelcolor':'#263e4c','text.color':'#263e4c','axes.edgecolor':'#7f929e','axes.spines.top':False,'axes.spines.right':False,'grid.color':'#dae3e8','grid.linewidth':.6,'lines.linewidth':1.6,'savefig.facecolor':'white'})
fig,axs=plt.subplots(3,2,figsize=(15,11),layout='constrained');axs=axs.ravel()
main=[('avionics.cpu','Processor','avionics','-'),('battery.core','Battery core','battery','--'),('payload.rf','Payload RF','payload','-.'),('propulsion.winding','Motor winding','propulsion',':')]
for key,label,group,ls in main:axs[0].plot(x,y[key],label=label,color=P[group],ls=ls)
axs[0].set(title='Component temperatures',ylabel='Temperature [°C]')
for group in ['avionics','battery','payload','propulsion']:axs[1].plot(x,y[group+'.Pheat'],label=group.title(),color=P[group],ls={'avionics':'-','battery':'--','payload':'-.','propulsion':':'}[group])
axs[1].set(title='Heater power / ideal averaged control',ylabel='Delivered heater power [W]')
axs[2].plot(x,np.array(y['power.Ppv'])/1000,color=P['avionics'],label='PV used');axs[2].plot(x,np.array(y['power.Pload'])/1000,color=P['propulsion'],ls='--',label='DC load (heaters included)');axs[2].set(title='Electrical power',ylabel='Power [kW]')
axs[3].plot(x,np.array(y['battery.SOC'])*100,color=P['battery'],label='Assumed 60 kWh battery');axs[3].set(title='Battery state of charge',ylabel='SOC [%]',ylim=(0,100))
axs[4].plot(x,np.array(y['heaterEnergy'])/1000,color=P['propulsion'],label='Total delivered heat');axs[4].set(title='Cumulative heater energy / reset at day start',ylabel='Heater energy [kWh]',ylim=(0,None))
for key,label,color,ls in [('environment.bus.Tair','Air',P['neutral'],'--'),('hull.gas','Bulk helium',P['avionics'],'-'),('hull.solar','PV / substrate',P['propulsion'],'-.')]:axs[5].plot(x,y[key],label=label,color=color,ls=ls)
axs[5].set(title='Thermal environment and solar laminate',ylabel='Temperature [°C]')
for a in axs:
 a.set(xlim=(0,24),xticks=[0,6,12,18,24],xlabel='Local solar time [h]');a.grid(True);a.axvspan(0,6,color='#d5dfe5',alpha=.25);a.axvspan(18,24,color='#d5dfe5',alpha=.25);a.legend(loc='best',fontsize=8,frameon=False)
fig.suptitle('Integrated HAPS mission · reference case · final repeated 24-hour cycle',fontsize=17,fontweight='bold')
fig.supxlabel('Independent assumed model · OpenModelica on Intel · Numerical verification only; no hardware validation.',fontsize=10)
fig.savefig(R/'mission-reference.png',dpi=150);plt.close(fig)
fig,axs=plt.subplots(3,1,figsize=(14,12),layout='constrained',height_ratios=[1.5,1,1]);labels=['Reference','Heading +90°','Radiators exposed','Air −10 K','Heaters off','Payload ×2','Straps ×0.35'];positions=np.arange(len(S))
for j,(key,label,group,ls) in enumerate(main):
 xp=positions+(j-1.5)*.16;lo=[q['node_temperatures'][key]['min_C'] for q in S];hi=[q['node_temperatures'][key]['max_C'] for q in S]
 axs[0].vlines(xp,lo,hi,color=P[group],linewidth=2);axs[0].scatter(xp,lo,facecolors='white',edgecolors=P[group],s=35,zorder=3);axs[0].scatter(xp,hi,color=P[group],label=label,s=35,zorder=3)
axs[0].set(title='Component temperature ranges / open = minimum, filled = maximum',ylabel='Temperature [°C]');axs[0].axhline(0,color='#657681',linewidth=.7);axs[0].legend(ncol=4,loc='upper left',frameon=False)
for a,key,title,color in [(axs[1],'heater_energy_Wh','Delivered heater energy (part of DC demand)',P['propulsion']),(axs[2],'load_energy_kWh','Total DC-bus demand (includes heaters)',P['avionics'])]:
 vals=[q[key]/1000 if key=='heater_energy_Wh' else q[key] for q in S];a.bar(positions,vals,color=color,width=.6)
 for xx,v in zip(positions,vals):a.text(xx,v+.12,f'{v:.2f}',ha='center',va='bottom',fontsize=10)
 a.set(title=title,ylabel='Energy [kWh / 24 h]',ylim=(0,max(vals)*1.2))
for a in axs:a.set_xticks(positions,labels);a.tick_params(axis='x',rotation=0,labelsize=9);a.grid(axis='y');a.set_axisbelow(True)
fig.suptitle('Controlled mission sensitivities · same 24-hour period',fontsize=17,fontweight='bold');fig.supxlabel('Prescribed forcing and unknown hardware inputs are assumptions. Temperature excursions do not establish functioning hardware.',fontsize=10)
fig.savefig(R/'mission-comparisons.png',dpi=150);plt.close(fig)

sub={'Avionics':'avionics','Battery':'battery','Payload':'payload','Propulsion':'propulsion','HullSolar':'hull','Structure':'structure'}
short={'ThermalMass':'Thermal capacity','Heater':'Heater control','ExternalSurface':'External exchange','Modelica.Thermal.HeatTransfer.Components.ThermalConductor':'Thermal conductance'}
for cls,g in H.items():
 nodes=g['components'];pos={n['name']:(550+1.6*n['position'][0],110+1.35*(140-n['position'][1])) for n in nodes};height=max(600,max((p[1] for p in pos.values()),default=500)+100)
 out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 {height}" role="img" aria-labelledby="title desc"><title id="title">HAPSDiurnal.{cls}: native connection map</title><desc id="desc">Source-derived diagram checked against native OpenModelica model introspection. Rectangles are actual model instances; thermal colors can show selected-time lumped temperatures. Not a screenshot or spatial temperature field.</desc><rect width="1100" height="{height}" fill="#ffffff"/><g font-family="system-ui,sans-serif"><text x="30" y="30" font-size="20" fill="#17394d">HAPSDiurnal.{cls}</text><text x="30" y="52" font-size="13" fill="#506a7b">Native components and connect equations · select a subsystem or thermal node</text>']
 def endpoint(key):
  first=key.split('.')[0]
  if first in pos:return pos[first]
  return (35 if first in ['env','mount'] else 1065,220 if first=='env' else 390)
 for c in g['connections']:
  p1,p2=endpoint(c['a']),endpoint(c['b']);kind='environment' if any(z in (c['a']+' '+c['b']) for z in ['env','bus']) else 'thermal' if any(z in (c['a']+' '+c['b']) for z in ['port','mount','underside']) or c['a']=='hull' or c['b']=='hull' else 'power'
  color={'environment':'#92a4af','thermal':'#b37037','power':'#3d799b'}[kind]
  out.append(f'<path data-connection="{kind}" d="M{p1[0]},{p1[1]} L{p2[0]},{p2[1]}" stroke="{color}" stroke-width="1.5" fill="none" opacity=".65"><title>{html.escape(c["a"]+" ↔ "+c["b"])}</title></path>')
 for n in nodes:
  name=n['name'];typ=n['type'];cx,cy=pos[name];state=sub.get(cls,'')+'.'+name if typ=='ThermalMass' else '';isMain=cls=='IntegratedMission';attrs=f'data-model="{html.escape(typ)}"' if isMain else f'data-state="{html.escape(state)}"' if state else ''
  out.append(f'<g {attrs} tabindex="0" role="button" aria-label="{html.escape(name)}"><rect data-node-fill="" x="{cx-92}" y="{cy-32}" width="184" height="64" rx="7" fill="#edf4f7" stroke="#5e879a"/><text data-node-ink="" x="{cx}" y="{cy-9}" text-anchor="middle" font-size="15" fill="#17394d">{html.escape(name)}</text><text data-node-ink="" x="{cx}" y="{cy+10}" text-anchor="middle" font-size="11" fill="#506a7b">{html.escape(short.get(typ,typ))}</text><text data-node-value="" x="{cx}" y="{cy+26}" text-anchor="middle" font-size="12" fill="#17394d">{("temperature" if state else "open subsystem" if isMain else "source binding")}</text><title>{html.escape(n["declaration"])}</title></g>')
 # Modifier bindings carry controller feedback and local source terms in the native model.
 if cls!='IntegratedMission':
  for n in nodes:
   for par,component,field in re.findall(r'\b(Q|T)=(\w+)\.(\w+)',n['declaration']):
    if component not in pos:continue
    p1,p2=pos[component],pos[n['name']];out.append(f'<path data-connection="binding" d="M{p1[0]},{p1[1]-35} Q{(p1[0]+p2[0])/2},{min(p1[1],p2[1])-65} {p2[0]},{p2[1]-35}" stroke="#7d8791" stroke-dasharray="5 4" stroke-width="1.3" fill="none"><title>Native modifier binding: {html.escape(n["name"]+"."+par+"="+component+"."+field)}</title></path>')
 out.append(f'<text x="30" y="{height-24}" font-size="12" fill="#506a7b">Blue: electrical signals · orange: conservative heat ports · grey: environment / dashed source bindings</text></g></svg>')
 svg=''.join(out).replace('font-size="15"','font-size="23"').replace('font-size="12" fill="#17394d"','font-size="20" fill="#17394d"').replace('<g  tabindex="0" role="button"','<g role="group"')
 (R/('model-'+cls+'.svg')).write_text(svg)
print('Scientific plots and eight native connection maps rendered.')
