from pathlib import Path
import csv,json,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'plots';OUT.mkdir(exist_ok=True)
D=ROOT/'data';D.mkdir(exist_ok=True)
names=['Avionics','Battery','Payload','Power conversion','ECLSS','Cabin','Wall','Cold plate','Coolant','Radiator','CMGs','Solar arrays','Tank resources']
limits={1:(0,55),2:(10,35),3:(10,40),4:(0,55),5:(5,50),6:(18,27),9:(8,35),11:(0,55),13:(5,40)}
cases=json.loads((ROOT/'cases.json').read_text())
inputs=json.loads((ROOT/'inputs.json').read_text())
labels={'baseline':'6 m² fixed radiator','larger_radiator':'10 m² fixed radiator','cold_fixed':'Low duty: fixed cooling','cold_bypass':'Low duty: modulated bypass','resolution_check':'10 m², 5 s numerical check'}
colors=['#54c9fa','#bd9bff','#ffb36d','#79e1bb','#fb8d9a','#ffe477']
plt.rcParams.update({'figure.facecolor':'#091727','axes.facecolor':'#102237','savefig.facecolor':'#091727','axes.edgecolor':'#698398','axes.labelcolor':'#dfebf4','xtick.color':'#c4d5e4','ytick.color':'#c4d5e4','text.color':'#ecf3f8','grid.color':'#4d6174','grid.alpha':.25,'font.family':'DejaVu Sans','font.size':11,'axes.titleweight':'bold','axes.titlesize':15,'legend.facecolor':'#102237','legend.edgecolor':'#395063'})
def save(fig,name):
 fig.savefig(OUT/(name+'.png'),dpi=160,bbox_inches='tight');fig.savefig(OUT/(name+'.svg'),bbox_inches='tight');plt.close(fig)
def clean(f):
 with open(f) as h:
  reader=csv.DictReader(h);keys=reader.fieldnames;rows=list(reader)
 # Keep final event state at each timestamp. Native CSV remains retained unchanged.
 r={float(x['time']):x for x in rows}
 out={k:np.array([float(r[t][k]) for t in sorted(r)]) for k in keys if k and k in next(iter(r.values()))}
 out['_raw_rows']=rows
 return out
all_data={}
summary={'title':'Haven-1 representative integrated thermal study R1','solver':'OpenModelica DASSL','run_host':'Intel falcon-intel','nodes':13,'duration_s':86400,'time_zero':'Assumed sunrise, every node initially20C','classification':'Uncalibrated public-reference screening. No manufacturer temperatures or qualified design claims.','inputs':'inputs.json','native_model':'source/Haven1Thermal.mo','native_run_script':'source/run.mos','plots':{},'cases':[],'limits_assumed_C':{names[i-1]:{'min':r[0],'max':r[1]} for i,r in limits.items()}}
for c in cases:
 cid=c['id'];x=clean(ROOT/(cid+'_res.csv'));all_data[cid]=x;t=x['time'];last=t>=81000
 cols=['time']+[f'T[{i}]' for i in range(1,14)]+['sunlight','heaterBattery','heaterResources','heaterCoolant','heaterTotal','energyHeaters','powerLoad','powerAvailable','powerPV','powerCharge','powerDischarge','powerBatteryHeat','powerCurtail','batteryEnergy','SOC','radiatorLink','radiatorG','radiatorEmission','wallEmission','arrayEmission','radiatorSolar','radiatorIR','wallSolar','wallIR','arraySolar','arrayIR','energyLoad','energyPV','energyExternal','storedThermal','closureJ','energyEnvironment','wholeEnergyClosureJ']
 with open(D/(cid+'.csv'),'w') as h:
  w=csv.writer(h);w.writerow(cols)
  for j in range(len(t)):w.writerow([format(x[k][j],'.12g') for k in cols])
 nodes=[];fail=[]
 for i,n in enumerate(names,1):
  temp=x[f'T[{i}]']-273.15;entry={'index':i,'name':n,'min_C':float(temp.min()),'max_C':float(temp.max()),'end_C':float(temp[-1]),'last_orbit_min_C':float(temp[last].min()),'last_orbit_max_C':float(temp[last].max())}
  if i in limits:
   lo,hi=limits[i];entry.update({'assumed_min_C':lo,'assumed_max_C':hi,'within_assumed_limits_final_orbit':bool(temp[last].min()>=lo and temp[last].max()<=hi)})
   if not entry['within_assumed_limits_final_orbit']:fail.append(n)
  nodes.append(entry)
 initialEnergy=.8*15*3.6e6
 # Whole-system ledger includes electrical storage plus thermal storage.
 ext=x['radiatorSolar']+x['radiatorIR']+x['wallSolar']+x['wallIR']+x['arraySolar']+x['arrayIR']+480-x['radiatorEmission']-x['wallEmission']-x['arrayEmission']
 # Integration output contains discontinuities; endpoint trapezoids have known finite-output error.
 raw=x['_raw_rows'];rt=np.array([float(r['time']) for r in raw])
 rin=np.array([sum(float(r[k]) for k in ['radiatorSolar','radiatorIR','wallSolar','wallIR','arraySolar','arrayIR'])+480 for r in raw])
 rout=np.array([sum(float(r[k]) for k in ['radiatorEmission','wallEmission','arrayEmission']) for r in raw])
 ext_integral=float(np.trapezoid(rin-rout,rt));gross_input=float(np.trapezoid(rin,rt));global_storage=float(x['storedThermal'][-1]+x['batteryEnergy'][-1]-initialEnergy)
 with open(D/(cid+'-event-rows.csv'),'w') as eh:
  ew=csv.writer(eh);ew.writerow(['time','environment_plus_crew_input_W','total_emission_W','thermal_storage_J','battery_energy_J'])
  for j,r in enumerate(raw):ew.writerow([r['time'],rin[j],rout[j],r['storedThermal'],r['batteryEnergy']])
 periodic_delta=max(abs(float(x[f'T[{i}]'][-1]-np.interp(81000,t,x[f'T[{i}]']))) for i in range(1,14))
 qrad=float(x['energyReject'][-1]) if 'energyReject' in x else 1
 entry={**c,'name':labels[cid],'csv':'data/'+cid+'.csv','nodes':nodes,'heater_energy_kWh':float(x['energyHeaters'][-1]/3.6e6),'heater_peak_W':float(x['heaterTotal'].max()),'coolant_heater_peak_W':float(x['heaterCoolant'].max()),'battery_SOC_min_pct':float(x['SOC'].min()*100),'battery_SOC_end_pct':float(x['SOC'][-1]*100),'electrical_load_energy_kWh':float(x['energyLoad'][-1]/3.6e6),'PV_generated_energy_kWh':float(x['energyPV'][-1]/3.6e6),'max_integrated_thermal_balance_residual_J':float(abs(x['closureJ']).max()),'max_integrated_whole_energy_balance_residual_J':float(abs(x['wholeEnergyClosureJ']).max()),'whole_energy_sampled_balance_residual_kWh':(global_storage-ext_integral)/3.6e6,'sampled_energy_residual_fraction_gross_input':(global_storage-ext_integral)/gross_input,'sampled_energy_method':'Trapezoidal integration of native CSV preserving all duplicate pre/post-event rows; outputs remain finite-time samples.','sampled_energy_csv':'data/'+cid+'-event-rows.csv','last_two_orbits_end_state_max_difference_K':periodic_delta,'unmet_assumed_limits_final_orbit':fail,'reached_end_time':bool(abs(t[-1]-86400)<1e-8),'rows':len(t)}
 summary['cases'].append(entry)
# Compare common grid, exclude at discontinuity? Temp continuous so compare all points.
a=all_data['larger_radiator'];b=all_data['resolution_check']
changes={names[i-1]:float(max(abs(a[f'T[{i}]']-np.interp(a['time'],b['time'],b[f'T[{i}]'])))) for i in range(1,14)}
summary['numerical_check']={'comparison':'10s vs5s maximum step, DASSL tolerance1e-7','temperature_max_abs_delta_K':changes,'worst_delta_K':max(changes.values()),'qualification':'Numerical sensitivity only. No comparison to physical test.'}
# Figure1: native model conceptual view with explicit equation coupled nodes.
fig,ax=plt.subplots(figsize=(15,9));ax.set_xlim(0,15);ax.set_ylim(0,9);ax.axis('off')
ax.text(.3,8.7,'Integrated orbital thermal model',fontsize=24,weight='bold');ax.text(.3,8.18,'13 thermal capacitances + electrical storage and heater control',fontsize=14,color='#a9c8dd')
boxes={'Avionics':(0.5,6.6),'Battery':(0.5,5.35),'Payload':(0.5,4.1),'Power conversion':(0.5,2.85),'CMGs':(0.5,1.6),'Cold plate':(4,4.1),'ECLSS':(4,6.6),'Cabin':(7.4,6.6),'Coolant':(7.4,4.1),'Radiator':(10.8,4.1),'Wall / MLI':(10.8,6.6),'Solar arrays':(10.8,1.6),'Tank resources':(7.4,1.6)}
for n,(x,y) in boxes.items():
 fill='#193b50' if n in ['Cold plate','Coolant','Radiator'] else '#26324d' if n in ['Battery','Solar arrays','Power conversion'] else '#173249'
 ax.add_patch(FancyBboxPatch((x,y),2.6,.8,boxstyle='round,pad=.04',edgecolor='#61a2c7',facecolor=fill,linewidth=1.3));ax.text(x+1.3,y+.4,n,ha='center',va='center',fontsize=12)
def arrow(a,b,col='#66cafa',ls='-'):
 x1,y1=boxes[a];x2,y2=boxes[b];p=(x1+2.6,y1+.4);q=(x2,y2+.4)
 ax.add_patch(FancyArrowPatch(p,q,arrowstyle='<->',mutation_scale=11,linewidth=1.5,color=col,linestyle=ls,connectionstyle='arc3,rad=0'))
for n in ['Avionics','Battery','Payload','Power conversion','CMGs']:arrow(n,'Cold plate')
arrow('Cold plate','Coolant');arrow('Coolant','Radiator');arrow('ECLSS','Cabin');arrow('Cabin','Wall / MLI');arrow('Cabin','Coolant')
ax.text(10.8,3.3,'Radiation to space\nSolar + Earth IR in',fontsize=11,color='#ffce7d');ax.text(7.5,3.3,'Pump heat + proposed\nflow-bypass conductance',fontsize=11,color='#b4d5e8');ax.text(7.5,.8,'Heaters and resource\ntemperature protection',fontsize=11,color='#b4d5e8');ax.text(10.8,.8,'Solar generation\nBattery energy ledger',fontsize=11,color='#c8b3ff')
ax.text(.35,.35,'All hardware sizing, loads, contacts and orbit values are study assumptions. Equation-coupled nodes, no resolved fluid passages.',fontsize=10,color='#9db6ca')
save(fig,'model-diagram');summary['plots']['model_diagram']='plots/model-diagram.png'
# Hotcase2rows: four mission temperatures.
fig,axes=plt.subplots(2,1,figsize=(13,8),sharex=True,sharey=True)
for ax,cid in zip(axes,['baseline','larger_radiator']):
 x=all_data[cid];hh=x['time']/3600
 for i,col in zip([1,2,3,6],colors):ax.plot(hh,x[f'T[{i}]']-273.15,label=names[i-1],color=col,lw=1.8)
 ax.axhline(40,color='#ffb36d',ls=':',lw=1,alpha=.8);ax.axhline(27,color='#79e1bb',ls=':',lw=1,alpha=.8)
 ax.set_title(labels[cid],loc='left');ax.set_ylabel('Temperature (°C)');ax.grid();ax.legend(ncol=4,loc='upper left',fontsize=10)
axes[-1].set_xlabel('Mission time (h), t=0 assumed sunrise');fig.suptitle('Increasing radiator area reduces temperatures, but some assumed limits remain unmet',fontsize=17,y=1.01);fig.tight_layout();save(fig,'hot-case-temperatures');summary['plots']['hot_case_temperatures']='plots/hot-case-temperatures.png'
# Coldcase temp andheat energy
fig,axes=plt.subplots(2,2,figsize=(14,9),sharex=True)
for j,cid in enumerate(['cold_fixed','cold_bypass']):
 x=all_data[cid];hh=x['time']/3600
 for i,col in zip([1,2,3,6],colors):axes[0,j].plot(hh,x[f'T[{i}]']-273.15,color=col,label=names[i-1],lw=1.6)
 axes[0,j].axhline(18,color='#79e1bb',ls=':',lw=1);axes[0,j].set_ylim(0,38);axes[0,j].set_title(labels[cid],loc='left');axes[0,j].legend(ncol=2,fontsize=9);axes[0,j].set_ylabel('Temperature (°C)')
 axes[1,j].plot(hh,x['heaterTotal'],color='#ffb36d',label='Total heater power');axes[1,j].set_ylabel('Heater power (W)');axes[1,j].set_ylim(-20,1050)
 twin=axes[1,j].twinx();twin.plot(hh,x['energyHeaters']/3.6e6,color='#bd9bff',label='Heater energy');twin.set_ylim(-.3,11);twin.set_ylabel('Heater energy (kWh)',color='#bd9bff');axes[1,j].set_xlabel('Mission time (h)');axes[1,j].text(.03,.9,f"24 h heater energy: {x['energyHeaters'][-1]/3.6e6:.2f} kWh",transform=axes[1,j].transAxes,fontsize=12)
for ax in axes.flat:ax.grid()
fig.suptitle('Matched low-duty sensitivity: reducing radiator coupling avoids unnecessary heater use',fontsize=17);fig.tight_layout();save(fig,'cold-bypass-comparison');summary['plots']['cold_bypass_comparison']='plots/cold-bypass-comparison.png'
# electrical actual generation andloads, soc fornominalfinal3orbits
fig,axes=plt.subplots(3,1,figsize=(13,9),sharex=True);x=all_data['larger_radiator'];h=x['time']/3600
axes[0].plot(h,x['powerAvailable']/1000,label='Available PV',color='#ffe477',lw=1);axes[0].plot(h,x['powerPV']/1000,label='Converted PV after curtailment',color='#79e1bb',lw=1.5);axes[0].plot(h,x['powerLoad']/1000,label='Bus load',color='#54c9fa',lw=1.5);axes[0].set_ylabel('Electrical power (kW)');axes[0].legend(ncol=3,fontsize=10)
axes[1].plot(h,x['SOC']*100,color='#bd9bff');axes[1].set_ylabel('Battery SOC (%)');axes[1].set_ylim(70,102)
for i,col in zip([7,10,12],colors):axes[2].plot(h,x[f'T[{i}]']-273.15,label=names[i-1],color=col,lw=1.5)
axes[2].set_ylabel('External nodes (°C)');axes[2].set_xlabel('Mission time (h)');axes[2].legend(ncol=3,fontsize=10)
for ax in axes:ax.grid()
fig.suptitle('Power and thermal resources share the same orbit clock',fontsize=18);fig.tight_layout();save(fig,'power-and-exterior');summary['plots']['power_and_exterior']='plots/power-and-exterior.png'
# Tempmaxbar includeslimits
fig,ax=plt.subplots(figsize=(13,6));idx=np.arange(4);width=.35
for offset,cid,col in [(-width/2,'baseline','#fb8d9a'),(width/2,'larger_radiator','#54c9fa')]:
 x=all_data[cid];vals=[max(x[f'T[{i}]']-273.15) for i in [1,2,3,6]];bars=ax.bar(idx+offset,vals,width,label=labels[cid],color=col)
 for bar,v in zip(bars,vals):ax.text(bar.get_x()+bar.get_width()/2,v+1,f'{v:.1f}',ha='center',fontsize=11)
for xval,i in zip(idx,[1,2,3,6]):ax.plot([xval-.4,xval+.4],[limits[i][1]]*2,color='#ffe477',lw=2)
ax.set_xticks(idx,['Avionics','Battery','Payload','Cabin']);ax.set_ylim(0,92);ax.set_ylabel('24 h maximum temperature (°C)');ax.legend(ncol=2);ax.grid(axis='y');ax.set_title('Yellow lines mark assumed study limits, not Vast requirements',loc='left');save(fig,'temperature-margin');summary['plots']['temperature_margin']='plots/temperature-margin.png'
# Results & inputs easy CSV
with open(ROOT/'results-summary.csv','w') as f:
 w=csv.writer(f);w.writerow(['case','node','min_C','max_C','final_C','last_orbit_min_C','last_orbit_max_C','passes_assumed_final_orbit_limits','heater_kWh','heater_peak_W','min_SOC_pct'])
 for c in summary['cases']:
  for n in c['nodes']:w.writerow([c['id'],n['name'],n['min_C'],n['max_C'],n['end_C'],n['last_orbit_min_C'],n['last_orbit_max_C'],n.get('within_assumed_limits_final_orbit','unassigned'),c['heater_energy_kWh'],c['heater_peak_W'],c['battery_SOC_min_pct']])
with open(ROOT/'input-table.csv','w') as f:
 w=csv.writer(f);w.writerow(['category','parameter','value','unit_or_status'])
 for node in inputs['nodes']:w.writerow(['thermal_capacitance',node['name'],node['capacitance_J_K'],'J/K, analyst assumption'])
 for l in inputs['links']:w.writerow(['conductance',l['from']+' to '+l['to'],l['G_W_K'],'W/K, analyst assumption'])
 for cat in ['orbit','radiation','heat_loads_W','electrical','radiator_link']:
  for key,v in inputs[cat].items():w.writerow([cat,key,v,'see inputs.json for units and provenance'])
summary['findings']=['The6m² assumed radiator baseline exceeds multiple study limits.','10m² cooling materially lowers equipment temperatures but battery,payload andcabin still miss their assumed final-orbit limits.','Matched50%-duty80%-environment sensitivities show fixed cooling needs heater energy; proposed bypass reduces cold-case rejection and heater demand.','No physical test correlation. No final sizing,qualifying margins or mission thermal acceptance.']
(ROOT/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps({'plots':summary['plots'],'case_metrics':[{'id':c['id'],'heater_kWh':c['heater_energy_kWh'],'unmet':c['unmet_assumed_limits_final_orbit']} for c in summary['cases']],'numerical_check':summary['numerical_check']},indent=2))
